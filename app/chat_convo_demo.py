import uuid
from langchain_core.runnables import RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from pydantic import BaseModel, Field
from collections.abc import Sequence
from .llm import chat_response
from .config import LLM_MODEL, LLM_TEMPERATURE, LLM_TIMEOUT, LLM_MAX_RETRIES, LLM_MAX_TOKENS, RANDOM_NUMBER
import os
from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn


load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

session_id = uuid.uuid4()

app = FastAPI()

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
        ("system", "You're an assistant"),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}")
    ]
)


chain = prompt | ChatGoogleGenerativeAI(
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            timeout=LLM_TIMEOUT,
            max_retries=LLM_MAX_RETRIES,
            max_tokens=LLM_MAX_TOKENS,
            google_api_key=GOOGLE_API_KEY
        )


conversational_rag_chain = RunnableWithMessageHistory(
    chain, 
    get_session_history,
    input_messages_key="input",        
    history_messages_key="chat_history" 
)

class ChatRequest(BaseModel):
    input: str

message_count, total_input_tokens, total_output_tokens = 0, 0, 0

@app.post("/test")
def test_endpoint(request: ChatRequest):

    global message_count, total_input_tokens, total_output_tokens

    message_count += 1

    llm_response = conversational_rag_chain.invoke(
        {"input": request.input},
        config={"configurable": {"session_id": str(session_id)}}
    )

    total_input_tokens += llm_response.usage_metadata["input_tokens"]
    total_output_tokens += llm_response.usage_metadata["output_tokens"]

    return llm_response.content, total_input_tokens, total_output_tokens, message_count

if __name__ == "__main__":
    uvicorn.run(
        app=app,
        host="127.0.0.1",
        port=8000
        )
