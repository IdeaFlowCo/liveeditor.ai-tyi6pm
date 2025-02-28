"""
Unit tests for the Redis-based session store implementation that handles
anonymous and authenticated user sessions in the AI writing enhancement platform.
"""

import pytest
import fakeredis
import json
import time
from unittest.mock import patch

from src.backend.data.redis.session_store import SessionStore
from src.backend.tests.fixtures.user_fixtures import anonymous_user_data, regular_user_data

# Test prefix for Redis keys
TEST_PREFIX = 'test_session:'


@pytest.fixture
def mock_redis():
    """Create a fake Redis server for testing."""
    server = fakeredis.FakeServer()
    fake_redis = fakeredis.FakeRedis(server=server, decode_responses=True)
    return fake_redis


def test_session_store_initialization():
    """Test that SessionStore initializes correctly with the provided prefix."""
    with patch('src.backend.data.redis.session_store.get_session_store_connection') as mock_get_connection:
        mock_redis = fakeredis.FakeRedis(decode_responses=True)
        mock_get_connection.return_value = mock_redis
        
        store = SessionStore(prefix=TEST_PREFIX)
        
        # Verify that the prefix is set correctly
        assert store._prefix == TEST_PREFIX
        # Verify that Redis client is initialized
        assert store._redis_client is not None


def test_create_session(mock_redis):
    """Test creating a new session with basic data."""
    with patch('src.backend.data.redis.session_store.get_session_store_connection', return_value=mock_redis):
        store = SessionStore(prefix=TEST_PREFIX)
        
        test_data = {
            'key1': 'value1',
            'key2': 'value2'
        }
        
        session_id = store.create_session(data=test_data)
        
        # Verify a session_id is returned
        assert session_id is not None
        
        # Verify session was stored in Redis with correct data
        redis_key = f"{TEST_PREFIX}{session_id}"
        stored_data = mock_redis.get(redis_key)
        assert stored_data is not None
        
        # Parse the JSON data and verify it contains our test data
        parsed_data = json.loads(stored_data)
        assert parsed_data['key1'] == 'value1'
        assert parsed_data['key2'] == 'value2'
        assert parsed_data['session_id'] == session_id
        assert parsed_data['is_authenticated'] is False


def test_create_anonymous_session(mock_redis, anonymous_user_data):
    """Test creating an anonymous session."""
    with patch('src.backend.data.redis.session_store.get_session_store_connection', return_value=mock_redis):
        store = SessionStore(prefix=TEST_PREFIX)
        
        session_id = store.create_anonymous_session(data=anonymous_user_data)
        
        # Verify a session_id is returned
        assert session_id is not None
        
        # Verify session was stored in Redis with correct data
        redis_key = f"{TEST_PREFIX}{session_id}"
        stored_data = mock_redis.get(redis_key)
        assert stored_data is not None
        
        # Parse the JSON data and verify session properties
        parsed_data = json.loads(stored_data)
        assert parsed_data['is_authenticated'] is False
        
        # Verify TTL is set to ANONYMOUS_SESSION_TTL
        ttl = mock_redis.ttl(redis_key)
        assert ttl > 0  # TTL should be positive


def test_create_authenticated_session(mock_redis, regular_user_data):
    """Test creating an authenticated session with user ID."""
    with patch('src.backend.data.redis.session_store.get_session_store_connection', return_value=mock_redis):
        store = SessionStore(prefix=TEST_PREFIX)
        
        user_id = regular_user_data['_id']
        
        session_id = store.create_authenticated_session(user_id=user_id, data=regular_user_data)
        
        # Verify a session_id is returned
        assert session_id is not None
        
        # Verify session was stored in Redis with correct data
        redis_key = f"{TEST_PREFIX}{session_id}"
        stored_data = mock_redis.get(redis_key)
        assert stored_data is not None
        
        # Parse the JSON data and verify session properties
        parsed_data = json.loads(stored_data)
        assert parsed_data['is_authenticated'] is True
        assert parsed_data['user_id'] == user_id
        
        # Verify TTL is set to AUTHENTICATED_SESSION_TTL
        ttl = mock_redis.ttl(redis_key)
        assert ttl > 0  # TTL should be positive


