import os
from dotenv import load_dotenv
from .config import llm, SYSTEM_MESSAGE


load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

def chat_response(external_context:dict[str, str]) -> tuple | None:
    """Connects with the Google Gemini API in order to get a llm response for the user's message."""

    try:
        response = llm.invoke(
            [("system", SYSTEM_MESSAGE),
            ("human", f"Answer With the following external context material: {external_context}")]
        )

        return str(response.content), response.usage_metadata
    
    except Exception as e:
        raise RuntimeError("Problem with llm") from e
    