import pytest
from unittest.mock import Mock, patch
from app.llm import chat_response

# Error testing

# Error 1: The llm api fails in some way
def test_llm_error():
    with patch("app.llm.ChatGoogleGenerativeAI") as mock_llm_class:
        fake_llm = Mock()
        fake_llm.invoke.side_effect = Exception("LLM failed")

        mock_llm_class.return_value = fake_llm

        with pytest.raises(RuntimeError):
            chat_response({"test": "test"})
