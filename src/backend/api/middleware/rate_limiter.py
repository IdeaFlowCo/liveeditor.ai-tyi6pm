"""
Middleware implementation of rate limiting for API endpoints based on user type and endpoint category.
Uses Redis to track request counts and implements token bucket algorithm with different limits for
anonymous, authenticated, and admin users.
"""

from flask import Flask, request, jsonify, current_app
from functools import wraps
import time

from ...data.redis.rate_limiter import RateLimiter
from ...core.auth.user_service import get_current_user
from ...config import config
from ...core.utils.logger import logger

# Rate limit constants
ANONYMOUS_RATE_LIMIT = 10  # requests per minute
AUTHENTICATED_RATE_LIMIT = 50  # requests per minute
ADMIN_RATE_LIMIT = 100  # requests per minute
RATE_LIMIT_WINDOW = 60  # seconds

# Endpoint categories with rate limits
ENDPOINT_CATEGORIES = {
    'ai_suggestion': {
        'anonymous': 10,
        'authenticated': 50,
        'admin': 100
    }
}


def get_request_identifier(request):
    """
    Generates a unique identifier for rate limiting based on user ID or IP address
    
    Args:
        request: Flask request object
        
    Returns:
        str: Unique identifier string
    """
    # Get current user from request context
    user = get_current_user()
    
    # For authenticated users, use user ID
    if user and not user.get('isAnonymous', True):
        user_id = str(user.get('_id', ''))
        return f"user:{user_id}:{request.endpoint}"
    
    # For anonymous users, use IP address
    ip_address = request.remote_addr
    return f"ip:{ip_address}:{request.endpoint}"


def parse_rate_limit(limit_str):
    """
    Parse rate limit string in format "n/period" where period is one of 
    minute, hour, or day
    
    Args:
        limit_str: Rate limit string e.g. "10/minute"
        
    Returns:
        tuple: (limit, period_seconds)
    """
    parts = limit_str.split('/')
    if len(parts) != 2:
        # Invalid format, return default
        return ANONYMOUS_RATE_LIMIT, RATE_LIMIT_WINDOW
    
    try:
        limit = int(parts[0])
        period = parts[1].lower()
        
        if period == 'minute':
            period_seconds = 60
        elif period == 'hour':
            period_seconds = 3600
        elif period == 'day':
            period_seconds = 86400
        else:
            # Invalid period, return default
            return ANONYMOUS_RATE_LIMIT, RATE_LIMIT_WINDOW
        
        return limit, period_seconds
    except ValueError:
        # Invalid number format, return default
        return ANONYMOUS_RATE_LIMIT, RATE_LIMIT_WINDOW


def get_rate_limit_for_user(user, endpoint):
    """
    Determines the appropriate rate limit based on user type and endpoint category
    
    Args:
        user: User object or None for anonymous
        endpoint: API endpoint being accessed
        
    Returns:
        tuple: Rate limit count and window period
    """
    # Determine user type
    user_type = 'anonymous'
    if user:
        if user.get('isAdmin', False):
            user_type = 'admin'
        elif not user.get('isAnonymous', True):
            user_type = 'authenticated'
    
    # Try to get from configuration if available
    rate_limits = getattr(config, 'RATE_LIMITS', {})
    
    # Determine endpoint category from path
    endpoint_parts = endpoint.split('.')
    category = None
    
    # Check if endpoint matches a specific category
    for cat in ENDPOINT_CATEGORIES:
        if any(cat in part for part in endpoint_parts):
            category = cat
            break
    
    # If we found a category in our endpoint categories mapping
    if category and category in ENDPOINT_CATEGORIES:
        limit = ENDPOINT_CATEGORIES[category].get(user_type)
        if limit:
            return limit, RATE_LIMIT_WINDOW
    
    # Default limits based on user type
    if user_type == 'admin':
        return ADMIN_RATE_LIMIT, RATE_LIMIT_WINDOW
    elif user_type == 'authenticated':
        return AUTHENTICATED_RATE_LIMIT, RATE_LIMIT_WINDOW
    else:
        return ANONYMOUS_RATE_LIMIT, RATE_LIMIT_WINDOW


def is_exempt_from_rate_limiting(endpoint):
    """
    Checks if a given endpoint should be exempt from rate limiting
    
    Args:
        endpoint: The endpoint path being checked
        
    Returns:
        bool: True if exempt, False otherwise
    """
    exempt_endpoints = current_app.config.get('RATE_LIMIT_EXEMPT_ENDPOINTS', [])
    return endpoint in exempt_endpoints


def rate_limited_response(retry_after):
    """
    Generates standardized response for rate-limited requests
    
    Args:
        retry_after: Seconds until rate limit resets
        
    Returns:
        tuple: JSON response and HTTP status code
    """
    response = jsonify({
        'error': 'Too many requests',
        'message': 'Rate limit exceeded',
        'retry_after': retry_after
    })
    
    response.status_code = 429
    response.headers['Retry-After'] = str(retry_after)
    
    logger.warning(f"Rate limit exceeded. Retry after {retry_after} seconds.")
    
    return response


