"""
Centralized configuration module for the AI writing enhancement platform backend.

This module provides environment-specific settings for services including database
connections, authentication, external APIs, application behavior, and security parameters.
It loads configuration from environment variables with sensible defaults and supports
different environments (development, testing, staging, production).

Usage:
    from config import current_config
    app.config.from_object(current_config)
    
    # Or to use a specific configuration
    from config import get_config
    config = get_config('production')
    app.config.from_object(config)
"""

import os
from datetime import datetime, timedelta

# Environment variables
ENV = os.environ.get('FLASK_ENV', 'development')
DEBUG = os.environ.get('FLASK_DEBUG', '0') == '1'
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', None)


class Config:
    """Base configuration class with common settings for all environments."""
    
    def __init__(self):
        # Environment-related configurations
        self.ENV = ENV
        self.DEBUG = DEBUG
        self.SECRET_KEY = SECRET_KEY
        
        # Security-related configurations
        self.JWT_SECRET_KEY = JWT_SECRET_KEY
        self.JWT_ALGORITHM = 'HS256'
        self.JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1).total_seconds()
        self.JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7).total_seconds()
        
        # OpenAI API configurations
        self.OPENAI_API_KEY = OPENAI_API_KEY
        self.OPENAI_DEFAULT_MODEL = 'gpt-4'
        self.OPENAI_FALLBACK_MODEL = 'gpt-3.5-turbo'
        self.OPENAI_MAX_TOKENS = 8192
        self.OPENAI_TEMPERATURE = 0.7
        self.OPENAI_REQUEST_TIMEOUT = 30  # seconds
        self.OPENAI_USE_CACHE = True
        
        # MongoDB configurations
        self.MONGODB_CONFIG = {
            'host': os.environ.get('MONGODB_HOST', 'localhost'),
            'port': int(os.environ.get('MONGODB_PORT', 27017)),
            'db_name': os.environ.get('MONGODB_DB', 'ai_writing_enhancement'),
            'username': os.environ.get('MONGODB_USERNAME', ''),
            'password': os.environ.get('MONGODB_PASSWORD', ''),
            'auth_source': os.environ.get('MONGODB_AUTH_SOURCE', 'admin'),
            'replica_set': os.environ.get('MONGODB_REPLICA_SET', None),
            'read_preference': os.environ.get('MONGODB_READ_PREFERENCE', 'primaryPreferred'),
            'connect_timeout_ms': 5000,
            'server_selection_timeout_ms': 30000,
        }
        
        # Redis configurations
        self.REDIS_CONFIG = {
            'host': os.environ.get('REDIS_HOST', 'localhost'),
            'port': int(os.environ.get('REDIS_PORT', 6379)),
            'db': int(os.environ.get('REDIS_DB', 0)),
            'password': os.environ.get('REDIS_PASSWORD', None),
            'socket_timeout': 5,
            'socket_connect_timeout': 5,
            'socket_keepalive': True,
            'retry_on_timeout': True,
            'decode_responses': True,
        }
        
        # S3 configurations
        self.S3_CONFIG = {
            'bucket_name': os.environ.get('S3_BUCKET_NAME', 'ai-writing-enhancement'),
            'region_name': os.environ.get('S3_REGION_NAME', 'us-east-1'),
            'access_key_id': os.environ.get('AWS_ACCESS_KEY_ID', None),
            'secret_access_key': os.environ.get('AWS_SECRET_ACCESS_KEY', None),
            'endpoint_url': os.environ.get('S3_ENDPOINT_URL', None),  # For local development with minio
            'use_ssl': os.environ.get('S3_USE_SSL', '1') == '1',
            'verify': os.environ.get('S3_VERIFY', '1') == '1',
        }
        
        # Application behavior configurations
        self.CORS_ORIGINS = ['http://localhost:3000']
        self.MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25MB max upload size
        self.RATE_LIMITING = {
            'default': '100/hour',
            'anonymous': {
                'ai_suggestions': '10/minute',
                'document_save': '5/hour',
            },
            'authenticated': {
                'ai_suggestions': '50/minute',
                'document_save': '100/day',
            }
        }


class DevelopmentConfig(Config):
    """Configuration for the development environment with debugging enabled."""
    
    def __init__(self):
        super().__init__()
        # Enable debugging
        self.DEBUG = True
        
        # Set MongoDB to use local development instance
        self.MONGODB_CONFIG = {
            **self.MONGODB_CONFIG,
            'host': 'localhost',
            'port': 27017,
            'db_name': 'ai_writing_enhancement_dev',
        }
        
        # Set Redis to use local development instance
        self.REDIS_CONFIG = {
            **self.REDIS_CONFIG,
            'host': 'localhost',
            'port': 6379,
            'db': 0,
        }
        
        # Set S3 to use local minio or AWS development bucket
        self.S3_CONFIG = {
            **self.S3_CONFIG,
            'bucket_name': 'ai-writing-enhancement-dev',
            'endpoint_url': 'http://localhost:9000',  # For local minio
        }
        
        # Allow CORS from local frontend development server
        self.CORS_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000']


