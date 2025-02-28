"""
Middleware that provides structured request/response logging for the AI writing enhancement platform.
Includes support for correlation IDs, performance metrics, and PII masking to enable
comprehensive monitoring of API traffic while ensuring data privacy.
"""

import flask
from flask import request, g
import time
import uuid

from ...core.utils.logger import get_logger
from ...core.utils.logger import RequestLogger
from ...core.utils.logger import generate_correlation_id
from ...core.utils.logger import mask_pii

# Initialize loggers
logger = get_logger(__name__)
request_logger = RequestLogger(logger)

def setup_logging(app):
    """
    Configures the Flask application with request/response logging middleware.
    
    Args:
        app: Flask application object
        
    Returns:
        None
    """
    # Register before and after request handlers
    app.before_request(log_request)
    app.after_request(log_response)
    
    logger.info("Request/response logging middleware configured")
    return None

def log_request():
    """
    Handles logging of incoming HTTP requests with PII protection.
    
    Called before each request is processed.
    
    Returns:
        None
    """
    # Get or generate correlation ID
    correlation_id = get_correlation_id()
    
    # Store correlation ID and start time in flask.g for later use
    g.correlation_id = correlation_id
    g.start_time = time.time()
    
    # Add correlation ID to request headers for propagation to downstream services
    if not request.headers.get('X-Correlation-ID'):
        # In a real middleware we can't modify the incoming request, but we want
        # to ensure it's available in the headers for downstream processing
        # This is for documentation purposes; in actuality we'd use g
        pass
    
    # Extract and log request data
    request_data = extract_loggable_request_data()
    
    # Log the request
    request_logger.log_request(
        request_data['method'],
        request_data['path'],
        request_data['headers'],
        request_data['query_params'],
        request_data['body'],
        correlation_id
    )
    
    return None

def log_response(response):
    """
    Handles logging of outgoing HTTP responses with performance metrics.
    
    Called after each request is processed but before the response is sent.
    
    Args:
        response: Flask response object
        
    Returns:
        The original response object, unmodified
    """
    # Calculate request duration
    duration = time.time() - getattr(g, 'start_time', time.time())
    
    # Get correlation ID
    correlation_id = getattr(g, 'correlation_id', None)
    
    # Extract and log response data
    response_data = extract_loggable_response_data(response)
    
    # Log the response
    request_logger.log_response(
        response_data['status_code'],
        response_data['headers'],
        response_data['body'],
        duration,
        correlation_id
    )
    
    # Add correlation ID to response headers for client-side tracing
    if correlation_id:
        response.headers['X-Correlation-ID'] = correlation_id
    
    return response

def get_correlation_id():
    """
    Extracts correlation ID from request headers or generates a new one.
    
    Returns:
        str: Correlation ID for the current request
    """
    correlation_id = request.headers.get('X-Correlation-ID')
    
    # Validate the correlation ID format if present
    if correlation_id:
        try:
            # Attempt to parse as UUID to validate format
            uuid.UUID(correlation_id)
            return correlation_id
        except (ValueError, AttributeError):
            # If invalid format, log and generate a new one
            logger.warning(f"Invalid correlation ID format: {correlation_id}, generating new ID")
            correlation_id = None
    
    # Generate a new correlation ID if not present or invalid
    if not correlation_id:
        correlation_id = generate_correlation_id()
    
    return correlation_id

def extract_loggable_request_data():
    """
    Extracts and masks sensitive data from the request for logging.
    
    Returns:
        dict: Sanitized request data safe for logging
    """
    # Extract basic request information
    req_data = {
        'method': request.method,
        'path': request.path,
        'headers': dict(request.headers),
        'query_params': dict(request.args),
        'body': None
    }
    
    # Extract request body if it exists and is appropriate
    if request.is_json:
        req_data['body'] = request.get_json(silent=True)
    elif request.form:
        req_data['body'] = dict(request.form)
    elif request.data and len(request.data) > 0:
        try:
            req_data['body'] = request.data.decode('utf-8')
        except UnicodeDecodeError:
            req_data['body'] = "[Binary data]"
    
    # Apply PII masking to sensitive fields
    # Note: Not masking headers here as RequestLogger.log_request handles that
    if req_data['body']:
        req_data['body'] = mask_pii(req_data['body'])
    
    if req_data['query_params']:
        req_data['query_params'] = mask_pii(req_data['query_params'])
    
    return req_data

def extract_loggable_response_data(response):
    """
    Extracts and masks sensitive data from the response for logging.
    
    Args:
        response: Flask response object
        
    Returns:
        dict: Sanitized response data safe for logging
    """
    # Extract basic response information
    resp_data = {
        'status_code': response.status_code,
        'headers': dict(response.headers),
        'body': None
    }
    
    # Extract response body if possible
    content_type = response.headers.get('Content-Type', '')
    
    if 'application/json' in content_type:
        # For JSON responses, try to parse the data
        try:
            if hasattr(response, 'get_json'):
                resp_data['body'] = response.get_json(silent=True)
            elif hasattr(response, 'get_data'):
                data = response.get_data(as_text=True)
                if data:
                    import json
                    resp_data['body'] = json.loads(data)
        except (ValueError, AttributeError):
            # If can't parse as JSON, use raw data
            if hasattr(response, 'get_data'):
                resp_data['body'] = response.get_data(as_text=True)
    elif 'text/' in content_type and hasattr(response, 'get_data'):
        # For text responses, get as text
        resp_data['body'] = response.get_data(as_text=True)
    elif hasattr(response, 'get_data'):
        # For other types, try to get data but don't decode
        try:
            data = response.get_data(as_text=True)
            if len(data) > 1000:
                resp_data['body'] = f"[Large response: {len(data)} bytes]"
            else:
                resp_data['body'] = data
        except (UnicodeDecodeError, AttributeError):
            resp_data['body'] = f"[Binary data: {response.headers.get('Content-Length', 'unknown')} bytes]"
    
    # Apply PII masking to response body
    if resp_data['body']:
        resp_data['body'] = mask_pii(resp_data['body'])
    
    return resp_data