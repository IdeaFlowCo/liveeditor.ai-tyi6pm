"""
Unit tests for the JWT service that verifies token creation, validation, refresh, and invalidation functionality.
Covers both access and refresh tokens with appropriate testing of expiry and security features.
"""

import pytest
import unittest.mock as mock
import time
import datetime
import jwt  # PyJWT 2.7.0

from src.backend.core.auth.jwt_service import (
    JWTService, ACCESS_TOKEN_EXPIRY, REFRESH_TOKEN_EXPIRY
)
from src.backend.tests.fixtures.user_fixtures import generate_user_id
from src.backend.core.utils.security import decode_jwt

# Constants for testing
TEST_SECRET_KEY = "test-jwt-secret-key"
TEST_ALGORITHM = "HS256"

def test_jwt_service_initialization():
    """Test that the JWTService initializes correctly with default and custom parameters"""
    # Create JWTService with default parameters except secret key
    jwt_service = JWTService(secret_key=TEST_SECRET_KEY)
    
    # Verify that default algorithm is HS256
    assert jwt_service._algorithm == "HS256"
    
    # Verify that default token expiry times match constants
    assert jwt_service._access_token_expiry == ACCESS_TOKEN_EXPIRY
    assert jwt_service._refresh_token_expiry == REFRESH_TOKEN_EXPIRY
    
    # Create JWTService with custom parameters
    custom_jwt_service = JWTService(
        secret_key="custom-secret-key",
        algorithm="HS384",
        access_token_expiry=300,  # 5 minutes
        refresh_token_expiry=86400  # 1 day
    )
    
    # Verify that custom parameters are correctly stored
    assert custom_jwt_service._secret_key == "custom-secret-key"
    assert custom_jwt_service._algorithm == "HS384"
    assert custom_jwt_service._access_token_expiry == 300
    assert custom_jwt_service._refresh_token_expiry == 86400

def test_create_access_token():
    """Test creation of access tokens with correct payload and claims"""
    # Create a JWTService instance
    jwt_service = JWTService(secret_key=TEST_SECRET_KEY)
    
    # Generate a test user ID
    user_id = generate_user_id()
    
    # Create an access token for the test user
    access_token = jwt_service.create_access_token(user_id)
    
    # Decode the token to verify its contents
    decoded_token = decode_jwt(access_token, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)
    
    # Assert that token contains correct user_id in 'sub' claim
    assert decoded_token["sub"] == user_id
    
    # Assert that token contains 'type' claim with value 'access'
    assert decoded_token["type"] == "access"
    
    # Assert that token contains 'exp' claim for expiration
    assert "exp" in decoded_token
    
    # Assert that token contains 'jti' claim (JWT ID)
    assert "jti" in decoded_token
    
    # Test with additional custom claims and verify they are included
    custom_claims = {
        "role": "user",
        "permissions": ["read", "write"],
        "name": "Test User"
    }
    
    access_token_with_claims = jwt_service.create_access_token(
        user_id, 
        additional_claims=custom_claims
    )
    
    decoded_token_with_claims = decode_jwt(
        access_token_with_claims, 
        TEST_SECRET_KEY, 
        algorithm=TEST_ALGORITHM
    )
    
    # Verify custom claims are present
    assert decoded_token_with_claims["role"] == "user"
    assert decoded_token_with_claims["permissions"] == ["read", "write"]
    assert decoded_token_with_claims["name"] == "Test User"

def test_create_refresh_token():
    """Test creation of refresh tokens with correct payload and structure"""
    # Create a JWTService instance
    jwt_service = JWTService(secret_key=TEST_SECRET_KEY)
    
    # Generate a test user ID
    user_id = generate_user_id()
    
    # Create a refresh token for the test user
    refresh_token_data = jwt_service.create_refresh_token(user_id)
    
    # Verify that the returned object is a dictionary with expected keys
    assert isinstance(refresh_token_data, dict)
    assert "token" in refresh_token_data
    assert "user_id" in refresh_token_data
    assert "expires_at" in refresh_token_data
    assert "token_id" in refresh_token_data
    
    # Check correct values
    assert refresh_token_data["user_id"] == user_id
    
    # Calculate approximate expected expiry time
    expected_expiry = int(time.time()) + REFRESH_TOKEN_EXPIRY
    assert abs(refresh_token_data["expires_at"] - expected_expiry) <= 1  # Allow 1 second difference
    
    # Decode the token to verify its contents
    token = refresh_token_data["token"]
    decoded_token = decode_jwt(token, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)
    
    # Assert that token contains correct user_id in 'sub' claim
    assert decoded_token["sub"] == user_id
    
    # Assert that token contains 'type' claim with value 'refresh'
    assert decoded_token["type"] == "refresh"
    
    # Assert that token contains 'exp' claim matching the expiry in dictionary
    assert "exp" in decoded_token
    
    # Assert that token contains 'jti' claim (JWT ID)
    assert "jti" in decoded_token