class TestingConfig(Config):
    """Configuration for testing environment with test databases and mock services."""
    
    def __init__(self):
        super().__init__()
        # Enable testing mode
        self.TESTING = True
        
        # Set MongoDB to use test database
        self.MONGODB_CONFIG = {
            **self.MONGODB_CONFIG,
            'db_name': 'ai_writing_enhancement_test',
        }
        
        # Set Redis to use test database
        self.REDIS_CONFIG = {
            **self.REDIS_CONFIG,
            'db': 1,
        }
        
        # Set S3 to use test bucket or mock
        self.S3_CONFIG = {
            **self.S3_CONFIG,
            'bucket_name': 'ai-writing-enhancement-test',
        }
        
        # Disable context preservation for better error reporting
        self.PRESERVE_CONTEXT_ON_EXCEPTION = False


class StagingConfig(Config):
    """Configuration for staging environment with production-like settings."""
    
    def __init__(self):
        super().__init__()
        # Disable debugging
        self.DEBUG = False
        
        # Set MongoDB to use staging cluster
        self.MONGODB_CONFIG = {
            **self.MONGODB_CONFIG,
            'host': os.environ.get('MONGODB_HOST', 'mongodb.staging.example.com'),
            'port': int(os.environ.get('MONGODB_PORT', 27017)),
            'db_name': os.environ.get('MONGODB_DB', 'ai_writing_enhancement_staging'),
            'replica_set': 'rs0',
        }
        
        # Set Redis to use staging instance
        self.REDIS_CONFIG = {
            **self.REDIS_CONFIG,
            'host': os.environ.get('REDIS_HOST', 'redis.staging.example.com'),
            'port': int(os.environ.get('REDIS_PORT', 6379)),
        }
        
        # Set S3 to use staging bucket
        self.S3_CONFIG = {
            **self.S3_CONFIG,
            'bucket_name': 'ai-writing-enhancement-staging',
            'endpoint_url': None,  # Use AWS S3 directly
        }
        
        # Set CORS for staging frontend domain
        self.CORS_ORIGINS = ['https://staging.example.com']


class ProductionConfig(Config):
    """Configuration for production environment with secure and optimized settings."""
    
    def __init__(self):
        super().__init__()
        # Disable debugging and testing
        self.DEBUG = False
        self.TESTING = False
        
        # Enable rate limiting
        self.USE_RATE_LIMITING = True
        
        # Set MongoDB to use production cluster with replica set
        self.MONGODB_CONFIG = {
            **self.MONGODB_CONFIG,
            'host': os.environ.get('MONGODB_HOST', 'mongodb.production.example.com'),
            'port': int(os.environ.get('MONGODB_PORT', 27017)),
            'db_name': os.environ.get('MONGODB_DB', 'ai_writing_enhancement'),
            'replica_set': os.environ.get('MONGODB_REPLICA_SET', 'rs0'),
            'read_preference': 'secondaryPreferred',
            'w': 'majority',
            'j': True,
        }
        
        # Set Redis to use production instance with cluster mode
        self.REDIS_CONFIG = {
            **self.REDIS_CONFIG,
            'host': os.environ.get('REDIS_HOST', 'redis.production.example.com'),
            'port': int(os.environ.get('REDIS_PORT', 6379)),
            'socket_timeout': 10,
            'socket_connect_timeout': 10,
            'cluster': True,
        }
        
        # Set S3 to use production bucket with encryption
        self.S3_CONFIG = {
            **self.S3_CONFIG,
            'bucket_name': 'ai-writing-enhancement-prod',
            'endpoint_url': None,  # Use AWS S3 directly
            'use_ssl': True,
            'verify': True,
            'server_side_encryption': 'AES256',
        }
        
        # Set CORS for production domains only
        self.CORS_ORIGINS = [
            'https://example.com',
            'https://www.example.com',
        ]
        
        # Configure secure cookie options
        self.SESSION_COOKIE_OPTIONS = {
            'httponly': True,
            'secure': True,
            'samesite': 'Lax',
            'domain': '.example.com',
            'expires': timedelta(days=1).total_seconds(),
        }


# Dictionary mapping environment names to configuration classes
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """
    Get the configuration object for the specified or current environment.
    
    Args:
        config_name (str, optional): The name of the configuration to load.
                                     If None, uses the current environment.
    
    Returns:
        An instance of the appropriate configuration class.
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    if config_name not in config:
        config_name = 'default'
    
    return config[config_name]()


# Get the current configuration based on the environment
current_config = get_config()


# Check for insecure configuration in production
if ENV == 'production':
    if SECRET_KEY == 'dev-secret-key-change-in-production':
        import warnings
        warnings.warn(
            "WARNING: Using default SECRET_KEY in production environment. "
            "This is insecure. Please set the SECRET_KEY environment variable.",
            RuntimeWarning
        )
    
    if JWT_SECRET_KEY == 'jwt-secret-key-change-in-production':
        import warnings
        warnings.warn(
            "WARNING: Using default JWT_SECRET_KEY in production environment. "
            "This is insecure. Please set the JWT_SECRET_KEY environment variable.",
            RuntimeWarning
        )
    
    if not OPENAI_API_KEY:
        import warnings
        warnings.warn(
            "WARNING: No OpenAI API key set in production environment. "
            "AI capabilities will not function properly.",
            RuntimeWarning
        )