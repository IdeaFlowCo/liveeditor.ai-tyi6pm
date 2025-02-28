"""
Manages connections to AWS S3 service for document storage operations.

This module provides client and resource interfaces with proper configuration,
retry mechanisms, and error handling for the AI writing enhancement platform's
document storage needs. It handles connection pooling, credential management,
and resilient operations with S3.
"""

import os  # standard library
import time  # standard library
from typing import Union, Callable, Any, Dict, Optional  # standard library

import boto3  # AWS SDK for Python ~=1.26.0
import botocore.exceptions  # Exception handling for AWS operations ~=1.26.0
from botocore.config import Config  # Configuration options for boto3 clients ~=1.26.0

from ...core.utils.logger import get_logger  # Import logging functionality
from ... import config  # Import application configuration including S3 connection settings

# Initialize logger
logger = get_logger(__name__)

# Default settings
DEFAULT_S3_REGION = 'us-east-1'
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_RETRY_MODE = 'adaptive'
DEFAULT_BACKOFF_FACTOR = 2

# Global connection objects (for connection pooling)
_s3_client = None
_s3_resource = None


def get_s3_client(config_override=None):
    """
    Creates or returns an existing boto3 S3 client with appropriate configuration and retry settings.
    
    Args:
        config_override (dict): Override default configuration settings
        
    Returns:
        boto3.client: Configured S3 client instance
    
    Raises:
        S3ConnectionError: If unable to establish a connection to S3
    """
    global _s3_client
    
    # Return existing client if already initialized
    if _s3_client is not None:
        logger.debug("Returning existing S3 client")
        return _s3_client
    
    try:
        # Get S3 configuration from config module or environment variables
        env = os.environ.get('FLASK_ENV', 'development')
        if env == 'development':
            s3_config = config.DevelopmentConfig().S3_CONFIG
        elif env == 'testing':
            s3_config = config.TestingConfig().S3_CONFIG
        elif env == 'production':
            s3_config = config.ProductionConfig().S3_CONFIG
        else:
            s3_config = config.DevelopmentConfig().S3_CONFIG
            
        # Apply any provided configuration overrides
        if config_override:
            s3_config.update(config_override)
        
        # Configure boto3 retry settings using botocore.config.Config
        boto_config = Config(
            region_name=s3_config.get('region_name', DEFAULT_S3_REGION),
            retries={
                'max_attempts': s3_config.get('max_attempts', DEFAULT_MAX_ATTEMPTS),
                'mode': s3_config.get('retry_mode', DEFAULT_RETRY_MODE)
            }
        )
        
        # Prepare client initialization parameters
        client_kwargs = {
            'service_name': 's3',
            'config': boto_config
        }
        
        # Add endpoint URL if specified (used for local development with MinIO)
        if s3_config.get('endpoint_url'):
            client_kwargs['endpoint_url'] = s3_config['endpoint_url']
            
        # Add AWS credentials if provided
        if s3_config.get('access_key_id') and s3_config.get('secret_access_key'):
            client_kwargs['aws_access_key_id'] = s3_config['access_key_id']
            client_kwargs['aws_secret_access_key'] = s3_config['secret_access_key']
            
        # Add SSL verification settings if specified
        if 'use_ssl' in s3_config:
            client_kwargs['use_ssl'] = s3_config['use_ssl']
        if 'verify' in s3_config:
            client_kwargs['verify'] = s3_config['verify']
            
        # Create the S3 client
        logger.info("Creating new S3 client", 
                   region=s3_config.get('region_name', DEFAULT_S3_REGION),
                   endpoint_url=s3_config.get('endpoint_url', 'default AWS'))
        
        _s3_client = boto3.client(**client_kwargs)
        
        # Verify connection using a simple head_bucket call
        if not check_connection(_s3_client):
            raise S3ConnectionError("Failed to verify S3 client connection", 
                                   Exception("Connection verification failed"))
        
        # Cache client in _s3_client global variable
        return _s3_client
        
    except botocore.exceptions.BotoCoreError as e:
        logger.error("Failed to create S3 client", error=str(e), exc_info=True)
        raise S3ConnectionError(f"Failed to create S3 client: {str(e)}", e)
    except Exception as e:
        logger.error("Unexpected error creating S3 client", error=str(e), exc_info=True)
        raise S3ConnectionError(f"Unexpected error creating S3 client: {str(e)}", e)


