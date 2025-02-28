"""
Initializes the middleware package for the API, providing access to authentication, CORS, error handling, logging, and rate limiting middlewares.
"""

# Import middleware functions from their respective modules
from .auth_middleware import auth_required, setup_auth
from .cors_middleware import configure_cors
from .error_handler import register_error_handlers
from .logging_middleware import setup_logging
from .rate_limiter import RateLimiterMiddleware

# Define wrapper functions for consistent naming
def setup_cors(app):
    """
    Configure CORS for a Flask application.
    
    Args:
        app: Flask application object
    """
    configure_cors(app)
    return app

def setup_error_handler(app):
    """
    Configure error handling for a Flask application.
    
    Args:
        app: Flask application object
    """
    register_error_handlers(app)
    return app

def setup_rate_limiter(app):
    """
    Configure rate limiting for a Flask application.
    
    Args:
        app: Flask application object
    """
    middleware = RateLimiterMiddleware()
    middleware.init_app(app)
    return app

def setup_all_middlewares(app):
    """
    Configures all middleware components for a Flask application in the correct order.
    
    Args:
        app: The Flask app with all middlewares configured
        
    Returns:
        The Flask app with all middlewares configured
    """
    # Call setup_cors to enable cross-origin resource sharing
    setup_cors(app)
    
    # Call setup_logging to configure request logging
    setup_logging(app)
    
    # Call setup_error_handler to register error handling
    setup_error_handler(app)
    
    # Call setup_auth to configure authentication
    # setup_auth requires additional parameters and must be called separately
    
    # Call setup_rate_limiter to add rate limiting protection
    setup_rate_limiter(app)
    
    return app

# Export middleware functions for external use
__all__ = [
    'auth_required',
    'setup_auth',
    'setup_cors',
    'setup_error_handler',
    'setup_logging',
    'setup_rate_limiter',
    'setup_all_middlewares',
]