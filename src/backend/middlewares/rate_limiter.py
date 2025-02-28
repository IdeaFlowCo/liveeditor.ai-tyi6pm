"""
Core middleware component for implementing rate limiting on Flask endpoints,
providing a decorator-based approach for limiting API request rates based on user type.
"""

from flask import Flask, request, current_app, g, make_response, jsonify
from functools import wraps
import time
from redis import Redis

from ..data.redis.connection import get_redis_connection
from ..core.utils.logger import logger

# Rate limits per minute for different user types
ANONYMOUS_RATE_LIMIT = 10  # requests per minute for anonymous users
AUTHENTICATED_RATE_LIMIT = 50  # requests per minute for authenticated users
ADMIN_RATE_LIMIT = 100  # requests per minute for admin operations

# Rate limit window size in seconds
RATE_LIMIT_WINDOW = 60  # window size in seconds (1 minute)

# Global Redis client
_redis_client = None


def init_rate_limiter(app):
    """
    Initializes the rate limiter middleware with Redis connection.
    
    Args:
        app: Flask application instance
    
    Returns:
        None
    """
    global _redis_client
    try:
        _redis_client = get_redis_connection(db=2)  # Use the rate limiter DB (2)
        logger.info("Rate limiter initialized with Redis connection")
    except Exception as e:
        logger.error(f"Failed to initialize rate limiter: {str(e)}")
        _redis_client = None


def limiter(limit_type='default'):
    """
    Decorator function that applies rate limiting to a Flask route.
    
    Args:
        limit_type: String indicating the type of limit to apply (default: 'default')
    
    Returns:
        function: Decorated route function
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Skip rate limiting if not enabled
            if not _redis_client:
                logger.info("Rate limiting disabled or not initialized")
                return f(*args, **kwargs)
            
            try:
                # Determine the rate limit for this request
                rate_limit = get_rate_limit(limit_type)
                
                # Get client identifier
                client_id = get_client_identifier()
                
                # Check rate limit
                is_limited, remaining, reset = check_rate_limit(client_id, limit_type, rate_limit)
                
                # If rate limited, return error response
                if is_limited:
                    logger.warning(f"Rate limit exceeded for {client_id} ({limit_type})")
                    return rate_limit_exceeded_response(rate_limit, remaining, reset)
                
                # Execute the route function
                response = f(*args, **kwargs)
                
                # Add rate limit headers to the response
                try:
                    # Handle different response types
                    if isinstance(response, tuple) and len(response) >= 1:
                        # For tuple responses (data, status_code, headers)
                        data = response[0]
                        if hasattr(data, 'headers'):
                            data.headers['X-RateLimit-Limit'] = str(rate_limit)
                            data.headers['X-RateLimit-Remaining'] = str(remaining)
                            data.headers['X-RateLimit-Reset'] = str(reset)
                    elif hasattr(response, 'headers'):
                        # For regular response objects
                        response.headers['X-RateLimit-Limit'] = str(rate_limit)
                        response.headers['X-RateLimit-Remaining'] = str(remaining)
                        response.headers['X-RateLimit-Reset'] = str(reset)
                except Exception as e:
                    logger.error(f"Error adding rate limit headers: {str(e)}")
                
                return response
            except Exception as e:
                logger.error(f"Error in rate limiter: {str(e)}")
                # Fail open - allow the request if rate limiting fails
                return f(*args, **kwargs)
        return wrapper
    return decorator


def get_client_identifier():
    """
    Extracts a unique identifier for the client from the request.
    
    Returns:
        str: A unique identifier for rate limiting
    """
    # Try to get user_id if user is authenticated
    if hasattr(g, 'user_id'):
        return f"user:{g.user_id}"
    
    # Otherwise use IP address
    ip = request.remote_addr
    
    # Check for X-Forwarded-For header if behind proxy
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    
    return f"ip:{ip}"


def get_rate_limit(limit_type):
    """
    Determines the appropriate rate limit based on the limit type and user status.
    
    Args:
        limit_type: String indicating the type of limit to apply
    
    Returns:
        int: Number of allowed requests per time window
    """
    # Check if user is authenticated
    is_authenticated = hasattr(g, 'user_id')
    
    # AI suggestion rate limits
    if limit_type == 'ai':
        if not is_authenticated:
            return ANONYMOUS_RATE_LIMIT
        else:
            return AUTHENTICATED_RATE_LIMIT
    
    # Admin operations rate limit
    elif limit_type == 'admin':
        return ADMIN_RATE_LIMIT
    
    # Default to a conservative limit
    return min(ANONYMOUS_RATE_LIMIT, 10)


def check_rate_limit(client_id, limit_type, limit):
    """
    Checks if a client has exceeded their rate limit and updates the counter.
    
    Args:
        client_id: Unique identifier for the client
        limit_type: Type of limit being applied
        limit: Maximum number of requests allowed per window
    
    Returns:
        tuple: (is_limited, remaining, reset_time) - whether limit is exceeded, 
               remaining requests, and seconds until reset
    """
    if not _redis_client:
        logger.warning("Rate limiter not initialized, skipping rate limit check")
        return False, limit, 0
    
    try:
        current_time = int(time.time())
        window_key = f"ratelimit:{limit_type}:{client_id}:{current_time // RATE_LIMIT_WINDOW}"
        
        # Increment the counter for this window
        count = _redis_client.incr(window_key)
        
        # If this is the first request in this window, set expiry
        if count == 1:
            _redis_client.expire(window_key, RATE_LIMIT_WINDOW * 2)  # 2x window for safety
        
        # Calculate remaining requests and reset time
        remaining = max(0, limit - count)
        reset_time = RATE_LIMIT_WINDOW - (current_time % RATE_LIMIT_WINDOW)
        
        # Return whether limit is exceeded, remaining requests, and reset time
        return count > limit, remaining, reset_time
    except Exception as e:
        logger.error(f"Error checking rate limit: {str(e)}")
        # In case of errors, fail open (don't rate limit)
        return False, limit, 0


def rate_limit_exceeded_response(limit, remaining, reset):
    """
    Creates a standardized response for when rate limits are exceeded.
    
    Args:
        limit: The rate limit that was exceeded
        remaining: Remaining requests in the current window
        reset: Seconds until the rate limit resets
    
    Returns:
        Response: Flask response object with appropriate headers and status code
    """
    response = make_response(jsonify({
        'error': 'Rate limit exceeded',
        'message': f'Too many requests. Try again in {reset} seconds.',
    }), 429)  # 429 Too Many Requests
    
    # Add rate limit headers
    response.headers['X-RateLimit-Limit'] = str(limit)
    response.headers['X-RateLimit-Remaining'] = str(remaining)
    response.headers['X-RateLimit-Reset'] = str(reset)
    response.headers['Retry-After'] = str(reset)
    
    return response