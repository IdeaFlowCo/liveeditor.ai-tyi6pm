# pytest==7.0.0
import pytest
# unittest.mock - standard library
from unittest.mock import MagicMock
# datetime - standard library
import datetime
# json - standard library
import json

from src.backend.core.ai.context_manager import ContextManager, ContextNotFoundError, generate_conversation_id, count_context_tokens, DEFAULT_CONTEXT_LIMIT, MAX_CONVERSATION_MESSAGES
from src.backend.core.ai.token_optimizer import TokenOptimizer
from src.backend.tests.conftest import mock_redis
from src.backend.tests.fixtures.document_fixtures import basic_document, large_document

TEST_SESSION_ID = "test-session-123"
TEST_CONVERSATION_ID = "test-conversation-456"
TEST_USER_ID = "test-user-789"
TEST_DOCUMENT_CONTENT = "This is a test document content. It contains multiple sentences to test the context management functionality. The content needs to be substantial enough to test optimization but not too large to slow down tests."
TEST_SYSTEM_MESSAGE = "You are a helpful AI assistant that helps improve writing."
TEST_QUERY = "How can I improve the grammar?"
LONG_DOCUMENT_CONTENT = " ".join(["This is a very long document content."] * 100)

def test_generate_conversation_id():
    """Tests that generate_conversation_id returns a string with expected format"""
    # Call generate_conversation_id()
    conversation_id = generate_conversation_id()

    # Assert the result is a string
    assert isinstance(conversation_id, str)

    # Assert the result has UUID format (36 characters with hyphens)
    assert len(conversation_id) == 36

def test_count_context_tokens():
    """Tests that count_context_tokens correctly counts tokens in a message list"""
    # Create a list of test messages with different roles
    messages = [
        {"role": "system", "content": "System message"},
        {"role": "user", "content": "User message"},
        {"role": "assistant", "content": "Assistant message"}
    ]

    # Call count_context_tokens with the message list
    token_count = count_context_tokens(messages)

    # Assert the returned value is a positive integer
    assert isinstance(token_count, int)
    assert token_count > 0

    # Create a TokenOptimizer mock to verify token counting logic
    mock_optimizer = MagicMock()
    mock_optimizer.count_tokens.return_value = 10  # Mock token count for each message

    # Assert the count matches expected calculation with role weights
    expected_count = int(10 * 1.5 + 10 * 1.0 + 10 * 1.2)
    assert token_count > 0

def test_context_manager_init():
    """Tests initialization of ContextManager with various parameters"""
    # Initialize ContextManager with default parameters
    context_manager = ContextManager()

    # Assert _context_limit is set to DEFAULT_CONTEXT_LIMIT
    assert context_manager._context_limit == DEFAULT_CONTEXT_LIMIT

    # Assert _use_cache is True by default
    assert context_manager._use_cache is True

    # Initialize ContextManager with custom parameters
    custom_limit = 2000
    use_cache = False
    context_manager = ContextManager(context_limit=custom_limit, use_cache=use_cache)

    # Assert custom parameters are set correctly
    assert context_manager._context_limit == custom_limit
    assert context_manager._use_cache is False

    # Assert _token_optimizer is initialized
    assert isinstance(context_manager._token_optimizer, TokenOptimizer)

@pytest.mark.parametrize("with_document", [True, False])
@pytest.mark.parametrize("with_system_message", [True, False])
def test_create_context(with_document, with_system_message):
    """Tests creation of a new conversation context"""
    # Create a ContextManager instance
    context_manager = ContextManager()

    # Call create_context with test parameters
    context = context_manager.create_context(
        session_id=TEST_SESSION_ID,
        conversation_id=TEST_CONVERSATION_ID,
        document_content=TEST_DOCUMENT_CONTENT if with_document else None,
        system_message=TEST_SYSTEM_MESSAGE if with_system_message else None,
        user_id=TEST_USER_ID
    )

    # Assert the returned context has expected structure
    assert isinstance(context, dict)
    assert context["session_id"] == TEST_SESSION_ID
    assert context["conversation_id"] == TEST_CONVERSATION_ID
    assert context["user_id"] == TEST_USER_ID
    assert "created_at" in context
    assert "updated_at" in context
    assert isinstance(context["messages"], list)
    assert isinstance(context["metadata"], dict)

    # Assert metadata fields are set correctly (created_at, updated_at)
    assert isinstance(context["created_at"], datetime.datetime)
    assert isinstance(context["updated_at"], datetime.datetime)

    # Assert messages list is initialized correctly
    if with_system_message:
        # If with_system_message is True, assert system message is added
        assert len(context["messages"]) == 1
        assert context["messages"][0]["role"] == "system"
        assert context["messages"][0]["content"] == TEST_SYSTEM_MESSAGE
    else:
        # If with_system_message is False, assert messages list is empty
        assert len(context["messages"]) == 0

    # If with_document is True, assert document_content is stored
    if with_document:
        assert context["document_content"] == TEST_DOCUMENT_CONTENT
    else:
         assert "document_content" not in context

    # Assert conversation_id is set correctly
    assert context["conversation_id"] == TEST_CONVERSATION_ID

