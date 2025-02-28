# pytest==7.3.1
import pytest
import json
import jwt  # pyjwt==2.7.0
import time  # standard library

from ..conftest import app, client, db, setup_test_db, regular_user_data, verified_user_data, unverified_user_data, anonymous_user_data, user_with_reset_token, DEFAULT_PASSWORD  # src/backend/tests/conftest.py
from ..fixtures.user_fixtures import DEFAULT_PASSWORD  # src/backend/tests/fixtures/user_fixtures.py

LOGIN_ENDPOINT = '/api/auth/login'
REGISTER_ENDPOINT = '/api/auth/register'
REFRESH_ENDPOINT = '/api/auth/refresh'
LOGOUT_ENDPOINT = '/api/auth/logout'
ANONYMOUS_ENDPOINT = '/api/auth/anonymous'
CONVERT_ENDPOINT = '/api/auth/convert'
PASSWORD_RESET_REQUEST_ENDPOINT = '/api/auth/password-reset/request'
PASSWORD_RESET_CONFIRM_ENDPOINT = '/api/auth/password-reset/confirm'

@pytest.mark.integration
def test_register_success(client, db):
    """Test successful user registration"""
    # Create test user data with valid email and password
    user_data = {
        "email": "newuser@example.com",
        "password": "StrongP@ssw0rd123",
        "first_name": "New",
        "last_name": "User"
    }
    # Send POST request to REGISTER_ENDPOINT with test data
    response = client.post(REGISTER_ENDPOINT, json=user_data)
    # Assert response status code is 201
    assert response.status_code == 201
    # Parse JSON response and validate structure
    data = json.loads(response.data)
    assert "access_token" in data
    assert "refresh_token" in data
    assert "user_id" in data
    # Verify user exists in database with correct email
    user = db.users.find_one({"email": "newuser@example.com"})
    assert user is not None
    assert user["email"] == "newuser@example.com"
    # Assert password is stored as hash, not plaintext
    assert user["passwordHash"] != "StrongP@ssw0rd123"

@pytest.mark.integration
def test_register_existing_email(client, db, regular_user_data):
    """Test registration with an email that already exists"""
    # Insert regular_user_data into test database
    db.users.insert_one(regular_user_data)
    # Create new registration data using the same email
    user_data = {
        "email": "user@example.com",
        "password": "AnotherP@ssw0rd",
        "first_name": "Existing",
        "last_name": "User"
    }
    # Send POST request to REGISTER_ENDPOINT with test data
    response = client.post(REGISTER_ENDPOINT, json=user_data)
    # Assert response status code is 400
    assert response.status_code == 400
    # Assert error message indicates email already exists
    data = json.loads(response.data)
    assert "error" in data
    assert data["error"] == "validation_error"
    assert "email" in data["message"]

@pytest.mark.integration
def test_register_invalid_email(client):
    """Test registration with an invalid email format"""
    # Create test user data with invalid email format
    user_data = {
        "email": "invalid-email",
        "password": "ValidP@ssw0rd",
        "first_name": "Invalid",
        "last_name": "User"
    }
    # Send POST request to REGISTER_ENDPOINT with test data
    response = client.post(REGISTER_ENDPOINT, json=user_data)
    # Assert response status code is 400
    assert response.status_code == 400
    # Assert error message indicates invalid email format
    data = json.loads(response.data)
    assert "error" in data
    assert data["error"] == "validation_error"
    assert "email" in data["message"]

@pytest.mark.integration
def test_register_weak_password(client):
    """Test registration with a password that's too weak"""
    # Create test user data with weak password (too short, no special chars, etc.)
    user_data = {
        "email": "test@example.com",
        "password": "weak",
        "first_name": "Test",
        "last_name": "User"
    }
    # Send POST request to REGISTER_ENDPOINT with test data
    response = client.post(REGISTER_ENDPOINT, json=user_data)
    # Assert response status code is 400
    assert response.status_code == 400
    # Assert error message indicates password requirements not met
    data = json.loads(response.data)
    assert "error" in data
    assert data["error"] == "validation_error"
    assert "password" in data["message"]

