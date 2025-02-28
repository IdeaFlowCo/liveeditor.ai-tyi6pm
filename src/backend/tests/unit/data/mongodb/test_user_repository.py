"""
Unit tests for the UserRepository class which handles MongoDB operations for user data including
creation, retrieval, updates, and deletion of both regular and anonymous users.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock
import mongomock
from bson import ObjectId
import pymongo.errors

from src.backend.data.mongodb.repositories.user_repository import (
    UserRepository, UserNotFoundError, DuplicateEmailError
)
from src.backend.data.mongodb.connection import str_to_object_id, object_id_to_str
from src.backend.tests.fixtures.user_fixtures import (
    regular_user_data, verified_user_data, anonymous_user_data, user_with_preferences
)


@pytest.mark.unit
def test_user_repository_init():
    """Tests the initialization of the UserRepository class"""
    # Initialize UserRepository
    repo = UserRepository()
    
    # Assert that the repository has the correct collection name
    assert repo.COLLECTION_NAME == 'users'
    
    # Assert that the repository has a valid MongoDB collection reference
    assert repo._collection is not None


@pytest.mark.unit
def test_create_user(mocker):
    """Tests creating a new user successfully"""
    # Set up test user data using regular_user_data fixture
    user_data = regular_user_data()
    
    # Mock MongoDB collection insert_one method to return a mock result with inserted_id
    mock_collection = MagicMock()
    mock_result = MagicMock()
    mock_result.inserted_id = ObjectId(user_data['_id'])
    mock_collection.insert_one.return_value = mock_result
    mock_collection.find_one.return_value = None  # No existing email
    
    # Initialize UserRepository with mocked collection
    repo = UserRepository()
    repo._collection = mock_collection
    
    # Call create_user with test data
    input_data = {
        'email': user_data['email'],
        'password_hash': user_data['passwordHash'],
        'first_name': user_data['firstName'],
        'last_name': user_data['lastName']
    }
    
    # Mock get_by_id to return the created user
    mocker.patch.object(repo, 'get_by_id', return_value={
        '_id': user_data['_id'],
        'email': user_data['email'],
        'firstName': user_data['firstName'],
        'lastName': user_data['lastName'],
        'emailVerified': False,
        'isAnonymous': False
    })
    
    created_user = repo.create_user(input_data)
    
    # Assert the user was created with expected data
    assert created_user is not None
    assert created_user['email'] == user_data['email']
    assert 'passwordHash' not in created_user
    
    # Assert find_one was called to check for existing email
    mock_collection.find_one.assert_called_once()
    
    # Assert insert_one was called with correct parameters
    mock_collection.insert_one.assert_called_once()
    args, kwargs = mock_collection.insert_one.call_args
    inserted_doc = args[0]
    assert inserted_doc['email'] == user_data['email']
    assert inserted_doc['passwordHash'] == user_data['passwordHash']


@pytest.mark.unit
def test_create_user_duplicate_email(mocker):
    """Tests creating a user with an email that already exists"""
    # Set up test user data using regular_user_data fixture
    user_data = regular_user_data()
    
    # Mock MongoDB collection find_one to return an existing user with the same email
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = user_data
    
    # Initialize UserRepository with mocked collection
    repo = UserRepository()
    repo._collection = mock_collection
    
    # Assert that calling create_user raises DuplicateEmailError
    input_data = {
        'email': user_data['email'],
        'password_hash': 'new_password_hash',
        'first_name': 'New',
        'last_name': 'User'
    }
    
    with pytest.raises(DuplicateEmailError):
        repo.create_user(input_data)
    
    # Assert find_one was called to check for existing email
    mock_collection.find_one.assert_called_once()
    
    # Assert insert_one was not called
    mock_collection.insert_one.assert_not_called()


@pytest.mark.unit
def test_create_user_duplicate_key_error(mocker):
    """Tests handling of MongoDB duplicate key error during user creation"""
    # Set up test user data using regular_user_data fixture
    user_data = regular_user_data()
    
    # Mock MongoDB collection find_one to return None (no existing email)
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = None
    
    # Mock MongoDB collection insert_one to raise pymongo.errors.DuplicateKeyError
    mock_collection.insert_one.side_effect = pymongo.errors.DuplicateKeyError("E11000 duplicate key error")
    
    # Initialize UserRepository with mocked collection
    repo = UserRepository()
    repo._collection = mock_collection
    
    # Call create_user with test data
    input_data = {
        'email': user_data['email'],
        'password_hash': user_data['passwordHash'],
        'first_name': user_data['firstName'],
        'last_name': user_data['lastName']
    }
    
    # Assert that calling create_user raises DuplicateEmailError
    with pytest.raises(DuplicateEmailError):
        repo.create_user(input_data)
    
    # Assert find_one was called to check for existing email
    mock_collection.find_one.assert_called_once()
    
    # Assert insert_one was called with correct parameters
    mock_collection.insert_one.assert_called_once()


@pytest.mark.unit
def test_create_anonymous_user(mocker):
    """Tests creating a new anonymous user successfully"""
    # Set up a test session ID
    session_id = "test-session-123"
    
    # Mock MongoDB collection insert_one method to return a mock result with inserted_id
    mock_collection = MagicMock()
    mock_result = MagicMock()
    mock_result.inserted_id = ObjectId()
    mock_collection.insert_one.return_value = mock_result
    
    # Initialize UserRepository with mocked collection
    repo = UserRepository()
    repo._collection = mock_collection
    
    # Mock get_by_id to return the created anonymous user
    mocker.patch.object(repo, 'get_by_id', return_value={
        '_id': str(mock_result.inserted_id),
        'sessionId': session_id,
        'isAnonymous': True,
        'createdAt': datetime.utcnow().isoformat(),
        'expiresAt': datetime.utcnow().isoformat()
    })
    
    # Call create_anonymous_user with test session ID
    created_user = repo.create_anonymous_user(session_id)
    
    # Assert the user was created with expected data
    assert created_user is not None
    assert created_user['sessionId'] == session_id
    assert created_user['isAnonymous'] is True
    assert 'expiresAt' in created_user
    
    # Assert insert_one was called with correct parameters
    mock_collection.insert_one.assert_called_once()
    args, kwargs = mock_collection.insert_one.call_args
    inserted_doc = args[0]
    assert inserted_doc['sessionId'] == session_id
    assert inserted_doc['isAnonymous'] is True


@pytest.mark.unit
def test_get_by_id(mocker):
    """Tests retrieving a user by ID successfully"""
    # Set up test user data with known ID
    user_data = regular_user_data()
    user_id = user_data['_id']
    
    # Mock MongoDB collection find_one method to return test user
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = user_data
    
    # Initialize UserRepository with mocked collection
    repo = UserRepository()
    repo._collection = mock_collection
    
    # Call get_by_id with test ID
    found_user = repo.get_by_id(user_id)
    
    # Assert the returned user matches expected data
    assert found_user is not None
    assert found_user['_id'] == user_id
    assert found_user['email'] == user_data['email']
    assert 'passwordHash' not in found_user
    
    # Assert find_one was called with correct query parameters
    mock_collection.find_one.assert_called_once()
    args, kwargs = mock_collection.find_one.call_args
    query = args[0]
    assert '_id' in query
    assert query['_id'] == ObjectId(user_id)


@pytest.mark.unit
def test_get_by_id_include_password(mocker):
    """Tests retrieving a user by ID with password hash included"""
    # Set up test user data with known ID and password hash
    user_data = regular_user_data()
    user_id = user_data['_id']
    
    # Mock MongoDB collection find_one method to return test user
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = user_data
    
    # Initialize UserRepository with mocked collection
    repo = UserRepository()
    repo._collection = mock_collection
    
    # Call get_by_id with test ID and include_password_hash=True
    found_user = repo.get_by_id(user_id, include_password_hash=True)
    
    # Assert the returned user matches expected data
    assert found_user is not None
    assert found_user['_id'] == user_id
    assert 'passwordHash' in found_user
    
    # Assert find_one was called with correct query parameters
    mock_collection.find_one.assert_called_once()
    args, kwargs = mock_collection.find_one.call_args
    query = args[0]
    assert '_id' in query
    assert query['_id'] == ObjectId(user_id)
    # Should not exclude passwordHash in the projection
    assert args[1] is None


@pytest.mark.unit
def test_get_by_id_not_found(mocker):
    """Tests retrieving a user by ID that doesn't exist"""
    # Mock MongoDB collection find_one method to return None
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = None
    
    # Initialize UserRepository with mocked collection
    repo = UserRepository()
    repo._collection = mock_collection
    
    # Call get_by_id with a non-existent ID
    non_existent_id = str(ObjectId())
    found_user = repo.get_by_id(non_existent_id)
    
    # Assert None is returned
    assert found_user is None
    
    # Assert find_one was called with correct query parameters
    mock_collection.find_one.assert_called_once()
    args, kwargs = mock_collection.find_one.call_args
    query = args[0]
    assert '_id' in query
    assert query['_id'] == ObjectId(non_existent_id)


