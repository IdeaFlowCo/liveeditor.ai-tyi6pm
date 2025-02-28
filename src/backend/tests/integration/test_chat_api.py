# pytest==latest - Testing framework for writing and running tests
import pytest
# json==standard library - JSON serialization and deserialization for API payloads
import json
# unittest.mock==standard library - Mocking and patching functionality for tests
import unittest.mock
# time==standard library - Time functions for testing timeouts and delays
import time

# Internal imports
from ..conftest import app, client, auth_header, mock_openai_service, setup_test_user  # Flask application and test client fixtures
from ..conftest import setup_test_db  # Flask application and test client fixtures
from ...api.resources.chat_resource import ANONYMOUS_CHAT_LIMIT, AUTHENTICATED_CHAT_LIMIT  # Rate limit constants for testing rate limiting functionality
from .fixtures.user_fixtures import generate_session_id  # Generate session IDs for anonymous user tests
from ...data.redis.rate_limiter import USER_TYPE_ANONYMOUS, USER_TYPE_AUTHENTICATED  # User type constants for rate limiting tests

# Global constants for testing
CHAT_ENDPOINT = '/api/chat'
CHAT_HISTORY_ENDPOINT = '/api/chat/history'
CHAT_STREAM_ENDPOINT = '/api/chat/stream'
VALID_MESSAGE = "Can you help improve my writing?"
DOCUMENT_CONTENT = "The company needs to prioritize customer satisfaction and make sure to address all complaints promptly."
MOCK_AI_RESPONSE = "I suggest improving your text by using more concise language. For example: The company [-needs to-]{+should+} prioritize customer satisfaction and [-make sure to-]{+ensure+} all complaints are addressed promptly."


def create_chat_payload(message: str, session_id: str = None, conversation_id: str = None, document_id: str = None, document_content: str = None) -> dict:
    """Helper function to create a valid chat request payload for tests"""
    payload = {"message": message}
    if session_id:
        payload["session_id"] = session_id
    if conversation_id:
        payload["conversation_id"] = conversation_id
    if document_id:
        payload["document_id"] = document_id
    elif document_content:
        payload["document_content"] = document_content
    return payload


def send_multiple_requests(client, endpoint: str, payload: dict, headers: dict = None, count: int = 1) -> list:
    """Helper function to send multiple requests to test rate limiting"""
    responses = []
    for _ in range(count):
        response = client.post(endpoint, json=payload, headers=headers)
        responses.append(response)
    return responses


