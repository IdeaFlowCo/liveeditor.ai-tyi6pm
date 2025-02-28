import pytest
from unittest.mock import MagicMock, patch

from src.backend.core.auth.user_service import UserService
from src.backend.core.auth.password_service import PasswordService
from src.backend.data.mongodb.repositories.user_repository import UserRepository
from src.backend.core.utils.validators import UserNotFoundError, ValidationError, AuthenticationError, InvalidTokenError
from src.backend.tests.fixtures.user_fixtures import sample_user_data, sample_user_credentials

@patch('src.backend.data.mongodb.repositories.user_repository.UserRepository')
def test_create_user(mock_user_repository):
    # Set up mock UserRepository
    mock_repo = mock_user_repository.return_value
    
    # Create sample user data
    user_data = sample_user_data()
    
    # Mock repository create method to return user with ID
    mock_repo.create_user.return_value = user_data
    
    # Create UserService instance with mocked repository
    user_service = UserService(mock_repo)
    
    # Call create_user with sample data
    result = user_service.create_user(
        user_data["email"], 
        "SecurePassword123!", 
        {
            "first_name": user_data["firstName"],
            "last_name": user_data["lastName"]
        }
    )
    
    # Assert that repository create method was called with correct data
    mock_repo.create_user.assert_called_once()
    
    # Assert that returned user has expected properties
    assert result["email"] == user_data["email"]
    assert result["firstName"] == user_data["firstName"]
    assert result["lastName"] == user_data["lastName"]
    assert "_id" in result

@patch('src.backend.data.mongodb.repositories.user_repository.UserRepository')
def test_create_user_with_duplicate_email(mock_user_repository):
    # Set up mock UserRepository
    mock_repo = mock_user_repository.return_value
    
    # Create sample user data
    user_data = sample_user_data()
    
    # Mock repository to raise exception for duplicate email
    mock_repo.create_user.side_effect = ValidationError("Email already exists")
    
    # Create UserService instance with mocked repository
    user_service = UserService(mock_repo)
    
    # Assert that calling create_user with duplicate email raises ValidationError
    with pytest.raises(ValidationError) as excinfo:
        user_service.create_user(
            user_data["email"],
            "SecurePassword123!",
            {
                "first_name": user_data["firstName"],
                "last_name": user_data["lastName"]
            }
        )
    
    # Verify that error message contains information about duplicate email
    assert "Email already exists" in str(excinfo.value)

@pytest.mark.parametrize('invalid_field, invalid_value, expected_error', [
    ('email', 'not_an_email', 'Invalid email'),
    ('password', '123', 'Password must'),
    ('first_name', '', 'First name is required'),
])
@patch('src.backend.data.mongodb.repositories.user_repository.UserRepository')
def test_create_user_with_invalid_data(mock_user_repository, invalid_field, invalid_value, expected_error):
    # Set up mock UserRepository
    mock_repo = mock_user_repository.return_value
    
    # Create sample user data with the specified invalid field
    user_data = sample_user_data()
    
    # Create UserService instance with mocked repository
    user_service = UserService(mock_repo)
    
    # Prepare valid data
    email = user_data["email"]
    password = "SecurePassword123!"
    profile_data = {
        "first_name": user_data["firstName"],
        "last_name": user_data["lastName"]
    }
    
    # Override with invalid data
    if invalid_field == 'email':
        email = invalid_value
    elif invalid_field == 'password':
        password = invalid_value
    elif invalid_field == 'first_name':
        profile_data['first_name'] = invalid_value
    
    # Assert that calling create_user with invalid data raises ValidationError
    with pytest.raises(ValidationError) as excinfo:
        user_service.create_user(email, password, profile_data)
    
    # Verify that error message contains information about the invalid field
    assert expected_error in str(excinfo.value)

