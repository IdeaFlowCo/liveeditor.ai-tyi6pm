"""
Package initialization file for MongoDB repository unit tests.
Provides common test utilities, mocks, and fixtures specifically
for testing MongoDB data access components.
"""

import pytest                   # pytest ^7.0.0
import mongomock                # mongomock ^4.1.0
from unittest.mock import MagicMock, patch  # standard library
from bson import ObjectId       # pymongo ~=4.3.0

from backend.core.utils.logger import get_logger  # Import logging functionality

# Set up the logger
logger = get_logger(__name__)

def create_mock_collection(collection_name: str) -> MagicMock:
    """
    Creates a mocked MongoDB collection for unit testing repository classes
    
    Args:
        collection_name: Name of the collection to mock
        
    Returns:
        Mocked MongoDB collection with common methods configured
    """
    # Create a MagicMock instance for the collection
    mock_collection = MagicMock()
    
    # Configure find_one method to return None by default
    mock_collection.find_one.return_value = None
    
    # Configure find method to return a mock cursor with empty results
    mock_cursor = MagicMock()
    mock_cursor.__iter__.return_value = iter([])
    mock_cursor.count.return_value = 0
    mock_collection.find.return_value = mock_cursor
    
    # Configure insert_one method to return a mock with inserted_id
    insert_result = MagicMock()
    insert_result.inserted_id = ObjectId()
    mock_collection.insert_one.return_value = insert_result
    
    # Configure update_one and update_many methods with mock results
    update_result = MagicMock()
    update_result.modified_count = 0
    update_result.acknowledged = True
    mock_collection.update_one.return_value = update_result
    mock_collection.update_many.return_value = update_result
    
    # Configure delete_one and delete_many methods with mock results
    delete_result = MagicMock()
    delete_result.deleted_count = 0
    delete_result.acknowledged = True
    mock_collection.delete_one.return_value = delete_result
    mock_collection.delete_many.return_value = delete_result
    
    # Configure count_documents method to return 0 by default
    mock_collection.count_documents.return_value = 0
    
    # Configure find_one_and_update with appropriate return value
    mock_collection.find_one_and_update.return_value = None
    
    return mock_collection

def create_mock_db_client() -> MagicMock:
    """
    Creates a mocked MongoDB client for unit testing connection logic
    
    Returns:
        Mocked MongoDB client with database and collection access
    """
    # Create a MagicMock instance for the MongoDB client
    mock_client = MagicMock()
    
    # Configure the __getitem__ method to access mock databases
    mock_db = MagicMock()
    mock_client.__getitem__.return_value = mock_db
    
    # Configure the get_database method to return a mock database
    mock_client.get_database.return_value = mock_db
    
    # Create a mock database with collection access methods
    mock_db.__getitem__.return_value = create_mock_collection("default")
    
    return mock_client

def create_object_id(id_str: str = None) -> ObjectId:
    """
    Creates a BSON ObjectId for test data or returns string as ObjectId
    
    Args:
        id_str: String representation of ObjectId or None to generate new
        
    Returns:
        ObjectId instance for use in tests
    """
    # If id_str is already an ObjectId, return it directly
    if isinstance(id_str, ObjectId):
        return id_str
    
    # If id_str is a valid 24-character hex string, convert to ObjectId
    if id_str and len(id_str) == 24:
        try:
            return ObjectId(id_str)
        except Exception:
            logger.warning(f"Invalid ObjectId format: {id_str}, generating a new one")
    
    # If id_str is None or invalid, generate a new random ObjectId
    return ObjectId()

