"""
Unit tests for the OpenAIService class that implements AI-powered writing enhancements.
Tests validate core functionality including suggestion generation, chat responses, error handling,
caching, retry logic, and performance metrics tracking.
"""
import pytest  # pytest ^7.0.0
import openai  # openai ^1.0.0
import json  # standard library
import time  # standard library
from unittest.mock import MagicMock  # unittest.mock standard library

from src.backend.core.ai.openai_service import OpenAIService, DEFAULT_MODEL, FALLBACK_MODEL  # src/backend/core/ai/openai_service.py
from src.backend.core.ai.token_optimizer import TokenOptimizer  # src/backend/core/ai/token_optimizer.py
from src.backend.data.redis.caching_service import cache_set, cache_get  # src/backend/data/redis/caching_service.py
from src.backend.tests.conftest import mock_openai_service, mock_redis  # src/backend/tests/conftest.py

TEST_API_KEY = "test-api-key-not-real"
SAMPLE_DOCUMENT = "The company needs to prioritize customer satisfaction and make sure to address all complaints promptly. The big advantage of this approach is that it allows for greater flexibility."
SAMPLE_PROMPT = "Make this text more professional."
SAMPLE_CHAT_MESSAGES = [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "How can I improve my writing?"}]
MOCK_SUGGESTION_RESPONSE = '{"choices": [{"message": {"content": "The company should prioritize customer satisfaction and ensure all complaints are addressed promptly. The significant advantage of this approach is that it allows for greater flexibility."}}]}'
MOCK_CHAT_RESPONSE = '{"choices": [{"message": {"content": "To improve your writing, focus on clarity, conciseness, and coherence. Edit your work for grammar and spelling errors, and vary your sentence structure."}}]}'


def create_mock_openai_response(content: str, response_type: str) -> dict:
    """Creates a mock OpenAI API response for testing

    Args:
        content (str): Content of the response
        response_type (str): Type of response (completion or chat)

    Returns:
        dict: Structured response mimicking OpenAI API format
    """
    if response_type == "completion":
        return {
            "choices": [{"text": content}],
            "usage": {"prompt_tokens": 50, "completion_tokens": 75, "total_tokens": 125},
            "model": DEFAULT_MODEL
        }
    elif response_type == "chat":
        return {
            "choices": [{"message": {"content": content}}],
            "usage": {"prompt_tokens": 50, "completion_tokens": 75, "total_tokens": 125},
            "model": DEFAULT_MODEL
        }
    else:
        raise ValueError("Invalid response_type. Must be 'completion' or 'chat'.")