@patch('src.backend.data.mongodb.repositories.user_repository.UserRepository')
@patch('src.backend.core.auth.password_service.PasswordService')
def test_authenticate_user_success(mock_password_service, mock_user_repository):
    # Set up mock UserRepository and PasswordService
    mock_repo = mock_user_repository.return_value
    mock_password = mock_password_service.return_value
    
    # Create sample credentials and user data
    credentials = sample_user_credentials()
    user = sample_user_data()
    
    # Mock repository to return a user with matching email
    mock_repo.get_by_email.return_value = user
    
    # Mock password service to verify password as valid
    mock_password.verify_password.return_value = True
    
    # Create UserService instance with mocked dependencies
    user_service = UserService(mock_repo, None, mock_password, None)
    
    # Call authenticate with sample credentials
    result = user_service.authenticate(credentials['email'], credentials['password'])
    
    # Assert that repository find_by_email was called with correct email
    mock_repo.get_by_email.assert_called_with(credentials['email'], include_password_hash=True)
    
    # Assert that password service verify_password was called with correct password
    mock_password.verify_password.assert_called_with(credentials['password'], user['passwordHash'])
    
    # Assert that returned user matches expected user
    assert result['_id'] == user['_id']
    assert result['email'] == user['email']

@patch('src.backend.data.mongodb.repositories.user_repository.UserRepository')
def test_authenticate_user_invalid_email(mock_user_repository):
    # Set up mock UserRepository
    mock_repo = mock_user_repository.return_value
    
    # Create sample credentials with non-existent email
    credentials = sample_user_credentials()
    credentials['email'] = 'nonexistent@example.com'
    
    # Mock repository to return None for non-existent email
    mock_repo.get_by_email.return_value = None
    
    # Create UserService instance with mocked repository
    user_service = UserService(mock_repo)
    
    # Assert that calling authenticate with invalid email raises AuthenticationError
    with pytest.raises(AuthenticationError) as excinfo:
        user_service.authenticate(credentials['email'], credentials['password'])
    
    # Verify that error message indicates invalid credentials
    assert "Invalid credentials" in str(excinfo.value)

@patch('src.backend.data.mongodb.repositories.user_repository.UserRepository')
@patch('src.backend.core.auth.password_service.PasswordService')
def test_authenticate_user_invalid_password(mock_password_service, mock_user_repository):
    # Set up mock UserRepository and PasswordService
    mock_repo = mock_user_repository.return_value
    mock_password = mock_password_service.return_value
    
    # Create sample credentials and user data
    credentials = sample_user_credentials()
    user = sample_user_data()
    
    # Mock repository to return a user with matching email
    mock_repo.get_by_email.return_value = user
    
    # Mock password service to verify password as invalid
    mock_password.verify_password.return_value = False
    
    # Create UserService instance with mocked dependencies
    user_service = UserService(mock_repo, None, mock_password, None)
    
    # Assert that calling authenticate with incorrect password raises AuthenticationError
    with pytest.raises(AuthenticationError) as excinfo:
        user_service.authenticate(credentials['email'], credentials['password'])
    
    # Verify that error message indicates invalid credentials
    assert "Invalid credentials" in str(excinfo.value)

@patch('src.backend.data.mongodb.repositories.user_repository.UserRepository')
def test_get_user_by_id(mock_user_repository):
    # Set up mock UserRepository
    mock_repo = mock_user_repository.return_value
    
    # Create sample user ID and data
    user = sample_user_data()
    user_id = user['_id']
    
    # Mock repository to return user for the given ID
    mock_repo.get_by_id.return_value = user
    
    # Create UserService instance with mocked repository
    user_service = UserService(mock_repo)
    
    # Call get_user_by_id with sample ID
    result = user_service.get_user_by_id(user_id)
    
    # Assert that repository find_by_id was called with correct ID
    mock_repo.get_by_id.assert_called_with(user_id)
    
    # Assert that returned user matches expected user
    assert result['_id'] == user['_id']
    assert result['email'] == user['email']

@patch('src.backend.data.mongodb.repositories.user_repository.UserRepository')
def test_get_user_by_id_not_found(mock_user_repository):
    # Set up mock UserRepository
    mock_repo = mock_user_repository.return_value
    
    # Create sample non-existent user ID
    user_id = "nonexistent_id"
    
    # Mock repository to return None for the given ID
    mock_repo.get_by_id.return_value = None
    
    # Create UserService instance with mocked repository
    user_service = UserService(mock_repo)
    
    # Assert that calling get_user_by_id with non-existent ID raises UserNotFoundError
    with pytest.raises(UserNotFoundError) as excinfo:
        user_service.get_user_by_id(user_id)
    
    # Verify that error message contains the user ID
    assert user_id in str(excinfo.value)