class MongoDBTestMixin:
    """
    Mixin class providing common MongoDB test utilities for repository test classes
    """
    
    def __init__(self):
        """Initializes the MongoDB test mixin"""
        self._mock_collection = None
        self._mock_db = None
        self._test_data = None
        
    def setup_mongodb_mocks(self, collection_name: str) -> MagicMock:
        """
        Sets up MongoDB mocks for testing a repository
        
        Args:
            collection_name: Name of the collection to mock
            
        Returns:
            The mock collection for test configuration
        """
        # Create mock collection using create_mock_collection
        self._mock_collection = create_mock_collection(collection_name)
        
        # Store mock collection in _mock_collection property
        # Create a patch for the get_collection function
        # Note: The actual path should be adjusted in concrete test classes
        get_collection_patcher = patch('backend.data.mongodb.connection.get_collection')
        mock_get_collection = get_collection_patcher.start()
        
        # Configure the patch to return the mock collection
        mock_get_collection.return_value = self._mock_collection
        
        # Return the mock collection for further test configuration
        return self._mock_collection
    
    def configure_find_one(self, return_value: dict, query_filter: dict = None) -> None:
        """
        Configures the find_one method of the mock collection
        
        Args:
            return_value: The value to return from find_one
            query_filter: Query filter to match, if None applies to all queries
        """
        # Access the _mock_collection.find_one method
        if query_filter is None:
            # Configure it to return the specified return_value when called with any filter
            self._mock_collection.find_one.return_value = return_value
        else:
            # Configure it to return the specified return_value when called with query_filter
            self._mock_collection.find_one.side_effect = lambda filter_arg, *args, **kwargs: \
                return_value if filter_arg == query_filter else None
    
    def configure_find(self, return_values: list, query_filter: dict = None) -> None:
        """
        Configures the find method of the mock collection
        
        Args:
            return_values: The list of values to return from find cursor
            query_filter: Query filter to match, if None applies to all queries
        """
        # Access the _mock_collection.find method
        # Create a mock cursor that will return the specified return_values
        mock_cursor = MagicMock()
        mock_cursor.__iter__.return_value = iter(return_values)
        mock_cursor.count.return_value = len(return_values)
        
        # Configure cursor iteration, count, and other methods
        if query_filter is None:
            # Configure find to return this cursor when called with any filter
            self._mock_collection.find.return_value = mock_cursor
        else:
            # Configure find to return this cursor when called with query_filter
            self._mock_collection.find.side_effect = lambda filter_arg, *args, **kwargs: \
                mock_cursor if filter_arg == query_filter else MagicMock(__iter__=lambda self: iter([]))
    
    def configure_insert_result(self, inserted_id: str = None) -> None:
        """
        Configures the insert_one method result of the mock collection
        
        Args:
            inserted_id: The ID to use for the inserted document
        """
        # Create a mock InsertOneResult with the specified inserted_id
        insert_result = MagicMock()
        # Convert inserted_id to ObjectId if it's a string
        insert_result.inserted_id = create_object_id(inserted_id)
        
        # Configure _mock_collection.insert_one to return this result
        self._mock_collection.insert_one.return_value = insert_result
    
    def configure_update_result(self, modified_count: int = 1, acknowledged: bool = True) -> None:
        """
        Configures the update_one and update_many method results
        
        Args:
            modified_count: Number of documents modified
            acknowledged: Whether the operation was acknowledged
        """
        # Create a mock UpdateResult with the specified modified_count and acknowledged status
        update_result = MagicMock()
        update_result.modified_count = modified_count
        update_result.acknowledged = acknowledged
        
        # Configure _mock_collection.update_one to return this result
        self._mock_collection.update_one.return_value = update_result
        
        # Configure _mock_collection.update_many to return this result
        self._mock_collection.update_many.return_value = update_result
        
        # Configure _mock_collection.find_one_and_update with appropriate return value
        self._mock_collection.find_one_and_update.return_value = {"_id": ObjectId()} if modified_count > 0 else None
    
    def configure_delete_result(self, deleted_count: int = 1, acknowledged: bool = True) -> None:
        """
        Configures the delete_one and delete_many method results
        
        Args:
            deleted_count: Number of documents deleted
            acknowledged: Whether the operation was acknowledged
        """
        # Create a mock DeleteResult with the specified deleted_count and acknowledged status
        delete_result = MagicMock()
        delete_result.deleted_count = deleted_count
        delete_result.acknowledged = acknowledged
        
        # Configure _mock_collection.delete_one to return this result
        self._mock_collection.delete_one.return_value = delete_result
        
        # Configure _mock_collection.delete_many to return this result
        self._mock_collection.delete_many.return_value = delete_result
    
    def configure_count_documents(self, count: int = 0, query_filter: dict = None) -> None:
        """
        Configures the count_documents method result
        
        Args:
            count: The count to return
            query_filter: Query filter to match, if None applies to all queries
        """
        # Configure _mock_collection.count_documents to return the specified count
        if query_filter is None:
            # If query_filter is provided, make it only return for that specific filter
            self._mock_collection.count_documents.return_value = count
        else:
            self._mock_collection.count_documents.side_effect = lambda filter_arg, *args, **kwargs: \
                count if filter_arg == query_filter else 0