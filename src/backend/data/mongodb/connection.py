"""
Provides MongoDB connection functionality with connection pooling for the application's document storage services.
Establishes and manages connections to MongoDB with appropriate configuration, error handling, and retry mechanisms.
"""

import os
import time
import pymongo
from pymongo import MongoClient
import pymongo.errors
from bson.objectid import ObjectId

from ...config import DevelopmentConfig, ProductionConfig, TestingConfig
from ...core.utils.logger import get_logger
from ...core.utils.validators import validate_object_id

# Default MongoDB configuration values
DEFAULT_MONGODB_HOST = 'localhost'
DEFAULT_MONGODB_PORT = 27017
DEFAULT_MONGODB_DB = 'ai_writing_enhancement'
DEFAULT_MAX_POOL_SIZE = 100
DEFAULT_MIN_POOL_SIZE = 10
DEFAULT_MAX_IDLE_TIME_MS = 60000
DEFAULT_CONNECTION_TIMEOUT_MS = 30000
DEFAULT_SERVER_SELECTION_TIMEOUT_MS = 30000
DEFAULT_RETRY_WRITES = True
DEFAULT_RETRY_READS = True
DEFAULT_W_CONCERN = 'majority'
DEFAULT_READ_PREFERENCE = 'primaryPreferred'
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 0.5

# Setup logger
logger = get_logger(__name__)

# Global connection objects
_db_client = None
_db_instance = None
_collections = {}


class MongoDBConnectionError(Exception):
    """Custom exception class for MongoDB connection errors"""
    
    def __init__(self, message, original_exception=None):
        """Initialize the MongoDB connection error
        
        Args:
            message (str): Error message
            original_exception (Exception): The original exception that caused this error
        """
        super().__init__(message)
        self.original_exception = original_exception


def get_mongodb_client(config_override=None):
    """Creates or returns an existing MongoDB client instance with connection pooling
    
    Args:
        config_override (dict): Optional dictionary with configuration overrides
        
    Returns:
        pymongo.MongoClient: MongoDB client instance with configured connection pool
        
    Raises:
        MongoDBConnectionError: If connection to MongoDB fails
    """
    global _db_client
    
    # Return existing client if available
    if _db_client is not None:
        return _db_client
    
    # Get environment
    env = os.environ.get('FLASK_ENV', 'development')
    
    # Get config based on environment
    if env == 'production':
        config = ProductionConfig().MONGODB_CONFIG
    elif env == 'testing':
        config = TestingConfig().MONGODB_CONFIG
    else:
        config = DevelopmentConfig().MONGODB_CONFIG
    
    # Apply overrides if provided
    if config_override:
        config.update(config_override)
    
    # Build MongoDB connection URI
    if config.get('username') and config.get('password'):
        uri = f"mongodb://{config.get('username')}:{config.get('password')}@"
        uri += f"{config.get('host', DEFAULT_MONGODB_HOST)}:{config.get('port', DEFAULT_MONGODB_PORT)}"
        uri += f"/{config.get('db_name', DEFAULT_MONGODB_DB)}"
        
        # Add auth source if provided
        if config.get('auth_source'):
            uri += f"?authSource={config.get('auth_source')}"
    else:
        uri = f"mongodb://{config.get('host', DEFAULT_MONGODB_HOST)}:{config.get('port', DEFAULT_MONGODB_PORT)}"
    
    # Connection parameters
    max_pool_size = config.get('max_pool_size', DEFAULT_MAX_POOL_SIZE)
    min_pool_size = config.get('min_pool_size', DEFAULT_MIN_POOL_SIZE)
    max_idle_time_ms = config.get('max_idle_time_ms', DEFAULT_MAX_IDLE_TIME_MS)
    connect_timeout_ms = config.get('connect_timeout_ms', DEFAULT_CONNECTION_TIMEOUT_MS)
    server_selection_timeout_ms = config.get('server_selection_timeout_ms', DEFAULT_SERVER_SELECTION_TIMEOUT_MS)
    
    # Read and write concerns
    read_preference = config.get('read_preference', DEFAULT_READ_PREFERENCE)
    w = config.get('w', DEFAULT_W_CONCERN)
    
    # Retry options
    retry_writes = config.get('retry_writes', DEFAULT_RETRY_WRITES)
    retry_reads = config.get('retry_reads', DEFAULT_RETRY_READS)
    
    # Connect to MongoDB with retries
    retries = 0
    max_retries = DEFAULT_MAX_RETRIES
    retry_delay = DEFAULT_RETRY_DELAY
    
    logger.info(f"Connecting to MongoDB at {config.get('host', DEFAULT_MONGODB_HOST)}:{config.get('port', DEFAULT_MONGODB_PORT)}")
    
    while retries <= max_retries:
        try:
            client_kwargs = {
                'host': uri,
                'maxPoolSize': max_pool_size,
                'minPoolSize': min_pool_size,
                'maxIdleTimeMS': max_idle_time_ms,
                'connectTimeoutMS': connect_timeout_ms,
                'serverSelectionTimeoutMS': server_selection_timeout_ms,
                'retryWrites': retry_writes,
                'retryReads': retry_reads,
                'w': w,
            }
            
            # Add read preference
            if read_preference:
                client_kwargs['readPreference'] = read_preference
            
            # Add replica set if configured
            if config.get('replica_set'):
                client_kwargs['replicaSet'] = config.get('replica_set')
            
            # Create the client
            client = MongoClient(**client_kwargs)
            
            # Test the connection
            client.admin.command('ping')
            
            logger.info("Successfully connected to MongoDB")
            _db_client = client
            return client
            
        except pymongo.errors.ConnectionFailure as e:
            retries += 1
            if retries <= max_retries:
                wait_time = retry_delay * (2 ** (retries - 1))  # Exponential backoff
                logger.warning(f"MongoDB connection attempt {retries} failed. Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to connect to MongoDB after {max_retries} attempts: {str(e)}")
                raise MongoDBConnectionError(f"Failed to connect to MongoDB: {str(e)}", e)
                
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {str(e)}")
            raise MongoDBConnectionError(f"Unexpected error connecting to MongoDB: {str(e)}", e)