@pytest.mark.unit
def test_get_by_email(mocker):
    """Tests retrieving a user by email successfully"""
    # Set up test user data with known email
    user_data = regular_user_data()
    email = user_data['email']
    
    # Mock MongoDB collection find_one method to return test user
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = user_data
    
    # Initialize UserRepository with mocked collection
    repo = UserRepository()
    repo._collection = mock_collection
    
    # Call get_by_email with test email
    found_user = repo.get_by_email(email)
    
    # Assert the returned user matches expected data
    assert found_user is not None
    assert found_user['_id'] == user_data['_id']
    assert found_user['email'] == email
    assert 'passwordHash' not in found_user
    
    # Assert find_one was called with correct query parameters
    mock_collection.find_one.assert_called_once()
    args, kwargs = mock_collection.find_one.call_args
    query = args[0]
    assert 'email' in query
    # Assert case-insensitive email search was performed
    assert '$regex' in query['email']
    assert '$options' in query['email']
    assert 'i' in query['email']['$options']


@pytest.mark.unit
def test_get_by_email_not_found(mocker):
    """Tests retrieving a user by email that doesn't exist"""
    # Mock MongoDB collection find_one method to return None
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = None
    
    # Initialize UserRepository with mocked collection
    repo = UserRepository()
    repo._collection = mock_collection
    
    # Call get_by_email with a non-existent email
    non_existent_email = "nonexistent@example.com"
    found_user = repo.get_by_email(non_existent_email)
    
    # Assert None is returned
    assert found_user is None
    
    # Assert find_one was called with correct query parameters
    mock_collection.find_one.assert_called_once()
    args, kwargs = mock_collection.find_one.call_args
    query = args[0]
    assert 'email' in query