def test_get_session(mock_redis):
    """Test retrieving an existing session."""
    with patch('src.backend.data.redis.session_store.get_session_store_connection', return_value=mock_redis):
        store = SessionStore(prefix=TEST_PREFIX)
        
        # Create a test session with known data
        test_data = {'key': 'value'}
        session_id = store.create_session(data=test_data)
        
        # Call get_session with the session_id
        session = store.get_session(session_id)
        
        # Verify the returned data matches what was stored
        assert session is not None
        assert session['key'] == 'value'
        assert session['session_id'] == session_id


def test_get_session_nonexistent(mock_redis):
    """Test retrieving a non-existent session."""
    with patch('src.backend.data.redis.session_store.get_session_store_connection', return_value=mock_redis):
        store = SessionStore(prefix=TEST_PREFIX)
        
        # Call get_session with a non-existent session_id
        session = store.get_session('nonexistent-session-id')
        
        # Verify None is returned
        assert session is None


def test_update_session(mock_redis):
    """Test updating an existing session."""
    with patch('src.backend.data.redis.session_store.get_session_store_connection', return_value=mock_redis):
        store = SessionStore(prefix=TEST_PREFIX)
        
        # Create a test session with initial data
        initial_data = {'key1': 'value1', 'key2': 'value2'}
        session_id = store.create_session(data=initial_data)
        
        # Call update_session with session_id and new data
        update_data = {'key2': 'updated_value', 'key3': 'new_value'}
        result = store.update_session(session_id, update_data)
        
        # Verify the update returns True
        assert result is True
        
        # Get the updated session
        updated_session = store.get_session(session_id)
        
        # Verify the session contains the merged data
        assert updated_session['key1'] == 'value1'  # Original value
        assert updated_session['key2'] == 'updated_value'  # Updated value
        assert updated_session['key3'] == 'new_value'  # New value


def test_update_session_nonexistent(mock_redis):
    """Test updating a non-existent session."""
    with patch('src.backend.data.redis.session_store.get_session_store_connection', return_value=mock_redis):
        store = SessionStore(prefix=TEST_PREFIX)
        
        # Call update_session with a non-existent session_id
        result = store.update_session('nonexistent-session-id', {'key': 'value'})
        
        # Verify False is returned
        assert result is False


def test_delete_session(mock_redis):
    """Test deleting an existing session."""
    with patch('src.backend.data.redis.session_store.get_session_store_connection', return_value=mock_redis):
        store = SessionStore(prefix=TEST_PREFIX)
        
        # Create a test session
        session_id = store.create_session(data={'key': 'value'})
        
        # Call delete_session with the session_id
        result = store.delete_session(session_id)
        
        # Verify the delete returns True
        assert result is True
        
        # Verify get_session returns None for the deleted session
        assert store.get_session(session_id) is None


def test_delete_session_nonexistent(mock_redis):
    """Test deleting a non-existent session."""
    with patch('src.backend.data.redis.session_store.get_session_store_connection', return_value=mock_redis):
        store = SessionStore(prefix=TEST_PREFIX)
        
        # Call delete_session with a non-existent session_id
        result = store.delete_session('nonexistent-session-id')
        
        # Verify False is returned
        assert result is False


def test_extend_session(mock_redis):
    """Test extending the TTL of an existing session."""
    with patch('src.backend.data.redis.session_store.get_session_store_connection', return_value=mock_redis):
        store = SessionStore(prefix=TEST_PREFIX)
        
        # Create a test session
        session_id = store.create_session(data={'key': 'value'})
        
        # Get initial TTL of the session
        initial_ttl = store.get_session_ttl(session_id)
        
        # Call extend_session with session_id and new TTL
        new_ttl = initial_ttl + 1000  # Add 1000 seconds to TTL
        result = store.extend_session(session_id, ttl=new_ttl)
        
        # Verify the extend returns True
        assert result is True
        
        # Get new TTL with get_session_ttl
        extended_ttl = store.get_session_ttl(session_id)
        
        # Verify the new TTL is greater than the initial TTL
        assert extended_ttl > initial_ttl


