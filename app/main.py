from fastapi import FastAPI, HTTPException
import sys
import os
from dotenv import load_dotenv
import uvicorn
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime
import time
from zoneinfo import ZoneInfo
import logging.config
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from pydantic import BaseModel, Field
from collections.abc import Sequence
from .config import llm, CURRENT_TZ, LOGS_DIR, SESSION_ID, SYSTEM_MESSAGE, API_PERSONALITY
from .request import api_request
from .llm import chat_response


load_dotenv()

# Setting up logging
Path(LOGS_DIR).mkdir(parents=True, exist_ok=True)

logging_config = {
        "version": 1,
    "disable_existing_loggers": False, 
"formatters": {
    "minimal": {
        "format": "%(asctime)s %(message)s",
        "datefmt": "%d-%m-%Y %H:%M:%S",
    },
    "detailed": {
        "format": "%(levelname)s %(asctime)s [%(name)s:%(filename)s:%(funcName)s:%(lineno)d]\n%(message)s\n",
        "datefmt": "%d-%m-%Y %H:%M:%S",
    },
},
"handlers": {
    "console": {
        "class": "logging.StreamHandler",
        "stream": sys.stdout,
        "formatter": "minimal",
        "level": logging.DEBUG,
    },
    "info": {
        "class": "logging.handlers.RotatingFileHandler",
        "filename": Path(LOGS_DIR, "info.log"),
        "maxBytes": 10485760,  # 1 MB
        "backupCount": 10,
        "formatter": "detailed",
        "level": logging.INFO,
    },
    "error": {
        "class": "logging.handlers.RotatingFileHandler",
        "filename": Path(LOGS_DIR, "error.log"),
        "maxBytes": 10485760,  # 1 MB
        "backupCount": 10,
        "formatter": "detailed",
        "level": logging.ERROR,
    },
},
"root": {
    "handlers": ["console", "info", "error"],
    "level": logging.INFO,
    "propagate": True,
    },
}

logging.config.dictConfig(logging_config)
logger = logging.getLogger()


time_zone = ZoneInfo(CURRENT_TZ)
todays_date = datetime.now(tz=time_zone).date() # Time for NASA APOD api calls.
todays_date_time = todays_date.strftime("%d-%m-%Y %H:%M:%S") # Time for logging notes.
apod_parameters = {"date": todays_date,
                   "start_date": None,
                   "end_date": todays_date,
                   "count": None}

logger.info("Starting logging run in main.py\n"
            f"Date and Time: {todays_date_time}")

store = {}

app = FastAPI()

NASA_API_KEY = os.getenv("NASA_API_KEY")

#=======================APOD Endpoint setup============================

class ApodResponseValidation(BaseModel):
    final_message: str
    pic_link: str
    input_tokens: int | None
    output_tokens: int | None
    eclipsed_time: float
    session_id: str

#=======================APOD_convo Endpoint setup======================

class InMemoryHistory(BaseChatMessageHistory, BaseModel):
    """In memory implementation of chat message history."""

    messages: list[BaseMessage] = Field(default_factory=list)

    def add_messages(self, messages: Sequence[BaseMessage]) -> None:
        """Add a list of messages to the store."""
        self.messages.extend(messages)

    def clear(self) -> None:
        self.messages = []

store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryHistory()
    return store[session_id]
    

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_MESSAGE),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}")
    ]
)

chain = prompt | llm

conversational_rag_chain = RunnableWithMessageHistory(
    chain, 
    get_session_history,
    input_messages_key="input",          
    history_messages_key="chat_history" 
)


class ApodChatRequestValidation(BaseModel):
    request: str
    session_id: str | None

class ApodChatResponseValidation(BaseModel):
    message: str | None
    pic_link: str | None
    total_input_tokens: int
    total_output_tokens: int
    message_count: int
    api_personality: str
    session_id: str