@pytest.mark.unit
def test_get_by_session(mocker):
    """Tests retrieving an anonymous user by session ID"""
    # Set up anonymous user data with known session ID
    user_data = anonymous_user_data()
    session_id = user_data['sessionId']
    
    # Mock MongoDB collection find_one method to return test user
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = user_data
    
    # Initialize UserRepository with mocked collection
    repo = UserRepository()
    repo._collection = mock_collection
    
    # Call get_by_session with test session ID
    found_user = repo.get_by_session(session_id)
    
    # Assert the returned user matches expected data
    assert found_user is not None
    assert found_user['_id'] == user_data['_id']
    assert found_user['sessionId'] == session_id
    assert found_user['isAnonymous'] is True
    
    # Assert find_one was called with correct query parameters
    mock_collection.find_one.assert_called_once()
    args, kwargs = mock_collection.find_one.call_args
    query = args[0]
    assert 'sessionId' in query
    assert query['sessionId'] == session_id


@pytest.mark.unit
def test_get_by_session_expired(mocker):
    """Tests retrieving an expired anonymous user by session ID"""
    # Set up anonymous user data with expired expiresAt timestamp
    user_data = anonymous_user_data()
    session_id = user_data['sessionId']
    # Set expiration time in the past
    user_data['expiresAt'] = datetime.utcnow().replace(year=2000)
    
    # Mock MongoDB collection find_one method to return expired user
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = user_data
    mock_collection.delete_one = MagicMock()
    
    # Initialize UserRepository with mocked collection
    repo = UserRepository()
    repo._collection = mock_collection
    
    # Call get_by_session with test session ID
    found_user = repo.get_by_session(session_id)
    
    # Assert None is returned
    assert found_user is None
    
    # Assert delete_one was called to remove the expired user
    mock_collection.delete_one.assert_called_once()
    args, kwargs = mock_collection.delete_one.call_args
    query = args[0]
    assert '_id' in query
    assert query['_id'] == user_data['_id']


