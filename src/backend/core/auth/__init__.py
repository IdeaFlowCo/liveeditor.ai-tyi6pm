"""
Package initialization for the authentication module that provides a centralized
entry point for all authentication services.

This module exposes core authentication classes and functions for anonymous sessions, 
JWT management, password handling, and user management.
"""

# Import services from their respective modules
from .user_service import UserService, AuthenticationError, InvalidTokenError
from .jwt_service import JWTService
from .password_service import PasswordService
from .anonymous_session import AnonymousSessionManager

# Alias AnonymousSessionManager as AnonymousSession for cleaner imports
AnonymousSession = AnonymousSessionManager

# Define EmailVerificationRequired exception
class EmailVerificationRequired(Exception):
    """
    Exception raised when email verification is required before proceeding
    with a user operation.
    """
    def __init__(self, message=None):
        if message is None:
            message = "Email verification is required to proceed"
        super().__init__(message)

# Define what is exported when module is imported with *
__all__ = [
    # Core services
    'UserService',
    'JWTService',
    'PasswordService',
    'AnonymousSession',
    
    # Exceptions
    'AuthenticationError',
    'EmailVerificationRequired',
    'InvalidTokenError'
]