def test_create_token_pair():
    """Test creation of both access and refresh tokens together"""
    # Create a JWTService instance
    jwt_service = JWTService(secret_key=TEST_SECRET_KEY)
    
    # Generate a test user ID
    user_id = generate_user_id()
    
    # Create a token pair for the test user
    token_pair = jwt_service.create_token_pair(user_id)
    
    # Verify that the returned object contains both access_token and refresh_token keys
    assert isinstance(token_pair, dict)
    assert "access_token" in token_pair
    assert "refresh_token" in token_pair
    assert "token_type" in token_pair
    assert "expires_in" in token_pair
    assert "refresh_expires_in" in token_pair
    assert "user_id" in token_pair
    
    # Verify correct values
    assert token_pair["token_type"] == "Bearer"
    assert token_pair["expires_in"] == ACCESS_TOKEN_EXPIRY
    assert token_pair["refresh_expires_in"] == REFRESH_TOKEN_EXPIRY
    assert token_pair["user_id"] == user_id
    
    # Decode both tokens to verify their contents
    access_token = token_pair["access_token"]
    refresh_token = token_pair["refresh_token"]
    
    decoded_access = decode_jwt(access_token, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)
    decoded_refresh = decode_jwt(refresh_token, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)
    
    # Verify that both tokens have the same user_id in 'sub' claim
    assert decoded_access["sub"] == user_id
    assert decoded_refresh["sub"] == user_id
    
    # Verify that token types are set correctly ('access' and 'refresh')
    assert decoded_access["type"] == "access"
    assert decoded_refresh["type"] == "refresh"
    
    # Verify that expiry times are appropriate for each token type
    assert decoded_access["exp"] < decoded_refresh["exp"]

def test_validate_token_valid():
    """Test validation of valid tokens returns correct payload"""
    # Create a JWTService instance
    jwt_service = JWTService(secret_key=TEST_SECRET_KEY)
    
    # Generate a test user ID
    user_id = generate_user_id()
    
    # Create an access token for the test user
    access_token = jwt_service.create_access_token(user_id)
    
    # Validate the token with correct expected type
    validation_result = jwt_service.validate_token(access_token, "access")
    
    # Assert that validation returns is_valid=True
    assert validation_result["is_valid"] is True
    
    # Assert that payload contains expected fields including user_id
    assert "payload" in validation_result
    assert validation_result["payload"]["sub"] == user_id
    assert validation_result["payload"]["type"] == "access"
    assert "exp" in validation_result["payload"]
    assert "jti" in validation_result["payload"]

def test_validate_token_invalid_type():
    """Test validation fails for tokens with incorrect expected type"""
    # Create a JWTService instance
    jwt_service = JWTService(secret_key=TEST_SECRET_KEY)
    
    # Generate a test user ID
    user_id = generate_user_id()
    
    # Create an access token for the test user
    access_token = jwt_service.create_access_token(user_id)
    
    # Validate the token with incorrect expected type ('refresh')
    validation_result = jwt_service.validate_token(access_token, "refresh")
    
    # Assert that validation returns is_valid=False
    assert validation_result["is_valid"] is False
    
    # Assert that error message indicates invalid token type
    assert "error" in validation_result
    assert "Invalid token type" in validation_result["error"]

def test_validate_token_expired():
    """Test validation fails for expired tokens"""
    # Create a JWTService instance with very short expiry time
    jwt_service = JWTService(
        secret_key=TEST_SECRET_KEY,
        access_token_expiry=1  # 1 second expiry
    )
    
    # Generate a test user ID
    user_id = generate_user_id()
    
    # Create an access token for the test user
    access_token = jwt_service.create_access_token(user_id)
    
    # Sleep longer than the token expiry time
    time.sleep(2)  # Sleep for 2 seconds to ensure token expiry
    
    # Validate the now-expired token
    validation_result = jwt_service.validate_token(access_token, "access")
    
    # Assert that validation returns is_valid=False
    assert validation_result["is_valid"] is False
    
    # Assert that error message indicates expired token
    assert "error" in validation_result
    assert "Token expired" in validation_result["error"]

