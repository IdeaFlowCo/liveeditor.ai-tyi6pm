"""
Provides Redis-based caching functionality for the AI writing enhancement application with 
specialized methods for document, AI response, user data, and template caching. 
Implements efficient caching patterns with TTL controls and prefix-based organization.
"""

import json
import pickle
import hashlib
from typing import Any, Dict, List, Optional, Union

import redis

from .connection import get_cache_connection, is_redis_available
from ...core.utils.logger import get_logger

# Default TTL values in seconds
DEFAULT_CACHE_TTL = 300  # 5 minutes
DEFAULT_AI_RESPONSE_TTL = 1800  # 30 minutes
DEFAULT_USER_DATA_TTL = 900  # 15 minutes
DEFAULT_TEMPLATE_TTL = 3600  # 1 hour

# Cache key prefixes
DOCUMENT_CACHE_PREFIX = "doc:"
AI_RESPONSE_CACHE_PREFIX = "ai:"
USER_CACHE_PREFIX = "user:"
TEMPLATE_CACHE_PREFIX = "template:"

# Get logger
logger = get_logger(__name__)


def cache_set(key: str, value: Any, ttl: int = DEFAULT_CACHE_TTL) -> bool:
    """
    Sets a value in the cache with an optional TTL.
    
    Args:
        key: Cache key
        value: Value to cache
        ttl: Time-to-live in seconds (default: 5 minutes)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        redis_client = get_cache_connection()
        
        # Try to serialize as JSON first
        try:
            serialized_value = json.dumps(value)
            redis_client.setex(key, ttl, serialized_value)
            return True
        except (TypeError, ValueError):
            # If JSON serialization fails, use pickle
            serialized_value = pickle.dumps(value)
            redis_client.setex(key, ttl, serialized_value)
            return True
            
    except Exception as e:
        logger.error(f"Error setting cache key {key}: {str(e)}")
        return False


def cache_get(key: str) -> Optional[Any]:
    """
    Retrieves a value from the cache.
    
    Args:
        key: Cache key
        
    Returns:
        Cached value or None if not found
    """
    try:
        redis_client = get_cache_connection()
        value = redis_client.get(key)
        
        if value is None:
            return None
        
        # Try to deserialize from JSON first
        try:
            return json.loads(value)
        except (TypeError, ValueError, json.JSONDecodeError):
            # If JSON deserialization fails, try pickle
            try:
                return pickle.loads(value)
            except pickle.PickleError:
                # If both fail, return raw value
                return value
                
    except Exception as e:
        logger.error(f"Error getting cache key {key}: {str(e)}")
        return None


def cache_delete(key: str) -> bool:
    """
    Deletes a value from the cache.
    
    Args:
        key: Cache key
        
    Returns:
        True if successful, False otherwise
    """
    try:
        redis_client = get_cache_connection()
        redis_client.delete(key)
        return True
    except Exception as e:
        logger.error(f"Error deleting cache key {key}: {str(e)}")
        return False


def cache_exists(key: str) -> bool:
    """
    Checks if a key exists in the cache.
    
    Args:
        key: Cache key
        
    Returns:
        True if key exists, False otherwise
    """
    try:
        redis_client = get_cache_connection()
        return bool(redis_client.exists(key))
    except Exception as e:
        logger.error(f"Error checking existence of cache key {key}: {str(e)}")
        return False


def cache_multiple(key_values: Dict[str, Any], ttl: int = DEFAULT_CACHE_TTL) -> bool:
    """
    Sets multiple key-value pairs in the cache at once.
    
    Args:
        key_values: Dictionary mapping keys to values
        ttl: Time-to-live in seconds (default: 5 minutes)
        
    Returns:
        True if successful, False if any operation fails
    """
    try:
        redis_client = get_cache_connection()
        pipeline = redis_client.pipeline()
        
        for key, value in key_values.items():
            try:
                # Try JSON serialization first
                serialized_value = json.dumps(value)
            except (TypeError, ValueError):
                # Fall back to pickle if JSON fails
                serialized_value = pickle.dumps(value)
                
            pipeline.setex(key, ttl, serialized_value)
            
        pipeline.execute()
        return True
    except Exception as e:
        logger.error(f"Error setting multiple cache keys: {str(e)}")
        return False


def cache_clear_by_prefix(prefix: str) -> bool:
    """
    Clears all cache entries with a specific prefix.
    
    Args:
        prefix: Key prefix to match
        
    Returns:
        True if successful, False otherwise
    """
    try:
        redis_client = get_cache_connection()
        cursor = 0
        
        while True:
            cursor, keys = redis_client.scan(cursor, f"{prefix}*", 100)
            if keys:
                redis_client.delete(*keys)
                
            if cursor == 0:
                break
                
        return True
    except Exception as e:
        logger.error(f"Error clearing cache with prefix {prefix}: {str(e)}")
        return False


def cache_document(document_id: str, document_data: Dict, ttl: int = DEFAULT_CACHE_TTL) -> bool:
    """
    Caches a document with the document-specific prefix.
    
    Args:
        document_id: Unique document identifier
        document_data: Document data to cache
        ttl: Time-to-live in seconds (default: 5 minutes)
        
    Returns:
        True if successful, False otherwise
    """
    cache_key = f"{DOCUMENT_CACHE_PREFIX}{document_id}"
    return cache_set(cache_key, document_data, ttl)


def get_cached_document(document_id: str) -> Optional[Dict]:
    """
    Retrieves a cached document by ID.
    
    Args:
        document_id: Unique document identifier
        
    Returns:
        Document data or None if not found
    """
    cache_key = f"{DOCUMENT_CACHE_PREFIX}{document_id}"
    return cache_get(cache_key)


def cache_ai_response(content: str, prompt_type: str, response_data: Dict, 
                     ttl: int = DEFAULT_AI_RESPONSE_TTL) -> bool:
    """
    Caches an AI response using content hashing for efficient lookup.
    
    Args:
        content: The document content that was processed
        prompt_type: The type of prompt used (e.g., "make_shorter", "professional")
        response_data: AI response data to cache
        ttl: Time-to-live in seconds (default: 30 minutes)
        
    Returns:
        True if successful, False otherwise
    """
    # Generate a hash based on content and prompt type
    content_hash = _generate_hash(content, prompt_type)
    cache_key = f"{AI_RESPONSE_CACHE_PREFIX}{content_hash}"
    
    return cache_set(cache_key, response_data, ttl)


def get_cached_ai_response(content: str, prompt_type: str) -> Optional[Dict]:
    """
    Retrieves a cached AI response using content hashing.
    
    Args:
        content: The document content that was processed
        prompt_type: The type of prompt used
        
    Returns:
        AI response data or None if not found
    """
    content_hash = _generate_hash(content, prompt_type)
    cache_key = f"{AI_RESPONSE_CACHE_PREFIX}{content_hash}"
    
    return cache_get(cache_key)


def cache_user_data(user_id: str, user_data: Dict, ttl: int = DEFAULT_USER_DATA_TTL) -> bool:
    """
    Caches user data with the user-specific prefix.
    
    Args:
        user_id: Unique user identifier
        user_data: User data to cache
        ttl: Time-to-live in seconds (default: 15 minutes)
        
    Returns:
        True if successful, False otherwise
    """
    cache_key = f"{USER_CACHE_PREFIX}{user_id}"
    return cache_set(cache_key, user_data, ttl)


def get_cached_user_data(user_id: str) -> Optional[Dict]:
    """
    Retrieves cached user data by user ID.
    
    Args:
        user_id: Unique user identifier
        
    Returns:
        User data or None if not found
    """
    cache_key = f"{USER_CACHE_PREFIX}{user_id}"
    return cache_get(cache_key)


def cache_template(template_id: str, template_data: Dict, ttl: int = DEFAULT_TEMPLATE_TTL) -> bool:
    """
    Caches a template with the template-specific prefix.
    
    Args:
        template_id: Unique template identifier
        template_data: Template data to cache
        ttl: Time-to-live in seconds (default: 1 hour)
        
    Returns:
        True if successful, False otherwise
    """
    cache_key = f"{TEMPLATE_CACHE_PREFIX}{template_id}"
    return cache_set(cache_key, template_data, ttl)


def get_cached_template(template_id: str) -> Optional[Dict]:
    """
    Retrieves a cached template by ID.
    
    Args:
        template_id: Unique template identifier
        
    Returns:
        Template data or None if not found
    """
    cache_key = f"{TEMPLATE_CACHE_PREFIX}{template_id}"
    return cache_get(cache_key)


def is_cache_available() -> bool:
    """
    Checks if the cache service is available.
    
    Returns:
        True if cache is available, False otherwise
    """
    try:
        redis_client = get_cache_connection()
        return is_redis_available(redis_client)
    except Exception as e:
        logger.error(f"Error checking cache availability: {str(e)}")
        return False


def _generate_hash(content: str, prompt_type: str) -> str:
    """
    Helper function to generate a hash for content-based caching.
    
    Args:
        content: The document content
        prompt_type: The type of prompt used
        
    Returns:
        Hash string for the content and prompt combination
    """
    # Combine content and prompt type, then hash
    hash_input = f"{content}:{prompt_type}"
    return hashlib.sha256(hash_input.encode()).hexdigest()


class CacheManager:
    """
    Class-based interface for cache operations with specific prefix management.
    """
    
    def __init__(self, prefix: str):
        """
        Initialize the cache manager with a specific prefix.
        
        Args:
            prefix: Prefix to use for all cache keys
        """
        self.prefix = prefix
        self.logger = get_logger(__name__)
        
    def set(self, key: str, value: Any, ttl: int = DEFAULT_CACHE_TTL) -> bool:
        """
        Set a value in the cache with the manager's prefix.
        
        Args:
            key: Cache key (without prefix)
            value: Value to cache
            ttl: Time-to-live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        full_key = f"{self.prefix}{key}"
        return cache_set(full_key, value, ttl)
        
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache using the manager's prefix.
        
        Args:
            key: Cache key (without prefix)
            
        Returns:
            Cached value or None if not found
        """
        full_key = f"{self.prefix}{key}"
        return cache_get(full_key)
        
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache using the manager's prefix.
        
        Args:
            key: Cache key (without prefix)
            
        Returns:
            True if successful, False otherwise
        """
        full_key = f"{self.prefix}{key}"
        return cache_delete(full_key)
        
    def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache using the manager's prefix.
        
        Args:
            key: Cache key (without prefix)
            
        Returns:
            True if key exists, False otherwise
        """
        full_key = f"{self.prefix}{key}"
        return cache_exists(full_key)
        
    def clear_all(self) -> bool:
        """
        Clear all cache entries with the manager's prefix.
        
        Returns:
            True if successful, False otherwise
        """
        return cache_clear_by_prefix(self.prefix)
        
    def check_availability(self) -> bool:
        """
        Check if the cache is available.
        
        Returns:
            True if available, False otherwise
        """
        return is_cache_available()