"""Initializes the core package and exposes key services and functionality from core submodules.
This is the main entry point for accessing business logic components of the AI writing enhancement application.
"""

from ..core.auth.user_service import UserService  # Import UserService class
from ..core.auth.jwt_service import JWTService  # Import JWTService class
from ..core.auth.anonymous_session import AnonymousSession  # Import AnonymousSession class
from ..core.ai.suggestion_generator import SuggestionGenerator  # Import SuggestionGenerator class
from ..core.ai.chat_processor import ChatProcessor  # Import ChatProcessor class
from ..core.documents.document_service import DocumentService  # Import DocumentService class
from ..core.templates.template_service import TemplateService  # Import TemplateService class
from ..core.utils.logger import logger  # Import shared logging utility

__version__ = "1.0.0"


__all__ = [
    "UserService",  # Provide user authentication and management functionality
    "JWTService",  # Provide JWT token handling functionality
    "AnonymousSession",  # Provide anonymous user session management
    "SuggestionGenerator",  # Provide AI-powered writing suggestion functionality
    "ChatProcessor",  # Provide AI chat processing functionality
    "DocumentService",  # Provide document management functionality
    "TemplateService",  # Provide AI prompt template management functionality
    "__version__"  # Expose core package version information
]