def rate_limit(limit_override=None):
    """
    Decorator function that applies rate limiting to Flask routes
    
    Args:
        limit_override: Optional custom rate limit for specific routes
        
    Returns:
        function: Decorated function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip if endpoint is exempt
            if is_exempt_from_rate_limiting(request.endpoint):
                return f(*args, **kwargs)
            
            # Get request identifier
            identifier = get_request_identifier(request)
            
            # Get current user
            user = get_current_user()
            
            # Determine rate limit (use override if provided)
            if limit_override:
                if isinstance(limit_override, str):
                    limit, period = parse_rate_limit(limit_override)
                else:
                    limit, period = limit_override, RATE_LIMIT_WINDOW
            else:
                limit, period = get_rate_limit_for_user(user, request.endpoint)
            
            # Create rate limiter instance
            rate_limiter = RateLimiter()
            
            # Check if rate limited
            is_limited, remaining, reset_time = rate_limiter.check_rate_limit(
                identifier, limit, period
            )
            
            if is_limited:
                return rate_limited_response(reset_time)
            
            # Update rate limit counter
            success, remaining, reset_time = rate_limiter.update_rate_limit(
                identifier, limit, period
            )
            
            # Process the request
            response = f(*args, **kwargs)
            
            # Add rate limit headers to response if it's a Response object
            if hasattr(response, 'headers'):
                response.headers.update({
                    'X-RateLimit-Limit': str(limit),
                    'X-RateLimit-Remaining': str(remaining),
                    'X-RateLimit-Reset': str(reset_time)
                })
            
            return response
        return decorated_function
    return decorator


class RateLimiterMiddleware:
    """
    Middleware class that applies rate limiting to a Flask application
    """
    
    def __init__(self, app=None):
        """
        Initialize the rate limiter middleware
        
        Args:
            app: Optional Flask application instance
        """
        self.rate_limiter = RateLimiter()
        self.endpoint_limits = {}
        self.exempt_endpoints = []
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """
        Initialize rate limiting for Flask application
        
        Args:
            app: Flask application instance
        """
        # Register the before_request handler
        app.before_request(self.before_request)
        
        # Register the after_request handler to add headers
        app.after_request(self.after_request)
        
        # Load configuration
        self.exempt_endpoints = app.config.get('RATE_LIMIT_EXEMPT_ENDPOINTS', [])
        
        # Load endpoint limits from config
        self.endpoint_limits = app.config.get('RATE_LIMITS', {})
    
    def before_request(self):
        """
        Handler called before each request to check rate limits
        
        Returns:
            Response: Rate limit response if limit exceeded, None otherwise
        """
        # Skip rate limiting for OPTIONS requests (CORS preflight)
        if request.method == 'OPTIONS':
            return None
        
        # Skip if endpoint is exempt
        if request.endpoint in self.exempt_endpoints:
            return None
        
        # Get request identifier
        user = get_current_user()
        identifier = get_request_identifier(request)
        
        # Determine appropriate rate limit
        limit, period = get_rate_limit_for_user(user, request.endpoint)
        
        # Check if rate limited
        is_limited, remaining, reset_time = self.is_rate_limited(identifier, limit, period)
        
        if is_limited:
            logger.warning(f"Rate limit exceeded for {identifier}: {limit}/{period}s")
            return rate_limited_response(reset_time)
        
        # Update rate limit counter and store info in request
        success, remaining, reset_time = self.rate_limiter.update_rate_limit(
            identifier, limit, period
        )
        
        # Store rate limit info for adding headers later
        request._rate_limit_info = {
            'limit': limit,
            'remaining': remaining,
            'reset': reset_time
        }
        
        return None
    
    def after_request(self, response):
        """
        Add rate limit headers to the response
        
        Args:
            response: Flask response object
            
        Returns:
            Response: Modified response with rate limit headers
        """
        # Skip if rate limit info is not available
        if not hasattr(request, '_rate_limit_info'):
            return response
        
        rate_info = request._rate_limit_info
        
        # Add rate limit headers
        return self.add_rate_limit_headers(
            response, 
            rate_info['limit'],
            rate_info['remaining'],
            rate_info['reset']
        )
    
    def is_rate_limited(self, identifier, limit, period):
        """
        Checks if the current request exceeds rate limits
        
        Args:
            identifier: Request identifier string
            limit: Maximum requests allowed
            period: Time window in seconds
            
        Returns:
            tuple: Boolean indicating if limited and seconds until reset
        """
        is_limited, remaining, reset_time = self.rate_limiter.check_rate_limit(
            identifier, limit, period
        )
        
        return is_limited, remaining, reset_time
    
    def add_rate_limit_headers(self, response, limit, remaining, reset):
        """
        Adds rate limit information to response headers
        
        Args:
            response: Flask response object
            limit: Maximum requests allowed
            remaining: Remaining requests in window
            reset: Seconds until window reset
            
        Returns:
            Response: Flask response with added headers
        """
        response.headers.update({
            'X-RateLimit-Limit': str(limit),
            'X-RateLimit-Remaining': str(remaining),
            'X-RateLimit-Reset': str(reset)
        })
        
        return response