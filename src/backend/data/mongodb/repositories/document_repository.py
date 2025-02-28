"""
MongoDB repository implementation for document CRUD operations and management in the AI writing enhancement platform.
Handles persistent storage of documents, document metadata, and implements access control mechanisms for both 
authenticated and anonymous users.
"""

from datetime import datetime, timedelta
import pymongo
from pymongo.errors import PyMongoError, DuplicateKeyError
from bson import ObjectId
from typing import List, Dict, Tuple, Optional, Any, Union

from ..connection import get_collection, str_to_object_id, object_id_to_str
from ...core.utils.logger import get_logger
from ...core.utils.validators import validate_object_id, validate_document_content, is_valid_title

# Initialize logger
logger = get_logger(__name__)

# Constants
DEFAULT_DOCUMENT_TTL = 604800  # 7 days in seconds
ANONYMOUS_SESSION_TTL = 86400  # 1 day in seconds


class DocumentNotFoundError(Exception):
    """Exception raised when a document cannot be found"""
    
    def __init__(self, document_id: str, message: str = None):
        """Initializes the document not found error
        
        Args:
            document_id: The ID of the document that wasn't found
            message: Optional custom error message
        """
        if message is None:
            message = f"Document with ID {document_id} not found"
        super().__init__(message)
        self.document_id = document_id


class DocumentAccessError(Exception):
    """Exception raised when a user doesn't have access to a document"""
    
    def __init__(self, document_id: str, user_id: str = None, session_id: str = None, message: str = None):
        """Initializes the document access error
        
        Args:
            document_id: The ID of the document that was accessed
            user_id: The ID of the user attempting access
            session_id: The ID of the anonymous session attempting access
            message: Optional custom error message
        """
        if message is None:
            message = f"Access denied to document {document_id}"
        super().__init__(message)
        self.document_id = document_id
        self.user_id = user_id
        self.session_id = session_id