def get_database(db_name=None):
    """Gets a reference to the MongoDB database instance
    
    Args:
        db_name (str): Optional database name, uses default if not provided
        
    Returns:
        pymongo.database.Database: MongoDB database instance
        
    Raises:
        MongoDBConnectionError: If connection to MongoDB fails
    """
    global _db_instance
    
    # Get client
    client = get_mongodb_client()
    
    # If db_name not provided, get from config
    if db_name is None:
        # Get environment
        env = os.environ.get('FLASK_ENV', 'development')
        
        if env == 'production':
            config = ProductionConfig().MONGODB_CONFIG
        elif env == 'testing':
            config = TestingConfig().MONGODB_CONFIG
        else:
            config = DevelopmentConfig().MONGODB_CONFIG
        
        db_name = config.get('db_name', DEFAULT_MONGODB_DB)
    
    # Get or set the database instance
    if _db_instance is None or _db_instance.name != db_name:
        logger.debug(f"Getting database: {db_name}")
        _db_instance = client[db_name]
    
    return _db_instance


def get_collection(collection_name, db_name=None):
    """Gets a reference to a specific MongoDB collection
    
    Args:
        collection_name (str): Name of the collection to get
        db_name (str): Optional database name, uses default if not provided
        
    Returns:
        pymongo.collection.Collection: MongoDB collection instance
        
    Raises:
        MongoDBConnectionError: If connection to MongoDB fails
    """
    global _collections
    
    # Get database
    db = get_database(db_name)
    
    # Cache key is db_name:collection_name
    cache_key = f"{db.name}:{collection_name}"
    
    # Return cached collection if available
    if cache_key in _collections:
        return _collections[cache_key]
    
    # Get the collection and cache it
    logger.debug(f"Getting collection: {collection_name}")
    collection = db[collection_name]
    _collections[cache_key] = collection
    
    return collection


