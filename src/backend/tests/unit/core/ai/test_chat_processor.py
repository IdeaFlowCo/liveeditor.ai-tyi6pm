"""
Unit tests for the ChatProcessor class that handles chat interactions between users and the AI assistant,
validating message processing, response generation, suggestion extraction, and conversation management.
"""
import unittest.mock  # Mocking library for isolating the unit under test
import json  # JSON serialization/deserialization for testing responses
import asyncio  # Testing asynchronous streaming functionality
import time  # Measuring processing time in tests
import pytest  # Testing framework for writing and running tests

from src.backend.core.ai.chat_processor import ChatProcessor, ChatProcessingError, extract_suggestions, sanitize_message  # The main class being tested
from src.backend.core.ai.openai_service import OpenAIService  # Dependency for interacting with OpenAI API
from src.backend.core.ai.context_manager import ContextManager  # Dependency for managing conversation context
from src.backend.core.ai.token_optimizer import TokenOptimizer  # Dependency for optimizing token usage
from src.backend.core.ai.prompt_manager import PromptManager  # Dependency for managing AI prompts
from src.backend.data.mongodb.repositories.ai_interaction_repository import AIInteractionRepository  # Dependency for storing chat interactions
from src.backend.tests.fixtures.suggestion_fixtures import track_changes_data  # Test fixture for track changes format data
from src.backend.tests.conftest import mock_openai_service  # Fixture for mocking OpenAI service

TEST_SESSION_ID = "test-session-123"
TEST_CONVERSATION_ID = "test-conversation-456"
TEST_USER_ID = "test-user-789"
TEST_DOCUMENT_ID = "test-document-abc"
TEST_MESSAGE = "How can I improve this document?"
TEST_DOCUMENT_CONTENT = "The company needs to prioritize customer satisfaction and make sure to address all complaints promptly. The big advantage of this approach is that it allows for greater flexibility."
SAMPLE_AI_RESPONSE = "I suggest making the following improvements to your document: The company [-needs to-]{+should+} prioritize customer satisfaction and [-make sure to-]{+ensure+} address all complaints promptly. The [-big-]{+significant+} advantage of this approach is that it allows for greater flexibility."
SAMPLE_SYSTEM_INSTRUCTION = "You are an AI writing assistant helping to improve documents. Be helpful, concise, and focus on the user's specific questions about their document."


def test_chat_processor_init():
    """Tests initialization of ChatProcessor with dependencies"""
    # Create mock objects for all dependencies (OpenAIService, ContextManager, etc.)
    mock_openai_service = unittest.mock.Mock(OpenAIService)
    mock_context_manager = unittest.mock.Mock(ContextManager)
    mock_token_optimizer = unittest.mock.Mock(TokenOptimizer)
    mock_prompt_manager = unittest.mock.Mock(PromptManager)
    mock_repository = unittest.mock.Mock(AIInteractionRepository)

    # Initialize ChatProcessor with mock dependencies
    chat_processor = ChatProcessor(
        openai_service=mock_openai_service,
        context_manager=mock_context_manager,
        token_optimizer=mock_token_optimizer,
        prompt_manager=mock_prompt_manager,
        repository=mock_repository
    )

    # Assert that all dependencies are properly stored as instance variables
    assert chat_processor._openai_service == mock_openai_service
    assert chat_processor._context_manager == mock_context_manager
    assert chat_processor._token_optimizer == mock_token_optimizer
    assert chat_processor._prompt_manager == mock_prompt_manager
    assert chat_processor._repository == mock_repository

    # Assert that the max_history is set to the default value
    assert chat_processor._max_history == 10

    # Initialize with custom max_history
    chat_processor = ChatProcessor(
        openai_service=mock_openai_service,
        context_manager=mock_context_manager,
        token_optimizer=mock_token_optimizer,
        prompt_manager=mock_prompt_manager,
        repository=mock_repository,
        max_history=5
    )

    # Assert that custom max_history is properly set
    assert chat_processor._max_history == 5


