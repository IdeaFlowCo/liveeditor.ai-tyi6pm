"""
Flask middleware package that centralizes imports and exports for authentication, 
error handling, logging, and rate limiting middleware components. 
Provides a single entry point for middleware registration with Flask applications.
"""

from flask import Flask  # Flask ~=2.3.0

from .auth import authenticate, login_required, optional_auth, admin_required, set_auth_cookies, set_anonymous_session_cookie, clear_auth_cookies, handle_auth_error  # Internal import
from .error_handler import error_handler, setup_error_handlers, ErrorResponse, CircuitBreaker, handle_error  # Internal import
from .logging import logging_middleware, LoggingMiddleware, log_with_correlation, get_correlation_id  # Internal import
from .rate_limiter import rate_limit, setup_rate_limiting, auth_rate_limiter, RateLimitExceeded  # Internal import


def setup_middlewares(app: Flask) -> Flask:
    """
    Register all middleware components with a Flask application

    Args:
        app: Flask application

    Returns:
        The modified Flask application with registered middlewares
    """
    # Apply authentication middleware
    app.before_request(authenticate)

    # Set up error handlers
    setup_error_handlers(app)

    # Configure logging middleware
    logging_middleware(app)

    # Set up rate limiting
    setup_rate_limiting(app)

    # Return the modified app instance
    return app


__all__ = [
    'authenticate',
    'login_required',
    'optional_auth',
    'admin_required',
    'set_auth_cookies',
    'set_anonymous_session_cookie',
    'clear_auth_cookies',
    'error_handler',
    'ErrorResponse',
    'CircuitBreaker',
    'logging_middleware',
    'LoggingMiddleware',
    'log_with_correlation',
    'rate_limit',
    'setup_rate_limiting',
    'auth_rate_limiter',
    'setup_middlewares',
    'handle_error',
    'handle_auth_error',
    'RateLimitExceeded'
]