def get_s3_resource(config_override=None):
    """
    Creates or returns an existing boto3 S3 resource with appropriate configuration.
    
    Args:
        config_override (dict): Override default configuration settings
        
    Returns:
        boto3.resource: Configured S3 resource instance
    
    Raises:
        S3ConnectionError: If unable to establish a connection to S3
    """
    global _s3_resource
    
    # Return existing resource if already initialized
    if _s3_resource is not None:
        logger.debug("Returning existing S3 resource")
        return _s3_resource
    
    try:
        # Get S3 configuration from config module or environment variables
        env = os.environ.get('FLASK_ENV', 'development')
        if env == 'development':
            s3_config = config.DevelopmentConfig().S3_CONFIG
        elif env == 'testing':
            s3_config = config.TestingConfig().S3_CONFIG
        elif env == 'production':
            s3_config = config.ProductionConfig().S3_CONFIG
        else:
            s3_config = config.DevelopmentConfig().S3_CONFIG
            
        # Apply any provided configuration overrides
        if config_override:
            s3_config.update(config_override)
        
        # Configure boto3 retry settings using botocore.config.Config
        boto_config = Config(
            region_name=s3_config.get('region_name', DEFAULT_S3_REGION),
            retries={
                'max_attempts': s3_config.get('max_attempts', DEFAULT_MAX_ATTEMPTS),
                'mode': s3_config.get('retry_mode', DEFAULT_RETRY_MODE)
            }
        )
        
        # Prepare resource initialization parameters
        resource_kwargs = {
            'service_name': 's3',
            'config': boto_config
        }
        
        # Add endpoint URL if specified (used for local development with MinIO)
        if s3_config.get('endpoint_url'):
            resource_kwargs['endpoint_url'] = s3_config['endpoint_url']
            
        # Add AWS credentials if provided
        if s3_config.get('access_key_id') and s3_config.get('secret_access_key'):
            resource_kwargs['aws_access_key_id'] = s3_config['access_key_id']
            resource_kwargs['aws_secret_access_key'] = s3_config['secret_access_key']
            
        # Add SSL verification settings if specified
        if 'use_ssl' in s3_config:
            resource_kwargs['use_ssl'] = s3_config['use_ssl']
        if 'verify' in s3_config:
            resource_kwargs['verify'] = s3_config['verify']
            
        # Create the S3 resource
        logger.info("Creating new S3 resource", 
                   region=s3_config.get('region_name', DEFAULT_S3_REGION),
                   endpoint_url=s3_config.get('endpoint_url', 'default AWS'))
        
        _s3_resource = boto3.resource(**resource_kwargs)
        
        # Verify connection by listing buckets
        if not check_connection(_s3_resource):
            raise S3ConnectionError("Failed to verify S3 resource connection", 
                                   Exception("Connection verification failed"))
        
        # Cache resource in _s3_resource global variable
        return _s3_resource
        
    except botocore.exceptions.BotoCoreError as e:
        logger.error("Failed to create S3 resource", error=str(e), exc_info=True)
        raise S3ConnectionError(f"Failed to create S3 resource: {str(e)}", e)
    except Exception as e:
        logger.error("Unexpected error creating S3 resource", error=str(e), exc_info=True)
        raise S3ConnectionError(f"Unexpected error creating S3 resource: {str(e)}", e)


def ensure_bucket_exists(bucket_name, region=None):
    """
    Ensures that the specified S3 bucket exists, creating it if necessary.
    
    Args:
        bucket_name (str): Name of the S3 bucket
        region (str): AWS region for bucket creation
    
    Returns:
        bool: True if bucket exists or was created, False otherwise
    """
    client = get_s3_client()
    
    try:
        # Use head_bucket to check if bucket already exists
        client.head_bucket(Bucket=bucket_name)
        logger.debug(f"Bucket already exists: {bucket_name}")
        return True
    except botocore.exceptions.ClientError as e:
        error_code = e.response.get('Error', {}).get('Code')
        
        # If bucket doesn't exist, attempt to create it
        if error_code == '404':
            logger.info(f"Bucket doesn't exist, creating: {bucket_name}")
            try:
                if region is None:
                    region = client.meta.config.region_name
                
                # Create bucket with appropriate region configuration
                if region == 'us-east-1':
                    # us-east-1 requires special handling (no LocationConstraint)
                    client.create_bucket(Bucket=bucket_name)
                else:
                    client.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': region}
                    )
                logger.info(f"Successfully created bucket: {bucket_name}")
                return True
            except botocore.exceptions.ClientError as create_error:
                logger.error(f"Failed to create bucket {bucket_name}", 
                            error=str(create_error), exc_info=True)
                return False
        # Handle AccessDenied and other exceptions appropriately
        elif error_code == '403':
            logger.error(f"Permission denied accessing bucket: {bucket_name}", 
                        error=str(e), exc_info=True)
            return False
        else:
            logger.error(f"Error checking bucket {bucket_name}", 
                        error=str(e), exc_info=True)
            return False