def test_sanitize_message():
    """Tests the message sanitization function"""
    # Create a set of test messages including normal text, potential injection patterns, and edge cases
    test_messages = [
        ("Normal message", "Normal message"),
        ("{{Potential injection}}", "Potential injection"),
        ("```system Malicious code ```", "Malicious code "),
        ("   Trimmed message   ", "Trimmed message"),
        ("", ""),
        ("A" * 6000, "A" * 5000)  # Test with excessively long input
    ]

    # For each test case, call sanitize_message
    for message, expected in test_messages:
        # Assert that sanitized output meets expected criteria (stripped, normalized, etc.)
        if message == "" or message == "A" * 6000:
            with pytest.raises(ValueError):
                sanitize_message(message)
        else:
            assert sanitize_message(message) == expected

    # Test with empty input to verify error handling
    with pytest.raises(ValueError):
        sanitize_message("")

    # Test with excessively long input to verify length constraints
    with pytest.raises(ValueError):
        sanitize_message("A" * 6000)


@pytest.mark.parametrize("response_text, expected_count", [
    ("No suggestions here", 0),
    (SAMPLE_AI_RESPONSE, 3)
])
def test_extract_suggestions(response_text, expected_count):
    """Tests extraction of suggestions from track changes format"""
    # Call extract_suggestions with each response_text
    suggestions = extract_suggestions(response_text)

    # Assert that the returned list has expected_count items
    assert len(suggestions) == expected_count

    # For responses with suggestions, verify each suggestion has original_text and suggested_text
    if expected_count > 0:
        for suggestion in suggestions:
            assert "original_text" in suggestion
            assert "suggested_text" in suggestion

    # Verify that the extracted text matches expected patterns
    if response_text == SAMPLE_AI_RESPONSE:
        assert suggestions[0]["original_text"] == "needs to"
        assert suggestions[0]["suggested_text"] == "should"
        assert suggestions[1]["original_text"] == "make sure to"
        assert suggestions[1]["suggested_text"] == "ensure"
        assert suggestions[2]["original_text"] == "big"
        assert suggestions[2]["suggested_text"] == "significant"

    # Test with complex nested suggestions
    # Test with malformed track changes format
    # TODO: Add more test cases for edge cases


def test_process_message(mock_openai_service):
    """Tests the main message processing workflow"""
    # Create mock dependencies (OpenAIService, ContextManager, etc.)
    mock_context_manager = unittest.mock.Mock(ContextManager)
    mock_token_optimizer = unittest.mock.Mock(TokenOptimizer)
    mock_prompt_manager = unittest.mock.Mock(PromptManager)
    mock_repository = unittest.mock.Mock(AIInteractionRepository)

    # Configure mocks to return appropriate test values
    mock_openai_service.get_chat_response.return_value = {"choices": [{"message": {"content": SAMPLE_AI_RESPONSE}}]}
    mock_context_manager.get_context.return_value = None
    mock_context_manager.create_context.return_value = {"session_id": TEST_SESSION_ID, "conversation_id": TEST_CONVERSATION_ID, "messages": []}

    # Initialize ChatProcessor with mock dependencies
    chat_processor = ChatProcessor(
        openai_service=mock_openai_service,
        context_manager=mock_context_manager,
        token_optimizer=mock_token_optimizer,
        prompt_manager=mock_prompt_manager,
        repository=mock_repository
    )

    # Call process_message with test inputs
    response = chat_processor.process_message(
        message=TEST_MESSAGE,
        session_id=TEST_SESSION_ID,
        conversation_id=None,
        user_id=TEST_USER_ID,
        document_id=TEST_DOCUMENT_ID,
        document_content=TEST_DOCUMENT_CONTENT
    )

    # Assert that context management functions were called correctly
    mock_context_manager.get_context.assert_called_once()
    mock_context_manager.create_context.assert_called_once()
    mock_context_manager.add_message_to_context.assert_called()

    # Assert that OpenAI service was called with expected parameters
    mock_openai_service.get_chat_response.assert_called_once()

    # Assert that the response contains expected fields (content, suggestions, etc.)
    assert "content" in response
    assert "conversation_id" in response
    assert "suggestions" in response
    assert "processing_time" in response

    # Assert that the interaction was logged to the repository
    mock_repository.log_chat_interaction.assert_called_once()

    # Assert that the processing_time was recorded
    assert response["processing_time"] > 0


