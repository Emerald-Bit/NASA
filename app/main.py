from fastapi import FastAPI, HTTPException
import sys
import os
from dotenv import load_dotenv
import uvicorn
from pydantic import BaseModel
from pathlib import Path
import random
from datetime import datetime
import time
from zoneinfo import ZoneInfo
import logging.config
from .config import CURRENT_TZ, LOGS_DIR, RANDOM_NUMBER
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


if RANDOM_NUMBER < 0.5:
    api_personality = "vader"
else:
    api_personality = "yoda"

app = FastAPI()

NASA_API_KEY = os.getenv("NASA_API_KEY")

class ApodResponseValidation(BaseModel):
    final_message: str
    pic_link: str
    input_tokens: int | None
    output_tokens: int | None
    eclipsed_time: float


@app.get("/health", 
         description="Check the health of the server.")
def get_health() -> dict[str, str]:
    return {"health": "okay"}


@app.get("/apod",
         response_model=ApodResponseValidation,
         description="Return NASA's astronomy picture of the day.")
async def get_apod():

    start_time = time.time()

    # NASA_API_KEY = os.getenv("NASA_API_KEY")


    if not NASA_API_KEY:
        logging.error("The API key is missing.")
        raise Exception("The API key is missing.")

    if type(NASA_API_KEY) != str:
        logging.error("The API is malformed, it is not a string type.")
        raise Exception("The API is malformed, it is not a string type.")

    apod_url = f"https://science.nasa.gov/wp-json/wp/v2/apod-basic?api_key={NASA_API_KEY}"


    payload = await api_request(url=apod_url, parameters=apod_parameters)

    if payload is None:
        logging.error("NASA APOD api call returned with no data.")
        raise Exception("NASA APOD api call returned with no data.")
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
        final_message = chat_response(external_llm_context)
    except RuntimeError as e:
        logger.error("Problem with llm")
        raise HTTPException(
            status_code=502,
            detail="Problem with llm"
        )

    if final_message is None:
        logger.error("Google LLM returned with no data.")
        raise HTTPException(
            status_code=503,
            detail="Google LLM returned with no data."
        )

    eclipsed_time = float(round((time.time() - start_time), 3))
    logger.info("APOD endpoint ran without error.")
 
    return {
        "final_message": final_message[0],
        "pic_link": external_llm_context["pic_link"],
        "input_tokens": int(final_message[1]["input_tokens"] or 0),
        "output_tokens": int(final_message[1]["output_tokens"] or 0),
        "eclipsed_time": eclipsed_time
        }

if __name__ == "__main__":
    uvicorn.run(app=app,
                host="127.0.0.1",
                port=8000)