def create_indexes():
    """Creates indexes on MongoDB collections to optimize query performance
    
    Returns:
        None: Creates indexes but doesn't return a value
        
    Raises:
        MongoDBConnectionError: If connection to MongoDB fails
    """
    try:
        db = get_database()
        
        # Documents collection indexes
        documents = get_collection('documents')
        documents.create_index('userId')
        documents.create_index([('userId', pymongo.ASCENDING), ('isArchived', pymongo.ASCENDING)])
        documents.create_index('tags')
        documents.create_index('createdAt')
        documents.create_index('updatedAt')
        
        # Users collection indexes
        users = get_collection('users')
        users.create_index('email', unique=True)
        users.create_index('accountStatus')
        
        # Document versions collection indexes
        document_versions = get_collection('document_versions')
        document_versions.create_index('documentId')
        document_versions.create_index([('documentId', pymongo.ASCENDING), ('versionNumber', pymongo.DESCENDING)])
        
        # AI prompt templates collection indexes
        templates = get_collection('ai_prompt_templates')
        templates.create_index('category')
        
        # AI interactions collection indexes
        interactions = get_collection('ai_interactions')
        interactions.create_index('sessionId')
        interactions.create_index([('documentId', pymongo.ASCENDING), ('timestamp', pymongo.DESCENDING)])
        
        # User preferences collection indexes
        preferences = get_collection('user_preferences')
        preferences.create_index('userId', unique=True)
        
        logger.info("Successfully created MongoDB indexes")
    except Exception as e:
        logger.error(f"Error creating MongoDB indexes: {str(e)}")
        raise MongoDBConnectionError(f"Error creating MongoDB indexes: {str(e)}", e)


def close_connections():
    """Closes all open MongoDB connections
    
    Returns:
        None: Closes connections but doesn't return a value
    """
    global _db_client, _db_instance, _collections
    
    if _db_client is not None:
        logger.info("Closing MongoDB connection")
        _db_client.close()
        _db_client = None
        _db_instance = None
        _collections = {}


def is_mongodb_available():
    """Checks if MongoDB server is available by attempting a simple command
    
    Returns:
        bool: True if MongoDB is available, False otherwise
    """
    try:
        client = get_mongodb_client()
        # Run a simple command to test connectivity
        client.admin.command('serverStatus')
        return True
    except Exception as e:
        logger.warning(f"MongoDB is not available: {str(e)}")
        return False


def object_id_to_str(object_id):
    """Converts MongoDB ObjectId to string representation
    
    Args:
        object_id (bson.objectid.ObjectId): MongoDB ObjectId to convert
        
    Returns:
        str: String representation of the ObjectId
    """
    if isinstance(object_id, str):
        return object_id
    
    return str(object_id)


def str_to_object_id(id_str):
    """Converts string to MongoDB ObjectId
    
    Args:
        id_str (str): String to convert to ObjectId
        
    Returns:
        bson.objectid.ObjectId: ObjectId representation of the string
        
    Raises:
        ValueError: If the string is not a valid ObjectId
    """
    try:
        # Validate format using imported validator
        validate_object_id(id_str)
        return ObjectId(id_str)
    except Exception as e:
        logger.error(f"Invalid ObjectId format: {id_str}, error: {str(e)}")
        raise ValueError(f"Invalid ObjectId format: {id_str}")


def reset_db_for_testing():
    """Resets the database for testing purposes by dropping all collections
    
    This function should only be used in the testing environment.
    
    Returns:
        None: Resets database but doesn't return a value
        
    Raises:
        RuntimeError: If not in testing environment
        MongoDBConnectionError: If connection to MongoDB fails
    """
    # Ensure we're in testing environment
    env = os.environ.get('FLASK_ENV', 'development')
    if env != 'testing':
        raise RuntimeError("reset_db_for_testing can only be used in testing environment")
    
    # Get database
    db = get_database()
    
    # Get list of collections
    collection_names = db.list_collection_names()
    
    # Drop each collection
    for collection_name in collection_names:
        logger.info(f"Dropping collection: {collection_name}")
        db.drop_collection(collection_name)
    
    logger.info("Reset database for testing")
    
    # Close connections to ensure clean state
    close_connections()