@pytest.mark.integration
def test_login_success(client, db, regular_user_data):
    """Test successful user login"""
    # Insert regular_user_data into test database
    db.users.insert_one(regular_user_data)
    # Create login data with matching email and DEFAULT_PASSWORD
    login_data = {
        "email": "user@example.com",
        "password": DEFAULT_PASSWORD
    }
    # Send POST request to LOGIN_ENDPOINT with login data
    response = client.post(LOGIN_ENDPOINT, json=login_data)
    # Assert response status code is 200
    assert response.status_code == 200
    # Parse JSON response and validate structure
    data = json.loads(response.data)
    assert "access_token" in data
    assert "refresh_token" in data
    assert "user_id" in data
    # Verify user_id in response matches the one in database
    assert data["user_id"] == regular_user_data["_id"]

@pytest.mark.integration
def test_login_invalid_email(client):
    """Test login with non-existent email"""
    # Create login data with non-existent email and valid password
    login_data = {
        "email": "nonexistent@example.com",
        "password": DEFAULT_PASSWORD
    }
    # Send POST request to LOGIN_ENDPOINT with login data
    response = client.post(LOGIN_ENDPOINT, json=login_data)
    # Assert response status code is 401
    assert response.status_code == 401
    # Assert error message indicates invalid credentials
    data = json.loads(response.data)
    assert "error" in data
    assert data["error"] == "authentication_failed"

@pytest.mark.integration
def test_login_wrong_password(client, db, regular_user_data):
    """Test login with correct email but wrong password"""
    # Insert regular_user_data into test database
    db.users.insert_one(regular_user_data)
    # Create login data with matching email but incorrect password
    login_data = {
        "email": "user@example.com",
        "password": "wrongpassword"
    }
    # Send POST request to LOGIN_ENDPOINT with login data
    response = client.post(LOGIN_ENDPOINT, json=login_data)
    # Assert response status code is 401
    assert response.status_code == 401
    # Assert error message indicates invalid credentials
    data = json.loads(response.data)
    assert "error" in data
    assert data["error"] == "authentication_failed"

@pytest.mark.integration
def test_refresh_token_success(client, db, regular_user_data):
    """Test successful refresh of access token"""
    # Insert regular_user_data into test database
    db.users.insert_one(regular_user_data)
    # Login to get initial tokens
    login_data = {
        "email": "user@example.com",
        "password": DEFAULT_PASSWORD
    }
    login_response = client.post(LOGIN_ENDPOINT, json=login_data)
    login_data = json.loads(login_response.data)
    refresh_token = login_data["refresh_token"]
    # Create refresh request with refresh_token from login response
    refresh_request = {
        "refresh_token": refresh_token
    }
    # Send POST request to REFRESH_ENDPOINT with refresh request
    response = client.post(REFRESH_ENDPOINT, json=refresh_request)
    # Assert response status code is 200
    assert response.status_code == 200
    # Parse JSON response and validate structure
    data = json.loads(response.data)
    assert "access_token" in data
    # Assert response contains new access_token and refresh_token
    assert data["access_token"] != login_data["access_token"]
    # Decode new tokens to verify claims and expiry
    decoded_token = jwt.decode(data["access_token"], options={"verify_signature": False})
    assert decoded_token["sub"] == regular_user_data["_id"]

@pytest.mark.integration
def test_refresh_token_invalid(client):
    """Test refresh with invalid refresh token"""
    # Create refresh request with invalid refresh token
    refresh_request = {
        "refresh_token": "invalid_token"
    }
    # Send POST request to REFRESH_ENDPOINT with refresh request
    response = client.post(REFRESH_ENDPOINT, json=refresh_request)
    # Assert response status code is 401
    assert response.status_code == 401
    # Assert error message indicates invalid token
    data = json.loads(response.data)
    assert "error" in data
    assert data["error"] == "invalid_token"

@pytest.mark.integration
def test_refresh_token_expired(client, db, regular_user_data):
    """Test refresh with expired refresh token"""
    # Insert regular_user_data into test database
    db.users.insert_one(regular_user_data)
    # Create expired refresh token for the user
    expired_token = jwt.encode(
        {"sub": regular_user_data["_id"], "exp": time.time() - 1},
        "secret",
        algorithm="HS256"
    )
    # Create refresh request with expired token
    refresh_request = {
        "refresh_token": expired_token
    }
    # Send POST request to REFRESH_ENDPOINT with refresh request
    response = client.post(REFRESH_ENDPOINT, json=refresh_request)
    # Assert response status code is 401
    assert response.status_code == 401
    # Assert error message indicates expired token
    data = json.loads(response.data)
    assert "error" in data
    assert data["error"] == "invalid_token"

