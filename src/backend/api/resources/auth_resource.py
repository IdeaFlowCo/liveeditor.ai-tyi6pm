"""
Flask RESTful resource for authentication endpoints including login, registration, token 
refresh, logout, and anonymous session management.
"""

from flask_restful import Resource
from flask import request, jsonify, current_app
from werkzeug.exceptions import HTTPException
from marshmallow import ValidationError

from ...core.auth.user_service import UserService
from ...core.auth.jwt_service import JWTService
from ...core.auth.password_service import PasswordService
from ...core.auth.anonymous_session import AnonymousSessionService
from ...data.redis.rate_limiter import RateLimiter

from ..schemas.auth_schema import (
    LoginSchema, RegisterSchema, RefreshTokenSchema, 
    ForgotPasswordSchema, ResetPasswordSchema,
    EmailVerificationSchema, AnonymousSessionSchema
)
from ...core.utils.logger import logger


class AuthResource(Resource):
    """Flask RESTful resource for handling authentication endpoints"""
    
    def __init__(self, user_service, jwt_service, password_service, 
                 anonymous_session_service, rate_limiter):
        """
        Initializes the AuthResource with required services
        
        Args:
            user_service: UserService instance for user operations
            jwt_service: JWTService instance for token operations
            password_service: PasswordService instance for password operations
            anonymous_session_service: AnonymousSessionService instance
            rate_limiter: RateLimiter instance for rate limiting
        """
        self.user_service = user_service
        self.jwt_service = jwt_service
        self.password_service = password_service
        self.anonymous_session_service = anonymous_session_service
        self.rate_limiter = rate_limiter
        
        # Map action to handler method
        self.action_handlers = {
            'login': self._handle_login,
            'register': self._handle_register,
            'refresh': self._handle_refresh,
            'logout': self._handle_logout,
            'forgot_password': self._handle_forgot_password,
            'reset_password': self._handle_reset_password,
            'verify_email': self._handle_verify_email,
            'anonymous_session': self._handle_anonymous_session,
        }
    
    def post(self):
        """
        Handles various authentication requests by routing to appropriate handlers
        
        Returns:
            JSON response with authentication results or error messages
        """
        try:
            # Get request data
            data = request.get_json()
            
            # Check for required action field
            if not data or 'action' not in data:
                return {'error': 'Missing required field: action'}, 400
            
            action = data.get('action')
            
            # Check if action is valid
            if action not in self.action_handlers:
                return {'error': f'Invalid action: {action}'}, 400
            
            # Call appropriate handler
            handler = self.action_handlers[action]
            result = handler(data)
            
            # Log successful action
            logger.info(f"Authentication action completed: {action}")
            
            return result
            
        except ValidationError as e:
            # Handle validation errors
            logger.warning(f"Validation error during authentication: {str(e)}")
            return {'error': 'Validation error', 'details': e.messages}, 400
            
        except HTTPException as e:
            # Re-raise HTTP exceptions
            raise
            
        except Exception as e:
            # Handle unexpected errors
            logger.error(f"Error during authentication: {str(e)}", exc_info=True)
            return {'error': 'An unexpected error occurred'}, 500
    
    def _handle_login(self, data):
        """
        Handles user login requests with rate limiting and security measures
        
        Args:
            data: Request data containing login credentials
            
        Returns:
            Authentication response with tokens and user data
        """
        # Validate login data
        login_data = LoginSchema().load(data)
        
        # Check rate limiting
        client_ip = self._get_client_ip()
        rate_limit_key = f"login:{client_ip}"
        
        if self.rate_limiter.check_rate_limit(rate_limit_key, 5, 300)[0]:  # 5 attempts per 5 minutes
            logger.warning(f"Login rate limit exceeded for IP: {client_ip}")
            return {'error': 'Too many login attempts. Please try again later.'}, 429
        
        # Extract credentials
        email = login_data['email']
        password = login_data['password']
        
        try:
            # Authenticate user
            user = self.user_service.authenticate_user(email, password)
            
            # Generate tokens
            tokens = self.jwt_service.generate_tokens(user['_id'])
            
            # Log successful login
            logger.info(f"User login successful: {email}")
            
            # Return user data and tokens
            return {
                'user': {
                    'id': user['_id'],
                    'email': user['email'],
                    'firstName': user.get('firstName', ''),
                    'lastName': user.get('lastName', ''),
                    'emailVerified': user.get('emailVerified', False)
                },
                'tokens': tokens
            }
            
        except Exception as e:
            # Update rate limit counter on failed attempt
            self.rate_limiter.update_rate_limit(rate_limit_key, 5, 300)
            
            logger.warning(f"Login failed for email: {email}")
            return {'error': 'Invalid email or password'}, 401
    
    def _handle_register(self, data):
        """
        Handles user registration requests with password strength validation
        
        Args:
            data: Request data containing registration information
            
        Returns:
            Registration response with user data and tokens
        """
        # Validate registration data
        register_data = RegisterSchema().load(data)
        
        # Check password strength
        password = register_data['password']
        if not self.password_service.check_password_strength(password):
            return {'error': 'Password does not meet security requirements'}, 400
        
        try:
            # Extract profile data
            profile_data = {
                'firstName': register_data.get('first_name', ''),
                'lastName': register_data.get('last_name', ''),
            }
            
            # Register user
            user = self.user_service.register_user(
                register_data['email'], 
                password,
                profile_data
            )
            
            # Check for anonymous session to convert
            anonymous_session_id = data.get('anonymous_session_id')
            if anonymous_session_id:
                # Convert anonymous session to authenticated
                self.anonymous_session_service.convert_to_authenticated(
                    anonymous_session_id, user['_id']
                )
            
            # Generate tokens
            tokens = self.jwt_service.generate_tokens(user['_id'])
            
            # Log successful registration
            logger.info(f"User registration successful: {register_data['email']}")
            
            # Return user data and tokens
            return {
                'user': {
                    'id': user['_id'],
                    'email': user['email'],
                    'firstName': user.get('firstName', ''),
                    'lastName': user.get('lastName', ''),
                    'emailVerified': False
                },
                'tokens': tokens
            }
            
        except Exception as e:
            logger.error(f"Registration failed: {str(e)}")
            
            # Check for duplicate email error
            if "duplicate key" in str(e).lower() or "already exists" in str(e).lower():
                return {'error': 'Email is already registered'}, 409
                
            return {'error': 'Registration failed'}, 400
    
    def _handle_refresh(self, data):
        """
        Handles token refresh requests with token rotation for security
        
        Args:
            data: Request data containing refresh token
            
        Returns:
            New authentication tokens
        """
        # Validate refresh token data
        token_data = RefreshTokenSchema().load(data)
        refresh_token = token_data['refresh_token']
        
        try:
            # Validate refresh token
            validation_result = self.jwt_service.validate_refresh_token(refresh_token)
            
            if not validation_result['is_valid']:
                return {'error': validation_result['error']}, 401
            
            user_id = validation_result['payload']['sub']
            
            # Invalidate old refresh token (rotation)
            token_id = validation_result['payload'].get('jti')
            if token_id:
                self.jwt_service.invalidate_tokens(user_id, [token_id])
            
            # Generate new tokens
            new_tokens = self.jwt_service.generate_tokens(user_id)
            
            # Log token refresh
            logger.info(f"Token refreshed for user: {user_id}")
            
            return new_tokens
            
        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            return {'error': 'Token refresh failed'}, 401
    
    def _handle_logout(self, data):
        """
        Handles user logout requests by invalidating tokens
        
        Args:
            data: Request data containing refresh token
            
        Returns:
            Logout confirmation response
        """
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return {'error': 'Refresh token is required'}, 400
        
        try:
            # Validate token to get user_id
            validation_result = self.jwt_service.validate_refresh_token(refresh_token)
            
            if not validation_result['is_valid']:
                return {'message': 'Logged out'}, 200  # Return success even if token is invalid
            
            user_id = validation_result['payload']['sub']
            
            # Invalidate all tokens for this user
            logout_all = data.get('logout_all_devices', False)
            self.jwt_service.invalidate_tokens(user_id, invalidate_all=logout_all)
            
            # Log logout
            logger.info(f"User logged out: {user_id}, all devices: {logout_all}")
            
            return {'message': 'Logged out successfully'}
            
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return {'message': 'Logged out'}, 200  # Return success even if error occurs
    
    def _handle_forgot_password(self, data):
        """
        Handles forgot password requests with rate limiting
        
        Args:
            data: Request data containing email
            
        Returns:
            Password reset instructions response
        """
        # Validate forgot password data
        reset_data = ForgotPasswordSchema().load(data)
        email = reset_data['email']
        
        # Check rate limiting
        client_ip = self._get_client_ip()
        rate_limit_key = f"password_reset:{client_ip}"
        
        if self.rate_limiter.check_rate_limit(rate_limit_key, 3, 3600)[0]:  # 3 attempts per hour
            logger.warning(f"Password reset rate limit exceeded for IP: {client_ip}")
            return {'error': 'Too many reset attempts. Please try again later.'}, 429
        
        try:
            # Generate reset token
            reset_data = self.password_service.generate_reset_token(email)
            
            # Log password reset request
            logger.info(f"Password reset requested for email: {email}")
            
            # In a real application, send an email with the reset link
            # For this implementation, we'll just return success
            return {
                'message': 'Password reset instructions have been sent to your email',
                'email': email
            }
            
        except Exception as e:
            logger.error(f"Password reset request failed: {str(e)}")
            
            # Return success even if email doesn't exist to prevent user enumeration
            return {
                'message': 'Password reset instructions have been sent to your email if the account exists',
                'email': email
            }
    
    def _handle_reset_password(self, data):
        """
        Handles password reset request verification and execution
        
        Args:
            data: Request data containing token and new password
            
        Returns:
            Password reset confirmation response
        """
        # Validate reset password data
        reset_data = ResetPasswordSchema().load(data)
        token = reset_data['token']
        new_password = reset_data['new_password']
        user_id = data.get('user_id')  # May not be in schema but needed for reset
        
        try:
            # Validate password strength
            if not self.password_service.check_password_strength(new_password):
                return {'error': 'Password does not meet security requirements'}, 400
                
            # Reset password
            success = self.password_service.reset_password(user_id, token, new_password)
            
            if not success:
                return {'error': 'Invalid or expired token'}, 400
            
            # Log password reset
            logger.info(f"Password reset completed for user: {user_id}")
            
            return {'message': 'Password has been reset successfully'}
            
        except Exception as e:
            logger.error(f"Password reset failed: {str(e)}")
            return {'error': 'Password reset failed'}, 400
    
    def _handle_verify_email(self, data):
        """
        Handles email verification token validation
        
        Args:
            data: Request data containing verification token
            
        Returns:
            Email verification confirmation response
        """
        # Extract verification token
        token = data.get('token')
        user_id = data.get('user_id')
        
        if not token or not user_id:
            return {'error': 'Verification token and user ID are required'}, 400
        
        try:
            # Verify email
            success = self.user_service.verify_email(user_id, token)
            
            if not success:
                return {'error': 'Invalid or expired verification token'}, 400
            
            # Log email verification
            logger.info(f"Email verified for user: {user_id}")
            
            return {'message': 'Email verified successfully'}
            
        except Exception as e:
            logger.error(f"Email verification failed: {str(e)}")
            return {'error': 'Email verification failed'}, 400
    
    def _handle_anonymous_session(self, data):
        """
        Creates or validates an anonymous session
        
        Args:
            data: Request data containing optional session ID
            
        Returns:
            Anonymous session response with session ID
        """
        # Validate anonymous session data if session_id is provided
        session_id = None
        if 'session_id' in data:
            try:
                session_data = AnonymousSessionSchema().load(data)
                session_id = session_data.get('session_id')
            except ValidationError:
                # Invalid session_id, will create a new one
                pass
        
        try:
            if session_id:
                # Validate existing session
                is_valid = self.anonymous_session_service.validate_session(session_id)
                
                if not is_valid:
                    # Create new session if invalid
                    session_id = self.anonymous_session_service.create_anonymous_session()
                    logger.info(f"Created new anonymous session: {session_id}")
                else:
                    logger.info(f"Validated existing anonymous session: {session_id}")
            else:
                # Create new session
                session_id = self.anonymous_session_service.create_anonymous_session()
                logger.info(f"Created new anonymous session: {session_id}")
            
            return {
                'session_id': session_id,
                'ttl': 86400  # 24 hours in seconds
            }
            
        except Exception as e:
            logger.error(f"Anonymous session error: {str(e)}")
            
            # Create new session as fallback
            try:
                session_id = self.anonymous_session_service.create_anonymous_session()
                
                return {
                    'session_id': session_id,
                    'ttl': 86400  # 24 hours in seconds
                }
            except Exception as e:
                logger.error(f"Failed to create anonymous session: {str(e)}")
                return {'error': 'Failed to create anonymous session'}, 500
    
    def _get_client_ip(self):
        """
        Helper method to get client IP address for rate limiting and logging
        
        Returns:
            Client IP address string
        """
        # Check for proxy headers first
        if 'X-Forwarded-For' in request.headers:
            # X-Forwarded-For header value is a comma-separated list of IP addresses
            # The first one is the original client IP
            forwarded_for = request.headers.get('X-Forwarded-For', '')
            ip = forwarded_for.split(',')[0].strip()
            return ip
        
        # Fall back to remote address
        return request.remote_addr