def test_process_message_with_document(mock_openai_service):
    """Tests message processing with document context"""
    # Create mock dependencies
    mock_context_manager = unittest.mock.Mock(ContextManager)
    mock_token_optimizer = unittest.mock.Mock(TokenOptimizer)
    mock_prompt_manager = unittest.mock.Mock(PromptManager)
    mock_repository = unittest.mock.Mock(AIInteractionRepository)

    # Configure mocks to return appropriate test values
    mock_openai_service.get_chat_response.return_value = {"choices": [{"message": {"content": SAMPLE_AI_RESPONSE}}]}
    mock_context_manager.get_context.return_value = None
    mock_context_manager.create_context.return_value = {"session_id": TEST_SESSION_ID, "conversation_id": TEST_CONVERSATION_ID, "messages": []}
    mock_context_manager.optimize_document_context.return_value = TEST_DOCUMENT_CONTENT

    # Initialize ChatProcessor with mock dependencies
    chat_processor = ChatProcessor(
        openai_service=mock_openai_service,
        context_manager=mock_context_manager,
        token_optimizer=mock_token_optimizer,
        prompt_manager=mock_prompt_manager,
        repository=mock_repository
    )

    # Call process_message with test message and document content
    response = chat_processor.process_message(
        message=TEST_MESSAGE,
        session_id=TEST_SESSION_ID,
        conversation_id=None,
        user_id=TEST_USER_ID,
        document_id=TEST_DOCUMENT_ID,
        document_content=TEST_DOCUMENT_CONTENT
    )

    # Assert that document content is optimized and included in context
    mock_context_manager.optimize_document_context.assert_called_once_with(TEST_DOCUMENT_CONTENT, query=TEST_MESSAGE)
    mock_prompt_manager.prepare_system_instruction.assert_called_once_with(TEST_DOCUMENT_CONTENT)

    # Assert that system instruction includes document-specific guidance
    # Assert that the response includes document suggestions
    assert "suggestions" in response

    # Verify that document_id is included in logged interaction
    mock_repository.log_chat_interaction.assert_called_once()
    args, kwargs = mock_repository.log_chat_interaction.call_args
    assert kwargs["document_id"] == TEST_DOCUMENT_ID


def test_process_message_error_handling(mock_openai_service):
    """Tests error handling during message processing"""
    # Create mock dependencies
    mock_context_manager = unittest.mock.Mock(ContextManager)
    mock_token_optimizer = unittest.mock.Mock(TokenOptimizer)
    mock_prompt_manager = unittest.mock.Mock(PromptManager)
    mock_repository = unittest.mock.Mock(AIInteractionRepository)

    # Configure OpenAIService mock to raise an exception
    mock_openai_service.get_chat_response.side_effect = Exception("AI service unavailable")

    # Initialize ChatProcessor with mock dependencies
    chat_processor = ChatProcessor(
        openai_service=mock_openai_service,
        context_manager=mock_context_manager,
        token_optimizer=mock_token_optimizer,
        prompt_manager=mock_prompt_manager,
        repository=mock_repository
    )

    # Assert that calling process_message raises ChatProcessingError
    with pytest.raises(ChatProcessingError) as exc_info:
        chat_processor.process_message(
            message=TEST_MESSAGE,
            session_id=TEST_SESSION_ID,
            conversation_id=None,
            user_id=TEST_USER_ID,
            document_id=TEST_DOCUMENT_ID,
            document_content=TEST_DOCUMENT_CONTENT
        )

    # Test with various error conditions (network error, context error, etc.)
    # Verify error is properly categorized in the exception
    assert "AI service unavailable" in str(exc_info.value)