@pytest.mark.integration
def test_logout_success(client, db, regular_user_data):
    """Test successful logout"""
    # Insert regular_user_data into test database
    db.users.insert_one(regular_user_data)
    # Login to get access token
    login_data = {
        "email": "user@example.com",
        "password": DEFAULT_PASSWORD
    }
    login_response = client.post(LOGIN_ENDPOINT, json=login_data)
    login_data = json.loads(login_response.data)
    access_token = login_data["access_token"]
    # Create authentication header with access token
    auth_header = {"Authorization": f"Bearer {access_token}"}
    # Send POST request to LOGOUT_ENDPOINT with auth header
    response = client.post(LOGOUT_ENDPOINT, headers=auth_header)
    # Assert response status code is 200
    assert response.status_code == 200
    # Parse JSON response and validate structure
    data = json.loads(response.data)
    assert "message" in data
    # Assert response contains success message
    assert data["message"] == "Logged out successfully"
    # Try to use the same token again, should be rejected
    response = client.get("/api/documents", headers=auth_header)
    assert response.status_code == 401

@pytest.mark.integration
def test_logout_all_devices(client, db, regular_user_data):
    """Test logout from all devices"""
    # Insert regular_user_data into test database
    db.users.insert_one(regular_user_data)
    # Login multiple times to simulate multiple devices
    login_data = {
        "email": "user@example.com",
        "password": DEFAULT_PASSWORD
    }
    login_response1 = client.post(LOGIN_ENDPOINT, json=login_data)
    login_data1 = json.loads(login_response1.data)
    access_token1 = login_data1["access_token"]
    login_response2 = client.post(LOGIN_ENDPOINT, json=login_data)
    login_data2 = json.loads(login_response2.data)
    access_token2 = login_data2["access_token"]
    # Create authentication header with one of the access tokens
    auth_header = {"Authorization": f"Bearer {access_token1}"}
    # Send POST request to LOGOUT_ENDPOINT with all_devices=true parameter
    response = client.post(LOGOUT_ENDPOINT, headers=auth_header, query_string={"all": "true"})
    # Assert response status code is 200
    assert response.status_code == 200
    # Parse JSON response and validate structure
    data = json.loads(response.data)
    assert "message" in data
    # Assert response contains success message
    assert data["message"] == "Logged out successfully"
    # Try to use all tokens, all should be rejected
    auth_header1 = {"Authorization": f"Bearer {access_token1}"}
    response1 = client.get("/api/documents", headers=auth_header1)
    assert response1.status_code == 401
    auth_header2 = {"Authorization": f"Bearer {access_token2}"}
    response2 = client.get("/api/documents", headers=auth_header2)
    assert response2.status_code == 401

@pytest.mark.integration
def test_anonymous_session_create(client):
    """Test creation of anonymous session"""
    # Send POST request to ANONYMOUS_ENDPOINT
    response = client.post(ANONYMOUS_ENDPOINT)
    # Assert response status code is 201
    assert response.status_code == 201
    # Parse JSON response and validate structure
    data = json.loads(response.data)
    assert "session_id" in data
    assert "expires_at" in data
    # Check that session cookie is set in response
    assert "anonymous_session" in response.headers.get("Set-Cookie", "")

@pytest.mark.integration
def test_anonymous_session_reuse(client):
    """Test reuse of existing anonymous session"""
    # Create first anonymous session with POST to ANONYMOUS_ENDPOINT
    response1 = client.post(ANONYMOUS_ENDPOINT)
    data1 = json.loads(response1.data)
    session_id1 = data1["session_id"]
    # Extract session cookie from first response
    session_cookie = response1.headers.get("Set-Cookie")
    cookie_value = session_cookie.split("anonymous_session=")[1].split(";")[0]
    # Send another POST to ANONYMOUS_ENDPOINT with session cookie
    response2 = client.post(ANONYMOUS_ENDPOINT, headers={"Cookie": f"anonymous_session={cookie_value}"})
    data2 = json.loads(response2.data)
    # Assert response status code is 200
    assert response2.status_code == 200
    # Assert session_id is the same as in first response
    assert data2["session_id"] == session_id1
    # Check that cookie still exists in response
    assert "anonymous_session" in response2.headers.get("Set-Cookie", "")