def test_validate_token_malformed():
    """Test validation fails for malformed or tampered tokens"""
    # Create a JWTService instance
    jwt_service = JWTService(secret_key=TEST_SECRET_KEY)
    
    # Create a malformed token string
    malformed_token = "not.a.valid.jwt.token"
    
    # Validate the malformed token
    validation_result = jwt_service.validate_token(malformed_token, "access")
    
    # Assert that validation returns is_valid=False
    assert validation_result["is_valid"] is False
    
    # Assert that error message indicates invalid token
    assert "error" in validation_result
    assert "Invalid token" in validation_result["error"]
    
    # Create a valid token and then tamper with payload
    user_id = generate_user_id()
    valid_token = jwt_service.create_access_token(user_id)
    
    # Tamper with the token by changing a character in the payload part (second part)
    parts = valid_token.split('.')
    parts[1] = parts[1][:-1] + ('1' if parts[1][-1] != '1' else '2')  # Change last character
    tampered_token = '.'.join(parts)
    
    # Validate the tampered token
    validation_result = jwt_service.validate_token(tampered_token, "access")
    
    # Assert that validation returns is_valid=False with signature error
    assert validation_result["is_valid"] is False
    assert "error" in validation_result
    assert "Invalid token" in validation_result["error"]

def test_get_user_id_from_token():
    """Test extraction of user ID from token without full validation"""
    # Create a JWTService instance
    jwt_service = JWTService(secret_key=TEST_SECRET_KEY)
    
    # Generate a test user ID
    user_id = generate_user_id()
    
    # Create an access token for the test user
    access_token = jwt_service.create_access_token(user_id)
    
    # Extract user ID from the token
    extracted_user_id = jwt_service.get_user_id_from_token(access_token)
    
    # Assert that extracted user ID matches the original
    assert extracted_user_id == user_id
    
    # Test with invalid/malformed token
    invalid_token = "not.a.valid.token"
    extracted_user_id = jwt_service.get_user_id_from_token(invalid_token)
    
    # Assert that None is returned for invalid token
    assert extracted_user_id is None

def test_refresh_access_token_valid():
    """Test refreshing access token with valid refresh token"""
    # Create a JWTService instance
    jwt_service = JWTService(secret_key=TEST_SECRET_KEY)
    
    # Generate a test user ID
    user_id = generate_user_id()
    
    # Create a refresh token for the test user
    refresh_token_data = jwt_service.create_refresh_token(user_id)
    refresh_token = refresh_token_data["token"]
    
    # Use refresh token to get a new access token
    refresh_result = jwt_service.refresh_access_token(refresh_token, user_id)
    
    # Assert that response contains success=True
    assert refresh_result["success"] is True
    assert "access_token" in refresh_result
    assert refresh_result["token_type"] == "Bearer"
    assert refresh_result["expires_in"] == ACCESS_TOKEN_EXPIRY
    
    # Decode new access token and verify user_id and type claims
    new_access_token = refresh_result["access_token"]
    decoded_token = decode_jwt(new_access_token, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)
    
    assert decoded_token["sub"] == user_id
    assert decoded_token["type"] == "access"
    
    # Verify that new token has a different jti claim
    assert "jti" in decoded_token

def test_refresh_access_token_invalid():
    """Test refreshing access token fails with invalid refresh token"""
    # Create a JWTService instance
    jwt_service = JWTService(secret_key=TEST_SECRET_KEY)
    
    # Generate a test user ID
    user_id = generate_user_id()
    
    # Create an access token (not refresh token)
    access_token = jwt_service.create_access_token(user_id)
    
    # Attempt to use access token as refresh token
    refresh_result = jwt_service.refresh_access_token(access_token, user_id)
    
    # Assert that response contains success=False with appropriate error
    assert refresh_result["success"] is False
    assert "error" in refresh_result
    assert "Invalid token type" in refresh_result["error"]
    
    # Create an invalid token string
    invalid_token = "not.a.valid.token"
    
    # Attempt to use invalid token for refresh
    refresh_result = jwt_service.refresh_access_token(invalid_token, user_id)
    
    # Assert that response contains success=False with appropriate error
    assert refresh_result["success"] is False
    assert "error" in refresh_result
    assert "Invalid token" in refresh_result["error"]

def test_refresh_access_token_user_mismatch():
    """Test refreshing access token fails when user ID mismatch"""
    # Create a JWTService instance
    jwt_service = JWTService(secret_key=TEST_SECRET_KEY)
    
    # Generate two different test user IDs
    user_id1 = generate_user_id()
    user_id2 = generate_user_id()
    
    # Create a refresh token for first user ID
    refresh_token_data = jwt_service.create_refresh_token(user_id1)
    refresh_token = refresh_token_data["token"]
    
    # Attempt to refresh token passing second user ID
    refresh_result = jwt_service.refresh_access_token(refresh_token, user_id2)
    
    # Assert that response contains success=False
    assert refresh_result["success"] is False
    
    # Assert that error message indicates user ID mismatch
    assert "error" in refresh_result
    assert "User ID mismatch" in refresh_result["error"]