@pytest.mark.unit
def test_update_user(mocker):
    """Tests updating a user's profile information"""
    # Set up test user data with known ID
    user_data = regular_user_data()
    user_id = user_data['_id']
    
    # Set up update data for the user (firstName, lastName)
    update_data = {
        'firstName': 'Updated',
        'lastName': 'User'
    }
    
    # Mock MongoDB collection update_one method to return successful result (modified_count=1)
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = user_data
    mock_result = MagicMock()
    mock_result.modified_count = 1
    mock_collection.update_one.return_value = mock_result
    
    # Initialize UserRepository with mocked collection
    repo = UserRepository()
    repo._collection = mock_collection
    
    # Mock get_by_id to return updated user
    updated_user = dict(user_data)
    updated_user.update(update_data)
    mocker.patch.object(repo, 'get_by_id', return_value=updated_user)
    
    # Call update_user with user ID and update data
    result = repo.update_user(user_id, update_data)
    
    # Assert the result matches expected updated user
    assert result is not None
    assert result['firstName'] == update_data['firstName']
    assert result['lastName'] == update_data['lastName']
    
    # Assert update_one was called with correct parameters
    mock_collection.update_one.assert_called_once()
    args, kwargs = mock_collection.update_one.call_args
    query, update = args
    assert query['_id'] == ObjectId(user_id)
    assert '$set' in update
    assert 'firstName' in update['$set']
    assert 'lastName' in update['$set']
    
    # Assert restricted fields were not included in update
    assert 'email' not in update['$set']
    assert 'passwordHash' not in update['$set']


@pytest.mark.unit
def test_update_user_not_found(mocker):
    """Tests updating a user that doesn't exist"""
    # Set up update data for a user
    user_id = str(ObjectId())
    update_data = {
        'firstName': 'Updated',
        'lastName': 'User'
    }
    
    # Mock MongoDB collection update_one method to return unsuccessful result (modified_count=0)
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = None
    
    # Initialize UserRepository with mocked collection
    repo = UserRepository()
    repo._collection = mock_collection
    
    # Call update_user with non-existent ID and update data
    with pytest.raises(UserNotFoundError):
        repo.update_user(user_id, update_data)
    
    # Assert update_one was called with correct parameters
    mock_collection.update_one.assert_not_called()


@pytest.mark.unit
def test_update_email(mocker):
    """Tests updating a user's email address"""
    # Set up test user data with known ID
    user_data = regular_user_data()
    user_id = user_data['_id']
    
    # Set up new email address
    new_email = "new.email@example.com"
    
    # Mock MongoDB collection find_one to return None for email check
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = None
    
    # Mock MongoDB collection update_one method to return successful result
    mock_result = MagicMock()
    mock_result.matched_count = 1
    mock_collection.update_one.return_value = mock_result
    
    # Initialize UserRepository with mocked collection
    repo = UserRepository()
    repo._collection = mock_collection
    
    # Mock get_by_id for retrieving updated user
    updated_user = dict(user_data)
    updated_user['email'] = new_email
    updated_user['emailVerified'] = False
    mocker.patch.object(repo, 'get_by_id', return_value=updated_user)
    
    # Call update_email with user ID and new email
    result = repo.update_email(user_id, new_email)
    
    # Assert the result contains updated email
    assert result['email'] == new_email
    
    # Assert emailVerified is set to False
    assert result['emailVerified'] is False
    
    # Assert find_one was called to check existing email
    mock_collection.find_one.assert_called_once()
    
    # Assert update_one was called with correct parameters
    mock_collection.update_one.assert_called_once()
    args, kwargs = mock_collection.update_one.call_args
    query, update = args
    assert query['_id'] == ObjectId(user_id)
    assert '$set' in update
    assert update['$set']['email'] == new_email
    assert update['$set']['emailVerified'] is False


@pytest.mark.unit
def test_update_email_duplicate(mocker):
    """Tests updating email to one that already exists"""
    # Set up test user data with known ID
    user_data = regular_user_data()
    user_id = user_data['_id']
    
    # Set up new email address
    new_email = "existing@example.com"
    
    # Mock MongoDB collection find_one to return another user with the same email
    existing_user = dict(regular_user_data())
    existing_user['_id'] = str(ObjectId())  # Different ID
    existing_user['email'] = new_email
    
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = existing_user
    
    # Initialize UserRepository with mocked collection
    repo = UserRepository()
    repo._collection = mock_collection
    
    # Assert calling update_email raises DuplicateEmailError
    with pytest.raises(DuplicateEmailError):
        repo.update_email(user_id, new_email)
    
    # Assert find_one was called to check existing email
    mock_collection.find_one.assert_called_once()
    
    # Assert update_one was not called
    mock_collection.update_one.assert_not_called()