def test_stream_response(mock_openai_service):
    """Tests the streaming response functionality"""
    # Create mock dependencies
    mock_context_manager = unittest.mock.Mock(ContextManager)
    mock_token_optimizer = unittest.mock.Mock(TokenOptimizer)
    mock_prompt_manager = unittest.mock.Mock(PromptManager)
    mock_repository = unittest.mock.Mock(AIInteractionRepository)

    # Configure OpenAIService.stream_response to yield test chunks
    async def chunk_generator():
        yield {"content": "This is"}
        yield {"content": " a test"}
        yield {"content": " stream."}
        yield {"done": True, "processing_time": 1.23}

    mock_openai_service.stream_response.return_value = chunk_generator()
    mock_context_manager.get_context.return_value = None
    mock_context_manager.create_context.return_value = {"session_id": TEST_SESSION_ID, "conversation_id": TEST_CONVERSATION_ID, "messages": []}

    # Initialize ChatProcessor with mock dependencies
    chat_processor = ChatProcessor(
        openai_service=mock_openai_service,
        context_manager=mock_context_manager,
        token_optimizer=mock_token_optimizer,
        prompt_manager=mock_prompt_manager,
        repository=mock_repository
    )

    # Call stream_response with test inputs
    stream = chat_processor.stream_response(
        message=TEST_MESSAGE,
        session_id=TEST_SESSION_ID,
        conversation_id=None,
        user_id=TEST_USER_ID,
        document_id=TEST_DOCUMENT_ID,
        document_content=TEST_DOCUMENT_CONTENT
    )

    # Collect chunks from the returned generator
    chunks = []
    for chunk in stream:
        chunks.append(chunk)

    # Assert that all chunks were received
    assert len(chunks) == 4
    assert chunks[0]["content"] == "This is"
    assert chunks[1]["content"] == " a test"
    assert chunks[2]["content"] == " stream."

    # Assert that interaction was logged after streaming completes
    mock_repository.log_chat_interaction.assert_called_once()

    # Assert that final chunk contains metadata (processing_time, etc.)
    assert chunks[3]["done"] is True
    assert "processing_time" in chunks[3]


@pytest.mark.parametrize("context_exists", [True, False])
def test_get_conversation_history(context_exists):
    """Tests retrieval of conversation history"""
    # Create mock dependencies
    mock_context_manager = unittest.mock.Mock(ContextManager)
    mock_repository = unittest.mock.Mock(AIInteractionRepository)

    # If context_exists, configure ContextManager to return test context
    if context_exists:
        mock_context_manager.get_context.return_value = {"session_id": TEST_SESSION_ID, "conversation_id": TEST_CONVERSATION_ID, "messages": [
            {"role": "user", "content": "Hello", "timestamp": 1},
            {"role": "assistant", "content": "Hi", "timestamp": 2}
        ]}
    # Otherwise, configure AIInteractionRepository to return test interactions
    else:
        mock_context_manager.get_context.return_value = None
        mock_repository.get_conversation_interactions.return_value = [
            {"custom_prompt": "Hello", "metadata": {"is_user_message": True}, "timestamp": 1},
            {"custom_prompt": "Hi", "metadata": {"is_user_message": False}, "timestamp": 2}
        ]

    # Initialize ChatProcessor with mock dependencies
    chat_processor = ChatProcessor(
        openai_service=unittest.mock.Mock(OpenAIService),
        context_manager=mock_context_manager,
        token_optimizer=unittest.mock.Mock(TokenOptimizer),
        prompt_manager=unittest.mock.Mock(PromptManager),
        repository=mock_repository
    )

    # Call get_conversation_history with test IDs
    history = chat_processor.get_conversation_history(TEST_SESSION_ID, TEST_CONVERSATION_ID)

    # Assert the returned list has expected message format
    assert len(history) == 2
    assert "role" in history[0]
    assert "content" in history[0]

    # Verify history is limited to max_history if needed
    # TODO: Add test case for max_history


@pytest.mark.parametrize("with_document", [True, False])
@pytest.mark.parametrize("with_user", [True, False])
def test_create_new_conversation(with_document, with_user):
    """Tests creation of a new conversation"""
    # Create mock dependencies
    mock_context_manager = unittest.mock.Mock(ContextManager)
    mock_token_optimizer = unittest.mock.Mock(TokenOptimizer)
    mock_prompt_manager = unittest.mock.Mock(PromptManager)

    # Configure ContextManager mock to return test context
    mock_context_manager.create_context.return_value = {"session_id": TEST_SESSION_ID, "conversation_id": TEST_CONVERSATION_ID, "messages": []}

    # Initialize ChatProcessor with mock dependencies
    chat_processor = ChatProcessor(
        openai_service=unittest.mock.Mock(OpenAIService),
        context_manager=mock_context_manager,
        token_optimizer=mock_token_optimizer,
        prompt_manager=mock_prompt_manager,
        repository=unittest.mock.Mock(AIInteractionRepository)
    )

    # Call create_new_conversation with appropriate parameters
    user_id = TEST_USER_ID if with_user else None
    document_content = TEST_DOCUMENT_CONTENT if with_document else None
    context = chat_processor.create_new_conversation(
        session_id=TEST_SESSION_ID,
        user_id=user_id,
        document_id=TEST_DOCUMENT_ID,
        document_content=document_content
    )

    # Assert ContextManager.create_context was called with expected parameters
    mock_context_manager.create_context.assert_called_once()
    args, kwargs = mock_context_manager.create_context.call_args
    assert kwargs["session_id"] == TEST_SESSION_ID
    assert kwargs["user_id"] == user_id

    # If with_document, verify document content is optimized
    if with_document:
        mock_context_manager.optimize_document_context.assert_called_once()

    # If with_user, verify user_id is included in context
    # Assert the returned context has expected structure
    assert "session_id" in context
    assert "conversation_id" in context
    assert "messages" in context