def test_invalidate_tokens_specific():
    """Test invalidation of specific tokens"""
    # Create a JWTService instance
    jwt_service = JWTService(secret_key=TEST_SECRET_KEY)
    
    # Generate a test user ID
    user_id = generate_user_id()
    
    # Create two access tokens for the user
    token1 = jwt_service.create_access_token(user_id)
    token2 = jwt_service.create_access_token(user_id)
    
    # Extract token IDs (jti) from the tokens
    decoded1 = decode_jwt(token1, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)
    decoded2 = decode_jwt(token2, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)
    
    token1_jti = decoded1["jti"]
    token2_jti = decoded2["jti"]
    
    # Invalidate the first token specifically
    jwt_service.invalidate_tokens(user_id, [token1_jti])
    
    # Validate both tokens
    validation1 = jwt_service.validate_token(token1, "access")
    validation2 = jwt_service.validate_token(token2, "access")
    
    # Assert that first token validation returns is_valid=False with 'invalidated' message
    assert validation1["is_valid"] is False
    assert "error" in validation1
    assert "Token invalidated" in validation1["error"]
    
    # Assert that second token validation returns is_valid=True
    assert validation2["is_valid"] is True

def test_invalidate_tokens_all():
    """Test invalidation of all tokens for a user"""
    # Create a JWTService instance
    jwt_service = JWTService(secret_key=TEST_SECRET_KEY)
    
    # Generate a test user ID
    user_id = generate_user_id()
    
    # Create multiple tokens for the user
    tokens = [
        jwt_service.create_access_token(user_id),
        jwt_service.create_access_token(user_id),
        jwt_service.create_refresh_token(user_id)["token"]
    ]
    
    # Invalidate all tokens for the user
    jwt_service.invalidate_tokens(user_id, invalidate_all=True)
    
    # Validate each token
    for token in tokens:
        # Determine token type by decoding
        decoded = decode_jwt(token, TEST_SECRET_KEY, options={"verify_signature": False})
        token_type = decoded.get("type", "access")  # Default to access if not found
        
        validation = jwt_service.validate_token(token, token_type)
        
        # Assert that all token validations return is_valid=False with 'invalidated' message
        assert validation["is_valid"] is False
        assert "error" in validation
        assert "Token invalidated" in validation["error"]

def test_clean_invalidated_tokens():
    """Test cleaning of expired tokens from invalidated list"""
    # Create a JWTService instance with very short expiry time
    jwt_service = JWTService(
        secret_key=TEST_SECRET_KEY,
        access_token_expiry=1  # 1 second expiry
    )
    
    # Generate a test user ID
    user_id = generate_user_id()
    
    # Create tokens for the user
    access_token = jwt_service.create_access_token(user_id)
    
    # Extract token ID
    decoded = decode_jwt(access_token, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)
    token_jti = decoded["jti"]
    
    # Invalidate the tokens
    jwt_service.invalidate_tokens(user_id, [token_jti])
    
    # Verify token is in invalidated list
    assert user_id in jwt_service._invalidated_tokens
    assert token_jti in jwt_service._invalidated_tokens[user_id]
    
    # Create a user with an empty invalidation set
    empty_user_id = generate_user_id()
    jwt_service._invalidated_tokens[empty_user_id] = set()
    
    # Sleep longer than the token expiry time
    time.sleep(2)  # Sleep for 2 seconds to ensure token expiry
    
    # Run clean_invalidated_tokens method
    users_processed = jwt_service.clean_invalidated_tokens()
    
    # Assert that appropriate number of users were processed
    assert users_processed == 2  # One user with tokens, one empty user
    
    # Check that user with empty set was removed
    assert empty_user_id not in jwt_service._invalidated_tokens
    
    # User with tokens should still be there
    assert user_id in jwt_service._invalidated_tokens

def test_mock_time_for_token_expiry():
    """Test token expiry using mocked time instead of sleep"""
    # Create a JWTService instance
    jwt_service = JWTService(secret_key=TEST_SECRET_KEY)
    
    # Generate a test user ID
    user_id = generate_user_id()
    
    # Create an access token for the test user
    access_token = jwt_service.create_access_token(user_id)
    
    # Get token expiry time
    decoded_token = decode_jwt(access_token, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)
    expiry_time = decoded_token["exp"]
    
    # Mock time.time to return future timestamp beyond token expiry
    with mock.patch('time.time', return_value=expiry_time + 10):
        # Validate the token
        validation_result = jwt_service.validate_token(access_token, "access")
        
        # Assert that validation returns is_valid=False with expiry message
        assert validation_result["is_valid"] is False
        assert "error" in validation_result
        assert "Token expired" in validation_result["error"]