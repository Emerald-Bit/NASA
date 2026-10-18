import pytest
from unittest.mock import Mock, patch
from app.llm import chat_response

# Error testing

# Error 1: The llm api fails in some way
def test_llm_error(monkeypatch):
    monkeypatch.setattr("app.llm.GOOGLE_API_KEY", "test-api-key")
    with patch("app.llm.llm") as mock_llm_class:
        mock_llm_class.invoke.side_effect = Exception("LLM failed")

        with pytest.raises(RuntimeError):
            chat_response({"test": "test"})