@pytest.mark.unit
def test_update_password(mocker):
    """Tests updating a user's password hash"""
    # Set up test user data with known ID
    user_data = regular_user_data()
    user_id = user_data['_id']
    
    # Set up new password hash
    new_password_hash = "new_hashed_password_123"
    
    # Mock MongoDB collection update_one method to return successful result
    mock_collection = MagicMock()
    mock_result = MagicMock()
    mock_result.matched_count = 1
    mock_collection.update_one.return_value = mock_result
    
    # Initialize UserRepository with mocked collection
    repo = UserRepository()
    repo._collection = mock_collection
    
    # Call update_password with user ID and new password hash
    result = repo.update_password(user_id, new_password_hash)
    
    # Assert True is returned
    assert result is True
    
    # Assert update_one was called with correct parameters
    mock_collection.update_one.assert_called_once()
    args, kwargs = mock_collection.update_one.call_args
    query, update = args
    assert query['_id'] == ObjectId(user_id)
    assert '$set' in update
    assert update['$set']['passwordHash'] == new_password_hash


@pytest.mark.unit
def test_update_password_user_not_found(mocker):
    """Tests updating password for a user that doesn't exist"""
    # Set up new password hash
    user_id = str(ObjectId())
    new_password_hash = "new_hashed_password_123"
    
    # Mock MongoDB collection update_one method to return unsuccessful result (modified_count=0)
    mock_collection = MagicMock()
    mock_result = MagicMock()
    mock_result.matched_count = 0
    mock_collection.update_one.return_value = mock_result
    
    # Initialize UserRepository with mocked collection
    repo = UserRepository()
    repo._collection = mock_collection
    
    # Call update_password with non-existent ID and new password hash
    with pytest.raises(UserNotFoundError):
        repo.update_password(user_id, new_password_hash)
    
    # Assert update_one was called with correct parameters
    mock_collection.update_one.assert_called_once()
    args, kwargs = mock_collection.update_one.call_args
    query, update = args
    assert query['_id'] == ObjectId(user_id)


@pytest.mark.unit
def test_delete_user(mocker):
    """Tests deleting a user from the database"""
    # Set up test user data with known ID
    user_data = regular_user_data()
    user_id = user_data['_id']
    
    # Mock MongoDB collection delete_one method to return successful result (deleted_count=1)
    mock_collection = MagicMock()
    mock_result = MagicMock()
    mock_result.deleted_count = 1
    mock_collection.delete_one.return_value = mock_result
    
    # Initialize UserRepository with mocked collection
    repo = UserRepository()
    repo._collection = mock_collection
    
    # Call delete_user with user ID
    result = repo.delete_user(user_id)
    
    # Assert True is returned
    assert result is True
    
    # Assert delete_one was called with correct parameters
    mock_collection.delete_one.assert_called_once()
    args, kwargs = mock_collection.delete_one.call_args
    query = args[0]
    assert query['_id'] == ObjectId(user_id)


@pytest.mark.unit
def test_delete_user_not_found(mocker):
    """Tests deleting a user that doesn't exist"""
    # Mock MongoDB collection delete_one method to return unsuccessful result (deleted_count=0)
    mock_collection = MagicMock()
    mock_result = MagicMock()
    mock_result.deleted_count = 0
    mock_collection.delete_one.return_value = mock_result
    
    # Initialize UserRepository with mocked collection
    repo = UserRepository()
    repo._collection = mock_collection
    
    # Call delete_user with non-existent ID
    user_id = str(ObjectId())
    result = repo.delete_user(user_id)
    
    # Assert False is returned
    assert result is False
    
    # Assert delete_one was called with correct parameters
    mock_collection.delete_one.assert_called_once()
    args, kwargs = mock_collection.delete_one.call_args
    query = args[0]
    assert query['_id'] == ObjectId(user_id)


