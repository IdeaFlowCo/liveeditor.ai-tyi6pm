"""
Authentication middleware for the AI writing enhancement platform that supports both anonymous and authenticated access paths.
It provides JWT token validation, user identification, and session management for securing API endpoints while allowing immediate usage without login.
"""

from flask import request, g, jsonify
import functools
import typing
import json

from ...core.auth.jwt_service import JWTService
from ...core.auth.anonymous_session import AnonymousSessionManager
from ...core.auth.user_service import UserService
from ...core.utils.logger import get_logger

# Constants for auth headers
AUTH_HEADER = "Authorization"
TOKEN_PREFIX = "Bearer "

# Initialize logger
logger = get_logger(__name__)

# Global service instances (to be set in setup_auth)
_jwt_service = None
_anonymous_session_manager = None
_user_service = None


class AuthenticationError(Exception):
    """Exception raised when authentication fails"""
    
    def __init__(self, message: str, status_code: int = 401):
        """Initialize authentication error with message and status code"""
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def setup_auth(app, jwt_service: JWTService, anonymous_session_manager: AnonymousSessionManager, user_service: UserService):
    """Initializes authentication middleware for the Flask application"""
    global _jwt_service, _anonymous_session_manager, _user_service
    
    # Store service instances in global variables for use by other functions
    _jwt_service = jwt_service
    _anonymous_session_manager = anonymous_session_manager
    _user_service = user_service
    
    # Register before_request handler for extracting credentials
    app.before_request(_extract_credentials)
    
    # Register after_request handler for applying session cookies
    app.after_request(_apply_session_cookies)
    
    logger.info("Auth middleware initialized successfully")


def auth_required(allow_anonymous: bool = False):
    """Decorator for routes that require authenticated users"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # If authentication required, verify user is authenticated
            if hasattr(g, 'authenticated') and g.authenticated:
                return func(*args, **kwargs)
            
            # If anonymous allowed, check either authenticated or valid anonymous session
            if allow_anonymous and hasattr(g, 'anonymous_session') and g.anonymous_session:
                return func(*args, **kwargs)
            
            # If authentication check fails, return 401 Unauthorized response
            error_message = "Authentication required"
            logger.warning(f"Authentication failed: {error_message}")
            
            return jsonify({
                "error": "unauthorized",
                "message": error_message
            }), 401
        
        return wrapper
    
    return decorator


def get_current_user() -> typing.Optional[dict]:
    """Retrieves the current user from the request context"""
    # Check if user is already stored in flask.g
    if hasattr(g, 'user') and g.user is not None:
        return g.user
    # Return None if no user found in context
    return None


def get_current_user_id() -> typing.Optional[str]:
    """Retrieves the current user ID from the request context"""
    # Check if user is already stored in flask.g
    if hasattr(g, 'user_id') and g.user_id is not None:
        return g.user_id
    # Return None if no user found in context
    return None


def is_authenticated() -> bool:
    """Checks if the current request is from an authenticated user"""
    # Check if authenticated flag is set in flask.g
    return hasattr(g, 'authenticated') and g.authenticated


def is_anonymous_session() -> bool:
    """Checks if the current request has a valid anonymous session"""
    # Check if anonymous_session flag is set in flask.g
    return hasattr(g, 'anonymous_session') and g.anonymous_session


def _extract_credentials():
    """Extracts and validates authentication credentials from the request"""
    global _jwt_service, _anonymous_session_manager, _user_service
    
    # Initialize authentication context in flask.g
    g.authenticated = False
    g.anonymous_session = False
    g.user = None
    g.user_id = None
    
    # Get Authorization header from request
    token = _extract_token()
    
    if token:
        # Validate JWT token and get user_id if valid
        validation_result = _jwt_service.validate_token(token, "access")
        
        if validation_result["is_valid"]:
            # If token valid, set authenticated flag and load user data
            g.authenticated = True
            
            user_id = validation_result["payload"]["sub"]
            g.user_id = user_id
            
            try:
                g.user = _user_service.get_user_by_id(user_id)
                logger.info(f"Authenticated request for user: {user_id}")
            except Exception as e:
                logger.warning(f"Error retrieving user data: {str(e)}")
        else:
            logger.warning(f"Token validation failed: {validation_result.get('error', 'Unknown error')}")
    
    # If no valid JWT, check for anonymous session
    if not g.authenticated:
        try:
            session_data = _anonymous_session_manager.get_session()
            if session_data:
                g.anonymous_session = True
                logger.debug("Anonymous session identified")
        except Exception as e:
            logger.error(f"Error getting anonymous session: {str(e)}")
    
    # Log authentication attempt result
    if g.authenticated:
        logger.debug(f"Request authenticated for user: {g.user_id}")
    elif g.anonymous_session:
        logger.debug("Request has valid anonymous session")
    else:
        logger.debug("Unauthenticated request")


def _extract_token() -> typing.Optional[str]:
    """Extracts JWT token from Authorization header"""
    # Get Authorization header from request
    auth_header = request.headers.get(AUTH_HEADER)
    
    # If header exists and starts with Bearer prefix, extract token
    if auth_header and auth_header.startswith(TOKEN_PREFIX):
        return auth_header[len(TOKEN_PREFIX):]
    
    return None


def _apply_session_cookies(response):
    """Applies session cookies to response for anonymous users"""
    # Check if anonymous_session is set in flask.g
    if hasattr(g, 'anonymous_session') and g.anonymous_session:
        # If anonymous session exists, apply session cookie to response
        response = _anonymous_session_manager.apply_session_to_response(response)
    
    # Return the modified response
    return response