import pytest
import unittest
from unittest.mock import Mock, AsyncMock, patch
from app.main import get_health, get_apod
from app.llm import chat_response
from app.request import api_request
from fastapi import HTTPException
from app.main import InMemoryHistory, apod_convo, ApodChatRequestValidation
from langchain_core.messages import HumanMessage 


# Unit testing

# Smoke test
def test_get_health():
    assert get_health() == {"health": "okay"}


def test_chat_response(monkeypatch):

    monkeypatch.setattr("app.llm.GOOGLE_API_KEY", "test-api-key")

    mock_data = ("Test Text.")

    mock_data_2 = ( {
        "input_tokens": 20,
        "output_tokens": 7,
        "total_tokens": 27,
        "input_token_details": {"cache_read": 0}})


    with patch("app.llm.llm") as mock_llm_class:
        fake_response = Mock()

        fake_response.content = mock_data
        fake_response.usage_metadata = mock_data_2

        mock_llm_class.invoke.return_value = fake_response

        response = chat_response(
            external_context = {"context": "external context"}
        )
    assert response == (mock_data, mock_data_2)


# Error testing

# Error 1: payload from api_request call is None
@pytest.mark.asyncio
async def test_apod_no_payload(monkeypatch):
    monkeypatch.setattr("app.main.NASA_API_KEY", "test-nasa-key")
    with patch("app.main.api_request", new_callable=AsyncMock) as mock_response_class:
        
        mock_response_class.side_effect = Exception("apod endpoint call failed")

        with pytest.raises(Exception):

            mock_response_class.return_value = None

            with pytest.raises(Exception) as error:
                await get_apod()

            assert str(error.value) == "There is an issue with this"


# Error 2: No image is returned from Nasa's APOD for whatever reason
@pytest.mark.asyncio
async def test_apod_missing_image(monkeypatch):
    monkeypatch.setattr("app.main.NASA_API_KEY", "test-nasa-key")
    with patch("app.main.api_request", new_callable=AsyncMock) as mock_api:
        mock_api.return_value = {
            "title": "Test",
            "explanation": "Test"
        }

        with pytest.raises(HTTPException) as error:
            await get_apod()

        assert error.value.status_code == 500

# Error 3: An error from the llm call in llm.py propagates to, and is caught in, main.py
@pytest.mark.asyncio
async def test_apod_llm_error(monkeypatch):
    monkeypatch.setattr("app.main.NASA_API_KEY", "test-nasa-key")
    with patch("app.main.api_request", new_callable=AsyncMock) as mock_api:
        with patch("app.main.chat_response") as mock_chat:

            mock_api.return_value = {
                "title": "Test",
                "explanation": "Test explanation",
                "alt": "Test alt text",
                "hdurl": "https://example.com/image.jpg"
            }

            mock_chat.side_effect = RuntimeError("LLM failed")

            with pytest.raises(HTTPException) as error:
                await get_apod()

            assert error.value.status_code == 502


#======================================

# Test the InMemoryHistory class

class TestInMemoryHistory(unittest.TestCase):
    def setUp(self):
        self.memory = InMemoryHistory()
        self.message = HumanMessage(content="Text")

    def test_add_messages(self):
        second_message = HumanMessage(content="Text")
        
        self.memory.add_messages([self.message])
        self.memory.add_messages([second_message])

        self.assertEqual(self.memory.messages, [self.message, second_message])

    def test_clear(self):
        self.memory.add_messages([self.message])
        self.memory.clear()
        self.assertEqual(self.memory.messages, [])


# Test in event of error

# Error 1: payload from api_request call is None
@pytest.mark.asyncio
async def test_apod_convo_llm_error(monkeypatch):
    monkeypatch.setattr("app.main.message_count", 1)

    request = ApodChatRequestValidation(request="Tell me about this pic.")

    with patch("app.main.conversational_rag_chain", new_callable=AsyncMock) as mock_chain:
        mock_chain.invoke.side_effect = RuntimeError("Issue with LLM.")

        with pytest.raises(RuntimeError) as error:
            await apod_convo(request)

        assert str(error.value) == (
            "There was an issue with the LLM API call within the "
            "apod_convo endpoint."
        )

        mock_chain.invoke.assert_called_once()
        