def test_extend_session_nonexistent(mock_redis):
    """Test extending a non-existent session."""
    with patch('src.backend.data.redis.session_store.get_session_store_connection', return_value=mock_redis):
        store = SessionStore(prefix=TEST_PREFIX)
        
        # Call extend_session with a non-existent session_id
        result = store.extend_session('nonexistent-session-id', ttl=3600)
        
        # Verify False is returned
        assert result is False


def test_get_session_ttl(mock_redis):
    """Test getting the TTL of an existing session."""
    with patch('src.backend.data.redis.session_store.get_session_store_connection', return_value=mock_redis):
        store = SessionStore(prefix=TEST_PREFIX)
        
        # Create a test session with known TTL
        test_ttl = 3600
        session_id = store.create_session(data={'key': 'value'})
        redis_key = f"{TEST_PREFIX}{session_id}"
        mock_redis.expire(redis_key, test_ttl)
        
        # Call get_session_ttl with the session_id
        ttl = store.get_session_ttl(session_id)
        
        # Verify the returned TTL is positive and close to expected value
        assert ttl > 0
        assert ttl <= test_ttl


def test_get_session_ttl_nonexistent(mock_redis):
    """Test getting the TTL of a non-existent session."""
    with patch('src.backend.data.redis.session_store.get_session_store_connection', return_value=mock_redis):
        store = SessionStore(prefix=TEST_PREFIX)
        
        # Call get_session_ttl with a non-existent session_id
        ttl = store.get_session_ttl('nonexistent-session-id')
        
        # Verify -2 is returned (Redis standard for non-existent key)
        assert ttl == -2


def test_upgrade_session(mock_redis, anonymous_user_data, regular_user_data):
    """Test upgrading an anonymous session to an authenticated session."""
    with patch('src.backend.data.redis.session_store.get_session_store_connection', return_value=mock_redis):
        store = SessionStore(prefix=TEST_PREFIX)
        
        # Create an anonymous session with anonymous_user_data
        anonymous_session_id = store.create_anonymous_session(data=anonymous_user_data)
        
        # Get user_id from regular_user_data
        user_id = regular_user_data['_id']
        
        # Call upgrade_session with anonymous session_id and user_id
        authenticated_session_id = store.upgrade_session(anonymous_session_id, user_id)
        
        # Verify a new session_id is returned
        assert authenticated_session_id is not None
        
        # Verify the new session has is_authenticated=True
        authenticated_session = store.get_session(authenticated_session_id)
        assert authenticated_session['is_authenticated'] is True
        
        # Verify the new session has the correct user_id
        assert authenticated_session['user_id'] == user_id
        
        # Verify the old anonymous session is deleted
        assert store.get_session(anonymous_session_id) is None


def test_upgrade_session_nonexistent(mock_redis, regular_user_data):
    """Test upgrading a non-existent session."""
    with patch('src.backend.data.redis.session_store.get_session_store_connection', return_value=mock_redis):
        store = SessionStore(prefix=TEST_PREFIX)
        
        # Get user_id from regular_user_data
        user_id = regular_user_data['_id']
        
        # Call upgrade_session with a non-existent session_id and user_id
        result = store.upgrade_session('nonexistent-session-id', user_id)
        
        # Verify None is returned
        assert result is None


def test_session_expiration(mock_redis):
    """Test that sessions expire after their TTL period."""
    with patch('src.backend.data.redis.session_store.get_session_store_connection', return_value=mock_redis):
        store = SessionStore(prefix=TEST_PREFIX)
        
        # Create a test session with a very short TTL (1 second)
        session_id = store.create_session(data={'key': 'value'})
        redis_key = f"{TEST_PREFIX}{session_id}"
        mock_redis.expire(redis_key, 1)
        
        # Verify the session exists immediately after creation
        assert store.get_session(session_id) is not None
        
        # Use time.sleep to wait for TTL to expire
        time.sleep(2)
        
        # Verify get_session returns None for the expired session
        assert store.get_session(session_id) is None