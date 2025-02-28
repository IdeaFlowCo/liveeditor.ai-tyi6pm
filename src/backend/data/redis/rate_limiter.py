"""
Provides Redis-backed rate limiting functionality implementing token bucket algorithm for API request throttling.
Supports different rate limits based on user types and endpoints to prevent abuse while ensuring fair resource usage.
"""

import redis
import time
from typing import Tuple, Optional

from .connection import get_rate_limiter_connection
from ...core.utils.logger import get_logger

# Configure logger
logger = get_logger(__name__)

# Default values
DEFAULT_EXPIRE_TIME = 60  # Default key expiration time in seconds
DEFAULT_WINDOW_SIZE = 60  # Default time window in seconds
DEFAULT_BUCKET_SIZE = 10  # Default number of requests allowed in window


def parse_rate_limit(rate_limit: str) -> Tuple[int, int]:
    """
    Parses rate limit string in format 'n/t' where n is max requests and t is time period in seconds
    
    Args:
        rate_limit: String representation of rate limit (e.g., "10/60")
    
    Returns:
        Tuple containing bucket size (max requests) and window size (time period in seconds)
    """
    parts = rate_limit.split('/')
    bucket_size = int(parts[0])
    window_size = int(parts[1]) if len(parts) > 1 else DEFAULT_WINDOW_SIZE
    return bucket_size, window_size


