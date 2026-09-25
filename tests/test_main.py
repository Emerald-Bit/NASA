import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.main import get_health, get_apod
from app.llm import chat_response
from app.request import api_request
from fastapi import HTTPException


# Unit testing

# Smoke test
def test_get_health():
    assert get_health() == {"health": "okay"}


def test_chat_response(monkeypatch):

    monkeypatch.setenv("GOOGLE_API_KEY", "test-api-key")
    monkeypatch.setenv("NASA_API_KEY", "test-nasa-key")

    mock_data = "Test Text."

    with patch("app.llm.ChatGoogleGenerativeAI") as mock_llm_class:
        fake_llm = Mock()
        fake_response = Mock()

        fake_response.content = mock_data
        fake_llm.invoke.return_value = fake_response
        mock_llm_class.return_value = fake_llm

        response = chat_response(
            external_context = {"context": "external context"}
        )
    assert response == mock_data


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
async def test_apod_llm_error():
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
