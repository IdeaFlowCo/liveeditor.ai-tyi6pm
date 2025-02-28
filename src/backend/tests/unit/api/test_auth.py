import pytest
from unittest.mock import patch, MagicMock
import json
from flask import Flask

# Import the authentication API resources to be tested
from src.backend.api.auth import auth_bp
from src.backend.core.auth.user_service import UserService, AuthenticationError, DuplicateEmailError
from src.backend.core.auth.jwt_service import JWTService, InvalidTokenError
from src.backend.core.auth.anonymous_session import AnonymousSessionManager
from src.backend.api.schemas.auth_schema import LoginSchema, RegisterSchema
from src.backend.tests.fixtures.user_fixtures import mock_user_data, mock_user_credentials

# Test prefix for authentication routes
TEST_PREFIX = '/api/auth'

def setup_test_client():
    """Helper function to create and configure a Flask test client for API testing"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    # Register auth endpoints with Flask-RESTful
    app.register_blueprint(auth_bp)
    
    return app.test_client()

@pytest.mark.unit
@patch('src.backend.core.auth.user_service.UserService')
def test_register_valid_user_data(mock_user_service):
    """Test that the registration endpoint successfully creates a new user with valid data"""
    # Create test client
    client = setup_test_client()
    
    # Mock UserService.register_user to return a user ID
    mock_instance = mock_user_service.return_value
    mock_instance.register_user.return_value = {
        "_id": "user123",
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "token_type": "Bearer",
        "expires_in": 3600
    }
    
    # Prepare valid registration data using user_fixtures
    registration_data = mock_user_data()
    
    # Send POST request to /api/auth/register
    response = client.post(
        f"{TEST_PREFIX}/register",
        data=json.dumps(registration_data),
        content_type='application/json'
    )
    
    # Assert response status code is 201
    assert response.status_code == 201
    
    # Assert response contains user ID and token
    response_data = json.loads(response.data)
    assert "user_id" in response_data
    assert "access_token" in response_data
    assert "refresh_token" in response_data
    
    # Assert UserService.register_user was called with correct arguments
    mock_instance.register_user.assert_called_with(
        email=registration_data["email"],
        password=registration_data["password"],
        profile_data={
            "firstName": registration_data["first_name"],
            "lastName": registration_data["last_name"]
        }
    )

@pytest.mark.unit
def test_register_invalid_user_data():
    """Test that the registration endpoint returns validation error for invalid data"""
    # Create test client
    client = setup_test_client()
    
    # Prepare invalid registration data (missing required fields)
    invalid_data = {
        "email": "invalid-email",
        "password": "short"
    }
    
    # Send POST request to /api/auth/register
    response = client.post(
        f"{TEST_PREFIX}/register",
        data=json.dumps(invalid_data),
        content_type='application/json'
    )
    
    # Assert response status code is 400
    assert response.status_code == 400
    
    # Parse the response data
    response_data = json.loads(response.data)
    
    # Assert response contains validation error messages
    assert "error" in response_data
    assert response_data["error"] == "validation_error"
    assert "details" in response_data

@pytest.mark.unit
@patch('src.backend.core.auth.user_service.UserService')
def test_register_duplicate_email(mock_user_service):
    """Test that the registration endpoint handles duplicate email addresses"""
    # Create test client
    client = setup_test_client()
    
    # Mock UserService.register_user to raise DuplicateEmailError
    mock_instance = mock_user_service.return_value
    mock_instance.register_user.side_effect = DuplicateEmailError("Email already exists")
    
    # Prepare valid registration data
    registration_data = mock_user_data()
    
    # Send POST request to /api/auth/register
    response = client.post(
        f"{TEST_PREFIX}/register",
        data=json.dumps(registration_data),
        content_type='application/json'
    )
    
    # Assert response status code is 409 (Conflict)
    assert response.status_code == 409
    
    # Parse the response data
    response_data = json.loads(response.data)
    
    # Assert response contains appropriate error message
    assert "error" in response_data
    assert "message" in response_data
    assert "email already exists" in response_data["message"].lower()
    
    # Assert UserService.register_user was called with correct arguments
    mock_instance.register_user.assert_called_with(
        email=registration_data["email"],
        password=registration_data["password"],
        profile_data={
            "firstName": registration_data["first_name"],
            "lastName": registration_data["last_name"]
        }
    )

@pytest.mark.unit
@patch('src.backend.core.auth.user_service.UserService')
@patch('src.backend.core.auth.jwt_service.JWTService')
def test_login_valid_credentials(mock_jwt_service, mock_user_service):
    """Test that the login endpoint returns JWT tokens for valid credentials"""
    # Create test client
    client = setup_test_client()
    
    # Mock UserService.authenticate_user to return a user ID
    user_id = "user123"
    mock_user_instance = mock_user_service.return_value
    mock_user_instance.authenticate_user.return_value = {
        "_id": user_id,
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "token_type": "Bearer",
        "expires_in": 3600
    }
    
    # Mock JWTService.generate_tokens to return access and refresh tokens
    mock_jwt_instance = mock_jwt_service.return_value
    mock_jwt_instance.create_token_pair.return_value = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "token_type": "Bearer",
        "expires_in": 3600
    }
    
    # Prepare valid login credentials using user_fixtures
    login_data = mock_user_credentials()
    
    # Send POST request to /api/auth/login
    response = client.post(
        f"{TEST_PREFIX}/login",
        data=json.dumps(login_data),
        content_type='application/json'
    )
    
    # Assert response status code is 200
    assert response.status_code == 200
    
    # Parse the response data
    response_data = json.loads(response.data)
    
    # Assert response contains access_token and refresh_token
    assert "access_token" in response_data
    assert "refresh_token" in response_data
    assert "token_type" in response_data
    assert "expires_in" in response_data
    
    # Assert UserService.authenticate_user was called with correct credentials
    mock_user_instance.authenticate_user.assert_called_with(
        login_data["email"],
        login_data["password"]
    )

@pytest.mark.unit
@patch('src.backend.core.auth.user_service.UserService')
def test_login_invalid_credentials(mock_user_service):
    """Test that the login endpoint returns error for invalid credentials"""
    # Create test client
    client = setup_test_client()
    
    # Mock UserService.authenticate_user to return None (authentication failure)
    mock_instance = mock_user_service.return_value
    mock_instance.authenticate_user.side_effect = AuthenticationError("Invalid credentials")
    
    # Prepare invalid login credentials
    invalid_credentials = {
        "email": "test@example.com",
        "password": "WrongPassword123"
    }
    
    # Send POST request to /api/auth/login
    response = client.post(
        f"{TEST_PREFIX}/login",
        data=json.dumps(invalid_credentials),
        content_type='application/json'
    )
    
    # Assert response status code is 401
    assert response.status_code == 401
    
    # Parse the response data
    response_data = json.loads(response.data)
    
    # Assert response contains appropriate error message
    assert "error" in response_data
    assert "message" in response_data
    assert "authentication_failed" in response_data["error"]
    
    # Assert UserService.authenticate_user was called with correct credentials
    mock_instance.authenticate_user.assert_called_with(
        invalid_credentials["email"],
        invalid_credentials["password"]
    )

@pytest.mark.unit
@patch('src.backend.core.auth.jwt_service.JWTService')
def test_refresh_token_valid(mock_jwt_service):
    """Test that the refresh token endpoint issues new tokens with valid refresh token"""
    # Create test client
    client = setup_test_client()
    
    # Mock JWTService.refresh_tokens to return new access and refresh tokens
    mock_instance = mock_jwt_service.return_value
    mock_instance.get_user_id_from_token.return_value = "user123"
    mock_instance.refresh_access_token.return_value = {
        "success": True,
        "access_token": "new_access_token",
        "token_type": "Bearer",
        "expires_in": 3600
    }
    
    # Prepare request with valid refresh token
    refresh_data = {
        "refresh_token": "valid_refresh_token"
    }
    
    # Send POST request to /api/auth/refresh
    response = client.post(
        f"{TEST_PREFIX}/refresh",
        data=json.dumps(refresh_data),
        content_type='application/json'
    )
    
    # Assert response status code is 200
    assert response.status_code == 200
    
    # Parse the response data
    response_data = json.loads(response.data)
    
    # Assert response contains new access_token and refresh_token
    assert "access_token" in response_data
    assert "token_type" in response_data
    assert "expires_in" in response_data
    
    # Assert JWTService.refresh_tokens was called with correct refresh token
    mock_instance.get_user_id_from_token.assert_called_with(refresh_data["refresh_token"])
    mock_instance.refresh_access_token.assert_called_with(
        refresh_data["refresh_token"], 
        "user123"
    )

@pytest.mark.unit
@patch('src.backend.core.auth.jwt_service.JWTService')
def test_refresh_token_expired(mock_jwt_service):
    """Test that the refresh token endpoint handles expired refresh tokens"""
    # Create test client
    client = setup_test_client()
    
    # Mock JWTService.refresh_tokens to raise TokenExpiredError
    mock_instance = mock_jwt_service.return_value
    mock_instance.get_user_id_from_token.return_value = "user123"
    mock_instance.refresh_access_token.return_value = {
        "success": False,
        "error": "Token has expired"
    }
    
    # Prepare request with expired refresh token
    refresh_data = {
        "refresh_token": "expired_refresh_token"
    }
    
    # Send POST request to /api/auth/refresh
    response = client.post(
        f"{TEST_PREFIX}/refresh",
        data=json.dumps(refresh_data),
        content_type='application/json'
    )
    
    # Assert response status code is 401
    assert response.status_code == 401
    
    # Parse the response data
    response_data = json.loads(response.data)
    
    # Assert response contains appropriate error message
    assert "error" in response_data
    assert "message" in response_data
    assert "invalid_token" in response_data["error"]
    
    # Assert JWTService.refresh_tokens was called with the expired token
    mock_instance.get_user_id_from_token.assert_called_with(refresh_data["refresh_token"])
    mock_instance.refresh_access_token.assert_called_with(
        refresh_data["refresh_token"], 
        "user123"
    )

@pytest.mark.unit
@patch('src.backend.core.auth.jwt_service.JWTService')
def test_refresh_token_invalid(mock_jwt_service):
    """Test that the refresh token endpoint handles invalid refresh tokens"""
    # Create test client
    client = setup_test_client()
    
    # Mock JWTService.refresh_tokens to raise InvalidTokenError
    mock_instance = mock_jwt_service.return_value
    mock_instance.get_user_id_from_token.return_value = "user123"
    mock_instance.refresh_access_token.side_effect = InvalidTokenError("Invalid token")
    
    # Prepare request with invalid refresh token
    refresh_data = {
        "refresh_token": "invalid_refresh_token"
    }
    
    # Send POST request to /api/auth/refresh
    response = client.post(
        f"{TEST_PREFIX}/refresh",
        data=json.dumps(refresh_data),
        content_type='application/json'
    )
    
    # Assert response status code is 401
    assert response.status_code == 401
    
    # Parse the response data
    response_data = json.loads(response.data)
    
    # Assert response contains appropriate error message
    assert "error" in response_data
    assert "message" in response_data
    assert "invalid_token" in response_data["error"]
    
    # Assert JWTService.refresh_tokens was called with the invalid token
    mock_instance.get_user_id_from_token.assert_called_with(refresh_data["refresh_token"])
    mock_instance.refresh_access_token.assert_called_with(
        refresh_data["refresh_token"], 
        "user123"
    )

@pytest.mark.unit
@patch('src.backend.core.auth.jwt_service.JWTService')
def test_logout(mock_jwt_service):
    """Test that the logout endpoint invalidates tokens"""
    # Create test client
    client = setup_test_client()
    
    # Mock JWTService.invalidate_token to return success
    mock_instance = mock_jwt_service.return_value
    mock_instance.validate_token.return_value = {
        "is_valid": True,
        "payload": {"jti": "token_id_123", "sub": "user123"}
    }
    
    # Prepare request with valid refresh token in cookie or Authorization header
    headers = {
        "Authorization": "Bearer valid_access_token"
    }
    
    # Send POST request to /api/auth/logout
    response = client.post(
        f"{TEST_PREFIX}/logout",
        headers=headers,
        data=json.dumps({"refresh_token": "valid_refresh_token"}),
        content_type='application/json'
    )
    
    # Assert response status code is 200
    assert response.status_code == 200
    
    # Parse the response data
    response_data = json.loads(response.data)
    
    # Assert response contains success message
    assert "message" in response_data
    assert "logged out successfully" in response_data["message"].lower()

@pytest.mark.unit
@patch('src.backend.core.auth.user_service.UserService')
@patch('src.backend.core.auth.jwt_service.JWTService')
@patch('src.backend.core.auth.anonymous_session.AnonymousSessionManager')
def test_session_transfer_anonymous_to_user(mock_anonymous_session, mock_jwt_service, mock_user_service):
    """Test that anonymous session data is transferred to user account upon login"""
    # Create test client
    client = setup_test_client()
    
    # Mock UserService.authenticate_user to return a user ID
    user_id = "user123"
    mock_user_instance = mock_user_service.return_value
    mock_user_instance.authenticate_user.return_value = {
        "_id": user_id,
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "token_type": "Bearer",
        "expires_in": 3600
    }
    
    # Mock JWTService.generate_tokens to return access and refresh tokens
    mock_jwt_instance = mock_jwt_service.return_value
    mock_jwt_instance.create_token_pair.return_value = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "token_type": "Bearer",
        "expires_in": 3600
    }
    
    # Mock AnonymousSessionManager.transfer_session_to_user to return success
    mock_session_instance = mock_anonymous_session.return_value
    mock_session_instance.get_session.return_value = {"session_id": "anon_session123"}
    mock_session_instance.upgrade_to_authenticated_user.return_value = True
    
    # Prepare login credentials with anonymous session ID
    login_data = mock_user_credentials()
    
    # Send POST request to /api/auth/login with session cookie
    response = client.post(
        f"{TEST_PREFIX}/login",
        data=json.dumps(login_data),
        content_type='application/json',
        environ_base={'HTTP_COOKIE': 'anonymous_session=anon_session123'}
    )
    
    # Assert response status code is 200
    assert response.status_code == 200
    
    # Parse the response data
    response_data = json.loads(response.data)
    
    # Assert AnonymousSessionManager.transfer_session_to_user was called with session ID and user ID
    mock_session_instance.upgrade_to_authenticated_user.assert_called_with(user_id)
    
    # Assert response contains successful token data
    assert "access_token" in response_data
    assert "refresh_token" in response_data
    assert "user_id" in response_data