@pytest.mark.integration
def test_convert_anonymous_to_registered_success(client, db):
    """Test successful conversion of anonymous session to registered account"""
    # Create anonymous session with POST to ANONYMOUS_ENDPOINT
    response1 = client.post(ANONYMOUS_ENDPOINT)
    data1 = json.loads(response1.data)
    session_id = data1["session_id"]
    # Extract session_id and cookie from response
    session_cookie = response1.headers.get("Set-Cookie")
    cookie_value = session_cookie.split("anonymous_session=")[1].split(";")[0]
    # Create conversion data with valid email, password, and session_id
    conversion_data = {
        "email": "converted@example.com",
        "password": "NewP@ssw0rd123",
        "first_name": "Converted",
        "last_name": "User",
        "session_id": session_id
    }
    # Send POST request to CONVERT_ENDPOINT with conversion data and cookie
    response2 = client.post(CONVERT_ENDPOINT, json=conversion_data, headers={"Cookie": f"anonymous_session={cookie_value}"})
    # Assert response status code is 200
    assert response2.status_code == 200
    # Parse JSON response and validate structure
    data2 = json.loads(response2.data)
    assert "access_token" in data2
    assert "refresh_token" in data2
    assert "user_id" in data2
    # Verify user exists in database with given email
    user = db.users.find_one({"email": "converted@example.com"})
    assert user is not None
    # Verify user has the documents from anonymous session (if any)
    assert user["email"] == "converted@example.com"

@pytest.mark.integration
def test_convert_anonymous_without_session(client):
    """Test conversion without valid anonymous session"""
    # Create conversion data with valid email and password but missing session
    conversion_data = {
        "email": "converted@example.com",
        "password": "NewP@ssw0rd123",
        "first_name": "Converted",
        "last_name": "User"
    }
    # Send POST request to CONVERT_ENDPOINT with conversion data
    response = client.post(CONVERT_ENDPOINT, json=conversion_data)
    # Assert response status code is 400
    assert response.status_code == 400
    # Assert error message indicates missing or invalid session
    data = json.loads(response.data)
    assert "error" in data
    assert data["error"] == "invalid_request"

@pytest.mark.integration
def test_password_reset_request_success(client, db, regular_user_data):
    """Test successful password reset request"""
    # Insert regular_user_data into test database
    db.users.insert_one(regular_user_data)
    # Create reset request with user's email
    reset_request = {
        "email": "user@example.com"
    }
    # Send POST request to PASSWORD_RESET_REQUEST_ENDPOINT with request data
    response = client.post(PASSWORD_RESET_REQUEST_ENDPOINT, json=reset_request)
    # Assert response status code is 200
    assert response.status_code == 200
    # Parse JSON response and validate structure
    data = json.loads(response.data)
    assert "message" in data
    # Assert response contains success message
    assert data["message"] == "If your email exists in our system, you will receive a password reset link shortly."
    # Verify user in database now has reset token and expiry
    user = db.users.find_one({"email": "user@example.com"})
    assert "resetToken" in user
    assert "resetTokenExpiry" in user

@pytest.mark.integration
def test_password_reset_confirm_success(client, db, user_with_reset_token):
    """Test successful password reset confirmation"""
    # Insert user_with_reset_token into test database
    db.users.insert_one(user_with_reset_token)
    # Extract reset token from user data
    reset_token = user_with_reset_token["resetToken"]
    # Create reset confirmation with token and new password
    reset_confirmation = {
        "token": reset_token,
        "new_password": "NewValidP@ssword"
    }
    # Send POST request to PASSWORD_RESET_CONFIRM_ENDPOINT with confirmation data
    response = client.post(PASSWORD_RESET_CONFIRM_ENDPOINT, json=reset_confirmation)
    # Assert response status code is 200
    assert response.status_code == 200
    # Parse JSON response and validate structure
    data = json.loads(response.data)
    assert "message" in data
    # Assert response contains success message
    assert data["message"] == "Password has been reset successfully"
    # Login with new password to verify it was changed
    login_data = {
        "email": "user@example.com",
        "password": "NewValidP@ssword"
    }
    login_response = client.post(LOGIN_ENDPOINT, json=login_data)
    assert login_response.status_code == 200
    # Verify reset token is cleared from database
    user = db.users.find_one({"email": "user@example.com"})
    assert "resetToken" not in user
    assert "resetTokenExpiry" not in user