def create_presigned_url(bucket_name, object_key, operation='get_object', expiration=3600):
    """
    Creates a pre-signed URL for temporary access to an S3 object.
    
    Args:
        bucket_name (str): Name of the S3 bucket
        object_key (str): S3 object key
        operation (str): S3 operation (get_object, put_object, etc.)
        expiration (int): URL expiration in seconds
    
    Returns:
        str: Pre-signed URL for accessing the S3 object
    """
    client = get_s3_client()
    
    try:
        # Set default expiration if not provided
        if not expiration:
            expiration = 3600  # 1 hour default
            
        # Generate pre-signed URL using client.generate_presigned_url
        url = client.generate_presigned_url(
            ClientMethod=operation,
            Params={
                'Bucket': bucket_name,
                'Key': object_key
            },
            ExpiresIn=expiration
        )
        
        logger.debug(f"Generated presigned URL for {operation} operation",
                    bucket=bucket_name,
                    key=object_key,
                    expiration=expiration)
        
        return url
    except botocore.exceptions.ClientError as e:
        logger.error(f"Failed to generate presigned URL", 
                    operation=operation,
                    bucket=bucket_name,
                    key=object_key,
                    error=str(e),
                    exc_info=True)
        raise S3ConnectionError(f"Failed to generate presigned URL: {str(e)}", e)


def check_connection(s3_conn):
    """
    Validates connection to S3 by performing a simple operation.
    
    Args:
        s3_conn (typing.Union[boto3.client, boto3.resource]): S3 client or resource to check
    
    Returns:
        bool: True if connection is valid, False otherwise
    """
    try:
        # Check the type of connection (client or resource)
        if isinstance(s3_conn, boto3.resources.factory.ServiceResource):
            # For resource, try list(s3_conn.buckets.all())
            list(s3_conn.buckets.all())[0:1]  # Just get the first bucket if any
        else:
            # For client, try list_buckets() operation
            s3_conn.list_buckets()
        
        logger.debug("S3 connection successfully verified")
        return True
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        logger.error("S3 connection verification failed", error=str(e), exc_info=True)
        return False
    except Exception as e:
        logger.error("Unexpected error during S3 connection verification", 
                    error=str(e), exc_info=True)
        return False