@patch('src.backend.data.mongodb.repositories.user_repository.UserRepository')
def test_get_user_by_email(mock_user_repository):
    # Set up mock UserRepository
    mock_repo = mock_user_repository.return_value
    
    # Create sample user email and data
    user = sample_user_data()
    email = user['email']
    
    # Mock repository to return user for the given email
    mock_repo.get_by_email.return_value = user
    
    # Create UserService instance with mocked repository
    user_service = UserService(mock_repo)
    
    # Call get_user_by_email with sample email
    result = user_service.get_user_by_email(email)
    
    # Assert that repository find_by_email was called with correct email
    mock_repo.get_by_email.assert_called_with(email)
    
    # Assert that returned user matches expected user
    assert result['_id'] == user['_id']
    assert result['email'] == user['email']

@patch('src.backend.data.mongodb.repositories.user_repository.UserRepository')
def test_update_profile(mock_user_repository):
    # Set up mock UserRepository
    mock_repo = mock_user_repository.return_value
    
    # Create sample user ID and updated profile data
    user = sample_user_data()
    user_id = user['_id']
    updated_profile = {
        "firstName": "Updated",
        "lastName": "Name"
    }
    
    # Mock repository find_by_id to return existing user
    mock_repo.get_by_id.return_value = user
    
    # Mock repository update to return updated user
    updated_user = dict(user)
    updated_user.update({
        "firstName": updated_profile["firstName"],
        "lastName": updated_profile["lastName"]
    })
    mock_repo.update_user.return_value = updated_user
    
    # Create UserService instance with mocked repository
    user_service = UserService(mock_repo)
    
    # Call update_profile with user ID and updated data
    result = user_service.update_profile(user_id, updated_profile)
    
    # Assert that repository find_by_id was called with correct ID
    mock_repo.get_by_id.assert_called_with(user_id)
    
    # Assert that repository update was called with correct data
    mock_repo.update_user.assert_called_once()
    
    # Assert that returned user has updated properties
    assert result['firstName'] == updated_profile['firstName']
    assert result['lastName'] == updated_profile['lastName']

@patch('src.backend.data.mongodb.repositories.user_repository.UserRepository')
@patch('src.backend.core.auth.password_service.PasswordService')
def test_change_password(mock_password_service, mock_user_repository):
    # Set up mock UserRepository and PasswordService
    mock_repo = mock_user_repository.return_value
    mock_password = mock_password_service.return_value
    
    # Create sample user ID, current password, and new password
    user = sample_user_data()
    user_id = user['_id']
    current_password = "CurrentPassword123!"
    new_password = "NewPassword456!"
    
    # Mock repository find_by_id to return existing user
    mock_repo.get_by_id.return_value = user
    
    # Mock password service verify_password to return True for current password
    mock_password.verify_password.return_value = True
    
    # Mock password service hash_password to return hashed new password
    new_password_hash = "hashed_new_password"
    mock_password.hash_password.return_value = new_password_hash
    
    # Mock repository update to return updated user
    updated_user = dict(user)
    updated_user['passwordHash'] = new_password_hash
    mock_repo.update_password.return_value = True
    
    # Create UserService instance with mocked dependencies
    user_service = UserService(mock_repo, None, mock_password, None)
    
    # Call change_password with user ID, current password, and new password
    result = user_service.change_password(user_id, current_password, new_password)
    
    # Assert that password service verify_password was called with current password
    mock_password.verify_password.assert_called_with(current_password, user['passwordHash'])
    
    # Assert that password service hash_password was called with new password
    mock_password.hash_password.assert_called_with(new_password)
    
    # Assert that repository update was called with updated password hash
    mock_repo.update_password.assert_called_once()
    
    # Assert that operation was successful
    assert result is True

@patch('src.backend.data.mongodb.repositories.user_repository.UserRepository')
def test_request_password_reset(mock_user_repository):
    # Set up mock UserRepository
    mock_repo = mock_user_repository.return_value
    
    # Create sample user email
    user = sample_user_data()
    email = user['email']
    
    # Mock repository find_by_email to return existing user
    mock_repo.get_by_email.return_value = user
    
    # Mock repository update to store reset token
    reset_token = "reset_token_123"
    mock_repo.store_reset_token.return_value = True
    
    # Create UserService instance with mocked repository
    user_service = UserService(mock_repo)
    
    # Call request_password_reset with email
    result = user_service.request_password_reset(email)
    
    # Assert that repository find_by_email was called with correct email
    mock_repo.get_by_email.assert_called_with(email)
    
    # Assert that repository update was called with reset token
    mock_repo.store_reset_token.assert_called_once()
    
    # Assert that reset token is returned
    assert 'user_id' in result
    assert 'reset_token' in result