def test_extract_document_suggestions():
    """Tests extraction of document improvement suggestions"""
    # Initialize ChatProcessor with mock dependencies
    chat_processor = ChatProcessor(
        openai_service=unittest.mock.Mock(OpenAIService),
        context_manager=unittest.mock.Mock(ContextManager),
        token_optimizer=unittest.mock.Mock(TokenOptimizer),
        prompt_manager=unittest.mock.Mock(PromptManager),
        repository=unittest.mock.Mock(AIInteractionRepository)
    )

    # Call extract_document_suggestions with test response text
    suggestions = chat_processor.extract_document_suggestions(SAMPLE_AI_RESPONSE)

    # Assert the returned list has expected suggestion objects
    assert len(suggestions) == 3
    assert "original_text" in suggestions[0]
    assert "suggested_text" in suggestions[0]

    # Verify each suggestion has original_text and suggested_text
    # Test with response containing no suggestions
    # Test with response containing multiple suggestions
    # TODO: Add more test cases for edge cases


@pytest.mark.parametrize("success", [True, False])
def test_clear_conversation(success):
    """Tests clearing a conversation's history"""
    # Create mock dependencies
    mock_context_manager = unittest.mock.Mock(ContextManager)

    # Configure ContextManager.clear_context to return success
    mock_context_manager.clear_context.return_value = success

    # Initialize ChatProcessor with mock dependencies
    chat_processor = ChatProcessor(
        openai_service=unittest.mock.Mock(OpenAIService),
        context_manager=mock_context_manager,
        token_optimizer=unittest.mock.Mock(TokenOptimizer),
        prompt_manager=unittest.mock.Mock(PromptManager),
        repository=unittest.mock.Mock(AIInteractionRepository)
    )

    # Call clear_conversation with test IDs
    result = chat_processor.clear_conversation(TEST_SESSION_ID, TEST_CONVERSATION_ID)

    # Assert the returned value matches expected success status
    assert result == success

    # Verify ContextManager.clear_context was called with correct IDs
    mock_context_manager.clear_context.assert_called_once_with(TEST_SESSION_ID, TEST_CONVERSATION_ID)


def test_format_chat_history():
    """Tests formatting of previous chat interactions"""
    # Create test interaction records with various roles
    interactions = [
        {"custom_prompt": "Hello", "metadata": {"is_user_message": True}, "timestamp": 1},
        {"custom_prompt": "Hi", "metadata": {"is_user_message": False}, "timestamp": 2},
        {"custom_prompt": "How can I help?", "metadata": {"is_user_message": False}, "timestamp": 3}
    ]

    # Initialize ChatProcessor with mock dependencies
    chat_processor = ChatProcessor(
        openai_service=unittest.mock.Mock(OpenAIService),
        context_manager=unittest.mock.Mock(ContextManager),
        token_optimizer=unittest.mock.Mock(TokenOptimizer),
        prompt_manager=unittest.mock.Mock(PromptManager),
        repository=unittest.mock.Mock(AIInteractionRepository)
    )

    # Call format_chat_history with test interactions
    messages = chat_processor.format_chat_history(interactions)

    # Assert returned list has expected format [{role, content}, ...]
    assert len(messages) == 3
    assert "role" in messages[0]
    assert "content" in messages[0]

    # Verify chronological ordering of messages
    assert messages[0]["content"] == "Hello"
    assert messages[1]["content"] == "Hi"
    assert messages[2]["content"] == "How can I help?"

    # Test with empty interactions list
    # Test with interactions exceeding max_history
    # TODO: Add more test cases for edge cases