def with_retry(max_attempts=DEFAULT_MAX_ATTEMPTS, backoff_factor=DEFAULT_BACKOFF_FACTOR):
    """
    Decorator that adds retry logic with exponential backoff to S3 operations.
    
    Args:
        max_attempts (int): Maximum number of retry attempts
        backoff_factor (float): Factor for exponential backoff calculation
    
    Returns:
        typing.Callable: Decorated function with retry logic
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            attempts = 0
            last_exception = None
            
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except (botocore.exceptions.ClientError, 
                        botocore.exceptions.BotoCoreError) as e:
                    attempts += 1
                    last_exception = e
                    
                    # If max attempts reached, log error and re-raise exception
                    if attempts >= max_attempts:
                        logger.error(f"Operation failed after {max_attempts} attempts",
                                    function=func.__name__,
                                    error=str(e),
                                    exc_info=True)
                        break
                    
                    # Calculate backoff delay using exponential formula
                    delay = backoff_factor ** attempts
                    
                    # Log retry attempt and wait for calculated delay
                    logger.warning(f"Operation failed, retrying in {delay:.2f} seconds",
                                  function=func.__name__,
                                  attempt=attempts,
                                  max_attempts=max_attempts,
                                  error=str(e))
                    
                    time.sleep(delay)
            
            # Retry the function call
            raise S3ConnectionError(
                f"Operation {func.__name__} failed after {max_attempts} attempts", 
                last_exception
            )
            
        return wrapper
    return decorator


def close_connections():
    """
    Closes all open S3 connections and releases resources.
    """
    global _s3_client, _s3_resource
    
    logger.info("Closing all S3 connections")
    _s3_client = None
    _s3_resource = None


class S3ConnectionError(Exception):
    """
    Custom exception for S3 connection errors.
    """
    
    def __init__(self, message, original_exception=None):
        """
        Initialize the S3 connection error.
        
        Args:
            message (str): Error message
            original_exception (Exception): Original exception that caused this error
        """
        super().__init__(message)
        self.original_exception = original_exception


class S3Connection:
    """
    Manages AWS S3 connection lifecycle and provides access to client and resource 
    interfaces with retry capabilities.
    """
    
    def __init__(self, config=None, max_attempts=DEFAULT_MAX_ATTEMPTS, 
                retry_mode=DEFAULT_RETRY_MODE):
        """
        Initializes the S3Connection with configuration and retry settings.
        
        Args:
            config (dict): Configuration options
            max_attempts (int): Maximum retry attempts
            retry_mode (str): Retry mode (legacy, standard, adaptive)
        """
        # Store configuration or get from config import if None
        self._config = config
        self._max_attempts = max_attempts if max_attempts else DEFAULT_MAX_ATTEMPTS
        self._retry_mode = retry_mode if retry_mode else DEFAULT_RETRY_MODE
        
        # Initialize client and resource to None
        self._client = None
        self._resource = None
        self._initialized = False
    
    def initialize(self):
        """
        Establishes connections to AWS S3 service with retry capabilities.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Try to create S3 client using get_s3_client with config
            if self._config is None:
                self._config = {}
            
            if 'max_attempts' not in self._config:
                self._config['max_attempts'] = self._max_attempts
                
            if 'retry_mode' not in self._config:
                self._config['retry_mode'] = self._retry_mode
            
            # Try to create S3 client using get_s3_client with config
            self._client = get_s3_client(self._config)
            
            # Try to create S3 resource using get_s3_resource with config
            self._resource = get_s3_resource(self._config)
            
            # Validate connections with check_connection
            client_ok = check_connection(self._client)
            resource_ok = check_connection(self._resource)
            
            # Set initialized flag to True if successful
            self._initialized = client_ok and resource_ok
            
            if self._initialized:
                logger.info("S3Connection successfully initialized")
            else:
                logger.error("S3Connection initialization failed")
                
            return self._initialized
        
        except Exception as e:
            logger.error("Failed to initialize S3Connection", error=str(e), exc_info=True)
            self._initialized = False
            return False
    
    def get_client(self):
        """
        Returns the S3 client, initializing if necessary.
        
        Returns:
            boto3.client: S3 client instance
        
        Raises:
            S3ConnectionError: If initialization fails
        """
        # Initialize if not already initialized
        if not self._initialized and not self.initialize():
            raise S3ConnectionError("S3Connection is not initialized")
        
        # Return the client instance
        return self._client
    
    def get_resource(self):
        """
        Returns the S3 resource, initializing if necessary.
        
        Returns:
            boto3.resource: S3 resource instance
        
        Raises:
            S3ConnectionError: If initialization fails
        """
        # Initialize if not already initialized
        if not self._initialized and not self.initialize():
            raise S3ConnectionError("S3Connection is not initialized")
        
        # Return the resource instance
        return self._resource
    
    def close(self):
        """
        Closes connections and releases resources.
        """
        logger.info("Closing S3Connection")
        
        # Set client and resource to None
        self._client = None
        self._resource = None
        
        # Set initialized flag to False
        self._initialized = False
    
    def __enter__(self):
        """
        Context manager entry point.
        
        Returns:
            S3Connection: Self reference
        """
        # Initialize connection if not already initialized
        if not self._initialized:
            self.initialize()
        
        # Return self to be used in with statement
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit point.
        
        Args:
            exc_type (type): Exception type
            exc_val (Exception): Exception value
            exc_tb (traceback): Exception traceback
        
        Returns:
            bool: False to propagate exceptions, True to suppress
        """
        # Log any exceptions that occurred in the context
        if exc_type:
            logger.error("Exception occurred within S3Connection context",
                        error=str(exc_val),
                        exc_info=True)
        
        # Close connections regardless of exception
        self.close()
        
        # Return False to propagate exceptions
        return False