class TestOpenAIService:
    """Test suite for the OpenAIService class"""

    def test_initialization(self):
        """Tests that the OpenAIService initializes with correct parameters"""
        service = OpenAIService(api_key=TEST_API_KEY, default_model="test_model", fallback_model="test_fallback", max_tokens=1000, temperature=0.5, request_timeout=15, use_cache=False)
        assert service._api_key == TEST_API_KEY
        assert service._default_model == "test_model"
        assert service._fallback_model == "test_fallback"
        assert service._default_max_tokens == 1000
        assert service._default_temperature == 0.5
        assert service._request_timeout == 15
        assert service._use_cache == False
        assert isinstance(service._token_optimizer, TokenOptimizer)

    def test_get_suggestions(self, mock_openai_service):
        """Tests successful generation of writing improvement suggestions"""
        mock_openai = mock_openai_service
        mock_openai.chat.completions.create.return_value = json.loads(MOCK_SUGGESTION_RESPONSE)
        service = OpenAIService(api_key=TEST_API_KEY)
        suggestions = service.get_suggestions(document_content=SAMPLE_DOCUMENT, prompt=SAMPLE_PROMPT)
        mock_openai.chat.completions.create.assert_called_once()
        assert "content" in suggestions["choices"][0]["message"]

    def test_get_chat_response(self, mock_openai_service):
        """Tests chat completion functionality"""
        mock_openai = mock_openai_service
        mock_openai.chat.completions.create.return_value = json.loads(MOCK_CHAT_RESPONSE)
        service = OpenAIService(api_key=TEST_API_KEY)
        response = service.get_chat_response(messages=SAMPLE_CHAT_MESSAGES)
        mock_openai.chat.completions.create.assert_called_once()
        assert "content" in response["choices"][0]["message"]

    def test_stream_response(self, mock_openai_service):
        """Tests streaming response functionality"""
        mock_openai = mock_openai_service
        mock_openai.chat.completions.create.return_value = [{"choices": [{"delta": {"content": "This"}}]}]
        service = OpenAIService(api_key=TEST_API_KEY)
        stream = service.stream_response(messages=SAMPLE_CHAT_MESSAGES)
        chunks = list(stream)
        assert len(chunks) > 0
        assert "content" in chunks[0]

    def test_cache_hit(self, mock_redis, mock_openai_service):
        """Tests cache hit scenario for repeated requests"""
        mock_cache_get = mock_redis
        mock_cache_get.get.return_value = MOCK_SUGGESTION_RESPONSE
        mock_openai = mock_openai_service
        service = OpenAIService(api_key=TEST_API_KEY)
        service._use_cache = True
        suggestions = service.get_suggestions(document_content=SAMPLE_DOCUMENT, prompt=SAMPLE_PROMPT)
        mock_cache_get.get.assert_called_once()
        mock_openai.chat.completions.create.assert_not_called()
        assert "content" in suggestions["choices"][0]["message"]

    def test_cache_miss(self, mock_redis, mock_openai_service):
        """Tests cache miss scenario requiring API call"""
        mock_cache_get = mock_redis
        mock_cache_get.get.return_value = None
        mock_openai = mock_openai_service
        mock_openai.chat.completions.create.return_value = json.loads(MOCK_SUGGESTION_RESPONSE)
        service = OpenAIService(api_key=TEST_API_KEY)
        service._use_cache = True
        suggestions = service.get_suggestions(document_content=SAMPLE_DOCUMENT, prompt=SAMPLE_PROMPT)
        mock_cache_get.get.assert_called_once()
        mock_openai.chat.completions.create.assert_called_once()
        assert "content" in suggestions["choices"][0]["message"]

    def test_retry_logic(self, mock_openai_service):
        """Tests retry logic for transient API errors"""
        mock_openai = mock_openai_service
        mock_openai.chat.completions.create.side_effect = [openai.APIError("Transient error"), json.loads(MOCK_SUGGESTION_RESPONSE)]
        service = OpenAIService(api_key=TEST_API_KEY)
        suggestions = service.get_suggestions(document_content=SAMPLE_DOCUMENT, prompt=SAMPLE_PROMPT)
        assert mock_openai.chat.completions.create.call_count == 2
        assert "content" in suggestions["choices"][0]["message"]

    def test_error_handling(self, mock_openai_service):
        """Tests various error scenarios and handling"""
        mock_openai = mock_openai_service
        mock_openai.chat.completions.create.side_effect = openai.AuthenticationError("Invalid API key")
        service = OpenAIService(api_key=TEST_API_KEY)
        with pytest.raises(ValueError, match="Authentication to OpenAI API failed. Please check your API key."):
            service.get_suggestions(document_content=SAMPLE_DOCUMENT, prompt=SAMPLE_PROMPT)

    def test_fallback_model(self, mock_openai_service):
        """Tests fallback to alternative model when primary fails"""
        mock_openai = mock_openai_service
        mock_openai.chat.completions.create.side_effect = [openai.BadRequestError("Token limit exceeded", response=MagicMock(status_code=400), body=None), json.loads(MOCK_SUGGESTION_RESPONSE)]
        service = OpenAIService(api_key=TEST_API_KEY, default_model="gpt-4", fallback_model="gpt-3.5-turbo")
        suggestions = service.get_suggestions(document_content=SAMPLE_DOCUMENT, prompt=SAMPLE_PROMPT)
        assert mock_openai.chat.completions.create.call_count == 2
        assert "content" in suggestions["choices"][0]["message"]

    def test_token_optimization(self, mock_openai_service, mock_redis):
        """Tests token optimization for large documents"""
        mock_token_optimizer = MagicMock()
        mock_token_optimizer.optimize_prompt.return_value = SAMPLE_DOCUMENT
        mock_openai = mock_openai_service
        mock_openai.chat.completions.create.return_value = json.loads(MOCK_SUGGESTION_RESPONSE)
        service = OpenAIService(api_key=TEST_API_KEY)
        service._token_optimizer = mock_token_optimizer
        suggestions = service.get_suggestions(document_content=SAMPLE_DOCUMENT, prompt=SAMPLE_PROMPT)
        mock_token_optimizer.optimize_prompt.assert_called_once()
        assert "content" in suggestions["choices"][0]["message"]

    def test_performance_metrics(self, mock_openai_service):
        """Tests performance metrics collection"""
        mock_openai = mock_openai_service
        mock_openai.chat.completions.create.return_value = json.loads(MOCK_SUGGESTION_RESPONSE)
        service = OpenAIService(api_key=TEST_API_KEY)
        service.get_suggestions(document_content=SAMPLE_DOCUMENT, prompt=SAMPLE_PROMPT)
        metrics = service.get_performance_metrics()
        assert metrics["request_count"] == 1
        assert metrics["success_count"] == 1
        assert metrics["total_tokens"] > 0
        service.reset_metrics()
        metrics = service.get_performance_metrics()
        assert metrics["request_count"] == 0

    def test_health_check(self, mock_openai_service):
        """Tests the health check functionality"""
        mock_openai = mock_openai_service
        mock_openai.chat.completions.create.return_value = json.loads(MOCK_SUGGESTION_RESPONSE)
        service = OpenAIService(api_key=TEST_API_KEY)
        health = service.health_check()
        assert health["status"] == "ok"
        assert health["api_key_configured"] == True