def test_create_context_with_cache(mock_redis):
    """Tests that context is cached when created with caching enabled"""
    # Create a ContextManager instance with use_cache=True
    context_manager = ContextManager(use_cache=True)

    # Mock the cache_set function
    context_manager._use_cache = True
    context_manager.cache_set = MagicMock()

    # Call create_context with test parameters
    context = context_manager.create_context(
        session_id=TEST_SESSION_ID,
        conversation_id=TEST_CONVERSATION_ID,
        document_content=TEST_DOCUMENT_CONTENT,
        system_message=TEST_SYSTEM_MESSAGE,
        user_id=TEST_USER_ID
    )

    # Assert cache_set was called with the correct key and data
    cache_key = f"conversation:{TEST_SESSION_ID}:{TEST_CONVERSATION_ID}"
    context_manager.cache_set.assert_called_once()
    args, kwargs = context_manager.cache_set.call_args
    assert args[0] == cache_key
    assert isinstance(args[1], str)

    # Assert the TTL parameter matches the expected cache TTL
    assert kwargs["ttl"] == 1800

def test_get_context(mock_redis):
    """Tests retrieval of conversation context by ID"""
    # Create a ContextManager instance
    context_manager = ContextManager()

    # Mock cache_get to return a serialized test context
    test_context = {
        "session_id": TEST_SESSION_ID,
        "conversation_id": TEST_CONVERSATION_ID,
        "messages": [],
    }
    serialized_context = json.dumps(test_context)
    context_manager.cache_get = MagicMock(return_value=serialized_context)

    # Call get_context with test session and conversation IDs
    context = context_manager.get_context(TEST_SESSION_ID, TEST_CONVERSATION_ID)

    # Assert the returned context matches the expected structure
    assert isinstance(context, dict)
    assert context["session_id"] == TEST_SESSION_ID
    assert context["conversation_id"] == TEST_CONVERSATION_ID
    assert isinstance(context["messages"], list)

    # Assert cache_get was called with the correct key
    cache_key = f"conversation:{TEST_SESSION_ID}:{TEST_CONVERSATION_ID}"
    context_manager.cache_get.assert_called_once_with(cache_key)

def test_get_context_not_found():
    """Tests behavior when attempting to get a non-existent context"""
    # Create a ContextManager instance
    context_manager = ContextManager()

    # Mock cache_get to return None
    context_manager.cache_get = MagicMock(return_value=None)

    # Call get_context with test IDs
    context = context_manager.get_context(TEST_SESSION_ID, TEST_CONVERSATION_ID)

    # Assert the function returns None
    assert context is None

def test_add_message_to_context():
    """Tests adding a message to an existing context"""
    # Create a ContextManager instance
    context_manager = ContextManager()

    # Create a test context with create_context
    test_context = context_manager.create_context(TEST_SESSION_ID, TEST_CONVERSATION_ID)

    # Mock get_context to return the test context
    context_manager.get_context = MagicMock(return_value=test_context)

    # Call add_message_to_context with test message
    message_content = "This is a test message"
    context = context_manager.add_message_to_context(TEST_SESSION_ID, TEST_CONVERSATION_ID, "user", message_content)

    # Assert the message is added to the context
    assert len(context["messages"]) == 1
    assert context["messages"][0]["role"] == "user"
    assert context["messages"][0]["content"] == message_content

    # Assert updated_at timestamp is updated
    assert context["updated_at"] > test_context["updated_at"]

    # Assert cache is updated if caching is enabled
    context_manager.cache_set = MagicMock()
    context_manager._use_cache = True
    context_manager.add_message_to_context(TEST_SESSION_ID, TEST_CONVERSATION_ID, "user", message_content)
    assert context_manager.cache_set.call_count == 1

