"""
Implements a Flask Blueprint for authentication-related API endpoints, providing login, registration, token refresh, anonymous session management, and account management functionality for the AI writing enhancement platform.
"""

from flask import Blueprint, request, jsonify, make_response, current_app
import marshmallow
from http import HTTPStatus

from ..core.auth.jwt_service import JWTService
from ..core.auth.user_service import UserService, AuthenticationError, InvalidTokenError
from ..core.auth.anonymous_session import AnonymousSessionManager
from ..core.utils.logger import get_logger
from .schemas.auth_schema import (
    LoginSchema, RegisterSchema, TokenResponseSchema, RefreshTokenSchema,
    PasswordResetRequestSchema, PasswordResetConfirmSchema, AnonymousSessionSchema,
    AnonymousSessionConversionSchema
)
from .middleware.auth_middleware import auth_required, is_anonymous_session

# Create Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Initialize logger
logger = get_logger(__name__)

# Global service instances (to be initialized)
_jwt_service = None
_user_service = None
_anonymous_session_manager = None

def init_auth_resources(jwt_service: JWTService, user_service: UserService, anonymous_session_manager: AnonymousSessionManager):
    """
    Initialize authentication services and endpoints
    
    Args:
        jwt_service: JWTService instance for token handling
        user_service: UserService instance for user operations
        anonymous_session_manager: AnonymousSessionManager for session management
    """
    global _jwt_service, _user_service, _anonymous_session_manager
    
    # Store service instances in module-level variables for endpoint use
    _jwt_service = jwt_service
    _user_service = user_service
    _anonymous_session_manager = anonymous_session_manager
    
    logger.info("Auth resources initialized")
    
    # Validate that all required services are provided
    if not _jwt_service or not _user_service or not _anonymous_session_manager:
        raise ValueError("All service dependencies must be provided")

def validate_schema(schema_class):
    """
    Decorator to validate request with specified schema
    
    Args:
        schema_class: Marshmallow schema class to use for validation
        
    Returns:
        Decorated function with validation
    """
    def decorator(f):
        from functools import wraps
        
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Create schema instance
            schema = schema_class()
            
            # Get request data
            if request.is_json:
                data = request.json
            else:
                data = request.form
            
            try:
                # Validate request data
                validated_data = schema.load(data)
                
                # Call original function with validated data
                return f(validated_data, *args, **kwargs)
            except marshmallow.ValidationError as err:
                # Return validation errors
                return jsonify({
                    "error": "validation_error",
                    "message": "Invalid request data",
                    "details": err.messages
                }), HTTPStatus.BAD_REQUEST
        
        return wrapper
    
    return decorator