@pytest.mark.unit
def test_verify_email(mocker):
    """Tests verifying a user's email address"""
    # Set up test user data with known ID
    user_data = regular_user_data()
    user_id = user_data['_id']
    
    # Mock MongoDB collection update_one method to return successful result
    mock_collection = MagicMock()
    mock_result = MagicMock()
    mock_result.matched_count = 1
    mock_collection.update_one.return_value = mock_result
    
    # Initialize UserRepository with mocked collection
    repo = UserRepository()
    repo._collection = mock_collection
    
    # Call verify_email with user ID
    result = repo.verify_email(user_id)
    
    # Assert True is returned
    assert result is True
    
    # Assert update_one was called with correct parameters
    mock_collection.update_one.assert_called_once()
    args, kwargs = mock_collection.update_one.call_args
    query, update = args
    assert query['_id'] == ObjectId(user_id)
    assert '$set' in update
    assert 'emailVerified' in update['$set']
    assert update['$set']['emailVerified'] is True


@pytest.mark.unit
def test_convert_anonymous_to_registered(mocker):
    """Tests converting an anonymous user to a registered user"""
    # Set up anonymous user data with session ID
    anonymous_data = anonymous_user_data()
    session_id = anonymous_data['sessionId']
    
    # Set up registration data with email and password
    reg_data = {
        'email': 'registered@example.com',
        'password_hash': 'hashed_password_123',
        'first_name': 'Former',
        'last_name': 'Anonymous'
    }
    
    # Mock MongoDB collection find_one to find anonymous user by session ID
    mock_collection = MagicMock()
    mock_collection.find_one.side_effect = [
        anonymous_data,  # First call: find anonymous user
        None,  # Second call: check if email exists
    ]
    
    # Mock update_one to return successful result
    mock_result = MagicMock()
    mock_result.modified_count = 1
    mock_collection.update_one.return_value = mock_result
    
    # Initialize UserRepository with mocked collection
    repo = UserRepository()
    repo._collection = mock_collection
    
    # Mock get_by_id to return the updated user
    updated_user = {
        '_id': anonymous_data['_id'],
        'email': reg_data['email'],
        'firstName': reg_data['first_name'],
        'lastName': reg_data['last_name'],
        'isAnonymous': False,
        'emailVerified': False,
        'accountStatus': 'active',
        'createdAt': datetime.utcnow().isoformat()
    }
    mocker.patch.object(repo, 'get_by_id', return_value=updated_user)
    
    # Call convert_anonymous_to_registered with session ID and registration data
    result = repo.convert_anonymous_to_registered(session_id, reg_data)
    
    # Assert returned user has correct email and is not anonymous
    assert result is not None
    assert result['email'] == reg_data['email']
    assert result['isAnonymous'] is False
    
    # Assert sessionId and expiresAt were removed
    assert 'sessionId' not in result
    assert 'expiresAt' not in result
    
    # Assert update_one was called with correct parameters
    mock_collection.update_one.assert_called_once()
    args, kwargs = mock_collection.update_one.call_args
    query, update = args
    assert query['_id'] == anonymous_data['_id']
    assert '$set' in update
    assert '$unset' in update
    assert update['$set']['email'] == reg_data['email']
    assert update['$set']['passwordHash'] == reg_data['password_hash']
    assert update['$set']['isAnonymous'] is False
    assert 'sessionId' in update['$unset']
    assert 'expiresAt' in update['$unset']


@pytest.mark.unit
def test_convert_anonymous_user_not_found(mocker):
    """Tests converting a non-existent anonymous user"""
    # Set up registration data with email and password
    session_id = 'nonexistent-session'
    reg_data = {
        'email': 'registered@example.com',
        'password_hash': 'hashed_password_123',
        'first_name': 'New',
        'last_name': 'User'
    }
    
    # Mock MongoDB collection find_one to return None (no user with session ID)
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = None
    
    # Initialize UserRepository with mocked collection
    repo = UserRepository()
    repo._collection = mock_collection
    
    # Assert calling convert_anonymous_to_registered raises UserNotFoundError
    with pytest.raises(UserNotFoundError):
        repo.convert_anonymous_to_registered(session_id, reg_data)
    
    # Assert find_one was called to check for anonymous user
    mock_collection.find_one.assert_called_once()
    args, kwargs = mock_collection.find_one.call_args
    query = args[0]
    assert 'sessionId' in query
    assert query['sessionId'] == session_id
    assert 'isAnonymous' in query
    assert query['isAnonymous'] is True