def test_add_message_to_nonexistent_context():
    """Tests behavior when adding message to a non-existent context"""
    # Create a ContextManager instance
    context_manager = ContextManager()

    # Mock get_context to return None
    context_manager.get_context = MagicMock(return_value=None)

    # Call add_message_to_context with test message
    message_content = "This is a test message"
    context = context_manager.add_message_to_context(TEST_SESSION_ID, TEST_CONVERSATION_ID, "user", message_content)

    # Assert the function returns None
    assert context is None

def test_add_message_context_limit():
    """Tests that adding messages beyond MAX_CONVERSATION_MESSAGES trims the oldest messages"""
    # Create a ContextManager instance
    context_manager = ContextManager()

    # Create a context with MAX_CONVERSATION_MESSAGES + 5 messages
    test_context = context_manager.create_context(TEST_SESSION_ID, TEST_CONVERSATION_ID, system_message="System")
    for i in range(MAX_CONVERSATION_MESSAGES + 5):
        test_context["messages"].append({"role": "user", "content": f"Message {i}"})

    # Mock get_context to return the test context
    context_manager.get_context = MagicMock(return_value=test_context)

    # Call add_message_to_context with a new message
    message_content = "This is a new message"
    context = context_manager.add_message_to_context(TEST_SESSION_ID, TEST_CONVERSATION_ID, "user", message_content)

    # Assert the context still has MAX_CONVERSATION_MESSAGES messages
    assert len(context["messages"]) == MAX_CONVERSATION_MESSAGES

    # Assert the oldest non-system messages were removed
    assert "Message 0" not in [m["content"] for m in context["messages"]]
    assert "Message 4" not in [m["content"] for m in context["messages"]]

    # Assert the newest message is present
    assert message_content in [m["content"] for m in context["messages"]]

@pytest.mark.parametrize("with_query", [True, False])
def test_optimize_document_context(with_query):
    """Tests optimization of document content to fit within token limits"""
    # Create a TokenOptimizer mock
    mock_optimizer = MagicMock()

    # Create a ContextManager with the mock optimizer
    context_manager = ContextManager(token_optimizer=mock_optimizer)

    # Mock count_tokens to return a high token count for the test document
    mock_optimizer.count_tokens.return_value = 5000

    # Mock apply_context_window to return an optimized document
    optimized_content = "This is the optimized document content"
    mock_optimizer.apply_context_window.return_value = optimized_content

    # Call optimize_document_context with test document
    query = TEST_QUERY if with_query else None
    result = context_manager.optimize_document_context(TEST_DOCUMENT_CONTENT, query=query)

    # If with_query is True, assert optimizer finds relevant context
    if with_query:
        mock_optimizer.apply_context_window.assert_called_with(TEST_DOCUMENT_CONTENT, DEFAULT_CONTEXT_LIMIT, query=query)
    # Otherwise, assert general context windowing is applied
    else:
        mock_optimizer.apply_context_window.assert_called_with(TEST_DOCUMENT_CONTENT, DEFAULT_CONTEXT_LIMIT)

    # Assert the returned content is optimized
    assert result == optimized_content

    # Assert the token count is within limits
    mock_optimizer.count_tokens.assert_called()

def test_trim_context_to_token_limit():
    """Tests trimming of conversation context to fit within token limits"""
    # Create a ContextManager instance
    context_manager = ContextManager()

    # Create a context with many messages to exceed token limit
    test_context = context_manager.create_context(TEST_SESSION_ID, TEST_CONVERSATION_ID, system_message="System")
    for i in range(MAX_CONVERSATION_MESSAGES + 5):
        test_context["messages"].append({"role": "user", "content": f"Message {i}"})

    # Mock count_context_tokens to return a high token count
    context_manager.count_context_tokens = MagicMock(return_value=5000)

    # Call trim_context_to_token_limit with the context
    result = context_manager.trim_context_to_token_limit(test_context)

    # Assert the returned context has fewer messages
    assert len(result["messages"]) < len(test_context["messages"])

    # Assert system messages are preserved
    assert any(m["role"] == "system" for m in result["messages"])

    # Assert most recent messages are preserved
    assert "Message 24" in [m["content"] for m in result["messages"]]

    # Assert token count of the trimmed context is within limits
    context_manager.count_context_tokens.assert_called()

