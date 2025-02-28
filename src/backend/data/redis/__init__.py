"""
Redis services for the AI writing enhancement application.

This package provides Redis-based data services including connection management,
caching, rate limiting, and session management. It abstracts Redis interactions
for the application and implements key patterns like token bucket rate limiting,
document and AI response caching, and anonymous/authenticated session handling.

Services:
- Connection management: Pooled Redis connections with environment-specific configuration
- Caching: Flexible caching with TTL for documents, AI responses, and application data
- Rate limiting: Token bucket algorithm to prevent API abuse while ensuring fair usage
- Session management: Stateful sessions for both anonymous and authenticated users

Usage:
    from data.redis import CacheManager, RateLimiter, SessionStore
    
    # Use the cache
    cache = CacheManager(prefix="myapp:")
    cache.set("key", "value", ttl=300)
    
    # Configure rate limiting
    limiter = RateLimiter()
    is_limited = limiter.is_rate_limited("user:123", RATE_LIMIT_AUTHENTICATED)
    
    # Manage user sessions
    session_store = SessionStore()
    session_id = session_store.create_anonymous_session({"visits": 1})
"""

# Import from connection module
from .connection import (
    get_redis_connection,
    get_session_store_connection,
    get_cache_connection,
    get_rate_limiter_connection,
    close_connections,
    is_redis_available
)

# Import from caching_service module
from .caching_service import (
    CacheManager,
    cache_set,
    cache_get,
    cache_delete,
    cache_document,
    get_cached_document,
    cache_ai_response,
    get_cached_ai_response,
    is_cache_available,
    DEFAULT_CACHE_TTL,
    DEFAULT_AI_RESPONSE_TTL
)

# Import from rate_limiter module
from .rate_limiter import RateLimiter

# Import from session_store module  
from .session_store import SessionStore

# Define rate limit constants based on requirements in the technical specification
# These values match the configuration in config.py
RATE_LIMIT_ANONYMOUS = "10/minute"  # For anonymous users (AI suggestions)
RATE_LIMIT_AUTHENTICATED = "50/minute"  # For authenticated users (AI suggestions)
RATE_LIMIT_ADMIN = "100/minute"  # For admin operations

# Define the generate_session_id function for creating unique session IDs
import uuid

def generate_session_id():
    """
    Generate a unique session ID.
    
    Returns:
        str: A unique session ID string in UUID format
    """
    return str(uuid.uuid4())