@auth_bp.route('/login', methods=['POST'])
@validate_schema(LoginSchema)
def login(validated_data):
    """
    Authenticate user with email and password
    
    Returns:
        JSON: User authentication tokens and basic profile information
    """
    email = validated_data['email']
    password = validated_data['password']
    
    try:
        # Extract email and password from validated request data
        user_data = _user_service.authenticate_user(email, password)
        
        # Format successful response with TokenResponseSchema
        response_data = TokenResponseSchema().dump({
            "access_token": user_data["access_token"],
            "refresh_token": user_data["refresh_token"],
            "token_type": user_data.get("token_type", "Bearer"),
            "expires_in": user_data.get("expires_in", 3600),
            "user_id": user_data["_id"]
        })
        
        # If anonymous session exists, associate with authenticated user
        if is_anonymous_session():
            session = _anonymous_session_manager.get_session()
            if session:
                _anonymous_session_manager.upgrade_to_authenticated_user(user_data["_id"])
        
        # Log successful authentication with user ID (not credentials)
        logger.info("User authenticated successfully", user_id=user_data["_id"])
        
        # Return JSON response with tokens and user information
        return jsonify(response_data), HTTPStatus.OK
    
    except AuthenticationError as e:
        # Catch AuthenticationError and return appropriate error response
        logger.warning(f"Authentication failed: {str(e)}")
        return jsonify({
            "error": "authentication_failed",
            "message": str(e)
        }), HTTPStatus.UNAUTHORIZED
    
    except Exception as e:
        logger.error(f"Unexpected error during authentication: {str(e)}")
        return jsonify({
            "error": "server_error",
            "message": "An unexpected error occurred"
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@auth_bp.route('/register', methods=['POST'])
@validate_schema(RegisterSchema)
def register(validated_data):
    """
    Register a new user account
    
    Returns:
        JSON: User authentication tokens and profile information
    """
    try:
        # Extract registration details from validated request data
        email = validated_data["email"]
        password = validated_data["password"]
        first_name = validated_data.get("first_name", "")
        last_name = validated_data.get("last_name", "")
        
        # Call user_service.register_user with user details
        registered_user = _user_service.register_user(
            email=email,
            password=password,
            profile_data={
                "firstName": first_name,
                "lastName": last_name
            }
        )
        
        # Format successful response with TokenResponseSchema
        response_data = TokenResponseSchema().dump({
            "access_token": registered_user["access_token"],
            "refresh_token": registered_user["refresh_token"],
            "token_type": registered_user.get("token_type", "Bearer"),
            "expires_in": registered_user.get("expires_in", 3600),
            "user_id": registered_user["_id"]
        })
        
        # If anonymous session exists, associate with new user
        if is_anonymous_session():
            session = _anonymous_session_manager.get_session()
            if session:
                _anonymous_session_manager.upgrade_to_authenticated_user(registered_user["_id"])
        
        # Log successful registration with user ID (not credentials)
        logger.info("User registered successfully", user_id=registered_user["_id"])
        
        # Return JSON response with tokens and user information
        return jsonify(response_data), HTTPStatus.CREATED
    
    except ValueError as e:
        # Catch potential registration errors (email exists, validation)
        logger.warning(f"Registration failed - validation error: {str(e)}")
        return jsonify({
            "error": "validation_error",
            "message": str(e)
        }), HTTPStatus.BAD_REQUEST
    
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
        return jsonify({
            "error": "registration_failed",
            "message": str(e)
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@auth_bp.route('/refresh', methods=['POST'])
@validate_schema(RefreshTokenSchema)
def refresh_token(validated_data):
    """
    Refresh the access token using a valid refresh token
    
    Returns:
        JSON: New access token and refresh token
    """
    refresh_token = validated_data['refresh_token']
    
    try:
        # Extract refresh token from validated request data
        user_id = _jwt_service.get_user_id_from_token(refresh_token)
        
        # Call user_service.refresh_auth_token with token and user ID
        token_data = _user_service.refresh_auth_token(refresh_token, user_id)
        
        # Catch InvalidTokenError and return appropriate error response
        if not token_data.get("success", False):
            return jsonify({
                "error": "invalid_token",
                "message": token_data.get("error", "Invalid refresh token")
            }), HTTPStatus.UNAUTHORIZED
        
        # Format successful response with TokenResponseSchema
        response_data = {
            "access_token": token_data["access_token"],
            "token_type": token_data.get("token_type", "Bearer"),
            "expires_in": token_data.get("expires_in", 3600)
        }
        
        # Log successful token refresh with user ID (not token values)
        logger.info("Token refreshed successfully", user_id=user_id)
        
        # Return JSON response with new tokens
        return jsonify(response_data), HTTPStatus.OK
    
    except InvalidTokenError as e:
        logger.warning(f"Token refresh failed: {str(e)}")
        return jsonify({
            "error": "invalid_token",
            "message": str(e)
        }), HTTPStatus.UNAUTHORIZED
    
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {str(e)}")
        return jsonify({
            "error": "server_error",
            "message": "An unexpected error occurred"
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@auth_bp.route('/logout', methods=['POST'])
@auth_required(allow_anonymous=False)
def logout():
    """
    Invalidate user tokens and log out
    
    Returns:
        JSON: Logout confirmation message
    """
    from flask import g
    
    try:
        # Get user ID from authenticated request
        user_id = g.user_id
        
        # Extract refresh token from request if available
        refresh_token = None
        if request.is_json and 'refresh_token' in request.json:
            refresh_token = request.json['refresh_token']
        
        # Extract token ID from token claims if available
        token_id = None
        if refresh_token:
            validation = _jwt_service.validate_token(refresh_token, "refresh")
            if validation["is_valid"]:
                token_id = validation["payload"].get("jti")
        
        # Determine if logging out from all devices (query parameter)
        all_devices = request.args.get('all', 'false').lower() == 'true'
        
        # Call user_service.logout_user with appropriate parameters
        _user_service.logout_user(user_id, token_id, all_devices)
        
        # Log successful logout with user ID
        logger.info("User logged out successfully", user_id=user_id, all_devices=all_devices)
        
        # Return success message JSON response
        return jsonify({
            "message": "Logged out successfully"
        }), HTTPStatus.OK
    
    except Exception as e:
        logger.error(f"Unexpected error during logout: {str(e)}")
        return jsonify({
            "error": "logout_failed",
            "message": "An unexpected error occurred"
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@auth_bp.route('/anonymous', methods=['POST'])
def create_anonymous_session():
    """
    Create a new anonymous session for immediate usage
    
    Returns:
        JSON: Anonymous session ID and expiration information
    """
    try:
        # Check if user already has an anonymous session
        if is_anonymous_session():
            session = _anonymous_session_manager.get_session()
            if session:
                # Return that session ID
                response_data = {
                    "session_id": session.get("session_id"),
                    "expires_at": session.get("expires_at")
                }
                
                # Create response object with session data
                response = make_response(jsonify(response_data))
                
                # Apply session cookie to response
                response = _anonymous_session_manager.apply_session_to_response(response)
                
                return response, HTTPStatus.OK
        
        # Create new anonymous session with anonymous_session_manager
        session_id = _anonymous_session_manager.create_session()
        
        # Format response with AnonymousSessionSchema
        response_data = {
            "session_id": session_id,
            "expires_at": datetime.now() + timedelta(seconds=86400)  # 24 hours
        }
        
        # Create response object
        response = make_response(jsonify(response_data))
        
        # Apply session cookie to response
        response = _anonymous_session_manager.apply_session_to_response(response, session_id)
        
        # Log anonymous session creation
        logger.info("Anonymous session created", session_id=session_id)
        
        # Return response with session data and cookie
        return response, HTTPStatus.CREATED
    
    except Exception as e:
        logger.error(f"Error creating anonymous session: {str(e)}")
        return jsonify({
            "error": "session_creation_failed",
            "message": "An unexpected error occurred"
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@auth_bp.route('/convert', methods=['POST'])
@validate_schema(AnonymousSessionConversionSchema)
def convert_anonymous_to_registered(validated_data):
    """
    Convert an anonymous user to a registered account
    
    Returns:
        JSON: User authentication tokens and profile information
    """
    try:
        # Check if request has a valid anonymous session
        if not is_anonymous_session():
            return jsonify({
                "error": "invalid_request",
                "message": "No anonymous session found"
            }), HTTPStatus.BAD_REQUEST
        
        # Extract registration details from validated request data
        email = validated_data["email"]
        password = validated_data["password"]
        first_name = validated_data.get("first_name", "")
        last_name = validated_data.get("last_name", "")
        
        # Get session ID from anonymous session
        session = _anonymous_session_manager.get_session()
        session_id = session.get("session_id")
        
        if not session_id:
            return jsonify({
                "error": "invalid_session",
                "message": "Invalid anonymous session"
            }), HTTPStatus.BAD_REQUEST
        
        # Call user_service.convert_to_registered_user with session ID and registration data
        registered_user = _user_service.convert_to_registered_user(
            session_id=session_id,
            email=email,
            password=password,
            profile_data={
                "first_name": first_name,
                "last_name": last_name
            }
        )
        
        # Format successful response with TokenResponseSchema
        response_data = TokenResponseSchema().dump({
            "access_token": registered_user["access_token"],
            "refresh_token": registered_user["refresh_token"],
            "token_type": registered_user.get("token_type", "Bearer"),
            "expires_in": registered_user.get("expires_in", 3600),
            "user_id": registered_user["_id"]
        })
        
        # Log successful conversion from anonymous to registered
        logger.info("Anonymous user converted to registered account", 
                  user_id=registered_user["_id"])
        
        # Return JSON response with tokens and user information
        return jsonify(response_data), HTTPStatus.OK
    
    except ValueError as e:
        logger.warning(f"Session conversion failed: {str(e)}")
        return jsonify({
            "error": "validation_error",
            "message": str(e)
        }), HTTPStatus.BAD_REQUEST
    
    except Exception as e:
        logger.error(f"Unexpected error during session conversion: {str(e)}")
        return jsonify({
            "error": "conversion_failed",
            "message": "An unexpected error occurred"
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@auth_bp.route('/password-reset/request', methods=['POST'])
@validate_schema(PasswordResetRequestSchema)
def request_password_reset(validated_data):
    """
    Request a password reset token
    
    Returns:
        JSON: Confirmation message with email delivery information
    """
    email = validated_data['email']
    
    try:
        # Extract email from validated request data
        reset_data = _user_service.request_password_reset(email)
        
        # Catch potential errors (user not found)
        # Note: In a production system, this would trigger an email
        # with the reset link rather than returning the token
        
        # Log password reset request (without exposing token)
        logger.info("Password reset requested", email=email)
        
        # Return success message indicating email delivery
        return jsonify({
            "message": "If your email exists in our system, you will receive a password reset link shortly."
        }), HTTPStatus.OK
    
    except Exception as e:
        # Don't expose if email exists for security reasons
        logger.error(f"Error processing password reset request: {str(e)}")
        return jsonify({
            "message": "If your email exists in our system, you will receive a password reset link shortly."
        }), HTTPStatus.OK

@auth_bp.route('/password-reset/confirm', methods=['POST'])
@validate_schema(PasswordResetConfirmSchema)
def reset_password(validated_data):
    """
    Reset password using a valid reset token
    
    Returns:
        JSON: Password reset confirmation
    """
    token = validated_data['token']
    new_password = validated_data['new_password']
    
    try:
        # Extract token and new password from validated request data
        # Extract user ID from token if possible
        user_id = _jwt_service.get_user_id_from_token(token)
        
        # Call user_service.reset_password with user ID, token, and new password
        reset_success = _user_service.reset_password(user_id, token, new_password)
        
        # Catch potential errors (invalid token, password policy)
        if not reset_success:
            return jsonify({
                "error": "password_reset_failed",
                "message": "Failed to reset password"
            }), HTTPStatus.BAD_REQUEST
        
        # Log successful password reset (without exposing password)
        logger.info("Password reset successful", user_id=user_id)
        
        # Return success message JSON response
        return jsonify({
            "message": "Password has been reset successfully"
        }), HTTPStatus.OK
    
    except InvalidTokenError as e:
        logger.warning(f"Password reset failed - invalid token: {str(e)}")
        return jsonify({
            "error": "invalid_token",
            "message": "The reset token is invalid or has expired"
        }), HTTPStatus.BAD_REQUEST
    
    except ValueError as e:
        logger.warning(f"Password reset failed - validation error: {str(e)}")
        return jsonify({
            "error": "validation_error",
            "message": str(e)
        }), HTTPStatus.BAD_REQUEST
    
    except Exception as e:
        logger.error(f"Unexpected error during password reset: {str(e)}")
        return jsonify({
            "error": "password_reset_failed",
            "message": "An unexpected error occurred"
        }), HTTPStatus.INTERNAL_SERVER_ERROR