async def get_nasa_information(NASA_API_KEY, apod_parameters):

    apod_url = f"https://science.nasa.gov/wp-json/wp/v2/apod-basic?api_key={NASA_API_KEY}"

    payload = await api_request(url=apod_url, parameters=apod_parameters)

    if payload is None:
        logging.error("NASA APOD api call returned with no data. This occurred within the apod_convo endpoint.")
        raise Exception("NASA APOD api call returned with no data. This occurred within the apod_convo endpoint.")
    else:
        external_llm_context = {
            "pic_title": payload.get("title", ""),
            "pic_long_description": payload.get("explanation", ""),
            "pic_short_description": payload.get("alt", ""),
            "pic_link": payload.get("hdurl", "No image found"),
            "input_tokens": payload.get("input_tokens", ""),
            "output_tokens": payload.get("output_tokens", "")
        }
        logging.info("NASA APOD api call was successful and contained data.")

    if external_llm_context["pic_link"] == "No image found":
        logger.error("NASA APOD did not return an image.")
        raise HTTPException(
            status_code=500,
            detail="NASA APOD did not return an image."
        )

    try:
        initial_message = chat_response(external_llm_context)
    except RuntimeError as e:
        logger.error("Problem with llm")
        raise HTTPException(
            status_code=502,
            detail="Problem with llm"
        )

    if initial_message is None:
        logger.error("Google LLM returned with no data.")
        raise HTTPException(
            status_code=503,
            detail="Google LLM returned with no data."
        )

    logger.info("APOD_convo endpoint ran without error.")

    return {
        "message": initial_message[0],
        "pic_link": external_llm_context["pic_link"],
        "input_tokens": int(initial_message[1]["input_tokens"] or 0),
        "output_tokens": int(initial_message[1]["output_tokens"] or 0),
        }


message_count, total_input_tokens, total_output_tokens = 0, 0, 0

#========================================================================

@app.get("/health", 
         description="Check the health of the server.")
def get_health() -> dict[str, str]:
    return {"health": "okay"}


@app.get("/apod",
         response_model=ApodResponseValidation,
         description="Return NASA's astronomy picture of the day.")
async def get_apod():

    start_time = time.time()

    if not NASA_API_KEY:
        logging.error("The API key is missing.")
        raise Exception("The API key is missing.")

    if type(NASA_API_KEY) != str:
        logging.error("The API is malformed, it is not a string type.")
        raise Exception("The API is malformed, it is not a string type.")

    nasa_info = await get_nasa_information(NASA_API_KEY, apod_parameters)

    final_nasa_info = {
        "final_message": nasa_info.get("message"),
        "pic_link": nasa_info.get("pic_link"),
        "input_tokens": nasa_info.get("input_tokens"),
        "output_tokens": nasa_info.get("output_tokens")
    }

    eclipsed_time = float(round((time.time() - start_time), 3))
    logger.info("APOD endpoint ran without error.")
 
    return {
        "final_message": final_nasa_info["final_message"], 
        "pic_link": final_nasa_info["pic_link"], 
        "input_tokens": final_nasa_info["input_tokens"], 
        "output_tokens": final_nasa_info["output_tokens"], 
        "eclipsed_time": eclipsed_time,
        "session_id": SESSION_ID
        }


@app.post("/apod_convo",
          response_model=ApodChatResponseValidation,
          description="Have a convo with the llm regarding NASA's astronomy picture of the day.")
async def apod_convo(request: ApodChatRequestValidation):

    global message_count, total_input_tokens, total_output_tokens

    if request.session_id == None:
                session_id = SESSION_ID
    else:
        session_id = request.session_id

    if message_count == 0:

        results = await get_nasa_information(NASA_API_KEY, apod_parameters)

        message = results.get("message")
        pic_link = results.get("pic_link")

        history = get_session_history(session_id)
        history.add_message(
            AIMessage(content=message)
        )

        message_count += 1

        return {
            "message": message,
            "pic_link": pic_link,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "message_count": message_count,
            "api_personality": API_PERSONALITY,
            "session_id": session_id
        }

    else:
        try:

            history = get_session_history(session_id)

            if not history.messages:
                results = await get_nasa_information(NASA_API_KEY, apod_parameters)
                history.add_message(AIMessage(content=results["message"]))

            llm_response = conversational_rag_chain.invoke(
                {"input": request.request},
                config={"configurable": {"session_id": session_id}}
            )

            total_input_tokens += llm_response.usage_metadata["input_tokens"]
            total_output_tokens += llm_response.usage_metadata["output_tokens"]

            message = llm_response.content

            message_count += 1

        except Exception as e:
            logger.error(f"Problem with LLM call:{e}")
            raise RuntimeError(f"There was an issue with the LLM API call within the apod_convo endpoint.")

        

        return {
            "message": message,
            "pic_link": None,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "message_count": message_count,
            "api_personality": API_PERSONALITY,
            "session_id": session_id
        }


if __name__ == "__main__":
    uvicorn.run(app=app,
                host="127.0.0.1",
                port=8000)

