from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
from .config import SYSTEM_MESSAGE, LLM_MODEL, LLM_TEMPERATURE, LLM_TIMEOUT, LLM_MAX_RETRIES, LLM_MAX_TOKENS



load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


if not GOOGLE_API_KEY:
    raise RuntimeError("The API key is missing.")

if not isinstance(SYSTEM_MESSAGE, str):
    raise TypeError("The system message for the llm not a 'str' type.")


def chat_response(external_context:dict[str, str]) -> str | None:
    """Connects with the Google Gemini API in order to get a llm response for the user's message."""

    try:
        llm = ChatGoogleGenerativeAI(
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            timeout=LLM_TIMEOUT,
            max_retries=LLM_MAX_RETRIES,
            max_tokens=LLM_MAX_TOKENS,
            google_api_key=GOOGLE_API_KEY
        )

        response = llm.invoke(
            [("system", SYSTEM_MESSAGE),
            ("human", f"Answer With the following external context material: {external_context}")]
        )

        return str(response.content)
    
    except Exception as e:
        raise RuntimeError("Problem with llm") from e
    