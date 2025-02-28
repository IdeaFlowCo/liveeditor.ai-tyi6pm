"""
Flask middleware for robust request logging, providing detailed tracking of HTTP requests
and responses with correlation IDs, timing metrics, and contextual information.
Implements the monitoring and observability requirements for the AI writing enhancement platform.
"""

import logging  # standard library
import time  # standard library
import uuid  # standard library
from functools import wraps  # standard library
from flask import request, g, current_app  # Flask ~=2.3.0

from ..core.utils.logger import get_logger, generate_correlation_id, mask_pii

# Initialize module logger
logger = get_logger(__name__)

# Constants
REQUEST_ID_HEADER = 'X-Request-ID'
CORRELATION_ID_HEADER = 'X-Correlation-ID'
EXCLUDED_PATHS = ['/health', '/metrics', '/static']
SENSITIVE_HEADERS = ['Authorization', 'Cookie', 'X-API-Key']


def setup_request_logging(app):
    """
    Configures request logging for the Flask application by attaching the logging middleware
    and setting up request ID handling.
    
    Args:
        app: Flask application instance
    """
    # Apply the logging middleware to the Flask application
    app.wsgi_app = LoggingMiddleware(app.wsgi_app)
    
    # Setup request start time capture
    @app.before_request
    def before_request():
        g.start_time = time.time()
        g.correlation_id = get_request_correlation_id()
        
        # Skip logging for excluded paths
        if not any(request.path.startswith(path) for path in EXCLUDED_PATHS):
            # Setup request logger
            request_logger = RequestLogger()
            
            # Log request start
            request_logger.log_request_started(
                request.method,
                request.path,
                dict(request.headers),
                g.correlation_id
            )
    
    # Setup request logging after completion
    @app.after_request
    def after_request(response):
        # Skip logging for excluded paths
        if not any(request.path.startswith(path) for path in EXCLUDED_PATHS):
            # Calculate request duration
            duration = time.time() - g.start_time
            
            # Get correlation ID
            correlation_id = g.get('correlation_id', 'unknown')
            
            # Log request completion
            request_logger = RequestLogger()
            request_logger.log_request_finished(
                request.method,
                request.path,
                response.status_code,
                duration,
                correlation_id
            )
            
            # Add correlation ID to response headers
            response.headers[CORRELATION_ID_HEADER] = correlation_id
            
        return response
    
    logger.info("Request logging configured for Flask application")


def get_request_correlation_id():
    """
    Extracts or generates a correlation ID for the current request.
    
    Returns:
        str: Correlation ID to use for the current request
    """
    # Check request headers first
    correlation_id = request.headers.get(CORRELATION_ID_HEADER)
    
    # If not in headers, check if already stored in flask.g
    if not correlation_id and hasattr(g, 'correlation_id'):
        correlation_id = g.correlation_id
    
    # If still not found, generate a new one
    if not correlation_id:
        correlation_id = generate_correlation_id()
    
    return correlation_id


def mask_sensitive_data(data):
    """
    Creates a copy of request data with sensitive information masked.
    
    Args:
        data: The data to mask
        
    Returns:
        dict: Copy of data with sensitive information replaced by '[REDACTED]'
    """
    # Use the mask_pii function from the logger module
    masked_data = mask_pii(data)
    
    # Further processing for specific request data
    if isinstance(masked_data, dict):
        # Handle headers separately - they may contain auth tokens
        if 'headers' in masked_data:
            headers = masked_data['headers']
            for header in SENSITIVE_HEADERS:
                if header in headers:
                    headers[header] = '[REDACTED]'
        
        # Remove large binary content or file uploads
        if 'files' in masked_data:
            masked_data['files'] = '[FILE DATA REDACTED]'
    
    return masked_data