class RateLimiter:
    """
    Implements token bucket rate limiting algorithm using Redis as storage backend.
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize the rate limiter with Redis client
        
        Args:
            redis_client: Redis client instance. If None, a default connection is used.
        """
        self.redis_client = redis_client or get_rate_limiter_connection()
        logger.info("Rate limiter initialized")
    
    def check_rate_limit(self, identifier: str, bucket_size: int, window_size: int) -> Tuple[bool, int, int]:
        """
        Check if a request should be rate limited based on identifier and limit settings
        
        Args:
            identifier: Unique identifier for the rate limit (e.g., "user:123:endpoint:ai_suggestions")
            bucket_size: Maximum number of requests allowed in the window
            window_size: Time window in seconds
            
        Returns:
            Tuple of (is_limited, remaining, reset_time) where:
            - is_limited: True if rate limit exceeded, False otherwise
            - remaining: Number of requests remaining in current window
            - reset_time: Seconds until rate limit resets
        """
        redis_key = self._get_redis_key(identifier)
        current_time = self._current_time()
        
        token_data = self.redis_client.hmget(redis_key, ['tokens', 'last_update'])
        current_tokens = float(token_data[0]) if token_data[0] else bucket_size
        last_update = float(token_data[1]) if token_data[1] else current_time
        
        # Calculate tokens to add based on time elapsed (token bucket algorithm)
        time_elapsed = current_time - last_update
        tokens_to_add = time_elapsed * (bucket_size / window_size)
        
        # Update current tokens with decay factor, not exceeding bucket_size
        new_token_count = min(current_tokens + tokens_to_add, bucket_size)
        
        # Check if rate limited (less than 1 token available)
        is_rate_limited = new_token_count < 1
        
        # Calculate time until refresh
        if is_rate_limited and current_tokens < 1:
            # Time to get at least 1 token
            reset_time = int((1 - current_tokens) * (window_size / bucket_size))
        else:
            # Time to full bucket
            reset_time = int((bucket_size - new_token_count) * (window_size / bucket_size))
        
        # Round remaining tokens for user-friendly display
        remaining = max(0, int(new_token_count))
        
        logger.debug(
            f"Rate limit check: {identifier} - {remaining}/{bucket_size} remaining, "
            f"reset in {reset_time}s, limited: {is_rate_limited}"
        )
        
        return is_rate_limited, remaining, reset_time
    
    def is_rate_limited(self, identifier: str, rate_limit: str) -> bool:
        """
        Simplified interface to check if identifier exceeds rate limit
        
        Args:
            identifier: Unique identifier for the rate limit
            rate_limit: Rate limit string in format "n/t" (e.g., "10/60")
            
        Returns:
            True if rate limited, False otherwise
        """
        bucket_size, window_size = parse_rate_limit(rate_limit)
        is_limited, _, _ = self.check_rate_limit(identifier, bucket_size, window_size)
        return is_limited
    
    def update_rate_limit(self, identifier: str, bucket_size: int, window_size: int, cost: int = 1) -> Tuple[bool, int, int]:
        """
        Consume a token for the identifier, updating the rate limit counter
        
        Args:
            identifier: Unique identifier for the rate limit
            bucket_size: Maximum number of requests allowed in the window
            window_size: Time window in seconds
            cost: Number of tokens to consume (default: 1)
            
        Returns:
            Tuple of (success, remaining, reset_time) where:
            - success: True if tokens were consumed, False if rate limited
            - remaining: Number of requests remaining in current window
            - reset_time: Seconds until rate limit resets
        """
        redis_key = self._get_redis_key(identifier)
        current_time = self._current_time()
        
        # Use a pipeline to make the operations atomic
        with self.redis_client.pipeline() as pipe:
            try:
                # Get current token count and last update time from Redis
                pipe.hmget(redis_key, ['tokens', 'last_update'])
                results = pipe.execute()
                token_data = results[0]
                
                # Parse data from Redis with defaults if not found
                current_tokens = float(token_data[0]) if token_data[0] else bucket_size
                last_update = float(token_data[1]) if token_data[1] else current_time
                
                # Calculate tokens to add based on time elapsed
                time_elapsed = current_time - last_update
                tokens_to_add = time_elapsed * (bucket_size / window_size)
                
                # Update token count with decay factor, not exceeding bucket_size
                new_token_count = min(current_tokens + tokens_to_add, bucket_size)
                
                # Check if we have enough tokens
                if new_token_count < cost:
                    # Rate limited, not enough tokens
                    if current_tokens < 1:
                        # Time to get at least 1 token
                        reset_time = int((1 - current_tokens) * (window_size / bucket_size))
                    else:
                        # Time to required tokens
                        reset_time = int((cost - new_token_count) * (window_size / bucket_size))
                    
                    # Return failure with current tokens and reset time
                    remaining = max(0, int(new_token_count))
                    return False, remaining, reset_time
                
                # Consume tokens
                final_token_count = new_token_count - cost
                
                # Update Redis with new values
                pipe.hmset(redis_key, {
                    'tokens': final_token_count,
                    'last_update': current_time
                })
                
                # Set expiration to clean up keys
                expiry = max(window_size * 2, DEFAULT_EXPIRE_TIME)
                pipe.expire(redis_key, expiry)
                
                # Execute the pipeline
                pipe.execute()
                
                # Calculate time to full bucket
                reset_time = int((bucket_size - final_token_count) * (window_size / bucket_size))
                
                # Round remaining tokens for user-friendly display
                remaining = max(0, int(final_token_count))
                
                logger.debug(
                    f"Rate limit update: {identifier} consumed {cost} tokens, "
                    f"{remaining}/{bucket_size} remaining, reset in {reset_time}s"
                )
                
                return True, remaining, reset_time
                
            except redis.RedisError as e:
                # Log the error and allow the request if Redis fails
                logger.error(f"Error updating rate limit: {e}", exc_info=True)
                return True, bucket_size - cost, window_size
    
    def get_remaining_requests(self, identifier: str, rate_limit: str) -> Tuple[int, int]:
        """
        Get the number of remaining requests allowed for an identifier
        
        Args:
            identifier: Unique identifier for the rate limit
            rate_limit: Rate limit string in format "n/t" (e.g., "10/60")
            
        Returns:
            Tuple of (remaining, reset_time) where:
            - remaining: Number of requests remaining in current window
            - reset_time: Seconds until rate limit resets
        """
        bucket_size, window_size = parse_rate_limit(rate_limit)
        _, remaining, reset_time = self.check_rate_limit(identifier, bucket_size, window_size)
        return remaining, reset_time
    
    def reset_rate_limit(self, identifier: str) -> bool:
        """
        Reset rate limit for a specific identifier
        
        Args:
            identifier: Unique identifier for the rate limit
            
        Returns:
            True if successful, False otherwise
        """
        try:
            redis_key = self._get_redis_key(identifier)
            self.redis_client.delete(redis_key)
            logger.info(f"Rate limit reset for {identifier}")
            return True
        except redis.RedisError as e:
            logger.error(f"Error resetting rate limit: {e}", exc_info=True)
            return False
    
    def _get_redis_key(self, identifier: str) -> str:
        """
        Generate a Redis key for a rate limit identifier
        
        Args:
            identifier: Unique identifier for the rate limit
            
        Returns:
            Formatted Redis key
        """
        # Normalize identifier to prevent Redis key injection
        normalized_id = identifier.replace(':', '_')
        return f"rate_limit:{normalized_id}"
    
    def _current_time(self) -> int:
        """
        Get current time in seconds for rate limit calculations
        
        Returns:
            Current unix timestamp
        """
        return int(time.time())