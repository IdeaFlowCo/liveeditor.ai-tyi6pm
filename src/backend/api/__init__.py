# flask v2.3.0 - Core web framework for the API
from flask import Flask, Blueprint, jsonify, request, g # flask==2.3.0
# flask_restful 0.3.10 - Extension for building RESTful APIs with Flask
from flask_restful import Api
# flask_cors 3.0.10 - Extension for handling Cross-Origin Resource Sharing
from flask_cors import CORS

# Internal imports
from .middleware.auth_middleware import setup_auth, get_current_user, get_current_user_id, is_authenticated, is_anonymous_session # src/backend/api/middleware/auth_middleware.py
from .middleware.cors_middleware import CORSMiddleware # src/backend/api/middleware/cors_middleware.py
from .middleware.error_handler import register_error_handlers # src/backend/api/middleware/error_handler.py
from .middleware.logging_middleware import setup_request_logging # src/backend/api/middleware/logging_middleware.py
from .middleware.rate_limiter import setup_rate_limiting # src/backend/api/middleware/rate_limiter.py
from .documents import documents_bp # src/backend/api/documents.py
from .auth import auth_bp # src/backend/api/auth.py
from .users import users_bp # src/backend/api/users.py
from .chat import chat_bp # src/backend/api/chat.py
from .suggestions import suggestions_bp # src/backend/api/suggestions.py
from .templates import templates_bp # src/backend/api/templates.py
from ..core.auth.jwt_service import JWTService # src/backend/core/auth/jwt_service.py
from ..core.auth.anonymous_session import AnonymousSessionManager # src/backend/core/auth/anonymous_session.py
from ..core.auth.user_service import UserService # src/backend/core/auth/user_service.py
from ..core.utils.logger import get_logger # src/backend/core/utils/logger.py

# Initialize logger
logger = get_logger(__name__)

def create_app(config: dict) -> Flask:
    """Factory function to create and configure a Flask application with all API routes and middleware"""
    # Create a new Flask application instance
    app = Flask(__name__)

    # Apply configuration from provided config dictionary
    app.config.update(config)

    # Initialize middleware components (CORS, logging, auth, rate limiting)
    init_middleware(app, config)

    # Register all API blueprints (documents, auth, users, chat, suggestions, templates)
    register_blueprints(app)

    # Register error handlers for standardized error responses
    error_handler.register_error_handlers(app)

    # Initialize service dependencies (JWT, session manager, services)
    init_services(config)

    # Create health routes
    create_health_routes(app)

    # Return the configured application
    return app

def register_blueprints(app: Flask) -> None:
    """Registers all API blueprints with the Flask application"""
    # Register auth_bp for authentication endpoints
    app.register_blueprint(auth_bp)
    # Register users_bp for user management endpoints
    app.register_blueprint(users_bp)
    # Register documents_bp for document operations
    app.register_blueprint(documents_bp)
    # Register chat_bp for AI chat functionality
    app.register_blueprint(chat_bp)
    # Register suggestions_bp for AI suggestions
    app.register_blueprint(suggestions_bp)
    # Register templates_bp for AI template management
    app.register_blueprint(templates_bp)

    # Log successful blueprint registration
    logger.info("API blueprints registered successfully")

def init_middleware(app: Flask, config: dict) -> None:
    """Initializes all middleware components for the Flask application"""
    # Initialize CORS middleware for cross-origin requests
    cors_middleware = CORSMiddleware(config)
    cors_middleware.init_app(app)

    # Set up request logging for API monitoring
    setup_request_logging(app)

    # Configure authentication middleware with JWT and session support
    global _jwt_service, _anonymous_session_manager, _user_service
    setup_auth(app, _jwt_service, _anonymous_session_manager, _user_service)

    # Set up rate limiting based on configuration
    setup_rate_limiting(app)

    # Register error handlers for consistent error responses
    register_error_handlers(app)

    # Log successful middleware initialization
    logger.info("Middleware initialized successfully")

def init_services(config: dict) -> tuple:
    """Initializes service dependencies required by the API"""
    # Initialize JWTService with appropriate configuration
    jwt_secret_key = config.get("JWT_SECRET_KEY")
    jwt_algorithm = config.get("JWT_ALGORITHM")
    jwt_access_token_expires = config.get("JWT_ACCESS_TOKEN_EXPIRES")
    jwt_refresh_token_expires = config.get("JWT_REFRESH_TOKEN_EXPIRES")
    global _jwt_service
    _jwt_service = JWTService(jwt_secret_key, jwt_algorithm, jwt_access_token_expires, jwt_refresh_token_expires)

    # Initialize AnonymousSessionManager for session handling
    global _anonymous_session_manager
    _anonymous_session_manager = AnonymousSessionManager()

    # Initialize UserService for user operations
    global _user_service
    from ..data.mongodb.repositories.user_repository import UserRepository
    user_repository = UserRepository()
    from ..core.auth.password_service import PasswordService
    password_service = PasswordService(user_repository)
    _user_service = UserService(user_repository, _jwt_service, password_service, _anonymous_session_manager)

    # Log successful service initialization
    logger.info("Services initialized successfully")

    return _jwt_service, _anonymous_session_manager, _user_service

def create_health_routes(app: Flask) -> None:
    """Creates health check endpoints for monitoring and infrastructure integration"""
    @app.route("/health/liveness")
    def liveness():
        """Returns 200 OK for basic health checks"""
        return "OK", 200

    @app.route("/health/readiness")
    def readiness():
        """Returns 200 OK if dependencies are ready"""
        # Implement handlers that perform appropriate checks
        # For example, check database connection, external API availability, etc.
        # Return appropriate status codes based on health state
        return "OK", 200