@patch('src.backend.data.mongodb.repositories.user_repository.UserRepository')
@patch('src.backend.core.auth.password_service.PasswordService')
def test_reset_password(mock_password_service, mock_user_repository):
    # Set up mock UserRepository and PasswordService
    mock_repo = mock_user_repository.return_value
    mock_password = mock_password_service.return_value
    
    # Create sample reset token and new password
    reset_token = "reset_token_123"
    new_password = "NewPassword456!"
    user = sample_user_data()
    user_id = user['_id']
    
    # Mock password service validate reset token to return True
    mock_password.validate_reset_token.return_value = True
    
    # Mock password service hash_password to return hashed new password
    new_password_hash = "hashed_new_password"
    mock_password.hash_password.return_value = new_password_hash
    
    # Mock repository update to return updated user
    mock_repo.update_password.return_value = True
    mock_repo.clear_reset_token.return_value = True
    
    # Create UserService instance with mocked dependencies
    user_service = UserService(mock_repo, None, mock_password, None)
    
    # Call reset_password with token and new password
    result = user_service.reset_password(user_id, reset_token, new_password)
    
    # Assert that password service validate_reset_token was called with correct token
    mock_password.validate_reset_token.assert_called_with(user_id, reset_token)
    
    # Assert that password service hash_password was called with new password
    mock_password.hash_password.assert_called_with(new_password)
    
    # Assert that repository update was called with new password hash and cleared token
    mock_repo.update_password.assert_called_once()
    mock_repo.clear_reset_token.assert_called_once()
    
    # Assert that operation was successful
    assert result is True

@patch('src.backend.data.mongodb.repositories.user_repository.UserRepository')
@patch('src.backend.core.auth.password_service.PasswordService')
def test_convert_anonymous_user(mock_password_service, mock_user_repository):
    # Set up mock UserRepository and PasswordService
    mock_repo = mock_user_repository.return_value
    mock_password = mock_password_service.return_value
    
    # Create sample anonymous session ID and registration data
    session_id = "anonymous_session_123"
    registration_data = {
        "email": "user@example.com",
        "password": "SecurePassword123!",
        "first_name": "Test",
        "last_name": "User"
    }
    
    # Create anonymous user data
    anonymous_user = {
        "_id": "anon_user_id",
        "isAnonymous": True,
        "sessionId": session_id,
        "documents": [],
        "createdAt": "2023-01-01T00:00:00Z"
    }
    
    # Create converted user data
    converted_user = {
        "_id": anonymous_user["_id"],
        "email": registration_data["email"],
        "firstName": registration_data["first_name"],
        "lastName": registration_data["last_name"],
        "isAnonymous": False,
        "emailVerified": False,
        "accountStatus": "active",
        "createdAt": anonymous_user["createdAt"],
        "documents": []
    }
    
    # Mock repository find_by_session_id to return anonymous user
    mock_repo.get_by_session.return_value = anonymous_user
    
    # Mock password service hash_password to return hashed password
    hashed_password = "hashed_password"
    mock_password.hash_password.return_value = hashed_password
    
    # Mock repository update to return converted user
    mock_repo.convert_anonymous_to_registered.return_value = converted_user
    
    # Create UserService instance with mocked dependencies
    user_service = UserService(mock_repo, None, mock_password, None)
    
    # Call convert_anonymous_user with session ID and registration data
    result = user_service.convert_anonymous_user(session_id, registration_data)
    
    # Assert that repository find_by_session_id was called with correct session ID
    mock_repo.get_by_session.assert_called_with(session_id)
    
    # Assert that password service hash_password was called with password
    mock_password.hash_password.assert_called_with(registration_data["password"])
    
    # Assert that repository update was called with registration data and hashed password
    mock_repo.convert_anonymous_to_registered.assert_called_once()
    
    # Assert that returned user has registered status and email
    assert result["isAnonymous"] is False
    assert result["email"] == registration_data["email"]