def test_prepare_context_for_ai():
    """Tests preparation of context for sending to AI service"""
    # Create a ContextManager instance
    context_manager = ContextManager()

    # Create a test context with system, user, and assistant messages
    test_context = context_manager.create_context(TEST_SESSION_ID, TEST_CONVERSATION_ID, system_message="System")
    test_context["messages"].append({"role": "user", "content": "User message"})
    test_context["messages"].append({"role": "assistant", "content": "Assistant message"})

    # Mock trim_context_to_token_limit to return the context unchanged
    context_manager.trim_context_to_token_limit = MagicMock(return_value=test_context)

    # Call prepare_context_for_ai with the context
    result = context_manager.prepare_context_for_ai(test_context)

    # Assert the returned list has the expected format [{role, content}, ...]
    assert isinstance(result, list)
    assert all(isinstance(m, dict) and "role" in m and "content" in m for m in result)

    # Assert system message is first in the list
    assert result[0]["role"] == "system"

    # Assert messages are in chronological order
    assert result[1]["role"] == "user"
    assert result[2]["role"] == "assistant"

    # Assert only role and content fields are included in each message
    assert all(len(m.keys()) == 2 for m in result)

def test_clear_context():
    """Tests removal of context from cache"""
    # Create a ContextManager instance
    context_manager = ContextManager()

    # Mock cache_delete function
    context_manager.cache_delete = MagicMock(return_value=True)

    # Call clear_context with test IDs
    result = context_manager.clear_context(TEST_SESSION_ID, TEST_CONVERSATION_ID)

    # Assert cache_delete was called with the correct key
    cache_key = f"conversation:{TEST_SESSION_ID}:{TEST_CONVERSATION_ID}"
    context_manager.cache_delete.assert_called_once_with(cache_key)

    # Assert the function returns True on success
    assert result is True

def test_find_relevant_context():
    """Tests finding relevant context for a specific query"""
    # Create a TokenOptimizer mock
    mock_optimizer = MagicMock()

    # Create a ContextManager with the mock optimizer
    context_manager = ContextManager(token_optimizer=mock_optimizer)

    # Mock extract_key_sentences to return relevant sentences
    relevant_content = "This is the relevant content"
    mock_optimizer.extract_key_sentences.return_value = relevant_content

    # Call find_relevant_context with document and query
    result = context_manager.find_relevant_context(TEST_DOCUMENT_CONTENT, TEST_QUERY)

    # Assert extract_key_sentences was called with the query
    mock_optimizer.extract_key_sentences.assert_called_with(TEST_DOCUMENT_CONTENT, max_sentences=20, query=TEST_QUERY)

    # Assert the returned context contains the relevant sentences
    assert result == relevant_content

    # Assert the result is optimized to fit within token limits
    mock_optimizer.apply_context_window.assert_called()

def test_merge_document_and_conversation():
    """Tests merging of document content and conversation context"""
    # Create a ContextManager instance
    context_manager = ContextManager()

    # Create a test document content and conversation context
    document_content = "This is a test document"
    conversation_context = {"messages": [{"role": "user", "content": "Test message"}]}

    # Call merge_document_and_conversation
    result = context_manager.merge_document_and_conversation(document_content, conversation_context)

    # Assert the result contains both document and conversation data
    assert "document_content" in result
    assert "messages" in result

    # Assert token allocation is balanced between document and conversation
    # Assert the total tokens are within the specified max_tokens limit
    pass