class LoggingMiddleware:
    """
    WSGI middleware that logs HTTP requests and responses with timing information
    and request details.
    """
    
    def __init__(self, app):
        """
        Initialize the middleware with the Flask application.
        
        Args:
            app: WSGI application
        """
        self.app = app
    
    def __call__(self, environ, start_response):
        """
        Makes the middleware callable as per WSGI specification and handles
        request/response logging.
        
        Args:
            environ: WSGI environment
            start_response: WSGI start_response function
            
        Returns:
            WSGI response from the wrapped application
        """
        # Generate a unique request ID for this request
        request_id = str(uuid.uuid4())
        
        # Extract basic request info
        method = environ.get('REQUEST_METHOD', 'UNKNOWN')
        path = environ.get('PATH_INFO', 'UNKNOWN')
        remote_addr = environ.get('REMOTE_ADDR', 'UNKNOWN')
        
        # Log the request if it's not an excluded path
        if self.should_log_path(path):
            self.log_request(environ, request_id)
        
        # Record start time
        start_time = time.time()
        
        # Create a response interceptor
        def custom_start_response(status, headers, exc_info=None):
            # Calculate request duration
            duration = time.time() - start_time
            
            # Log the response if it's not an excluded path
            if self.should_log_path(path):
                self.log_response(method, path, status, duration, headers, request_id)
            
            # Add request ID to response headers
            new_headers = list(headers)
            new_headers.append((REQUEST_ID_HEADER, request_id))
            
            # Call the original start_response
            return start_response(status, new_headers, exc_info)
        
        # Process the request and return the response
        return self.app(environ, custom_start_response)
    
    def log_request(self, environ, request_id):
        """
        Logs detailed information about an incoming HTTP request.
        
        Args:
            environ: WSGI environment
            request_id: Unique ID for the request
        """
        # Extract request details
        method = environ.get('REQUEST_METHOD', 'UNKNOWN')
        path = environ.get('PATH_INFO', 'UNKNOWN')
        remote_addr = environ.get('REMOTE_ADDR', 'UNKNOWN')
        
        # Extract and sanitize headers
        headers = {}
        for key, value in environ.items():
            if key.startswith('HTTP_'):
                header_name = key[5:].replace('_', '-').title()
                headers[header_name] = value
        
        # Skip logging for excluded paths
        if not self.should_log_path(path):
            return
        
        # Create request logger and log
        request_logger = RequestLogger()
        request_logger.log_request_started(method, path, headers, request_id)
    
    def log_response(self, method, path, status, duration, headers, request_id):
        """
        Logs information about the HTTP response and timing metrics.
        
        Args:
            method: HTTP method of the request
            path: Request path
            status: Response status string
            duration: Request duration in seconds
            headers: Response headers
            request_id: Request ID for correlation
        """
        # Extract status code
        status_code = int(status.split(' ')[0])
        
        # Skip logging for excluded paths
        if not self.should_log_path(path):
            return
        
        # Create request logger and log
        request_logger = RequestLogger()
        request_logger.log_request_finished(method, path, status_code, duration, request_id)
    
    def should_log_path(self, path):
        """
        Determines if the given path should be logged based on exclusion rules.
        
        Args:
            path: Request path
            
        Returns:
            bool: True if path should be logged, False if excluded
        """
        for excluded_path in EXCLUDED_PATHS:
            if path.startswith(excluded_path):
                return False
        return True


class RequestLogger:
    """
    Helper class that wraps the logging of request and response details.
    """
    
    def __init__(self):
        """
        Initializes the request logger.
        """
        self.logger = get_logger(__name__)
    
    def log_request_started(self, method, path, headers, request_id):
        """
        Logs the start of a request processing cycle.
        
        Args:
            method: HTTP method
            path: Request path
            headers: Request headers
            request_id: Correlation ID for the request
        """
        # Set correlation ID in the logging context
        self.logger.set_correlation_id(request_id)
        
        # Mask sensitive headers
        masked_headers = {}
        for header, value in headers.items():
            if header in SENSITIVE_HEADERS:
                masked_headers[header] = '[REDACTED]'
            else:
                masked_headers[header] = value
        
        # Log request start with context
        self.logger.info(
            f"Request started: {method} {path}",
            method=method,
            path=path,
            headers=masked_headers
        )
    
    def log_request_finished(self, method, path, status_code, duration, request_id):
        """
        Logs the completion of a request processing cycle with performance metrics.
        
        Args:
            method: HTTP method
            path: Request path
            status_code: HTTP status code
            duration: Request duration in seconds
            request_id: Correlation ID for the request
        """
        # Set correlation ID in the logging context
        self.logger.set_correlation_id(request_id)
        
        # Format duration for display
        formatted_duration = f"{duration * 1000:.3f}ms"
        
        # Log with appropriate level based on status code
        if status_code >= 400:
            self.logger.error(
                f"Request failed: {method} {path} {status_code} in {formatted_duration}",
                method=method,
                path=path,
                status_code=status_code,
                duration_ms=round(duration * 1000, 3)
            )
        else:
            self.logger.info(
                f"Request completed: {method} {path} {status_code} in {formatted_duration}",
                method=method,
                path=path,
                status_code=status_code,
                duration_ms=round(duration * 1000, 3)
            )