class DocumentRepository:
    """MongoDB repository for document operations with support for both authenticated and anonymous users"""
    
    COLLECTION_NAME = 'documents'
    
    def __init__(self):
        """Initializes the document repository with MongoDB collection"""
        self._collection = get_collection(self.COLLECTION_NAME)
        
        # Create indexes for efficient querying
        self._collection.create_index('userId')
        self._collection.create_index('sessionId')
        self._collection.create_index('createdAt')
        self._collection.create_index('updatedAt')
        self._collection.create_index('tags')
        self._collection.create_index([('userId', pymongo.ASCENDING), ('isArchived', pymongo.ASCENDING)])
        
        # Create text index for search functionality
        self._collection.create_index([('title', 'text'), ('description', 'text')])
        
        logger.info(f"DocumentRepository initialized with collection: {self.COLLECTION_NAME}")
    
    def create(self, document_data: dict, user_id: str = None, session_id: str = None) -> dict:
        """Creates a new document in the database
        
        Args:
            document_data: Document data including title, content, etc.
            user_id: User ID for authenticated users
            session_id: Session ID for anonymous users
            
        Returns:
            Created document with generated ID and metadata
            
        Raises:
            ValueError: If document data is invalid or neither user_id nor session_id is provided
        """
        # Validate document_data
        if not document_data:
            raise ValueError("Document data cannot be empty")
        
        # Ensure either user_id or session_id is provided
        if not user_id and not session_id:
            raise ValueError("Either user_id or session_id must be provided")
        
        # Validate title
        title = document_data.get('title')
        if not title:
            raise ValueError("Document title is required")
            
        if not is_valid_title(title):
            raise ValueError(f"Invalid document title: {title}")
        
        # Validate content if present
        content = document_data.get('content')
        if content:
            valid, error_message = validate_document_content(content)
            if not valid:
                raise ValueError(f"Invalid document content: {error_message}")
        
        # Prepare document object
        now = datetime.utcnow()
        document = {
            'title': title,
            'description': document_data.get('description', ''),
            'content': content or '',
            'userId': user_id,  # Will be None for anonymous users
            'sessionId': session_id if not user_id else None,  # Only set for anonymous
            'createdAt': now,
            'updatedAt': now,
            'isArchived': False,
            'tags': document_data.get('tags', []),
            'currentVersionId': None  # Will be updated when versions are created
        }
        
        # Insert document
        result = self._collection.insert_one(document)
        document['_id'] = object_id_to_str(result.inserted_id)
        
        logger.info(f"Created document: {document['_id']} for {'user: ' + user_id if user_id else 'session: ' + session_id}")
        
        return document
    
    def get_by_id(self, document_id: str, user_id: str = None, session_id: str = None, include_content: bool = True) -> Optional[dict]:
        """Retrieves a document by its ID with access control
        
        Args:
            document_id: ID of the document to retrieve
            user_id: User ID for authenticated users
            session_id: Session ID for anonymous users
            include_content: Whether to include document content in the response
            
        Returns:
            Document data if found and authorized, None otherwise
            
        Raises:
            DocumentNotFoundError: If document not found
            DocumentAccessError: If user doesn't have access to the document
            ValueError: If document_id is invalid
        """
        # Validate document_id
        validate_object_id(document_id)
        obj_id = str_to_object_id(document_id)
        
        # Build query
        query = {'_id': obj_id}
        
        # Define projection based on include_content
        projection = None if include_content else {'content': 0}
        
        # Get document
        document = self._collection.find_one(query, projection)
        
        if not document:
            logger.warning(f"Document not found: {document_id}")
            raise DocumentNotFoundError(document_id)
        
        # Check if user has access to this document
        if (document.get('userId') != user_id and 
            document.get('sessionId') != session_id):
            logger.warning(f"Access denied: document {document_id} accessed by user {user_id} or session {session_id}")
            raise DocumentAccessError(document_id, user_id, session_id)
        
        # Convert _id to string
        document['_id'] = object_id_to_str(document['_id'])
        
        # Convert ObjectId fields to string
        if document.get('currentVersionId'):
            document['currentVersionId'] = object_id_to_str(document['currentVersionId'])
        
        # Format datetime fields
        if document.get('createdAt'):
            document['createdAt'] = document['createdAt'].isoformat()
        if document.get('updatedAt'):
            document['updatedAt'] = document['updatedAt'].isoformat()
            
        logger.debug(f"Retrieved document: {document_id}")
        
        return document
    
    def find_by_user(self, user_id: str, filters: dict = None, skip: int = 0, limit: int = 20) -> Tuple[List[dict], int]:
        """Finds all documents owned by a specific user
        
        Args:
            user_id: User ID to find documents for
            filters: Additional query filters
            skip: Number of documents to skip for pagination
            limit: Maximum number of documents to return
            
        Returns:
            Tuple of (list of documents, total count)
            
        Raises:
            ValueError: If user_id is invalid or not provided
        """
        if not user_id:
            raise ValueError("User ID is required")
        
        # Build base query
        query = {'userId': user_id}
        
        # Add filters if provided
        if filters:
            # Check for archived filter
            if 'isArchived' in filters:
                query['isArchived'] = filters['isArchived']
            
            # Check for tags filter
            if 'tags' in filters and filters['tags']:
                if isinstance(filters['tags'], list):
                    query['tags'] = {'$all': filters['tags']}
                else:
                    query['tags'] = filters['tags']
        
        # Get total count
        total_count = self._collection.count_documents(query)
        
        # Get paginated documents
        documents = list(self._collection.find(
            query, 
            {'content': 0},  # Exclude content for listing
            skip=skip,
            limit=limit,
            sort=[('updatedAt', pymongo.DESCENDING)]  # Sort by most recently updated
        ))
        
        # Format documents
        formatted_docs = []
        for doc in documents:
            # Convert ObjectId to string
            doc['_id'] = object_id_to_str(doc['_id'])
            if doc.get('currentVersionId'):
                doc['currentVersionId'] = object_id_to_str(doc['currentVersionId'])
                
            # Format datetime fields
            if doc.get('createdAt'):
                doc['createdAt'] = doc['createdAt'].isoformat()
            if doc.get('updatedAt'):
                doc['updatedAt'] = doc['updatedAt'].isoformat()
                
            formatted_docs.append(doc)
        
        logger.debug(f"Found {len(formatted_docs)} documents for user {user_id}")
        
        return formatted_docs, total_count
    
    def find_by_session(self, session_id: str, filters: dict = None, skip: int = 0, limit: int = 20) -> Tuple[List[dict], int]:
        """Finds all documents associated with an anonymous session
        
        Args:
            session_id: Session ID to find documents for
            filters: Additional query filters
            skip: Number of documents to skip for pagination
            limit: Maximum number of documents to return
            
        Returns:
            Tuple of (list of documents, total count)
            
        Raises:
            ValueError: If session_id is invalid or not provided
        """
        if not session_id:
            raise ValueError("Session ID is required")
        
        # Build base query
        query = {'sessionId': session_id}
        
        # Add additional filters if provided
        if filters:
            if 'tags' in filters and filters['tags']:
                if isinstance(filters['tags'], list):
                    query['tags'] = {'$all': filters['tags']}
                else:
                    query['tags'] = filters['tags']
        
        # Get total count
        total_count = self._collection.count_documents(query)
        
        # Get paginated documents
        documents = list(self._collection.find(
            query, 
            {'content': 0},  # Exclude content for listing
            skip=skip,
            limit=limit,
            sort=[('updatedAt', pymongo.DESCENDING)]  # Sort by most recently updated
        ))
        
        # Format documents
        formatted_docs = []
        for doc in documents:
            # Convert ObjectId to string
            doc['_id'] = object_id_to_str(doc['_id'])
            if doc.get('currentVersionId'):
                doc['currentVersionId'] = object_id_to_str(doc['currentVersionId'])
                
            # Format datetime fields
            if doc.get('createdAt'):
                doc['createdAt'] = doc['createdAt'].isoformat()
            if doc.get('updatedAt'):
                doc['updatedAt'] = doc['updatedAt'].isoformat()
                
            formatted_docs.append(doc)
        
        logger.debug(f"Found {len(formatted_docs)} documents for session {session_id}")
        
        return formatted_docs, total_count
    
    def update(self, document_id: str, update_data: dict, user_id: str = None, session_id: str = None) -> dict:
        """Updates an existing document with access control
        
        Args:
            document_id: ID of the document to update
            update_data: New data to apply to the document
            user_id: User ID for authenticated users
            session_id: Session ID for anonymous users
            
        Returns:
            Updated document data
            
        Raises:
            DocumentNotFoundError: If document not found
            DocumentAccessError: If user doesn't have access to the document
            ValueError: If document_id or update_data is invalid
        """
        # Validate document_id
        validate_object_id(document_id)
        obj_id = str_to_object_id(document_id)
        
        # Get current document to check authorization
        try:
            current_doc = self.get_by_id(document_id, user_id, session_id)
        except DocumentNotFoundError:
            raise
        except DocumentAccessError:
            raise
        
        # Validate update data
        if not update_data:
            raise ValueError("Update data cannot be empty")
        
        # Check if trying to update title and validate it
        if 'title' in update_data:
            if not is_valid_title(update_data['title']):
                raise ValueError(f"Invalid document title: {update_data['title']}")
        
        # Check if trying to update content and validate it
        if 'content' in update_data:
            valid, error_message = validate_document_content(update_data['content'])
            if not valid:
                raise ValueError(f"Invalid document content: {error_message}")
        
        # Prepare update operation
        update_fields = {}
        
        # Copy allowed fields from update_data
        allowed_fields = ['title', 'description', 'content', 'tags']
        for field in allowed_fields:
            if field in update_data:
                update_fields[field] = update_data[field]
        
        # Always update updatedAt timestamp
        update_fields['updatedAt'] = datetime.utcnow()
        
        # Execute update
        result = self._collection.update_one(
            {'_id': obj_id},
            {'$set': update_fields}
        )
        
        if result.modified_count == 0:
            logger.warning(f"Document update had no effect: {document_id}")
        else:
            logger.info(f"Updated document: {document_id}")
        
        # Get updated document
        updated_doc = self.get_by_id(document_id, user_id, session_id)
        return updated_doc
    
    def delete(self, document_id: str, user_id: str = None, session_id: str = None) -> bool:
        """Deletes a document with ownership validation
        
        Args:
            document_id: ID of the document to delete
            user_id: User ID for authenticated users
            session_id: Session ID for anonymous users
            
        Returns:
            True if deleted successfully, False otherwise
            
        Raises:
            DocumentNotFoundError: If document not found
            DocumentAccessError: If user doesn't have access to the document
            ValueError: If document_id is invalid
        """
        # Validate document_id
        validate_object_id(document_id)
        obj_id = str_to_object_id(document_id)
        
        # Get current document to check authorization
        try:
            current_doc = self.get_by_id(document_id, user_id, session_id)
        except DocumentNotFoundError:
            raise
        except DocumentAccessError:
            raise
        
        # Verify ownership - require exact match of either user_id or session_id
        if user_id and current_doc.get('userId') != user_id:
            raise DocumentAccessError(document_id, user_id, None, "Only the document owner can delete it")
        
        if not user_id and session_id and current_doc.get('sessionId') != session_id:
            raise DocumentAccessError(document_id, None, session_id, "Only the session that created the document can delete it")
        
        # Execute delete
        result = self._collection.delete_one({'_id': obj_id})
        
        success = result.deleted_count > 0
        if success:
            logger.info(f"Deleted document: {document_id}")
        else:
            logger.warning(f"Failed to delete document: {document_id}")
        
        return success
    
    def search(self, query: str, user_id: str = None, session_id: str = None, 
               filters: dict = None, skip: int = 0, limit: int = 20) -> Tuple[List[dict], int]:
        """Searches for documents by text content with access control
        
        Args:
            query: Text search query
            user_id: User ID for authenticated users
            session_id: Session ID for anonymous users
            filters: Additional query filters
            skip: Number of documents to skip for pagination
            limit: Maximum number of documents to return
            
        Returns:
            Tuple of (list of matching documents, total count)
            
        Raises:
            ValueError: If neither user_id nor session_id is provided
        """
        # Ensure either user_id or session_id is provided
        if not user_id and not session_id:
            raise ValueError("Either user_id or session_id must be provided")
        
        # Build access control part of query
        access_query = {}
        if user_id:
            access_query['userId'] = user_id
        else:
            access_query['sessionId'] = session_id
        
        # Build search query
        search_query = {
            '$text': {'$search': query},
            **access_query
        }
        
        # Add additional filters if provided
        if filters:
            if 'isArchived' in filters:
                search_query['isArchived'] = filters['isArchived']
            
            if 'tags' in filters and filters['tags']:
                if isinstance(filters['tags'], list):
                    search_query['tags'] = {'$all': filters['tags']}
                else:
                    search_query['tags'] = filters['tags']
        
        # Get total count
        total_count = self._collection.count_documents(search_query)
        
        # Get paginated and sorted documents
        documents = list(self._collection.find(
            search_query,
            {
                'content': 0,  # Exclude content for listing
                'score': {'$meta': 'textScore'}  # Include text match score
            },
            skip=skip,
            limit=limit,
            sort=[('score', {'$meta': 'textScore'})]  # Sort by relevance
        ))
        
        # Format documents
        formatted_docs = []
        for doc in documents:
            # Convert ObjectId to string
            doc['_id'] = object_id_to_str(doc['_id'])
            if doc.get('currentVersionId'):
                doc['currentVersionId'] = object_id_to_str(doc['currentVersionId'])
                
            # Format datetime fields
            if doc.get('createdAt'):
                doc['createdAt'] = doc['createdAt'].isoformat()
            if doc.get('updatedAt'):
                doc['updatedAt'] = doc['updatedAt'].isoformat()
                
            formatted_docs.append(doc)
        
        logger.debug(f"Search found {len(formatted_docs)} documents for query: {query}")
        
        return formatted_docs, total_count
    
    def add_tag(self, document_id: str, tag: str, user_id: str = None, session_id: str = None) -> bool:
        """Adds a tag to a document with access control
        
        Args:
            document_id: ID of the document
            tag: Tag to add
            user_id: User ID for authenticated users
            session_id: Session ID for anonymous users
            
        Returns:
            True if tag added successfully, False otherwise
            
        Raises:
            DocumentNotFoundError: If document not found
            DocumentAccessError: If user doesn't have access to the document
            ValueError: If document_id or tag is invalid
        """
        # Validate document_id
        validate_object_id(document_id)
        obj_id = str_to_object_id(document_id)
        
        # Validate tag
        if not tag or not isinstance(tag, str):
            raise ValueError("Tag must be a non-empty string")
        
        # Get current document to check authorization
        try:
            current_doc = self.get_by_id(document_id, user_id, session_id, include_content=False)
        except DocumentNotFoundError:
            raise
        except DocumentAccessError:
            raise
        
        # Add tag using $addToSet to avoid duplicates and update timestamp
        result = self._collection.update_one(
            {'_id': obj_id},
            {
                '$addToSet': {'tags': tag},
                '$set': {'updatedAt': datetime.utcnow()}
            }
        )
        
        success = result.modified_count > 0
        if success:
            logger.info(f"Added tag '{tag}' to document: {document_id}")
        else:
            logger.debug(f"Tag '{tag}' already exists or no update made for document: {document_id}")
        
        return success
    
    def remove_tag(self, document_id: str, tag: str, user_id: str = None, session_id: str = None) -> bool:
        """Removes a tag from a document with access control
        
        Args:
            document_id: ID of the document
            tag: Tag to remove
            user_id: User ID for authenticated users
            session_id: Session ID for anonymous users
            
        Returns:
            True if tag removed successfully, False otherwise
            
        Raises:
            DocumentNotFoundError: If document not found
            DocumentAccessError: If user doesn't have access to the document
            ValueError: If document_id or tag is invalid
        """
        # Validate document_id
        validate_object_id(document_id)
        obj_id = str_to_object_id(document_id)
        
        # Validate tag
        if not tag or not isinstance(tag, str):
            raise ValueError("Tag must be a non-empty string")
        
        # Get current document to check authorization
        try:
            current_doc = self.get_by_id(document_id, user_id, session_id, include_content=False)
        except DocumentNotFoundError:
            raise
        except DocumentAccessError:
            raise
        
        # Remove tag and update timestamp
        result = self._collection.update_one(
            {'_id': obj_id},
            {
                '$pull': {'tags': tag},
                '$set': {'updatedAt': datetime.utcnow()}
            }
        )
        
        success = result.modified_count > 0
        if success:
            logger.info(f"Removed tag '{tag}' from document: {document_id}")
        else:
            logger.debug(f"Tag '{tag}' not found or no update made for document: {document_id}")
        
        return success
    
    def find_by_tags(self, tags: List[str], user_id: str = None, session_id: str = None, 
                    filters: dict = None, skip: int = 0, limit: int = 20) -> Tuple[List[dict], int]:
        """Finds documents with specific tags with access control
        
        Args:
            tags: List of tags to search for
            user_id: User ID for authenticated users
            session_id: Session ID for anonymous users
            filters: Additional query filters
            skip: Number of documents to skip for pagination
            limit: Maximum number of documents to return
            
        Returns:
            Tuple of (list of documents, total count)
            
        Raises:
            ValueError: If neither user_id nor session_id is provided
        """
        # Ensure either user_id or session_id is provided
        if not user_id and not session_id:
            raise ValueError("Either user_id or session_id must be provided")
        
        # Build access control part of query
        access_query = {}
        if user_id:
            access_query['userId'] = user_id
        else:
            access_query['sessionId'] = session_id
        
        # Build tag query
        tag_query = {
            'tags': {'$all': tags},
            **access_query
        }
        
        # Add additional filters if provided
        if filters:
            if 'isArchived' in filters:
                tag_query['isArchived'] = filters['isArchived']
        
        # Get total count
        total_count = self._collection.count_documents(tag_query)
        
        # Get paginated documents
        documents = list(self._collection.find(
            tag_query,
            {'content': 0},  # Exclude content for listing
            skip=skip,
            limit=limit,
            sort=[('updatedAt', pymongo.DESCENDING)]  # Sort by most recently updated
        ))
        
        # Format documents
        formatted_docs = []
        for doc in documents:
            # Convert ObjectId to string
            doc['_id'] = object_id_to_str(doc['_id'])
            if doc.get('currentVersionId'):
                doc['currentVersionId'] = object_id_to_str(doc['currentVersionId'])
                
            # Format datetime fields
            if doc.get('createdAt'):
                doc['createdAt'] = doc['createdAt'].isoformat()
            if doc.get('updatedAt'):
                doc['updatedAt'] = doc['updatedAt'].isoformat()
                
            formatted_docs.append(doc)
        
        logger.debug(f"Found {len(formatted_docs)} documents with tags: {tags}")
        
        return formatted_docs, total_count
    
    def archive(self, document_id: str, user_id: str) -> bool:
        """Archives a document with ownership validation
        
        Args:
            document_id: ID of the document to archive
            user_id: User ID of the document owner
            
        Returns:
            True if archived successfully, False otherwise
            
        Raises:
            DocumentNotFoundError: If document not found
            DocumentAccessError: If user doesn't have access to the document
            ValueError: If document_id or user_id is invalid
        """
        # Validate document_id
        validate_object_id(document_id)
        obj_id = str_to_object_id(document_id)
        
        # Validate user_id
        if not user_id:
            raise ValueError("User ID is required for archive operation")
        
        # Get current document to check authorization
        try:
            current_doc = self.get_by_id(document_id, user_id, None, include_content=False)
        except DocumentNotFoundError:
            raise
        except DocumentAccessError:
            raise
        
        # Verify user owns the document (not just has access)
        if current_doc.get('userId') != user_id:
            raise DocumentAccessError(document_id, user_id, None, "Only the document owner can archive it")
        
        # Execute update
        result = self._collection.update_one(
            {'_id': obj_id},
            {
                '$set': {
                    'isArchived': True,
                    'updatedAt': datetime.utcnow()
                }
            }
        )
        
        success = result.modified_count > 0
        if success:
            logger.info(f"Archived document: {document_id}")
        else:
            logger.debug(f"No update made for archive operation on document: {document_id}")
        
        return success
    
    def unarchive(self, document_id: str, user_id: str) -> bool:
        """Unarchives a document with ownership validation
        
        Args:
            document_id: ID of the document to unarchive
            user_id: User ID of the document owner
            
        Returns:
            True if unarchived successfully, False otherwise
            
        Raises:
            DocumentNotFoundError: If document not found
            DocumentAccessError: If user doesn't have access to the document
            ValueError: If document_id or user_id is invalid
        """
        # Validate document_id
        validate_object_id(document_id)
        obj_id = str_to_object_id(document_id)
        
        # Validate user_id
        if not user_id:
            raise ValueError("User ID is required for unarchive operation")
        
        # Get current document to check authorization
        try:
            current_doc = self.get_by_id(document_id, user_id, None, include_content=False)
        except DocumentNotFoundError:
            raise
        except DocumentAccessError:
            raise
        
        # Verify user owns the document (not just has access)
        if current_doc.get('userId') != user_id:
            raise DocumentAccessError(document_id, user_id, None, "Only the document owner can unarchive it")
        
        # Execute update
        result = self._collection.update_one(
            {'_id': obj_id},
            {
                '$set': {
                    'isArchived': False,
                    'updatedAt': datetime.utcnow()
                }
            }
        )
        
        success = result.modified_count > 0
        if success:
            logger.info(f"Unarchived document: {document_id}")
        else:
            logger.debug(f"No update made for unarchive operation on document: {document_id}")
        
        return success
    
    def transfer_ownership(self, document_id: str, from_user_id: str, to_user_id: str) -> bool:
        """Transfers document ownership from one user to another
        
        Args:
            document_id: ID of the document to transfer
            from_user_id: Current owner's user ID
            to_user_id: New owner's user ID
            
        Returns:
            True if transferred successfully, False otherwise
            
        Raises:
            DocumentNotFoundError: If document not found
            DocumentAccessError: If user doesn't have access to the document
            ValueError: If any parameter is invalid
        """
        # Validate parameters
        validate_object_id(document_id)
        obj_id = str_to_object_id(document_id)
        
        if not from_user_id:
            raise ValueError("Source user ID is required")
        
        if not to_user_id:
            raise ValueError("Destination user ID is required")
        
        # Get current document to check authorization
        try:
            current_doc = self.get_by_id(document_id, from_user_id, None, include_content=False)
        except DocumentNotFoundError:
            raise
        except DocumentAccessError:
            raise
        
        # Verify current user owns the document
        if current_doc.get('userId') != from_user_id:
            raise DocumentAccessError(document_id, from_user_id, None, "Only the document owner can transfer ownership")
        
        # Execute update
        result = self._collection.update_one(
            {'_id': obj_id},
            {
                '$set': {
                    'userId': to_user_id,
                    'updatedAt': datetime.utcnow()
                }
            }
        )
        
        success = result.modified_count > 0
        if success:
            logger.info(f"Transferred ownership of document {document_id} from user {from_user_id} to {to_user_id}")
        else:
            logger.warning(f"Failed to transfer ownership of document {document_id}")
        
        return success
    
    def transfer_anonymous_document(self, document_id: str, session_id: str, user_id: str) -> bool:
        """Transfers an anonymous document to a registered user
        
        Args:
            document_id: ID of the document to transfer
            session_id: Session ID of the anonymous user
            user_id: User ID of the registered user
            
        Returns:
            True if transferred successfully, False otherwise
            
        Raises:
            DocumentNotFoundError: If document not found
            DocumentAccessError: If session doesn't have access to the document
            ValueError: If any parameter is invalid
        """
        # Validate parameters
        validate_object_id(document_id)
        obj_id = str_to_object_id(document_id)
        
        if not session_id:
            raise ValueError("Session ID is required")
        
        if not user_id:
            raise ValueError("User ID is required")
        
        # Get current document to check authorization
        try:
            current_doc = self.get_by_id(document_id, None, session_id, include_content=False)
        except DocumentNotFoundError:
            raise
        except DocumentAccessError:
            raise
        
        # Verify document is from the anonymous session
        if current_doc.get('sessionId') != session_id:
            raise DocumentAccessError(document_id, None, session_id, "Document does not belong to this session")
        
        # Execute update
        result = self._collection.update_one(
            {'_id': obj_id},
            {
                '$set': {
                    'userId': user_id,
                    'updatedAt': datetime.utcnow()
                },
                '$unset': {
                    'sessionId': ""
                }
            }
        )
        
        success = result.modified_count > 0
        if success:
            logger.info(f"Transferred anonymous document {document_id} from session {session_id} to user {user_id}")
        else:
            logger.warning(f"Failed to transfer anonymous document {document_id}")
        
        return success
    
    def transfer_all_anonymous_documents(self, session_id: str, user_id: str) -> int:
        """Transfers all documents from an anonymous session to a registered user
        
        Args:
            session_id: Session ID of the anonymous user
            user_id: User ID of the registered user
            
        Returns:
            Number of documents transferred
            
        Raises:
            ValueError: If any parameter is invalid
        """
        # Validate parameters
        if not session_id:
            raise ValueError("Session ID is required")
        
        if not user_id:
            raise ValueError("User ID is required")
        
        # Execute batch update
        result = self._collection.update_many(
            {'sessionId': session_id},
            {
                '$set': {
                    'userId': user_id,
                    'updatedAt': datetime.utcnow()
                },
                '$unset': {
                    'sessionId': ""
                }
            }
        )
        
        count = result.modified_count
        if count > 0:
            logger.info(f"Transferred {count} anonymous documents from session {session_id} to user {user_id}")
        else:
            logger.debug(f"No documents found to transfer from session {session_id}")
        
        return count
    
    def update_current_version(self, document_id: str, version_id: str) -> bool:
        """Updates the currentVersionId of a document
        
        Args:
            document_id: ID of the document
            version_id: ID of the version to set as current
            
        Returns:
            True if updated successfully, False otherwise
            
        Raises:
            ValueError: If document_id or version_id is invalid
        """
        # Validate parameters
        validate_object_id(document_id)
        obj_id = str_to_object_id(document_id)
        
        validate_object_id(version_id)
        version_obj_id = str_to_object_id(version_id)
        
        # Execute update
        result = self._collection.update_one(
            {'_id': obj_id},
            {
                '$set': {
                    'currentVersionId': version_obj_id,
                    'updatedAt': datetime.utcnow()
                }
            }
        )
        
        success = result.modified_count > 0
        if success:
            logger.info(f"Updated current version of document {document_id} to version {version_id}")
        else:
            logger.warning(f"Failed to update current version of document {document_id}")
        
        return success
    
    def cleanup_expired_sessions(self) -> int:
        """Removes documents from expired anonymous sessions
        
        Returns:
            Number of documents cleaned up
        """
        # Calculate expiry threshold
        expiry_threshold = datetime.utcnow() - timedelta(seconds=ANONYMOUS_SESSION_TTL)
        
        # Find and delete documents from expired sessions
        result = self._collection.delete_many({
            'sessionId': {'$ne': None},  # Has a session ID (anonymous)
            'userId': None,              # Not claimed by a user
            'createdAt': {'$lt': expiry_threshold}  # Older than threshold
        })
        
        count = result.deleted_count
        if count > 0:
            logger.info(f"Cleaned up {count} documents from expired anonymous sessions")
        else:
            logger.debug("No expired anonymous documents found to clean up")
        
        return count