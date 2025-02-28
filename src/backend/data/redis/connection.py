"""
Provides Redis connection functionality with connection pooling for the application's Redis-backed
services including caching, session management, and rate limiting.

This module handles connection management, pooling, retries, and provides specialized connections
for different use cases (session storage, caching, rate limiting) with appropriate configurations.
"""

import os
import time
import redis

from config import REDIS_CONFIG
from core.utils.logger import get_logger

# Default Redis connection parameters
DEFAULT_REDIS_HOST = 'localhost'
DEFAULT_REDIS_PORT = 6379
DEFAULT_REDIS_DB = 0
DEFAULT_REDIS_PASSWORD = None
DEFAULT_CONNECTION_TIMEOUT = 5
DEFAULT_RETRY_COUNT = 3
DEFAULT_RETRY_DELAY = 0.5

# Connection pools cache
CONNECTION_POOLS = {}

# Logger for Redis connections
logger = get_logger(__name__)

# Database numbers for different services
SESSION_DB = 0
CACHE_DB = 1
RATE_LIMIT_DB = 2


def get_redis_connection(db=DEFAULT_REDIS_DB, config_override=None):
    """
    Creates or returns an existing Redis connection from the connection pool based on the specified database.

    Args:
        db (int): Redis database number
        config_override (dict): Optional dictionary with configuration values to override

    Returns:
        redis.Redis: A Redis client instance connected to the specified database
    """
    # Get Redis configuration from config module or environment variables
    redis_config = REDIS_CONFIG.copy()

    # Override configuration with provided parameters
    if config_override:
        redis_config.update(config_override)

    # Ensure database number is set
    redis_config['db'] = db

    # Create a unique key for this connection configuration
    pool_key = f"{redis_config.get('host')}:{redis_config.get('port')}:{db}"
    
    # Check if a connection pool exists for the specified database
    if pool_key not in CONNECTION_POOLS:
        # If not, create a new connection pool with the configuration
        CONNECTION_POOLS[pool_key] = create_connection_pool(redis_config)
    
    # Get the connection pool
    pool = CONNECTION_POOLS[pool_key]
    
    # Try to establish connection with retries
    retry_count = int(redis_config.get('retry_count', DEFAULT_RETRY_COUNT))
    retry_delay = float(redis_config.get('retry_delay', DEFAULT_RETRY_DELAY))
    
    # Create Redis client using the connection pool
    for attempt in range(retry_count + 1):
        try:
            client = redis.Redis(connection_pool=pool)
            # Test connection
            client.ping()
            logger.info(f"Connected to Redis at {redis_config.get('host')}:{redis_config.get('port')} (db {db})")
            return client
        except redis.RedisError as e:
            if attempt < retry_count:
                logger.warning(f"Redis connection attempt {attempt + 1} failed: {str(e)}. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                logger.error(f"Failed to connect to Redis after {retry_count} attempts: {str(e)}")
                raise


def get_redis_url(config):
    """
    Constructs a Redis URL from configuration parameters.

    Args:
        config (dict): Redis configuration dictionary

    Returns:
        str: A Redis URL string in the format redis://[:password@]host[:port][/database]
    """
    host = config.get('host', DEFAULT_REDIS_HOST)
    port = config.get('port', DEFAULT_REDIS_PORT)
    password = config.get('password', DEFAULT_REDIS_PASSWORD)
    db = config.get('db', DEFAULT_REDIS_DB)
    
    if password:
        return f"redis://:{password}@{host}:{port}/{db}"
    else:
        return f"redis://{host}:{port}/{db}"


def create_connection_pool(config):
    """
    Creates a new Redis connection pool with the specified configuration.

    Args:
        config (dict): Redis configuration dictionary

    Returns:
        redis.ConnectionPool: A Redis connection pool instance
    """
    # Extract relevant connection parameters
    host = config.get('host', DEFAULT_REDIS_HOST)
    port = config.get('port', DEFAULT_REDIS_PORT)
    db = config.get('db', DEFAULT_REDIS_DB)
    password = config.get('password', DEFAULT_REDIS_PASSWORD)
    socket_timeout = config.get('socket_timeout', DEFAULT_CONNECTION_TIMEOUT)
    socket_connect_timeout = config.get('socket_connect_timeout', DEFAULT_CONNECTION_TIMEOUT)
    
    # Check if using Redis URL
    if 'url' in config:
        logger.info(f"Creating Redis connection pool using URL for db {db}")
        pool = redis.ConnectionPool.from_url(
            config['url'], 
            db=db,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout
        )
    else:
        # Create connection pool with explicit parameters
        logger.info(f"Creating Redis connection pool for {host}:{port} (db {db})")
        pool = redis.ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            decode_responses=config.get('decode_responses', True),
            retry_on_timeout=config.get('retry_on_timeout', True),
            max_connections=config.get('max_connections', None)
        )
    
    logger.info(f"Created Redis connection pool for {host}:{port} (db {db})")
    return pool


def close_connections():
    """
    Closes all Redis connections in all connection pools.
    
    Should be called during application shutdown to properly release resources.
    """
    global CONNECTION_POOLS
    
    if not CONNECTION_POOLS:
        logger.info("No Redis connections to close")
        return
    
    logger.info(f"Closing {len(CONNECTION_POOLS)} Redis connection pools")
    
    for key, pool in CONNECTION_POOLS.items():
        try:
            pool.disconnect()
            logger.debug(f"Disconnected Redis connection pool: {key}")
        except Exception as e:
            logger.warning(f"Error closing Redis connection pool {key}: {str(e)}")
    
    # Clear the pools dictionary
    CONNECTION_POOLS = {}
    logger.info("All Redis connections closed")


def get_session_store_connection():
    """
    Returns a Redis connection specifically configured for session storage.
    
    Returns:
        redis.Redis: A Redis client instance configured for session storage
    """
    # Session-specific configuration overrides
    config_override = {
        'decode_responses': True,  # Automatically decode response bytes to strings
    }
    
    return get_redis_connection(SESSION_DB, config_override)


def get_cache_connection():
    """
    Returns a Redis connection specifically configured for caching.
    
    Returns:
        redis.Redis: A Redis client instance configured for caching
    """
    # Cache-specific configuration overrides
    config_override = {
        'decode_responses': True
    }
    
    return get_redis_connection(CACHE_DB, config_override)


def get_rate_limiter_connection():
    """
    Returns a Redis connection specifically configured for rate limiting.
    
    Returns:
        redis.Redis: A Redis client instance configured for rate limiting
    """
    # Rate limiting specific configuration overrides
    config_override = {
        'decode_responses': True
    }
    
    return get_redis_connection(RATE_LIMIT_DB, config_override)


def is_redis_available(redis_client):
    """
    Checks if Redis server is available by attempting a ping operation.
    
    Args:
        redis_client (redis.Redis): Redis client instance to check
        
    Returns:
        bool: True if Redis is available, False otherwise
    """
    try:
        return redis_client.ping()
    except redis.RedisError as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return False