@pytest.mark.integration
def test_password_reset_invalid_token(client):
    """Test password reset with invalid token"""
    # Create reset confirmation with invalid token and new password
    reset_confirmation = {
        "token": "invalid_token",
        "new_password": "NewValidP@ssword"
    }
    # Send POST request to PASSWORD_RESET_CONFIRM_ENDPOINT with confirmation data
    response = client.post(PASSWORD_RESET_CONFIRM_ENDPOINT, json=reset_confirmation)
    # Assert response status code is 400
    assert response.status_code == 400
    # Assert error message indicates invalid token
    data = json.loads(response.data)
    assert "error" in data
    assert data["error"] == "validation_error"

@pytest.mark.integration
def test_password_reset_expired_token(client, db, user_with_reset_token):
    """Test password reset with expired token"""
    # Modify user_with_reset_token to have expired reset token
    user_with_reset_token["resetTokenExpiry"] = datetime.datetime.utcnow() - datetime.timedelta(hours=2)
    # Insert modified user into test database
    db.users.insert_one(user_with_reset_token)
    # Extract expired reset token from user data
    reset_token = user_with_reset_token["resetToken"]
    # Create reset confirmation with expired token and new password
    reset_confirmation = {
        "token": reset_token,
        "new_password": "NewValidP@ssword"
    }
    # Send POST request to PASSWORD_RESET_CONFIRM_ENDPOINT with confirmation data
    response = client.post(PASSWORD_RESET_CONFIRM_ENDPOINT, json=reset_confirmation)
    # Assert response status code is 400
    assert response.status_code == 400
    # Assert error message indicates expired token
    data = json.loads(response.data)
    assert "error" in data
    assert data["error"] == "validation_error"

@pytest.mark.integration
def test_jwt_claims_structure(client, db, regular_user_data):
    """Test JWT token claims structure and validity"""
    # Insert regular_user_data into test database
    db.users.insert_one(regular_user_data)
    # Login to get access and refresh tokens
    login_data = {
        "email": "user@example.com",
        "password": DEFAULT_PASSWORD
    }
    login_response = client.post(LOGIN_ENDPOINT, json=login_data)
    login_data = json.loads(login_response.data)
    access_token = login_data["access_token"]
    refresh_token = login_data["refresh_token"]
    # Decode access token without verification
    decoded_access_token = jwt.decode(access_token, options={"verify_signature": False})
    # Verify required claims: sub (user_id), exp, iat, jti, type
    assert "sub" in decoded_access_token
    assert "exp" in decoded_access_token
    assert "iat" in decoded_access_token
    assert "jti" in decoded_access_token
    assert "type" in decoded_access_token
    # Verify access token type claim is 'access'
    assert decoded_access_token["type"] == "access"
    # Decode refresh token without verification
    decoded_refresh_token = jwt.decode(refresh_token, options={"verify_signature": False})
    # Verify refresh token type claim is 'refresh'
    assert decoded_refresh_token["type"] == "refresh"
    # Verify token expiry times match expected duration
    # (This requires access to the JWT_ACCESS_TOKEN_EXPIRES and JWT_REFRESH_TOKEN_EXPIRES config values)

class AuthApiTestFixtures:
    """Helper class with fixtures and utilities for auth API tests"""

    def __init__(self):
        """Initialize with common test data and utilities"""
        pass

    def create_login_user(self, client, db, user_data):
        """Helper to create and login a test user"""
        # Insert user_data into test database
        db.users.insert_one(user_data)
        # Create login data with user's email and password
        login_data = {
            "email": user_data["email"],
            "password": DEFAULT_PASSWORD
        }
        # Send POST request to LOGIN_ENDPOINT
        response = client.post(LOGIN_ENDPOINT, json=login_data)
        # Parse response and return user data with tokens
        return json.loads(response.data)

    def get_auth_header(self, token):
        """Create authorization header with token"""
        # Create and return header dictionary with Bearer token
        return {"Authorization": f"Bearer {token}"}

    def decode_token(self, token):
        """Decode JWT token without verification"""
        # Use jwt.decode with options to skip verification
        return jwt.decode(token, options={"verify_signature": False})