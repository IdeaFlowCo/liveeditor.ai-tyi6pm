# standard library
import os
import sys
import traceback
import atexit

# Flask 2.3.0 - Core web framework for the API
# dict - Used to specify configuration settings
from flask import Flask

# Internal imports
# Factory function to create and configure the Flask application
from api import create_app
# Configuration classes for different environments
from config import DevelopmentConfig, TestingConfig, ProductionConfig
# Initialize MongoDB database connection
from data.mongodb.connection import get_mongodb_client, is_mongodb_available, create_indexes
# Initialize Redis connection for caching and sessions
from data.redis.connection import get_redis_connection, is_redis_available
# Configure application logging
from core.utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)


def create_application(env_name: str) -> Flask:
    """Creates and configures the Flask application with appropriate environment settings

    Args:
        env_name (str): The environment name (development, testing, production)

    Returns:
        Flask: Configured Flask application instance
    """
    # Determine environment from parameter or FLASK_ENV environment variable
    env = env_name or os.environ.get('FLASK_ENV', 'development')
    logger.info(f"Initializing application in {env} environment")

    # Select appropriate configuration class based on environment
    config = get_config_by_environment(env)

    # Initialize database connections (MongoDB, Redis)
    try:
        mongodb_client, redis_client = initialize_databases(config)
    except Exception as db_init_error:
        logger.error(f"Database initialization failed: {str(db_init_error)}")
        # Consider a more graceful exit or fallback mechanism here
        raise

    # Create the Flask application using the create_app factory
    try:
        app = create_app(config)
    except Exception as app_creation_error:
        logger.error(f"Application creation failed: {str(app_creation_error)}")
        # Consider a more graceful exit or fallback mechanism here
        raise

    # Register cleanup functions with atexit for proper resource release
    atexit.register(cleanup_resources)

    # Handle any initialization errors with appropriate logging
    @app.errorhandler(500)
    def handle_internal_server_error(e):
        original = getattr(e, "original_exception", None)
        if original is None:
            logger.error(f"Internal server error: {str(e)}")
        else:
            logger.error(f"Internal server error: {str(original)}", exc_info=True)
        return "Internal Server Error", 500

    # Return the configured Flask application
    return app


def get_config_by_environment(env_name: str) -> object:
    """Determines the appropriate configuration class based on the environment name

    Args:
        env_name (str): The environment name (development, testing, production)

    Returns:
        object: Configuration class instance for the specified environment
    """
    # Default to 'development' if no environment specified
    if not env_name:
        env_name = 'development'

    # Log the environment being used
    logger.info(f"Using {env_name} configuration")

    # Select and return appropriate configuration class instance
    if env_name == 'development':
        return DevelopmentConfig()
    elif env_name == 'testing':
        return TestingConfig()
    elif env_name == 'production':
        return ProductionConfig()
    else:
        # For unknown environments, default to DevelopmentConfig with warning
        logger.warning(f"Unknown environment: {env_name}, defaulting to DevelopmentConfig")
        return DevelopmentConfig()


def initialize_databases(config: dict) -> tuple:
    """Initializes database connections and creates necessary indexes

    Args:
        config (dict): Application configuration

    Returns:
        tuple: (mongodb_client, redis_client)
    """
    # Initialize MongoDB connection using configuration
    try:
        mongodb_client = get_mongodb_client()
        logger.info("MongoDB client initialized successfully")
    except Exception as mongo_error:
        logger.error(f"MongoDB initialization failed: {str(mongo_error)}")
        raise

    # Create MongoDB indexes for optimized queries
    try:
        create_indexes()
        logger.info("MongoDB indexes created successfully")
    except Exception as index_error:
        logger.error(f"MongoDB index creation failed: {str(index_error)}")
        raise

    # Initialize Redis connection using configuration
    try:
        redis_client = get_redis_connection()
        logger.info("Redis client initialized successfully")
    except Exception as redis_error:
        logger.error(f"Redis initialization failed: {str(redis_error)}")
        raise

    # Log successful database initialization
    logger.info("Database initialization completed successfully")

    # Return database client instances for use in the application
    return mongodb_client, redis_client


def cleanup_resources() -> None:
    """Performs cleanup operations when application exits"""
    # Close MongoDB connections
    try:
        from data.mongodb.connection import close_connections as close_mongodb_connections
        close_mongodb_connections()
        logger.info("MongoDB connections closed successfully")
    except Exception as mongo_cleanup_error:
        logger.error(f"MongoDB cleanup failed: {str(mongo_cleanup_error)}")

    # Close Redis connections
    try:
        from data.redis.connection import close_connections as close_redis_connections
        close_redis_connections()
        logger.info("Redis connections closed successfully")
    except Exception as redis_cleanup_error:
        logger.error(f"Redis cleanup failed: {str(redis_cleanup_error)}")

    # Log successful cleanup operation
    logger.info("Resource cleanup completed")


# Export the create_application function for WSGI
if __name__ == "__main__":
    app = create_application('development')
    app.run(debug=True)