class TestChatAPI:
    """Test class for the chat API endpoints"""

    def test_valid_chat_message(self, client, mock_openai_service):
        """Test sending a valid chat message and receiving a response"""
        mock_openai_service.return_value = {"choices": [{"message": {"content": MOCK_AI_RESPONSE}}]}
        payload = create_chat_payload(message=VALID_MESSAGE, session_id=generate_session_id())
        response = client.post(CHAT_ENDPOINT, json=payload)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "message" in data
        assert "suggestions" in data
        assert data["message"] == MOCK_AI_RESPONSE

    def test_anonymous_chat(self, client, mock_openai_service):
        """Test chat functionality for anonymous users"""
        session_id = generate_session_id()
        payload = create_chat_payload(message=VALID_MESSAGE, session_id=session_id)
        mock_openai_service.return_value = {"choices": [{"message": {"content": MOCK_AI_RESPONSE}}]}
        response = client.post(CHAT_ENDPOINT, json=payload)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["session_id"] == session_id
        assert data["message"] == MOCK_AI_RESPONSE

    def test_authenticated_chat(self, client, mock_openai_service, setup_test_user, auth_header):
        """Test chat functionality for authenticated users"""
        user_id = setup_test_user["_id"]
        payload = create_chat_payload(message=VALID_MESSAGE)
        mock_openai_service.return_value = {"choices": [{"message": {"content": MOCK_AI_RESPONSE}}]}
        response = client.post(CHAT_ENDPOINT, json=payload, headers=auth_header)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "session_id" not in data
        assert data["message"] == MOCK_AI_RESPONSE

    def test_invalid_message(self, client):
        """Test sending an invalid chat message"""
        payload_empty = create_chat_payload(message="")
        response_empty = client.post(CHAT_ENDPOINT, json=payload_empty)
        assert response_empty.status_code == 400
        data_empty = json.loads(response_empty.data)
        assert "Message cannot be empty" in data_empty["message"]

        long_message = "a" * 5000  # Create a message that exceeds the maximum length
        payload_long = create_chat_payload(message=long_message)
        response_long = client.post(CHAT_ENDPOINT, json=payload_long)
        assert response_long.status_code == 400
        data_long = json.loads(response_long.data)
        assert "Message too long" in data_long["message"]

    def test_rate_limiting_anonymous(self, client, mock_openai_service):
        """Test rate limiting for anonymous users"""
        session_id = generate_session_id()
        payload = create_chat_payload(message=VALID_MESSAGE, session_id=session_id)
        mock_openai_service.return_value = {"choices": [{"message": {"content": MOCK_AI_RESPONSE}}]}
        responses = send_multiple_requests(client, CHAT_ENDPOINT, payload, count=ANONYMOUS_CHAT_LIMIT)
        assert all(response.status_code == 200 for response in responses)
        response_limited = client.post(CHAT_ENDPOINT, json=payload)
        assert response_limited.status_code == 429
        data_limited = json.loads(response_limited.data)
        assert "Rate limit exceeded" in data_limited["message"]
        assert response_limited.headers["Retry-After"] is not None
        assert data_limited["remaining"] == 0

    def test_rate_limiting_authenticated(self, client, mock_openai_service, setup_test_user, auth_header):
        """Test rate limiting for authenticated users"""
        payload = create_chat_payload(message=VALID_MESSAGE)
        mock_openai_service.return_value = {"choices": [{"message": {"content": MOCK_AI_RESPONSE}}]}
        responses = send_multiple_requests(client, CHAT_ENDPOINT, payload, headers=auth_header, count=AUTHENTICATED_CHAT_LIMIT)
        assert all(response.status_code == 200 for response in responses)
        response_limited = client.post(CHAT_ENDPOINT, json=payload, headers=auth_header)
        assert response_limited.status_code == 429
        data_limited = json.loads(response_limited.data)
        assert "Rate limit exceeded" in data_limited["message"]
        assert response_limited.headers["Retry-After"] is not None
        assert AUTHENTICATED_CHAT_LIMIT > ANONYMOUS_CHAT_LIMIT

    def test_chat_with_document_context(self, client, mock_openai_service):
        """Test chat with document context provided"""
        mock_openai_service.return_value = {"choices": [{"message": {"content": MOCK_AI_RESPONSE}}]}
        payload = create_chat_payload(message=VALID_MESSAGE, document_content=DOCUMENT_CONTENT)
        response = client.post(CHAT_ENDPOINT, json=payload)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "suggestions" in data
        assert "[-needs to-]{+should+}" in data["message"]

    def test_chat_history(self, client, mock_openai_service):
        """Test retrieving chat history"""
        session_id = generate_session_id()
        conversation_id = str(uuid.uuid4())
        mock_openai_service.return_value = {"choices": [{"message": {"content": MOCK_AI_RESPONSE}}]}
        payload1 = create_chat_payload(message="First message", session_id=session_id, conversation_id=conversation_id)
        response1 = client.post(CHAT_ENDPOINT, json=payload1)
        assert response1.status_code == 200
        payload2 = create_chat_payload(message="Second message", session_id=session_id, conversation_id=conversation_id)
        response2 = client.post(CHAT_ENDPOINT, json=payload2)
        assert response2.status_code == 200
        response_history = client.get(f"{CHAT_HISTORY_ENDPOINT}?conversation_id={conversation_id}")
        assert response_history.status_code == 200
        history_data = json.loads(response_history.data)
        assert "messages" in history_data
        assert len(history_data["messages"]) == 2
        assert history_data["messages"][0]["message"] == "First message"
        assert history_data["messages"][1]["message"] == "Second message"

    def test_streaming_response(self, client, mock_openai_service):
        """Test streaming chat response functionality"""
        mock_openai_service.return_value = iter([
            {"choices": [{"delta": {"content": "This "}}]},
            {"choices": [{"delta": {"content": "is "}}]},
            {"choices": [{"delta": {"content": "a "}}]},
            {"choices": [{"delta": {"content": "streaming "}}]},
            {"choices": [{"delta": {"content": "response."}}]},
            {"choices": [{"delta": {}}], "done": True, "processing_time": 1.234}
        ])
        payload = create_chat_payload(message=VALID_MESSAGE, session_id=generate_session_id())
        response = client.post(CHAT_STREAM_ENDPOINT, json=payload)
        assert response.status_code == 200
        assert response.content_type == "text/event-stream"
        full_response = ""
        for line in response.body.decode().splitlines():
            if line.startswith("{"):
                chunk = json.loads(line)
                if "content" in chunk:
                    full_response += chunk["content"]
        assert "This is a streaming response." in full_response

    def test_error_handling(self, client, mock_openai_service):
        """Test error handling in chat API"""
        mock_openai_service.side_effect = Exception("AI service unavailable")
        payload = create_chat_payload(message=VALID_MESSAGE, session_id=generate_session_id())
        response = client.post(CHAT_ENDPOINT, json=payload)
        assert response.status_code == 500
        data = json.loads(response.data)
        assert "AI service unavailable" in data["message"]