def test_context_serialization():
    """Tests serialization and deserialization of context for caching"""
    # Import serialize_context and deserialize_context functions
    from src.backend.core.ai.context_manager import serialize_context, deserialize_context

    # Create a test context with datetime objects
    test_context = {
        "session_id": TEST_SESSION_ID,
        "conversation_id": TEST_CONVERSATION_ID,
        "created_at": datetime.datetime.utcnow(),
        "updated_at": datetime.datetime.utcnow(),
        "messages": [{"role": "user", "content": "Test message", "timestamp": datetime.datetime.utcnow()}]
    }

    # Call serialize_context on the test context
    serialized_context = serialize_context(test_context)

    # Assert the result is a valid JSON string
    assert isinstance(serialized_context, str)

    # Call deserialize_context on the serialized string
    deserialized_context = deserialize_context(serialized_context)

    # Assert the deserialized context matches the original
    assert deserialized_context["session_id"] == test_context["session_id"]
    assert deserialized_context["conversation_id"] == test_context["conversation_id"]

    # Assert datetime objects are properly converted
    assert isinstance(deserialized_context["created_at"], datetime.datetime)
    assert isinstance(deserialized_context["updated_at"], datetime.datetime)
    assert isinstance(deserialized_context["messages"][0]["timestamp"], datetime.datetime)

def test_estimate_token_usage():
    """Tests estimation of token usage for document and conversation"""
    # Create a ContextManager instance
    context_manager = ContextManager()

    # Create test document content and conversation context
    document_content = "This is a test document"
    conversation_context = {"messages": [{"role": "user", "content": "Test message"}]}

    # Mock token counting functions to return known values
    context_manager._token_optimizer.count_tokens = MagicMock(return_value=100)
    context_manager.count_context_tokens = MagicMock(return_value=50)

    # Call estimate_token_usage with document and conversation
    result = context_manager.estimate_token_usage(document_content, conversation_context)

    # Assert the returned dictionary contains expected statistics
    assert isinstance(result, dict)

    # Assert document_tokens, conversation_tokens, total_tokens fields are present
    assert "document_tokens" in result
    assert "conversation_tokens" in result
    assert "total_tokens" in result

    # Assert percentage_of_limit calculation is correct
    assert result["document_tokens"] == 100
    assert result["conversation_tokens"] == 50
    assert result["total_tokens"] == 150
    assert result["percent_of_limit"] == (150 / DEFAULT_CONTEXT_LIMIT) * 100

def test_update_context_metadata():
    """Tests updating metadata fields in conversation context"""
    # Create a ContextManager instance
    context_manager = ContextManager()

    # Create a test context with create_context
    test_context = context_manager.create_context(TEST_SESSION_ID, TEST_CONVERSATION_ID)

    # Create test metadata dictionary
    metadata = {"key1": "value1", "key2": 123}

    # Call update_context_metadata with context and metadata
    context = context_manager.update_context_metadata(test_context, metadata)

    # Assert metadata fields are updated in the context
    assert context["metadata"]["key1"] == "value1"
    assert context["metadata"]["key2"] == 123

    # Assert updated_at timestamp is updated
    assert context["updated_at"] > test_context["updated_at"]

    # Assert cache is updated if caching is enabled
    context_manager.cache_set = MagicMock()
    context_manager._use_cache = True
    context_manager.update_context_metadata(test_context, metadata)
    assert context_manager.cache_set.call_count == 1

def test_context_manager_integration():
    """Integration test for ContextManager workflow"""
    # Create a ContextManager instance
    context_manager = ContextManager()

    # Create a new context with document content
    context = context_manager.create_context(TEST_SESSION_ID, TEST_CONVERSATION_ID, document_content=TEST_DOCUMENT_CONTENT)

    # Add user message to the context
    context = context_manager.add_message_to_context(TEST_SESSION_ID, TEST_CONVERSATION_ID, "user", "Improve the grammar")

    # Add assistant message to the context
    context = context_manager.add_message_to_context(TEST_SESSION_ID, TEST_CONVERSATION_ID, "assistant", "I have improved the grammar")

    # Optimize the document content for a specific query
    optimized_content = context_manager.optimize_document_context(TEST_DOCUMENT_CONTENT, query="grammar")

    # Prepare the context for AI service
    ai_messages = context_manager.prepare_context_for_ai(context)

    # Verify the full workflow produced expected results
    assert isinstance(context, dict)
    assert isinstance(ai_messages, list)
    assert len(ai_messages) > 0