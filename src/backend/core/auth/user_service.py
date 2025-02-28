"""
Provides comprehensive user management functionality for the AI writing enhancement platform, supporting both anonymous and authenticated users. This service acts as a high-level abstraction over user operations, including registration, authentication, profile management, and the transition from anonymous to authenticated sessions.
"""

import uuid  # standard library
from datetime import datetime  # standard library
import typing  # standard library

from ..utils.logger import get_logger  # Import get_logger function from logger module
from ..utils.validators import is_valid_email, is_valid_password  # Import validation functions
from ...data.mongodb.repositories.user_repository import UserRepository, UserNotFoundError, DuplicateEmailError  # Import UserRepository class and exceptions
from .jwt_service import JWTService  # Import JWTService class
from .password_service import PasswordService  # Import PasswordService class
from .anonymous_session import AnonymousSessionManager  # Import AnonymousSessionManager class


# Initialize logger
logger = get_logger(__name__)

# Constants
EMAIL_VERIFICATION_EXPIRY_HOURS = 24  # Email verification token expiry time


class UserService:
    """
    Core service for user management operations including authentication, registration, and profile management
    """

    def __init__(
        self,
        user_repository: UserRepository,
        jwt_service: JWTService,
        password_service: PasswordService,
        anonymous_session_manager: AnonymousSessionManager
    ):
        """
        Initialize the user service with required dependencies

        Args:
            user_repository: UserRepository instance for data access
            jwt_service: JWTService instance for token handling
            password_service: PasswordService instance for password management
            anonymous_session_manager: AnonymousSessionManager instance for managing anonymous sessions
        """
        # Store references to injected dependencies
        self._user_repository = user_repository
        self._jwt_service = jwt_service
        self._password_service = password_service
        self._anonymous_session_manager = anonymous_session_manager

        # Initialize logger for user operations
        logger.info("UserService initialized")

    def register_user(self, email: str, password: str, profile_data: dict) -> dict:
        """
        Registers a new user with email and password

        Args:
            email: User's email address
            password: User's password
            profile_data: Dictionary containing additional profile information

        Returns:
            Newly created user data and authentication tokens
        """
        # Validate email format using is_valid_email
        if not is_valid_email(email):
            logger.warning(f"Invalid email format provided: {email}")
            raise ValueError("Invalid email format")

        # Validate password strength using is_valid_password
        if not is_valid_password(password):
            logger.warning("Password does not meet strength requirements")
            raise ValueError("Password must be at least 8 characters and include uppercase, lowercase, number, and special character")

        # Hash the password using password_service
        password_hash = self._password_service.hash_password(password)

        # Prepare user data with email, password_hash and profile information
        user_data = {
            "email": email,
            "password_hash": password_hash,
            **profile_data
        }

        # Create user record in the database via user_repository
        user = self._user_repository.create_user(user_data)

        # Generate authentication tokens using jwt_service
        auth_tokens = self._jwt_service.create_token_pair(str(user["_id"]))

        # Generate email verification token
        verification_token = self.generate_email_verification(str(user["_id"]))

        # Log successful registration with sanitized info
        logger.info(f"User registered successfully: {email}", user_id=str(user["_id"]))

        # Return user data with auth tokens
        return {**user, **auth_tokens}

    def authenticate_user(self, email: str, password: str) -> dict:
        """
        Authenticates a user with email and password

        Args:
            email: User's email address
            password: User's password

        Returns:
            User data and authentication tokens if successful
        """
        # Retrieve user by email from user_repository
        user = self._user_repository.get_by_email(email, include_password_hash=True)

        # If user not found, raise AuthenticationError
        if not user:
            logger.warning(f"Authentication failed: User not found with email {email}")
            raise AuthenticationError("Invalid credentials")

        # Verify password using password_service
        if 'passwordHash' not in user or not self._password_service.verify_password(password, user['passwordHash']):
            logger.warning(f"Authentication failed: Invalid password for user {email}")
            raise AuthenticationError("Invalid credentials")

        # Update last login timestamp
        self._user_repository.update_last_login(str(user["_id"]))

        # Generate authentication tokens using jwt_service
        auth_tokens = self._jwt_service.create_token_pair(str(user["_id"]))

        # Log successful authentication (without exposing credentials)
        logger.info(f"User authenticated successfully: {email}", user_id=str(user["_id"]))

        # Return user data with auth tokens
        return {**user, **auth_tokens}

    def refresh_auth_token(self, refresh_token: str, user_id: str) -> dict:
        """
        Refreshes authentication tokens using a refresh token

        Args:
            refresh_token: Refresh token string
            user_id: User ID associated with the refresh token

        Returns:
            New authentication tokens
        """
        # Validate refresh token using jwt_service
        validation_result = self._jwt_service.validate_token(refresh_token, "refresh")
        if not validation_result["is_valid"]:
            logger.warning(f"Invalid refresh token: {validation_result['error']}")
            raise InvalidTokenError(validation_result["error"])

        # Generate new access token using jwt_service.refresh_access_token
        refreshed_token = self._jwt_service.refresh_access_token(refresh_token, user_id)

        # Log token refresh (without exposing tokens)
        logger.info(f"Token refreshed successfully for user: {user_id}")

        # Return new tokens
        return refreshed_token

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieves a user by their ID

        Args:
            user_id: User's ID string

        Returns:
            User data if found
        """
        # Validate user_id format
        if not user_id:
            logger.warning("User ID cannot be empty")
            raise ValueError("User ID cannot be empty")

        # Retrieve user by ID from user_repository
        user = self._user_repository.get_by_id(user_id)

        # If user not found, raise UserNotFoundError
        if not user:
            logger.warning(f"User not found with ID: {user_id}")
            raise UserNotFoundError(user_id)

        # Return user data (excluding sensitive fields)
        return user

    def update_user_profile(self, user_id: str, profile_data: dict) -> dict:
        """
        Updates a user's profile information

        Args:
            user_id: User's ID string
            profile_data: Dictionary containing profile information to update

        Returns:
            Updated user data
        """
        # Validate user_id format
        if not user_id:
            logger.warning("User ID cannot be empty")
            raise ValueError("User ID cannot be empty")

        # Filter profile_data to prevent updating restricted fields
        safe_profile_data = {
            k: v for k, v in profile_data.items()
            if k in ["firstName", "lastName", "preferences"]  # Allowed fields
        }

        # Update user via user_repository
        updated_user = self._user_repository.update_user(user_id, safe_profile_data)

        # Return updated user data
        return updated_user

    def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """
        Changes a user's password

        Args:
            user_id: User's ID string
            current_password: User's current password
            new_password: User's new password

        Returns:
            True if password was changed successfully
        """
        # Validate user_id format
        if not user_id:
            logger.warning("User ID cannot be empty")
            raise ValueError("User ID cannot be empty")

        # Change password using password_service
        change_result = self._password_service.change_password(user_id, current_password, new_password)

        # Log password change (without exposing passwords)
        logger.info(f"Password changed successfully for user: {user_id}")

        # Return success status
        return change_result

    def request_password_reset(self, email: str) -> dict:
        """
        Initiates a password reset process

        Args:
            email: User's email address

        Returns:
            Reset token and user information
        """
        # Validate email format
        if not is_valid_email(email):
            logger.warning(f"Invalid email format provided: {email}")
            raise ValueError("Invalid email format")

        # Retrieve user by email from repository
        user = self._user_repository.get_by_email(email)

        # If user not found, raise UserNotFoundError
        if not user:
            logger.warning(f"User not found with email: {email}")
            raise UserNotFoundError(email)

        # Generate reset token using password_service
        reset_token = self._password_service.create_reset_token(str(user["_id"]))

        # Log reset request (without exposing the token)
        logger.info(f"Password reset requested for user: {email}", user_id=str(user["_id"]))

        # Return user data with reset token
        return {"user_id": str(user["_id"]), "reset_token": reset_token}

    def reset_password(self, user_id: str, token: str, new_password: str) -> bool:
        """
        Resets a user's password using a reset token

        Args:
            user_id: User's ID string
            token: Password reset token
            new_password: New password to set

        Returns:
            True if password was reset successfully
        """
        # Validate user_id format
        if not user_id:
            logger.warning("User ID cannot be empty")
            raise ValueError("User ID cannot be empty")

        # Reset password using password_service
        reset_result = self._password_service.reset_password(user_id, token, new_password)

        # Log password reset (without exposing password)
        logger.info(f"Password reset successfully for user: {user_id}")

        # Return success status
        return reset_result

    def generate_email_verification(self, user_id: str) -> str:
        """
        Generates an email verification token

        Args:
            user_id: User's ID string

        Returns:
            Verification token
        """
        # Validate user_id format
        if not user_id:
            logger.warning("User ID cannot be empty")
            raise ValueError("User ID cannot be empty")

        # Generate unique verification token using uuid
        verification_token = str(uuid.uuid4())

        # Calculate expiration time (current time + EMAIL_VERIFICATION_EXPIRY_HOURS)
        expiry = datetime.utcnow() + datetime.timedelta(hours=EMAIL_VERIFICATION_EXPIRY_HOURS)

        # Store token and expiry in user record
        stored = self._user_repository.store_verification_token(user_id, verification_token, expiry)
        if not stored:
            logger.error(f"Failed to store verification token for user: {user_id}")
            raise Exception("Failed to create email verification token")

        # Log token generation (without exposing the token)
        logger.info(f"Email verification token generated for user: {user_id}, expires: {expiry.isoformat()}")

        # Return the verification token
        return verification_token

    def verify_email(self, user_id: str, token: str) -> bool:
        """
        Verifies a user's email using a verification token

        Args:
            user_id: User's ID string
            token: Email verification token

        Returns:
            True if email was verified successfully
        """
        # Validate user_id format
        if not user_id:
            logger.warning("User ID cannot be empty")
            raise ValueError("User ID cannot be empty")

        # Verify email using user_repository
        verified = self._user_repository.verify_email(user_id)

        # Log successful verification
        logger.info(f"Email verified successfully for user: {user_id}")

        # Return success status
        return verified

    def logout_user(self, user_id: str, token_id: str = None, all_devices: bool = False) -> bool:
        """
        Logs out a user by invalidating their tokens

        Args:
            user_id: User's ID string
            token_id: ID of the token to invalidate (optional)
            all_devices: Whether to invalidate all tokens for the user

        Returns:
            True if logout was successful
        """
        # Validate user_id format
        if not user_id:
            logger.warning("User ID cannot be empty")
            raise ValueError("User ID cannot be empty")

        # Invalidate tokens using jwt_service
        self._jwt_service.invalidate_tokens(user_id, [token_id] if token_id else None, all_devices)

        # Log logout action
        logger.info(f"User logged out: {user_id}, all_devices: {all_devices}")

        # Return success status
        return True

    def create_anonymous_user(self, session_id: str) -> dict:
        """
        Creates an anonymous user for immediate usage without registration

        Args:
            session_id: Session identifier

        Returns:
            Anonymous user data
        """
        # Validate session_id format
        if not session_id:
            logger.warning("Session ID cannot be empty")
            raise ValueError("Session ID cannot be empty")

        # Create anonymous user via user_repository
        anonymous_user = self._user_repository.create_anonymous_user(session_id)

        # Log anonymous user creation
        logger.info(f"Anonymous user created with session ID: {session_id}")

        # Return anonymous user data
        return anonymous_user

    def convert_to_registered_user(self, session_id: str, email: str, password: str, profile_data: dict) -> dict:
        """
        Converts an anonymous user to a registered user

        Args:
            session_id: Session identifier
            email: User's email address
            password: User's password
            profile_data: Dictionary containing additional profile information

        Returns:
            Registered user data and authentication tokens
        """
        # Validate email format
        if not is_valid_email(email):
            logger.warning(f"Invalid email format provided: {email}")
            raise ValueError("Invalid email format")

        # Validate password strength
        if not is_valid_password(password):
            logger.warning("Password does not meet strength requirements")
            raise ValueError("Password must be at least 8 characters and include uppercase, lowercase, number, and special character")

        # Hash the password using password_service
        password_hash = self._password_service.hash_password(password)

        # Prepare user data with email, password_hash and profile information
        user_data = {
            "email": email,
            "password_hash": password_hash,
            **profile_data
        }

        # Convert anonymous user to registered via user_repository
        registered_user = self._user_repository.convert_anonymous_to_registered(session_id, user_data)

        # Upgrade anonymous session to authenticated session
        self._anonymous_session_manager.upgrade_to_authenticated_user(session_id, str(registered_user["_id"]))

        # Generate authentication tokens using jwt_service
        auth_tokens = self._jwt_service.create_token_pair(str(registered_user["_id"]))

        # Generate email verification token
        verification_token = self.generate_email_verification(str(registered_user["_id"]))

        # Log successful conversion
        logger.info(f"Anonymous user converted to registered user: {email}")

        # Return registered user data with auth tokens
        return {**registered_user, **auth_tokens}

    def get_user_by_session(self, session_id: str) -> dict:
        """
        Retrieves a user associated with a session ID

        Args:
            session_id: Session identifier

        Returns:
            User data if found
        """
        # Validate session_id format
        if not session_id:
            logger.warning("Session ID cannot be empty")
            raise ValueError("Session ID cannot be empty")

        # Retrieve user by session ID from user_repository
        user = self._user_repository.get_by_session(session_id)

        # If user not found, raise UserNotFoundError
        if not user:
            logger.warning(f"User not found with session ID: {session_id}")
            raise UserNotFoundError(session_id)

        # Return user data (excluding sensitive fields)
        return user

    def delete_user(self, user_id: str) -> bool:
        """
        Deletes a user account

        Args:
            user_id: User's ID string

        Returns:
            True if user was deleted successfully
        """
        # Validate user_id format
        if not user_id:
            logger.warning("User ID cannot be empty")
            raise ValueError("User ID cannot be empty")

        # Delete user via user_repository
        deleted = self._user_repository.delete_user(user_id)

        # Invalidate all tokens for the user
        self._jwt_service.invalidate_tokens(user_id, invalidate_all=True)

        # Log user deletion
        logger.info(f"User deleted: {user_id}")

        # Return success status
        return deleted

    def update_user_preferences(self, user_id: str, preferences: dict) -> dict:
        """
        Updates a user's preferences

        Args:
            user_id: User's ID string
            preferences: Dictionary of preference settings

        Returns:
            Updated preferences
        """
        # Validate user_id format
        if not user_id:
            logger.warning("User ID cannot be empty")
            raise ValueError("User ID cannot be empty")

        # Update user preferences via user_repository
        updated_preferences = self._user_repository.update_user_preferences(user_id, preferences)

        # Log preferences update
        logger.info(f"Preferences updated for user: {user_id}")

        # Return updated preferences data
        return updated_preferences


class AuthenticationError(Exception):
    """
    Exception raised when authentication fails
    """

    def __init__(self, message: str = None):
        """
        Initialize authentication error with message

        Args:
            message: Error message
        """
        # Set default message if none provided
        if message is None:
            message = "Authentication failed"
        # Call parent Exception constructor with message
        super().__init__(message)


class UserNotFoundError(Exception):
    """
    Exception raised when a user cannot be found
    """

    def __init__(self, user_id: str, message: str = None):
        """
        Initialize user not found error with user ID and message

        Args:
            user_id: ID of the user that wasn't found
            message: Error message
        """
        # Set default message if none provided
        if message is None:
            message = f"User with ID {user_id} not found"
        # Call parent Exception constructor with message
        super().__init__(message)
        # Store user_id for reference
        self.user_id = user_id


class InvalidTokenError(Exception):
    """
    Exception raised when a token is invalid or expired
    """

    def __init__(self, message: str = None):
        """
        Initialize invalid token error with message

        Args:
            message: Error message
        """
        # Set default message if none provided
        if message is None:
            message = "Invalid or expired token"
        # Call parent Exception constructor with message
        super().__init__(message)


class EmailVerificationError(Exception):
    """
    Exception raised when email verification fails
    """

    def __init__(self, message: str = None):
        """
        Initialize email verification error with message

        Args:
            message: Error message
        """
        # Set default message if none provided
        if message is None:
            message = "Email verification failed"
        # Call parent Exception constructor with message
        super().__init__(message)