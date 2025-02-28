"""
Error handling middleware for the Flask API that provides consistent error responses,
logging, and exception handling for both HTTP and application-specific errors.
"""

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException
from marshmallow import ValidationError
import traceback

from ...core.utils.logger import setup_logger

# Initialize logger
logger = setup_logger('error_handler')

def create_error_response(message, status_code, details=None):
    """
    Creates a standardized error response structure.
    
    Args:
        message (str): Human-readable error message
        status_code (int): HTTP status code
        details (dict, optional): Additional error details
        
    Returns:
        tuple: Tuple containing JSON response dict and status code
    """
    response = {
        'error': {
            'message': message,
            'status_code': status_code
        }
    }
    
    if details:
        response['error']['details'] = details
        
    return response, status_code

def log_error(error, error_type):
    """
    Logs error details with request information.
    
    Args:
        error (Exception): The exception that occurred
        error_type (str): Type of error for categorization
    """
    # Extract request information if in request context
    request_info = {}
    try:
        if request:
            request_info = {
                'url': request.url,
                'method': request.method,
                'path': request.path,
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', 'Unknown'),
                'referrer': request.headers.get('Referer', 'Unknown'),
            }
            
            # Only include non-sensitive headers
            safe_headers = {}
            for key, value in request.headers.items():
                if key.lower() not in ['authorization', 'cookie', 'x-api-key']:
                    safe_headers[key] = value
            request_info['headers'] = safe_headers
            
            # Include query parameters if available
            if request.args:
                request_info['query_params'] = request.args.to_dict()
    except Exception:
        # In case we're outside of request context
        pass
    
    # Format error message
    error_message = f"{error_type} Error: {str(error)}"
    
    # Log with appropriate level based on error type
    if error_type in ['Server', 'Unhandled', 'AIService']:
        logger.error(error_message, exc_info=True, request_info=request_info)
    else:
        logger.warning(error_message, request_info=request_info)

def handle_http_exception(error):
    """
    Handler for HTTP exceptions from Flask/Werkzeug.
    
    Args:
        error (HTTPException): The HTTP exception
        
    Returns:
        tuple: Tuple containing JSON response dict and status code
    """
    log_error(error, 'HTTP')
    
    response_dict, status_code = create_error_response(
        message=error.description,
        status_code=error.code
    )
    return jsonify(response_dict), status_code

def handle_validation_error(error):
    """
    Handler for validation errors from request data.
    
    Args:
        error (ValidationError): The validation error
        
    Returns:
        tuple: Tuple containing JSON response dict and 400 status code
    """
    log_error(error, 'Validation')
    
    # Extract validation error details
    details = error.messages if hasattr(error, 'messages') else {'error': str(error)}
    
    response_dict, status_code = create_error_response(
        message="Invalid request data",
        status_code=400,
        details=details
    )
    return jsonify(response_dict), status_code

def handle_auth_error(error):
    """
    Handler for authentication and authorization errors.
    
    Args:
        error (Exception): The authentication/authorization error
        
    Returns:
        tuple: Tuple containing JSON response dict and 401/403 status code
    """
    log_error(error, 'Authentication')
    
    # Determine if this is an authentication error (401) or authorization error (403)
    status_code = 401 if 'authentication' in str(error).lower() else 403
    
    message = "Authentication required" if status_code == 401 else "Insufficient permissions"
    
    response_dict, status_code = create_error_response(
        message=message,
        status_code=status_code
    )
    return jsonify(response_dict), status_code

def handle_not_found_error(error):
    """
    Handler for resource not found errors.
    
    Args:
        error (Exception): The not found error
        
    Returns:
        tuple: Tuple containing JSON response dict and 404 status code
    """
    log_error(error, 'NotFound')
    
    response_dict, status_code = create_error_response(
        message="Requested resource not found",
        status_code=404
    )
    return jsonify(response_dict), status_code

def handle_ai_service_error(error):
    """
    Handler for AI service integration errors.
    
    Args:
        error (Exception): The AI service error
        
    Returns:
        tuple: Tuple containing JSON response dict and 503 status code
    """
    log_error(error, 'AIService')
    
    response_dict, status_code = create_error_response(
        message="Unable to process document with AI service at this time",
        status_code=503,
        details={
            "suggestion": "Please try again later. Our AI service is experiencing high demand."
        }
    )
    return jsonify(response_dict), status_code

def handle_generic_error(error):
    """
    Fallback handler for all unhandled exceptions.
    
    Args:
        error (Exception): The unhandled exception
        
    Returns:
        tuple: Tuple containing JSON response dict and 500 status code
    """
    log_error(error, 'Unhandled')
    
    response_dict, status_code = create_error_response(
        message="An unexpected error occurred",
        status_code=500
    )
    return jsonify(response_dict), status_code

def register_error_handlers(app):
    """
    Registers all error handlers with the Flask application.
    
    Args:
        app (Flask): The Flask application
    """
    # Register HTTP exception handler
    app.register_error_handler(HTTPException, handle_http_exception)
    
    # Register validation error handler
    app.register_error_handler(ValidationError, handle_validation_error)
    
    # Try to register handlers for custom exceptions, if they exist
    # These would typically be defined in the core.exceptions module
    try:
        from ...core.exceptions import AuthenticationError
        app.register_error_handler(AuthenticationError, handle_auth_error)
    except ImportError:
        logger.info("AuthenticationError class not found, skipping handler registration")
    
    try:
        from ...core.exceptions import ResourceNotFoundError
        app.register_error_handler(ResourceNotFoundError, handle_not_found_error)
    except ImportError:
        logger.info("ResourceNotFoundError class not found, skipping handler registration")
    
    try:
        from ...core.exceptions import AIServiceError
        app.register_error_handler(AIServiceError, handle_ai_service_error)
    except ImportError:
        logger.info("AIServiceError class not found, skipping handler registration")
    
    # Register fallback handler for all other exceptions
    app.register_error_handler(Exception, handle_generic_error)