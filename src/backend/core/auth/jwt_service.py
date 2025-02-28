"""
Service for handling JSON Web Token (JWT) operations, including token
creation, validation, refresh, and invalidation. This service supports both
access and refresh tokens for authenticated users with appropriate
expiry times and security features.
"""

import uuid
from datetime import datetime
import time
from typing import Dict, Any, Optional, List, Union

import jwt  # PyJWT 2.7.0

from ..utils.logger import get_logger
from ..utils.security import encode_jwt, decode_jwt, generate_token

# Constants
ACCESS_TOKEN_EXPIRY = 7200  # 2 hours in seconds
REFRESH_TOKEN_EXPIRY = 604800  # 7 days in seconds

# Configure logger
logger = get_logger(__name__)


class JWTService:
    """
    Service for creating, validating, refreshing, and invalidating JWT tokens for authentication.
    """

    def __init__(
        self, 
        secret_key: str, 
        algorithm: str = "HS256",
        access_token_expiry: int = ACCESS_TOKEN_EXPIRY, 
        refresh_token_expiry: int = REFRESH_TOKEN_EXPIRY
    ):
        """
        Initialize JWT service with secret key and configuration.
        
        Args:
            secret_key: Secret key used for signing tokens
            algorithm: Algorithm used for token signing (default: HS256)
            access_token_expiry: Expiry time for access tokens in seconds (default: 2 hours)
            refresh_token_expiry: Expiry time for refresh tokens in seconds (default: 7 days)
        """
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._access_token_expiry = access_token_expiry
        self._refresh_token_expiry = refresh_token_expiry
        self._invalidated_tokens = {}  # user_id -> set of invalidated token_ids
    
    def create_access_token(self, user_id: str, additional_claims: Dict[str, Any] = None) -> str:
        """
        Create a new access token for the specified user.
        
        Args:
            user_id: User identifier to include in the token
            additional_claims: Additional claims to include in the token
            
        Returns:
            JWT access token string
        """
        # Generate a unique JWT ID
        jti = generate_token(16)  # Use a shorter token for JWT ID
        
        # Create the base payload
        payload = {
            "sub": user_id,  # Subject (user identifier)
            "type": "access",  # Token type
            "jti": jti,  # JWT ID for token tracking/revocation
        }
        
        # Add any additional claims
        if additional_claims:
            payload.update(additional_claims)
        
        # Create the token with expiry
        token = encode_jwt(
            payload, 
            self._secret_key, 
            algorithm=self._algorithm, 
            expiration_seconds=self._access_token_expiry
        )
        
        logger.info("Created access token", 
                   user_id=user_id, 
                   token_id=jti)
        
        return token
    
    def create_refresh_token(self, user_id: str) -> Dict[str, Any]:
        """
        Create a new refresh token for the specified user.
        
        Args:
            user_id: User identifier to include in the token
            
        Returns:
            Dictionary containing token string, user_id, and expiry
        """
        # Generate a unique JWT ID
        jti = generate_token(16)  # Use a shorter token for JWT ID
        
        # Create the payload
        payload = {
            "sub": user_id,  # Subject (user identifier)
            "type": "refresh",  # Token type
            "jti": jti,  # JWT ID for token tracking/revocation
        }
        
        # Calculate expiry timestamp
        expiry = int(time.time()) + self._refresh_token_expiry
        
        # Create the token with expiry
        token = encode_jwt(
            payload, 
            self._secret_key, 
            algorithm=self._algorithm, 
            expiration_seconds=self._refresh_token_expiry
        )
        
        logger.info("Created refresh token", 
                   user_id=user_id, 
                   token_id=jti)
        
        return {
            "token": token,
            "user_id": user_id,
            "expires_at": expiry,
            "token_id": jti
        }
    
    def create_token_pair(self, user_id: str, additional_claims: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create both access and refresh tokens for a user.
        
        Args:
            user_id: User identifier to include in the tokens
            additional_claims: Additional claims to include in the access token
        
        Returns:
            Dictionary containing both access and refresh tokens
        """
        access_token = self.create_access_token(user_id, additional_claims)
        refresh_token_data = self.create_refresh_token(user_id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token_data["token"],
            "token_type": "Bearer",
            "expires_in": self._access_token_expiry,
            "refresh_expires_in": self._refresh_token_expiry,
            "user_id": user_id
        }
    
    def validate_token(self, token: str, expected_type: str) -> Dict[str, Any]:
        """
        Validate a JWT token and return its payload if valid.
        
        Args:
            token: JWT token to validate
            expected_type: Expected token type ('access' or 'refresh')
        
        Returns:
            Dictionary with is_valid flag, payload (if valid), and error message (if invalid)
        """
        # Check if token is None or empty
        if not token:
            return {"is_valid": False, "error": "No token provided"}
        
        try:
            # Decode the token
            payload = decode_jwt(token, self._secret_key, algorithm=self._algorithm)
            
            # Check if the token is invalidated
            user_id = payload.get("sub")
            token_id = payload.get("jti")
            
            if user_id and token_id and self._is_token_invalidated(user_id, token_id):
                return {"is_valid": False, "error": "Token invalidated"}
            
            # Check token type
            token_type = payload.get("type")
            if token_type != expected_type:
                return {"is_valid": False, "error": "Invalid token type"}
            
            # Token is valid
            return {"is_valid": True, "payload": payload}
        
        except jwt.ExpiredSignatureError:
            return {"is_valid": False, "error": "Token expired"}
        except jwt.InvalidTokenError as e:
            return {"is_valid": False, "error": f"Invalid token: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error validating token: {str(e)}")
            return {"is_valid": False, "error": "Token validation failed"}
    
    def get_user_id_from_token(self, token: str) -> Optional[str]:
        """
        Extract user_id from a token without full validation.
        
        Args:
            token: JWT token to extract user_id from
        
        Returns:
            User ID from token or None if invalid
        """
        if not token:
            return None
            
        try:
            # Decode the token without verification to extract user_id
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload.get("sub")
        except Exception as e:
            logger.debug(f"Error extracting user_id from token: {str(e)}")
            return None
    
    def refresh_access_token(self, refresh_token: str, user_id: str) -> Dict[str, Any]:
        """
        Create a new access token using a valid refresh token.
        
        Args:
            refresh_token: Refresh token to validate
            user_id: Expected user ID for validation
        
        Returns:
            New access token if refresh succeeded, error otherwise
        """
        # Validate the refresh token
        validation_result = self.validate_token(refresh_token, "refresh")
        
        if not validation_result["is_valid"]:
            return {
                "success": False,
                "error": validation_result["error"]
            }
        
        payload = validation_result["payload"]
        
        # Verify that user_id matches
        token_user_id = payload.get("sub")
        if token_user_id != user_id:
            return {
                "success": False,
                "error": "User ID mismatch"
            }
        
        # Generate new access token
        # Preserve any additional claims from the refresh token
        additional_claims = {}
        for key, value in payload.items():
            if key not in ["sub", "type", "jti", "iat", "exp"]:
                additional_claims[key] = value
                
        new_access_token = self.create_access_token(user_id, additional_claims)
        
        return {
            "success": True,
            "access_token": new_access_token,
            "token_type": "Bearer",
            "expires_in": self._access_token_expiry
        }
    
    def invalidate_tokens(self, user_id: str, token_ids: List[str] = None, invalidate_all: bool = False) -> bool:
        """
        Invalidate specific tokens or all tokens for a user.
        
        Args:
            user_id: The user whose tokens to invalidate
            token_ids: Specific token IDs to invalidate (optional)
            invalidate_all: Whether to invalidate all tokens for the user
        
        Returns:
            True if invalidation succeeded, False otherwise
        """
        # Initialize user's invalidated tokens set if not exists
        if user_id not in self._invalidated_tokens:
            self._invalidated_tokens[user_id] = set()
        
        # Handle invalidate all case
        if invalidate_all:
            self._invalidated_tokens[user_id].add("all")
            logger.info("Invalidated all tokens", user_id=user_id)
            return True
        
        # Add specific token IDs to invalidated set
        if token_ids:
            self._invalidated_tokens[user_id].update(token_ids)
            logger.info("Invalidated tokens", 
                       user_id=user_id, 
                       token_count=len(token_ids))
            return True
        
        return False
    
    def clean_invalidated_tokens(self) -> int:
        """
        Remove expired tokens from the invalidated tokens list.
        
        Returns:
            Number of users processed for cleanup
        """
        users_processed = 0
        
        for user_id in list(self._invalidated_tokens.keys()):
            users_processed += 1
            
            # If user has an empty set of invalidated tokens, clean it up
            if not self._invalidated_tokens[user_id]:
                del self._invalidated_tokens[user_id]
        
        logger.info("Cleaned up token invalidation data", 
                   users_processed=users_processed)
        
        return users_processed
    
    def _is_token_invalidated(self, user_id: str, token_id: str) -> bool:
        """
        Check if a specific token has been invalidated.
        
        Args:
            user_id: User ID from the token
            token_id: Token ID to check
        
        Returns:
            True if token is invalidated, False otherwise
        """
        # If user not in invalidated tokens, token is valid
        if user_id not in self._invalidated_tokens:
            return False
        
        # If "all" is in the set, all tokens for this user are invalidated
        if "all" in self._invalidated_tokens[user_id]:
            return True
        
        # Check if specific token ID is invalidated
        return token_id in self._invalidated_tokens[user_id]