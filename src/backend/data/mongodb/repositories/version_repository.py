"""
MongoDB repository implementation for document version management in the AI writing enhancement platform.
Handles storage, retrieval, and lifecycle management of document versions to support the track changes
functionality and AI suggestion review system.
"""

import datetime
import enum
import pymongo
from pymongo.errors import PyMongoError
import bson
import typing

from ..connection import get_collection, str_to_object_id, object_id_to_str
from ...core.utils.logger import get_logger
from ...core.utils.validators import validate_object_id

# Configure logger
logger = get_logger(__name__)

# Retention policy settings (None = keep forever)
MAJOR_VERSION_RETENTION = None  # Major versions are kept indefinitely
MINOR_VERSION_RETENTION_DAYS = 1  # Minor versions (auto-save) kept for 1 day
AI_SUGGESTION_RETENTION_DAYS = 7  # AI suggestions kept for 7 days


class VersionType(enum.Enum):
    """Enumeration of document version types for categorization and retention policies"""
    MAJOR = 1  # Explicit user saves
    MINOR = 2  # Auto-save versions
    AI_SUGGESTION = 3  # AI-generated suggestions


class VersionRepository:
    """MongoDB repository for document version operations with support for different version
    types and lifecycle management"""
    
    COLLECTION_NAME = "document_versions"
    
    def __init__(self):
        """Initializes the version repository with MongoDB collection"""
        self._collection = get_collection(self.COLLECTION_NAME)
        
        # Create indexes for efficient querying
        self._collection.create_index("documentId")
        self._collection.create_index([("documentId", pymongo.ASCENDING), ("versionNumber", pymongo.DESCENDING)])
        self._collection.create_index("createdAt")
        self._collection.create_index("userId")
        self._collection.create_index("sessionId")
        self._collection.create_index("type")
        self._collection.create_index([("documentId", pymongo.ASCENDING), ("type", pymongo.ASCENDING)])
        
        logger.info(f"Initialized version repository with collection: {self.COLLECTION_NAME}")
    
    def create_version(self, version_data: typing.Dict[str, typing.Any]) -> typing.Dict[str, typing.Any]:
        """Creates a new document version in the database
        
        Args:
            version_data: Dictionary containing version details including:
                - documentId: ID of the document
                - content: Document content for this version
                - type: Version type (from VersionType enum)
                - userId: User ID (optional)
                - sessionId: Session ID (for anonymous users, optional)
                - metadata: Additional metadata (optional)
                
        Returns:
            The created version with generated ID and metadata
            
        Raises:
            ValueError: If required fields are missing
            PyMongoError: If database operation fails
        """
        # Validate required fields
        if 'documentId' not in version_data:
            raise ValueError("documentId is required")
        
        # Convert string document ID to ObjectId if needed
        if isinstance(version_data['documentId'], str):
            version_data['documentId'] = str_to_object_id(version_data['documentId'])
        
        # Get the next version number for this document
        next_version = self._get_next_version_number(version_data['documentId'])
        
        # Prepare version document
        version = {
            'documentId': version_data['documentId'],
            'versionNumber': next_version,
            'content': version_data.get('content', ''),
            'createdAt': datetime.datetime.utcnow(),
            'type': version_data.get('type', VersionType.MAJOR.value),
        }
        
        # Add optional fields if present
        if 'userId' in version_data:
            version['userId'] = version_data['userId']
        
        if 'sessionId' in version_data:
            version['sessionId'] = version_data['sessionId']
        
        if 'metadata' in version_data:
            version['metadata'] = version_data['metadata']
        
        # Add previous version ID if provided
        if 'previousVersionId' in version_data:
            # Convert string ID to ObjectId if needed
            if isinstance(version_data['previousVersionId'], str):
                version['previousVersionId'] = str_to_object_id(version_data['previousVersionId'])
            else:
                version['previousVersionId'] = version_data['previousVersionId']
        
        try:
            # Insert version into database
            result = self._collection.insert_one(version)
            version['_id'] = result.inserted_id
            
            # Convert ObjectId to string for response
            version_with_string_id = self._format_version(version)
            
            logger.info(f"Created version {next_version} for document {version_data['documentId']}")
            return version_with_string_id
        
        except PyMongoError as e:
            logger.error(f"Failed to create version: {str(e)}")
            raise
    
    def get_version(self, version_id: str) -> typing.Dict[str, typing.Any]:
        """Retrieves a specific document version by its ID
        
        Args:
            version_id: The version ID
            
        Returns:
            The version data including content and metadata
            
        Raises:
            ValueError: If version_id is invalid
            VersionNotFoundError: If version not found
        """
        # Validate version ID format
        validate_object_id(version_id)
        
        # Convert to ObjectId
        version_oid = str_to_object_id(version_id)
        
        # Query the database
        version = self._collection.find_one({"_id": version_oid})
        
        # Check if version exists
        if not version:
            logger.warning(f"Version not found: {version_id}")
            raise VersionNotFoundError(version_id)
        
        # Format version for response (convert ObjectIds to strings)
        formatted_version = self._format_version(version)
        
        logger.debug(f"Retrieved version: {version_id}")
        return formatted_version
    
    def get_versions_by_document(self, document_id: str, version_type: typing.Optional[VersionType] = None, 
                               limit: int = 10, skip: int = 0) -> typing.Tuple[typing.List[typing.Dict[str, typing.Any]], int]:
        """Retrieves versions associated with a specific document
        
        Args:
            document_id: The document ID
            version_type: Filter by version type (optional)
            limit: Maximum number of versions to return
            skip: Number of versions to skip (for pagination)
            
        Returns:
            Tuple of (list of versions, total count)
            
        Raises:
            ValueError: If document_id is invalid
        """
        # Validate document ID format
        validate_object_id(document_id)
        
        # Convert to ObjectId
        document_oid = str_to_object_id(document_id)
        
        # Build query
        query = {"documentId": document_oid}
        
        # Add type filter if provided
        if version_type is not None:
            query["type"] = version_type.value
        
        # Get total count
        total_count = self._collection.count_documents(query)
        
        # Get versions with pagination
        versions = list(self._collection.find(
            query,
            sort=[("versionNumber", pymongo.DESCENDING)],
            skip=skip,
            limit=limit
        ))
        
        # Format versions for response
        formatted_versions = [self._format_version(version) for version in versions]
        
        logger.debug(f"Retrieved {len(formatted_versions)} versions for document {document_id}")
        return formatted_versions, total_count
    
    def get_latest_version(self, document_id: str, version_type: typing.Optional[VersionType] = None) -> typing.Optional[typing.Dict[str, typing.Any]]:
        """Gets the latest version of a document, optionally filtered by version type
        
        Args:
            document_id: The document ID
            version_type: Filter by version type (optional)
            
        Returns:
            Latest version data or None if no versions exist
            
        Raises:
            ValueError: If document_id is invalid
        """
        # Validate document ID format
        validate_object_id(document_id)
        
        # Convert to ObjectId
        document_oid = str_to_object_id(document_id)
        
        # Build query
        query = {"documentId": document_oid}
        
        # Add type filter if provided
        if version_type is not None:
            query["type"] = version_type.value
        
        # Get latest version
        version = self._collection.find_one(
            query,
            sort=[("versionNumber", pymongo.DESCENDING)]
        )
        
        # Check if version exists
        if not version:
            logger.debug(f"No versions found for document {document_id}")
            return None
        
        # Format version for response
        formatted_version = self._format_version(version)
        
        logger.debug(f"Retrieved latest version {formatted_version['versionNumber']} for document {document_id}")
        return formatted_version
    
    def get_version_history(self, document_id: str, limit: int = 10, skip: int = 0,
                          version_type: typing.Optional[VersionType] = None) -> typing.Tuple[typing.List[typing.Dict[str, typing.Any]], int]:
        """Retrieves version history for a document with pagination
        
        This method is similar to get_versions_by_document but excludes content
        for performance when only metadata is needed.
        
        Args:
            document_id: The document ID
            limit: Maximum number of versions to return
            skip: Number of versions to skip (for pagination)
            version_type: Filter by version type (optional)
            
        Returns:
            Tuple of (list of version metadata, total count)
            
        Raises:
            ValueError: If document_id is invalid
        """
        # Validate document ID format
        validate_object_id(document_id)
        
        # Convert to ObjectId
        document_oid = str_to_object_id(document_id)
        
        # Build query
        query = {"documentId": document_oid}
        
        # Add type filter if provided
        if version_type is not None:
            query["type"] = version_type.value
        
        # Get total count
        total_count = self._collection.count_documents(query)
        
        # Get versions with pagination, excluding content
        projection = {"content": 0}
        versions = list(self._collection.find(
            query,
            projection=projection,
            sort=[("versionNumber", pymongo.DESCENDING)],
            skip=skip,
            limit=limit
        ))
        
        # Format versions for response
        formatted_versions = [self._format_version(version) for version in versions]
        
        logger.debug(f"Retrieved {len(formatted_versions)} version history entries for document {document_id}")
        return formatted_versions, total_count
    
    def delete_version(self, version_id: str) -> bool:
        """Deletes a specific document version by ID
        
        Args:
            version_id: The version ID
            
        Returns:
            True if deleted successfully, False otherwise
            
        Raises:
            ValueError: If version_id is invalid
        """
        # Validate version ID format
        validate_object_id(version_id)
        
        # Convert to ObjectId
        version_oid = str_to_object_id(version_id)
        
        try:
            # Delete version
            result = self._collection.delete_one({"_id": version_oid})
            success = result.deleted_count > 0
            
            if success:
                logger.info(f"Deleted version: {version_id}")
            else:
                logger.warning(f"Version not found for deletion: {version_id}")
            
            return success
        
        except PyMongoError as e:
            logger.error(f"Failed to delete version {version_id}: {str(e)}")
            return False
    
    def update_version_metadata(self, version_id: str, metadata: typing.Dict[str, typing.Any]) -> bool:
        """Updates metadata for a specific version
        
        Args:
            version_id: The version ID
            metadata: Dictionary of metadata to update
            
        Returns:
            True if updated successfully, False otherwise
            
        Raises:
            ValueError: If version_id is invalid
        """
        # Validate version ID format
        validate_object_id(version_id)
        
        # Convert to ObjectId
        version_oid = str_to_object_id(version_id)
        
        try:
            # Prepare update operation
            update = {
                "$set": {f"metadata.{key}": value for key, value in metadata.items()}
            }
            
            # Update version
            result = self._collection.update_one({"_id": version_oid}, update)
            success = result.modified_count > 0
            
            if success:
                logger.info(f"Updated metadata for version: {version_id}")
            else:
                logger.warning(f"Version not found for metadata update: {version_id}")
            
            return success
        
        except PyMongoError as e:
            logger.error(f"Failed to update version metadata {version_id}: {str(e)}")
            return False
    
    def cleanup_minor_versions(self, document_id: str, retention_hours: int = 24) -> int:
        """Removes old minor versions according to retention policy
        
        Args:
            document_id: The document ID
            retention_hours: Number of hours to retain minor versions
            
        Returns:
            Number of versions deleted
            
        Raises:
            ValueError: If document_id is invalid
        """
        # Calculate cutoff timestamp
        cutoff_timestamp = datetime.datetime.utcnow() - datetime.timedelta(hours=retention_hours)
        
        # Convert to ObjectId if it's a string
        if isinstance(document_id, str):
            document_id = str_to_object_id(document_id)
        
        try:
            # Delete old minor versions
            result = self._collection.delete_many({
                "documentId": document_id,
                "type": VersionType.MINOR.value,
                "createdAt": {"$lt": cutoff_timestamp}
            })
            
            deleted_count = result.deleted_count
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} minor versions for document {document_id}")
            
            return deleted_count
        
        except PyMongoError as e:
            logger.error(f"Failed to cleanup minor versions: {str(e)}")
            return 0
    
    def cleanup_ai_suggestions(self, document_id: str, retention_days: int = AI_SUGGESTION_RETENTION_DAYS) -> int:
        """Removes old rejected AI suggestions according to retention policy
        
        Args:
            document_id: The document ID
            retention_days: Number of days to retain AI suggestions
            
        Returns:
            Number of suggestions deleted
            
        Raises:
            ValueError: If document_id is invalid
        """
        # Calculate cutoff timestamp
        cutoff_timestamp = datetime.datetime.utcnow() - datetime.timedelta(days=retention_days)
        
        # Convert to ObjectId if it's a string
        if isinstance(document_id, str):
            document_id = str_to_object_id(document_id)
        
        try:
            # Delete old AI suggestions that were rejected
            result = self._collection.delete_many({
                "documentId": document_id,
                "type": VersionType.AI_SUGGESTION.value,
                "createdAt": {"$lt": cutoff_timestamp},
                "metadata.status": "rejected"
            })
            
            deleted_count = result.deleted_count
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} rejected AI suggestions for document {document_id}")
            
            return deleted_count
        
        except PyMongoError as e:
            logger.error(f"Failed to cleanup AI suggestions: {str(e)}")
            return 0
    
    def transfer_version_ownership(self, document_id: str, session_id: str, user_id: str) -> int:
        """Transfers ownership of document versions from anonymous session to user
        
        Args:
            document_id: The document ID
            session_id: The anonymous session ID
            user_id: The user ID to transfer versions to
            
        Returns:
            Number of versions transferred
            
        Raises:
            ValueError: If document_id, session_id, or user_id is invalid
        """
        if not document_id or not session_id or not user_id:
            raise ValueError("document_id, session_id, and user_id are required")
        
        # Convert to ObjectId if it's a string
        if isinstance(document_id, str):
            document_id = str_to_object_id(document_id)
        
        try:
            # Update versions to transfer ownership
            result = self._collection.update_many(
                {
                    "documentId": document_id,
                    "sessionId": session_id
                },
                {
                    "$set": {"userId": user_id},
                    "$unset": {"sessionId": ""}
                }
            )
            
            transferred_count = result.modified_count
            
            if transferred_count > 0:
                logger.info(f"Transferred {transferred_count} versions from session {session_id} to user {user_id}")
            
            return transferred_count
        
        except PyMongoError as e:
            logger.error(f"Failed to transfer version ownership: {str(e)}")
            return 0
    
    def get_version_count(self, document_id: str, version_type: typing.Optional[VersionType] = None) -> int:
        """Gets the total count of versions for a document by type
        
        Args:
            document_id: The document ID
            version_type: Filter by version type (optional)
            
        Returns:
            Number of versions
            
        Raises:
            ValueError: If document_id is invalid
        """
        # Validate document ID format
        validate_object_id(document_id)
        
        # Convert to ObjectId
        document_oid = str_to_object_id(document_id)
        
        # Build query
        query = {"documentId": document_oid}
        
        # Add type filter if provided
        if version_type is not None:
            query["type"] = version_type.value
        
        # Get count
        count = self._collection.count_documents(query)
        
        logger.debug(f"Found {count} versions for document {document_id}")
        return count
    
    def get_version_by_number(self, document_id: str, version_number: int) -> typing.Optional[typing.Dict[str, typing.Any]]:
        """Retrieves a specific version by its version number
        
        Args:
            document_id: The document ID
            version_number: The version number
            
        Returns:
            Version data or None if not found
            
        Raises:
            ValueError: If document_id is invalid
        """
        # Validate document ID format
        validate_object_id(document_id)
        
        # Convert to ObjectId
        document_oid = str_to_object_id(document_id)
        
        # Query the database
        version = self._collection.find_one({
            "documentId": document_oid,
            "versionNumber": version_number
        })
        
        # Check if version exists
        if not version:
            logger.debug(f"Version {version_number} not found for document {document_id}")
            return None
        
        # Format version for response
        formatted_version = self._format_version(version)
        
        logger.debug(f"Retrieved version {version_number} for document {document_id}")
        return formatted_version
    
    def get_ai_suggestion_versions(self, document_id: str, status: typing.Optional[str] = None) -> typing.List[typing.Dict[str, typing.Any]]:
        """Retrieves AI suggestion versions for a document with optional status filter
        
        Args:
            document_id: The document ID
            status: Filter by suggestion status ("pending", "accepted", "rejected")
            
        Returns:
            List of AI suggestion versions
            
        Raises:
            ValueError: If document_id is invalid
        """
        # Validate document ID format
        validate_object_id(document_id)
        
        # Convert to ObjectId
        document_oid = str_to_object_id(document_id)
        
        # Build query
        query = {
            "documentId": document_oid,
            "type": VersionType.AI_SUGGESTION.value
        }
        
        # Add status filter if provided
        if status:
            query["metadata.status"] = status
        
        # Get AI suggestion versions
        versions = list(self._collection.find(
            query,
            sort=[("createdAt", pymongo.DESCENDING)]
        ))
        
        # Format versions for response
        formatted_versions = [self._format_version(version) for version in versions]
        
        logger.debug(f"Retrieved {len(formatted_versions)} AI suggestion versions for document {document_id}")
        return formatted_versions
    
    def mark_suggestion_status(self, version_id: str, status: str) -> bool:
        """Updates the status of an AI suggestion version
        
        Args:
            version_id: The version ID
            status: The new status ("pending", "accepted", "rejected")
            
        Returns:
            True if updated successfully, False otherwise
            
        Raises:
            ValueError: If version_id is invalid or status is invalid
        """
        # Validate version ID format
        validate_object_id(version_id)
        
        # Validate status
        valid_statuses = ["pending", "accepted", "rejected"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
        
        # Convert to ObjectId
        version_oid = str_to_object_id(version_id)
        
        try:
            # Update version status
            result = self._collection.update_one(
                {"_id": version_oid},
                {"$set": {"metadata.status": status}}
            )
            
            success = result.modified_count > 0
            
            if success:
                logger.info(f"Updated version {version_id} status to {status}")
            else:
                logger.warning(f"Version not found for status update: {version_id}")
            
            return success
        
        except PyMongoError as e:
            logger.error(f"Failed to update version status {version_id}: {str(e)}")
            return False
    
    def _get_next_version_number(self, document_id: bson.ObjectId) -> int:
        """Determines the next version number for a document
        
        Args:
            document_id: The document ID
            
        Returns:
            Next version number (starting at 1)
        """
        # Find the latest version for this document
        latest_version = self._collection.find_one(
            {"documentId": document_id},
            sort=[("versionNumber", pymongo.DESCENDING)],
            projection={"versionNumber": 1}
        )
        
        # If no versions exist, start at 1
        if not latest_version:
            return 1
        
        # Otherwise, increment the latest version number
        return latest_version["versionNumber"] + 1
    
    def _format_version(self, version: typing.Dict[str, typing.Any]) -> typing.Dict[str, typing.Any]:
        """Formats a version document for API response
        
        Args:
            version: The version document from MongoDB
            
        Returns:
            Formatted version with string IDs and ISO format dates
        """
        # Create a copy to avoid modifying the original
        formatted = version.copy()
        
        # Convert ObjectId to string
        if '_id' in formatted:
            formatted['_id'] = object_id_to_str(formatted['_id'])
        
        if 'documentId' in formatted:
            formatted['documentId'] = object_id_to_str(formatted['documentId'])
        
        if 'userId' in formatted and isinstance(formatted['userId'], bson.ObjectId):
            formatted['userId'] = object_id_to_str(formatted['userId'])
        
        if 'previousVersionId' in formatted and isinstance(formatted['previousVersionId'], bson.ObjectId):
            formatted['previousVersionId'] = object_id_to_str(formatted['previousVersionId'])
        
        # Format dates as ISO strings
        if 'createdAt' in formatted:
            formatted['createdAt'] = formatted['createdAt'].isoformat()
        
        return formatted


class VersionNotFoundError(Exception):
    """Exception raised when a requested version cannot be found"""
    
    def __init__(self, version_id: str, message: str = None):
        """Initializes the version not found error
        
        Args:
            version_id: The version ID that wasn't found
            message: Optional custom error message
        """
        if message is None:
            message = f"Version not found with ID: {version_id}"
        super().__init__(message)
        self.version_id = version_id


class VersionAccessError(Exception):
    """Exception raised when a user doesn't have permission to access a version"""
    
    def __init__(self, version_id: str, user_id: str = None, session_id: str = None, message: str = None):
        """Initializes the version access error
        
        Args:
            version_id: The version ID
            user_id: The user ID that attempted access
            session_id: The session ID that attempted access
            message: Optional custom error message
        """
        if message is None:
            message = f"Access denied to version: {version_id}"
        super().__init__(message)
        self.version_id = version_id
        self.user_id = user_id
        self.session_id = session_id