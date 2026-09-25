import pytest
from unittest.mock import Mock, patch
from app.request import api_request


# Unit testing

@pytest.mark.asyncio
async def test_api_request():

    mock_data = {
        "title": "Test image",
        "url": "https://example.com/image.jpg"
    }

    fake_response = Mock()
    fake_response.status_code = 200
    fake_response.json.return_value = [mock_data]
    fake_response.text = "text"

    with patch("app.request.requests.get") as mock_get:
        mock_get.return_value = fake_response

        response = await api_request(
            url="https://fake-url.com",
            parameters={}
        )
    assert response == mock_data