@pytest.mark.unit
def test_find_users(mocker):
    """Tests finding users with filtering and pagination"""
    # Set up filter criteria (e.g., emailVerified=True)
    filters = {'is_email_verified': True}
    
    # Mock MongoDB collection count_documents to return count
    mock_collection = MagicMock()
    mock_collection.count_documents.return_value = 2
    
    # Mock MongoDB collection find to return cursor with sample users
    users = [
        {'_id': ObjectId(), 'email': 'user1@example.com', 'emailVerified': True},
        {'_id': ObjectId(), 'email': 'user2@example.com', 'emailVerified': True}
    ]
    mock_cursor = MagicMock()
    mock_cursor.__iter__.return_value = iter(users)
    mock_collection.find.return_value = mock_cursor
    
    # Initialize UserRepository with mocked collection
    repo = UserRepository()
    repo._collection = mock_collection
    
    # Patch object_id_to_str to handle our ObjectId objects
    mocker.patch('src.backend.data.mongodb.repositories.user_repository.object_id_to_str', 
                 side_effect=lambda x: str(x))
    
    # Call find_users with filter criteria and pagination params
    result_users, count = repo.find_users(filters, skip=0, limit=10)
    
    # Assert the returned users and count match expected values
    assert len(result_users) == 2
    assert count == 2
    
    # Assert count_documents was called with correct filter
    mock_collection.count_documents.assert_called_once()
    args, kwargs = mock_collection.count_documents.call_args
    query = args[0]
    assert 'emailVerified' in query
    assert query['emailVerified'] is True
    
    # Assert find was called with correct query, projection, skip, limit, and sort
    mock_collection.find.assert_called_once()
    args, kwargs = mock_collection.find.call_args
    query = args[0]
    assert 'emailVerified' in query
    assert query['emailVerified'] is True
    assert 'projection' in kwargs
    assert kwargs['projection']['passwordHash'] == 0
    assert kwargs['skip'] == 0
    assert kwargs['limit'] == 10


@pytest.mark.unit
def test_cleanup_expired_anonymous(mocker):
    """Tests cleaning up expired anonymous users"""
    # Mock MongoDB collection delete_many to return result with deleted_count
    mock_collection = MagicMock()
    mock_result = MagicMock()
    mock_result.deleted_count = 5
    mock_collection.delete_many.return_value = mock_result
    
    # Initialize UserRepository with mocked collection
    repo = UserRepository()
    repo._collection = mock_collection
    
    # Call cleanup_expired_anonymous
    result = repo.cleanup_expired_anonymous()
    
    # Assert the returned count matches delete_many result
    assert result == 5
    
    # Assert delete_many was called with correct query (isAnonymous=True, expiresAt < now)
    mock_collection.delete_many.assert_called_once()
    args, kwargs = mock_collection.delete_many.call_args
    query = args[0]
    assert 'isAnonymous' in query
    assert query['isAnonymous'] is True
    assert 'expiresAt' in query
    assert '$lt' in query['expiresAt']


@pytest.mark.unit
def test_update_user_preferences(mocker):
    """Tests updating a user's preferences"""
    # Set up test user data with known ID
    user_data = user_with_preferences()
    user_id = user_data['_id']
    
    # Set up new preferences data
    new_preferences = {
        'theme': 'light',
        'fontSize': 16,
        'defaultPromptCategories': ['grammar', 'concise']
    }
    
    # Mock MongoDB collection update_one to return successful result
    mock_collection = MagicMock()
    mock_result = MagicMock()
    mock_result.matched_count = 1
    mock_collection.update_one.return_value = mock_result
    
    # Mock MongoDB collection find_one to return updated user with preferences
    updated_user = {'_id': ObjectId(user_id), 'preferences': new_preferences}
    mock_collection.find_one.return_value = updated_user
    
    # Initialize UserRepository with mocked collection
    repo = UserRepository()
    repo._collection = mock_collection
    
    # Call update_user_preferences with user ID and preferences data
    result = repo.update_user_preferences(user_id, new_preferences)
    
    # Assert the returned preferences match expected values
    assert result == new_preferences
    
    # Assert update_one was called with correct parameters
    mock_collection.update_one.assert_called_once()
    args, kwargs = mock_collection.update_one.call_args
    query, update = args
    assert query['_id'] == ObjectId(user_id)
    assert '$set' in update
    assert update['$set']['preferences'] == new_preferences
    
    # Assert find_one was called to retrieve updated user
    mock_collection.find_one.assert_called_once()
    args, kwargs = mock_collection.find_one.call_args
    query = args[0]
    assert query['_id'] == ObjectId(user_id)
    assert kwargs['projection'] == {'preferences': 1}