@pytest.mark.parametrize("document_content", [None, TEST_DOCUMENT_CONTENT])
@pytest.mark.parametrize("is_document_focused", [True, False])
def test_prepare_system_instruction(document_content, is_document_focused):
    """Tests preparation of system instruction with document context"""
    # Create mock dependencies
    mock_prompt_manager = unittest.mock.Mock(PromptManager)

    # Configure PromptManager mock to return test prompts
    mock_prompt_manager.create_system_prompt.return_value = SAMPLE_SYSTEM_INSTRUCTION

    # Initialize ChatProcessor with mock dependencies
    chat_processor = ChatProcessor(
        openai_service=unittest.mock.Mock(OpenAIService),
        context_manager=unittest.mock.Mock(ContextManager),
        token_optimizer=unittest.mock.Mock(TokenOptimizer),
        prompt_manager=mock_prompt_manager,
        repository=unittest.mock.Mock(AIInteractionRepository)
    )

    # Call prepare_system_instruction with test parameters
    instruction = chat_processor.prepare_system_instruction(document_content, is_document_focused)

    # Assert the returned instruction contains expected base guidance
    assert SAMPLE_SYSTEM_INSTRUCTION in instruction

    # If document_content provided, verify document context is included
    if document_content:
        assert f"The following document content is provided for context: '{document_content}'" in instruction

    # If is_document_focused, verify track changes pattern is included
    if is_document_focused or document_content:
        assert "Use track changes format" in instruction

    # Verify PromptManager.create_system_prompt was called appropriately
    mock_prompt_manager.create_system_prompt.assert_called_once()


def test_integration_process_message(mock_openai_service):
    """Integration test for the full message processing workflow"""
    # Create actual (non-mock) instances of dependencies
    from src.backend.core.ai.openai_service import OpenAIService
    from src.backend.core.ai.context_manager import ContextManager
    from src.backend.core.ai.token_optimizer import TokenOptimizer
    from src.backend.core.ai.prompt_manager import PromptManager
    from src.backend.data.mongodb.repositories.ai_interaction_repository import AIInteractionRepository

    openai_service = OpenAIService(api_key="test_api_key")
    context_manager = ContextManager()
    token_optimizer = TokenOptimizer()
    prompt_manager = PromptManager(template_service=unittest.mock.Mock(), token_optimizer=token_optimizer, context_manager=context_manager)
    repository = AIInteractionRepository()

    # Initialize ChatProcessor with real dependencies but mocked OpenAI service
    chat_processor = ChatProcessor(
        openai_service=mock_openai_service,
        context_manager=context_manager,
        token_optimizer=token_optimizer,
        prompt_manager=prompt_manager,
        repository=repository
    )

    # Configure mock_openai_service to return realistic responses
    mock_openai_service.get_chat_response.return_value = {"choices": [{"message": {"content": "The company should prioritize customer satisfaction."}}]}

    # Create a new conversation with document context
    context = chat_processor.create_new_conversation(
        session_id=TEST_SESSION_ID,
        document_content=TEST_DOCUMENT_CONTENT
    )

    # Process a test message
    response = chat_processor.process_message(
        message="Make it shorter",
        session_id=TEST_SESSION_ID,
        conversation_id=context["conversation_id"],
        document_content=TEST_DOCUMENT_CONTENT
    )

    # Verify response content and format
    assert "content" in response
    assert "conversation_id" in response
    assert response["content"] == "The company should prioritize customer satisfaction."

    # Process a follow-up message
    mock_openai_service.get_chat_response.return_value = {"choices": [{"message": {"content": "Great!"}}]}
    response2 = chat_processor.process_message(
        message="Great!",
        session_id=TEST_SESSION_ID,
        conversation_id=context["conversation_id"],
        document_content=TEST_DOCUMENT_CONTENT
    )

    # Verify conversation history maintains context
    history = chat_processor.get_conversation_history(TEST_SESSION_ID, context["conversation_id"])
    assert len(history) == 2
    assert history[0]["content"] == "Make it shorter"
    assert history[1]["content"] == "Great!"

    # Verify suggestions are properly extracted
    # Check processing time is within expected range
    assert response["processing_time"] > 0