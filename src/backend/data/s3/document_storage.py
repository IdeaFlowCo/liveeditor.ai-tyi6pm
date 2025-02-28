"""
Document storage module for the AI writing enhancement platform.

This module implements document storage functionality using AWS S3, providing methods for 
storing, retrieving, and managing document content in the cloud with appropriate security,
versioning, and error handling capabilities.
"""

import os  # standard library
import datetime  # standard library
import uuid  # standard library
import typing  # standard library
import io  # standard library
from botocore.exceptions import ClientError  # boto3 ~=1.26.0

from .connection import (
    get_s3_client, 
    get_s3_resource, 
    ensure_bucket_exists, 
    create_presigned_url, 
    with_retry, 
    S3ConnectionError
)
from ...core.utils.logger import get_logger
from ...core.utils.validators import validate_document_content, is_valid_document_format

# Initialize logger
logger = get_logger(__name__)

# Constants
DEFAULT_BUCKET_NAME = os.environ.get('DOCUMENT_STORAGE_BUCKET', 'ai-writing-documents')
DEFAULT_REGION = os.environ.get('AWS_REGION', 'us-east-1')
URL_EXPIRATION = 3600  # Default expiration for presigned URLs (1 hour)
DOCUMENT_PREFIX = 'documents/'
VERSION_PREFIX = 'versions/'


class DocumentStorageError(Exception):
    """Custom exception for document storage operations."""
    
    def __init__(self, message, original_error=None):
        """
        Initialize DocumentStorageError with message and original error.
        
        Args:
            message (str): Error message
            original_error (Exception): Original exception that caused this error
        """
        super().__init__(message)
        self.original_exception = original_error


class DocumentNotFoundError(Exception):
    """Exception raised when document is not found in storage."""
    
    def __init__(self, document_id, user_id=None, session_id=None, message=None):
        """
        Initialize DocumentNotFoundError with document details.
        
        Args:
            document_id (str): ID of the document that was not found
            user_id (str, optional): User ID associated with the document
            session_id (str, optional): Session ID for anonymous users
            message (str, optional): Custom error message
        """
        if message is None:
            message = f"Document {document_id} not found"
        super().__init__(message)
        self.document_id = document_id
        self.user_id = user_id
        self.session_id = session_id


def generate_document_key(document_id, user_id=None, session_id=None):
    """
    Generates a unique S3 object key for a document.
    
    Args:
        document_id (str): Unique document identifier
        user_id (str, optional): User ID for authenticated users
        session_id (str, optional): Session ID for anonymous users
        
    Returns:
        str: Unique S3 object key for the document
        
    Raises:
        ValueError: If neither user_id nor session_id is provided
    """
    # Validate that either user_id or session_id is provided
    if not user_id and not session_id:
        raise ValueError("Either user_id or session_id must be provided")
    
    # Determine owner identifier (user_id for authenticated, session_id for anonymous)
    owner_id = user_id if user_id else f"session_{session_id}"
    
    # Generate and return formatted key
    return f"{DOCUMENT_PREFIX}{owner_id}/{document_id}"


def generate_version_key(document_id, version_id, user_id=None, session_id=None):
    """
    Generates a unique S3 object key for a document version.
    
    Args:
        document_id (str): Unique document identifier
        version_id (str): Unique version identifier
        user_id (str, optional): User ID for authenticated users
        session_id (str, optional): Session ID for anonymous users
        
    Returns:
        str: Unique S3 object key for the document version
        
    Raises:
        ValueError: If neither user_id nor session_id is provided
    """
    # Validate that either user_id or session_id is provided
    if not user_id and not session_id:
        raise ValueError("Either user_id or session_id must be provided")
    
    # Determine owner identifier (user_id for authenticated, session_id for anonymous)
    owner_id = user_id if user_id else f"session_{session_id}"
    
    # Generate and return formatted key
    return f"{VERSION_PREFIX}{owner_id}/{document_id}/{version_id}"


@with_retry(max_attempts=3, backoff_factor=2)
def store_document(document_id, content, user_id=None, session_id=None, 
                  content_type="text/plain", metadata=None, 
                  bucket_name=DEFAULT_BUCKET_NAME, region=DEFAULT_REGION):
    """
    Stores document content in S3.
    
    Args:
        document_id (str): Unique document identifier
        content (str): Document content to store
        user_id (str, optional): User ID for authenticated users
        session_id (str, optional): Session ID for anonymous users
        content_type (str): MIME type of the document
        metadata (dict, optional): Additional metadata for the document
        bucket_name (str): S3 bucket name
        region (str): AWS region
        
    Returns:
        dict: Storage result with metadata
        
    Raises:
        DocumentStorageError: If storage operation fails
        ValueError: If validation fails
    """
    try:
        # Validate document content
        is_valid, error_message = validate_document_content(content)
        if not is_valid:
            raise ValueError(f"Invalid document content: {error_message}")
        
        # Ensure S3 bucket exists
        ensure_bucket_exists(bucket_name, region)
        
        # Generate document key
        key = generate_document_key(document_id, user_id, session_id)
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        
        # Add standard metadata
        upload_timestamp = datetime.datetime.utcnow().isoformat()
        metadata.update({
            'document_id': document_id,
            'upload_timestamp': upload_timestamp,
            'content_type': content_type
        })
        if user_id:
            metadata['user_id'] = user_id
        if session_id:
            metadata['session_id'] = session_id
        
        # Get S3 client
        s3_client = get_s3_client()
        
        # Upload content to S3
        response = s3_client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=content,
            ContentType=content_type,
            Metadata=metadata
        )
        
        logger.info(f"Document stored successfully", 
                   document_id=document_id, 
                   user_id=user_id,
                   session_id=session_id,
                   s3_key=key)
        
        # Return storage info
        return {
            'document_id': document_id,
            's3_key': key,
            'etag': response.get('ETag', '').strip('"'),
            'upload_timestamp': upload_timestamp,
            'metadata': metadata
        }
        
    except ValueError as e:
        # Re-raise validation errors
        raise
    except S3ConnectionError as e:
        logger.error(f"S3 connection error storing document", 
                    document_id=document_id, error=str(e), exc_info=True)
        raise DocumentStorageError(f"Failed to store document: {str(e)}", e)
    except Exception as e:
        logger.error(f"Error storing document", 
                    document_id=document_id, error=str(e), exc_info=True)
        raise DocumentStorageError(f"Failed to store document: {str(e)}", e)


@with_retry(max_attempts=3, backoff_factor=2)
def retrieve_document(document_id, user_id=None, session_id=None, 
                     bucket_name=DEFAULT_BUCKET_NAME, region=DEFAULT_REGION):
    """
    Retrieves document content from S3.
    
    Args:
        document_id (str): Unique document identifier
        user_id (str, optional): User ID for authenticated users
        session_id (str, optional): Session ID for anonymous users
        bucket_name (str): S3 bucket name
        region (str): AWS region
        
    Returns:
        dict: Document content and metadata
        
    Raises:
        DocumentNotFoundError: If document not found
        DocumentStorageError: If retrieval operation fails
    """
    try:
        # Generate document key
        key = generate_document_key(document_id, user_id, session_id)
        
        # Get S3 client
        s3_client = get_s3_client()
        
        # Retrieve object from S3
        try:
            response = s3_client.get_object(
                Bucket=bucket_name,
                Key=key
            )
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == 'NoSuchKey':
                raise DocumentNotFoundError(document_id, user_id, session_id)
            raise
        
        # Read content from response
        content = response['Body'].read().decode('utf-8')
        
        # Extract metadata
        metadata = response.get('Metadata', {})
        content_type = response.get('ContentType', 'text/plain')
        last_modified = response.get('LastModified')
        
        logger.info(f"Document retrieved successfully", 
                   document_id=document_id, 
                   user_id=user_id,
                   session_id=session_id,
                   s3_key=key)
        
        # Return document data
        return {
            'document_id': document_id,
            'content': content,
            'content_type': content_type,
            'last_modified': last_modified.isoformat() if last_modified else None,
            'metadata': metadata,
            's3_key': key
        }
        
    except DocumentNotFoundError:
        # Re-raise DocumentNotFoundError
        raise
    except S3ConnectionError as e:
        logger.error(f"S3 connection error retrieving document", 
                    document_id=document_id, error=str(e), exc_info=True)
        raise DocumentStorageError(f"Failed to retrieve document: {str(e)}", e)
    except Exception as e:
        logger.error(f"Error retrieving document", 
                    document_id=document_id, error=str(e), exc_info=True)
        raise DocumentStorageError(f"Failed to retrieve document: {str(e)}", e)


@with_retry(max_attempts=3, backoff_factor=2)
def store_document_version(document_id, version_id, content, user_id=None, session_id=None, 
                          content_type="text/plain", metadata=None, 
                          bucket_name=DEFAULT_BUCKET_NAME, region=DEFAULT_REGION):
    """
    Stores a specific version of document content in S3.
    
    Args:
        document_id (str): Unique document identifier
        version_id (str): Unique version identifier
        content (str): Document content to store
        user_id (str, optional): User ID for authenticated users
        session_id (str, optional): Session ID for anonymous users
        content_type (str): MIME type of the document
        metadata (dict, optional): Additional metadata for the document
        bucket_name (str): S3 bucket name
        region (str): AWS region
        
    Returns:
        dict: Storage result with metadata
        
    Raises:
        DocumentStorageError: If storage operation fails
        ValueError: If validation fails
    """
    try:
        # Validate document content
        is_valid, error_message = validate_document_content(content)
        if not is_valid:
            raise ValueError(f"Invalid document content: {error_message}")
        
        # Ensure S3 bucket exists
        ensure_bucket_exists(bucket_name, region)
        
        # Generate version key
        key = generate_version_key(document_id, version_id, user_id, session_id)
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        
        # Add standard metadata
        upload_timestamp = datetime.datetime.utcnow().isoformat()
        metadata.update({
            'document_id': document_id,
            'version_id': version_id,
            'upload_timestamp': upload_timestamp,
            'content_type': content_type
        })
        if user_id:
            metadata['user_id'] = user_id
        if session_id:
            metadata['session_id'] = session_id
        
        # Get S3 client
        s3_client = get_s3_client()
        
        # Upload content to S3
        response = s3_client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=content,
            ContentType=content_type,
            Metadata=metadata
        )
        
        logger.info(f"Document version stored successfully", 
                   document_id=document_id,
                   version_id=version_id,
                   user_id=user_id,
                   session_id=session_id,
                   s3_key=key)
        
        # Return storage info
        return {
            'document_id': document_id,
            'version_id': version_id,
            's3_key': key,
            'etag': response.get('ETag', '').strip('"'),
            'upload_timestamp': upload_timestamp,
            'metadata': metadata
        }
        
    except ValueError as e:
        # Re-raise validation errors
        raise
    except S3ConnectionError as e:
        logger.error(f"S3 connection error storing document version", 
                    document_id=document_id, 
                    version_id=version_id,
                    error=str(e), 
                    exc_info=True)
        raise DocumentStorageError(f"Failed to store document version: {str(e)}", e)
    except Exception as e:
        logger.error(f"Error storing document version", 
                    document_id=document_id,
                    version_id=version_id,
                    error=str(e), 
                    exc_info=True)
        raise DocumentStorageError(f"Failed to store document version: {str(e)}", e)


@with_retry(max_attempts=3, backoff_factor=2)
def retrieve_document_version(document_id, version_id, user_id=None, session_id=None, 
                             bucket_name=DEFAULT_BUCKET_NAME, region=DEFAULT_REGION):
    """
    Retrieves a specific version of document content from S3.
    
    Args:
        document_id (str): Unique document identifier
        version_id (str): Unique version identifier
        user_id (str, optional): User ID for authenticated users
        session_id (str, optional): Session ID for anonymous users
        bucket_name (str): S3 bucket name
        region (str): AWS region
        
    Returns:
        dict: Document version content and metadata
        
    Raises:
        DocumentNotFoundError: If document version not found
        DocumentStorageError: If retrieval operation fails
    """
    try:
        # Generate version key
        key = generate_version_key(document_id, version_id, user_id, session_id)
        
        # Get S3 client
        s3_client = get_s3_client()
        
        # Retrieve object from S3
        try:
            response = s3_client.get_object(
                Bucket=bucket_name,
                Key=key
            )
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == 'NoSuchKey':
                raise DocumentNotFoundError(
                    document_id, 
                    user_id, 
                    session_id, 
                    f"Document version {version_id} not found"
                )
            raise
        
        # Read content from response
        content = response['Body'].read().decode('utf-8')
        
        # Extract metadata
        metadata = response.get('Metadata', {})
        content_type = response.get('ContentType', 'text/plain')
        last_modified = response.get('LastModified')
        
        logger.info(f"Document version retrieved successfully", 
                   document_id=document_id,
                   version_id=version_id,
                   user_id=user_id,
                   session_id=session_id,
                   s3_key=key)
        
        # Return document version data
        return {
            'document_id': document_id,
            'version_id': version_id,
            'content': content,
            'content_type': content_type,
            'last_modified': last_modified.isoformat() if last_modified else None,
            'metadata': metadata,
            's3_key': key
        }
        
    except DocumentNotFoundError:
        # Re-raise DocumentNotFoundError
        raise
    except S3ConnectionError as e:
        logger.error(f"S3 connection error retrieving document version", 
                    document_id=document_id,
                    version_id=version_id,
                    error=str(e), 
                    exc_info=True)
        raise DocumentStorageError(f"Failed to retrieve document version: {str(e)}", e)
    except Exception as e:
        logger.error(f"Error retrieving document version", 
                    document_id=document_id,
                    version_id=version_id,
                    error=str(e), 
                    exc_info=True)
        raise DocumentStorageError(f"Failed to retrieve document version: {str(e)}", e)


@with_retry(max_attempts=3, backoff_factor=2)
def delete_document(document_id, user_id=None, session_id=None, 
                   bucket_name=DEFAULT_BUCKET_NAME, region=DEFAULT_REGION):
    """
    Deletes a document and all its versions from S3.
    
    Args:
        document_id (str): Unique document identifier
        user_id (str, optional): User ID for authenticated users
        session_id (str, optional): Session ID for anonymous users
        bucket_name (str): S3 bucket name
        region (str): AWS region
        
    Returns:
        bool: Success status of deletion operation
        
    Raises:
        DocumentStorageError: If deletion operation fails
    """
    try:
        # Determine owner identifier
        owner_id = user_id if user_id else f"session_{session_id}"
        
        # Generate document key prefix
        doc_prefix = f"{DOCUMENT_PREFIX}{owner_id}/{document_id}"
        
        # Generate version key prefix
        version_prefix = f"{VERSION_PREFIX}{owner_id}/{document_id}/"
        
        # Get S3 resource
        s3_resource = get_s3_resource()
        
        # Get bucket
        bucket = s3_resource.Bucket(bucket_name)
        
        # Delete document object
        deleted_count = 0
        for obj in bucket.objects.filter(Prefix=doc_prefix):
            obj.delete()
            deleted_count += 1
        
        # Delete all version objects
        for obj in bucket.objects.filter(Prefix=version_prefix):
            obj.delete()
            deleted_count += 1
        
        logger.info(f"Document and versions deleted successfully", 
                   document_id=document_id,
                   user_id=user_id,
                   session_id=session_id,
                   deleted_count=deleted_count)
        
        return True
        
    except S3ConnectionError as e:
        logger.error(f"S3 connection error deleting document", 
                    document_id=document_id,
                    error=str(e), 
                    exc_info=True)
        raise DocumentStorageError(f"Failed to delete document: {str(e)}", e)
    except Exception as e:
        logger.error(f"Error deleting document", 
                    document_id=document_id,
                    error=str(e), 
                    exc_info=True)
        raise DocumentStorageError(f"Failed to delete document: {str(e)}", e)


@with_retry(max_attempts=3, backoff_factor=2)
def delete_document_version(document_id, version_id, user_id=None, session_id=None, 
                           bucket_name=DEFAULT_BUCKET_NAME, region=DEFAULT_REGION):
    """
    Deletes a specific version of a document from S3.
    
    Args:
        document_id (str): Unique document identifier
        version_id (str): Unique version identifier
        user_id (str, optional): User ID for authenticated users
        session_id (str, optional): Session ID for anonymous users
        bucket_name (str): S3 bucket name
        region (str): AWS region
        
    Returns:
        bool: Success status of deletion operation
        
    Raises:
        DocumentStorageError: If deletion operation fails
    """
    try:
        # Generate version key
        key = generate_version_key(document_id, version_id, user_id, session_id)
        
        # Get S3 client
        s3_client = get_s3_client()
        
        # Delete version object
        try:
            s3_client.delete_object(
                Bucket=bucket_name,
                Key=key
            )
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == 'NoSuchKey':
                logger.warning(f"Document version not found for deletion", 
                              document_id=document_id,
                              version_id=version_id)
                return False
            raise
        
        logger.info(f"Document version deleted successfully", 
                   document_id=document_id,
                   version_id=version_id,
                   user_id=user_id,
                   session_id=session_id,
                   s3_key=key)
        
        return True
        
    except S3ConnectionError as e:
        logger.error(f"S3 connection error deleting document version", 
                    document_id=document_id,
                    version_id=version_id,
                    error=str(e), 
                    exc_info=True)
        raise DocumentStorageError(f"Failed to delete document version: {str(e)}", e)
    except Exception as e:
        logger.error(f"Error deleting document version", 
                    document_id=document_id,
                    version_id=version_id,
                    error=str(e), 
                    exc_info=True)
        raise DocumentStorageError(f"Failed to delete document version: {str(e)}", e)


def create_document_download_url(document_id, user_id=None, session_id=None, 
                                expiration=None, bucket_name=DEFAULT_BUCKET_NAME):
    """
    Creates a pre-signed URL for downloading a document.
    
    Args:
        document_id (str): Unique document identifier
        user_id (str, optional): User ID for authenticated users
        session_id (str, optional): Session ID for anonymous users
        expiration (int, optional): URL expiration in seconds (default: URL_EXPIRATION)
        bucket_name (str): S3 bucket name
        
    Returns:
        str: Pre-signed URL for document download
        
    Raises:
        DocumentStorageError: If URL creation fails
    """
    try:
        # Generate document key
        key = generate_document_key(document_id, user_id, session_id)
        
        # Set default expiration if not provided
        if expiration is None:
            expiration = URL_EXPIRATION
        
        # Create pre-signed URL
        url = create_presigned_url(
            bucket_name=bucket_name,
            object_key=key,
            operation='get_object',
            expiration=expiration
        )
        
        logger.info(f"Download URL created successfully", 
                   document_id=document_id,
                   user_id=user_id,
                   session_id=session_id,
                   expiration=expiration)
        
        return url
        
    except S3ConnectionError as e:
        logger.error(f"S3 connection error creating download URL", 
                    document_id=document_id,
                    error=str(e), 
                    exc_info=True)
        raise DocumentStorageError(f"Failed to create download URL: {str(e)}", e)
    except Exception as e:
        logger.error(f"Error creating download URL", 
                    document_id=document_id,
                    error=str(e), 
                    exc_info=True)
        raise DocumentStorageError(f"Failed to create download URL: {str(e)}", e)


def create_document_upload_url(document_id, user_id=None, session_id=None, 
                              content_type="text/plain", expiration=None,
                              bucket_name=DEFAULT_BUCKET_NAME):
    """
    Creates a pre-signed URL for uploading a document.
    
    Args:
        document_id (str): Unique document identifier
        user_id (str, optional): User ID for authenticated users
        session_id (str, optional): Session ID for anonymous users
        content_type (str): MIME type of the document
        expiration (int, optional): URL expiration in seconds (default: URL_EXPIRATION)
        bucket_name (str): S3 bucket name
        
    Returns:
        str: Pre-signed URL for document upload
        
    Raises:
        DocumentStorageError: If URL creation fails
    """
    try:
        # Generate document key
        key = generate_document_key(document_id, user_id, session_id)
        
        # Set default expiration if not provided
        if expiration is None:
            expiration = URL_EXPIRATION
        
        # Create pre-signed URL
        url = create_presigned_url(
            bucket_name=bucket_name,
            object_key=key,
            operation='put_object',
            expiration=expiration
        )
        
        logger.info(f"Upload URL created successfully", 
                   document_id=document_id,
                   user_id=user_id,
                   session_id=session_id,
                   content_type=content_type,
                   expiration=expiration)
        
        return url
        
    except S3ConnectionError as e:
        logger.error(f"S3 connection error creating upload URL", 
                    document_id=document_id,
                    error=str(e), 
                    exc_info=True)
        raise DocumentStorageError(f"Failed to create upload URL: {str(e)}", e)
    except Exception as e:
        logger.error(f"Error creating upload URL", 
                    document_id=document_id,
                    error=str(e), 
                    exc_info=True)
        raise DocumentStorageError(f"Failed to create upload URL: {str(e)}", e)


@with_retry(max_attempts=3, backoff_factor=2)
def list_document_versions(document_id, user_id=None, session_id=None, 
                          bucket_name=DEFAULT_BUCKET_NAME, region=DEFAULT_REGION):
    """
    Lists all versions of a document stored in S3.
    
    Args:
        document_id (str): Unique document identifier
        user_id (str, optional): User ID for authenticated users
        session_id (str, optional): Session ID for anonymous users
        bucket_name (str): S3 bucket name
        region (str): AWS region
        
    Returns:
        list: List of version keys and metadata
        
    Raises:
        DocumentStorageError: If list operation fails
    """
    try:
        # Determine owner identifier
        owner_id = user_id if user_id else f"session_{session_id}"
        
        # Generate version key prefix
        prefix = f"{VERSION_PREFIX}{owner_id}/{document_id}/"
        
        # Get S3 resource
        s3_resource = get_s3_resource()
        
        # Get bucket
        bucket = s3_resource.Bucket(bucket_name)
        
        # List all version objects
        versions = []
        for obj in bucket.objects.filter(Prefix=prefix):
            # Extract version ID from key
            key_parts = obj.key.split('/')
            version_id = key_parts[-1] if len(key_parts) > 0 else None
            
            if version_id:
                # Get object metadata
                response = s3_resource.meta.client.head_object(
                    Bucket=bucket_name,
                    Key=obj.key
                )
                
                # Extract metadata
                metadata = response.get('Metadata', {})
                last_modified = response.get('LastModified')
                content_type = response.get('ContentType', 'text/plain')
                
                # Add version info to list
                versions.append({
                    'version_id': version_id,
                    'document_id': document_id,
                    's3_key': obj.key,
                    'size': obj.size,
                    'last_modified': last_modified.isoformat() if last_modified else None,
                    'content_type': content_type,
                    'metadata': metadata
                })
        
        logger.info(f"Document versions listed successfully", 
                   document_id=document_id,
                   user_id=user_id,
                   session_id=session_id,
                   version_count=len(versions))
        
        # Sort versions by last_modified (newest first)
        versions.sort(key=lambda x: x.get('last_modified', ''), reverse=True)
        
        return versions
        
    except S3ConnectionError as e:
        logger.error(f"S3 connection error listing document versions", 
                    document_id=document_id,
                    error=str(e), 
                    exc_info=True)
        raise DocumentStorageError(f"Failed to list document versions: {str(e)}", e)
    except Exception as e:
        logger.error(f"Error listing document versions", 
                    document_id=document_id,
                    error=str(e), 
                    exc_info=True)
        raise DocumentStorageError(f"Failed to list document versions: {str(e)}", e)


def check_document_exists(document_id, user_id=None, session_id=None, 
                         bucket_name=DEFAULT_BUCKET_NAME, region=DEFAULT_REGION):
    """
    Checks if a document exists in S3.
    
    Args:
        document_id (str): Unique document identifier
        user_id (str, optional): User ID for authenticated users
        session_id (str, optional): Session ID for anonymous users
        bucket_name (str): S3 bucket name
        region (str): AWS region
        
    Returns:
        bool: True if document exists, False otherwise
    """
    try:
        # Generate document key
        key = generate_document_key(document_id, user_id, session_id)
        
        # Get S3 client
        s3_client = get_s3_client()
        
        # Check if object exists
        try:
            s3_client.head_object(
                Bucket=bucket_name,
                Key=key
            )
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == 'NoSuchKey' or error_code == '404':
                return False
            raise
        
    except S3ConnectionError as e:
        logger.error(f"S3 connection error checking document existence", 
                    document_id=document_id,
                    error=str(e), 
                    exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Error checking document existence", 
                    document_id=document_id,
                    error=str(e), 
                    exc_info=True)
        return False


@with_retry(max_attempts=3, backoff_factor=2)
def transfer_document_ownership(document_id, session_id, user_id, 
                               bucket_name=DEFAULT_BUCKET_NAME, region=DEFAULT_REGION):
    """
    Transfers document ownership from session to user.
    
    This is used when converting an anonymous document to a user-owned document.
    
    Args:
        document_id (str): Unique document identifier
        session_id (str): Session ID for anonymous user
        user_id (str): User ID to transfer ownership to
        bucket_name (str): S3 bucket name
        region (str): AWS region
        
    Returns:
        bool: Success status of transfer operation
        
    Raises:
        DocumentNotFoundError: If document not found
        DocumentStorageError: If transfer operation fails
    """
    try:
        # Generate source and target keys
        source_key = generate_document_key(document_id, None, session_id)
        target_key = generate_document_key(document_id, user_id, None)
        
        # Generate source and target version prefixes
        source_version_prefix = f"{VERSION_PREFIX}session_{session_id}/{document_id}/"
        target_version_prefix = f"{VERSION_PREFIX}{user_id}/{document_id}/"
        
        # Get S3 client and resource
        s3_client = get_s3_client()
        s3_resource = get_s3_resource()
        
        # Check if source document exists
        try:
            document_obj = s3_client.head_object(
                Bucket=bucket_name,
                Key=source_key
            )
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == 'NoSuchKey' or error_code == '404':
                raise DocumentNotFoundError(
                    document_id, 
                    None, 
                    session_id, 
                    f"Document not found for ownership transfer"
                )
            raise
        
        # Copy main document
        s3_client.copy_object(
            Bucket=bucket_name,
            CopySource={'Bucket': bucket_name, 'Key': source_key},
            Key=target_key,
            MetadataDirective='REPLACE',
            Metadata={
                **document_obj.get('Metadata', {}),
                'user_id': user_id,
                'transfer_timestamp': datetime.datetime.utcnow().isoformat(),
                'original_session_id': session_id
            }
        )
        
        # List and copy all versions
        bucket = s3_resource.Bucket(bucket_name)
        copied_versions = 0
        
        for obj in bucket.objects.filter(Prefix=source_version_prefix):
            # Extract version ID from key
            key_parts = obj.key.split('/')
            version_id = key_parts[-1] if len(key_parts) > 0 else None
            
            if version_id:
                # Get object metadata
                version_obj = s3_client.head_object(
                    Bucket=bucket_name,
                    Key=obj.key
                )
                
                # Generate target version key
                target_version_key = generate_version_key(document_id, version_id, user_id, None)
                
                # Copy version with updated metadata
                s3_client.copy_object(
                    Bucket=bucket_name,
                    CopySource={'Bucket': bucket_name, 'Key': obj.key},
                    Key=target_version_key,
                    MetadataDirective='REPLACE',
                    Metadata={
                        **version_obj.get('Metadata', {}),
                        'user_id': user_id,
                        'transfer_timestamp': datetime.datetime.utcnow().isoformat(),
                        'original_session_id': session_id
                    }
                )
                
                copied_versions += 1
        
        # Delete original document and versions
        deleted_count = 0
        for obj in bucket.objects.filter(Prefix=source_key):
            obj.delete()
            deleted_count += 1
            
        for obj in bucket.objects.filter(Prefix=source_version_prefix):
            obj.delete()
            deleted_count += 1
        
        logger.info(f"Document ownership transferred successfully", 
                   document_id=document_id,
                   session_id=session_id,
                   user_id=user_id,
                   copied_versions=copied_versions,
                   deleted_count=deleted_count)
        
        return True
        
    except DocumentNotFoundError:
        # Re-raise DocumentNotFoundError
        raise
    except S3ConnectionError as e:
        logger.error(f"S3 connection error transferring document ownership", 
                    document_id=document_id,
                    session_id=session_id,
                    user_id=user_id,
                    error=str(e), 
                    exc_info=True)
        raise DocumentStorageError(f"Failed to transfer document ownership: {str(e)}", e)
    except Exception as e:
        logger.error(f"Error transferring document ownership", 
                    document_id=document_id,
                    session_id=session_id,
                    user_id=user_id,
                    error=str(e), 
                    exc_info=True)
        raise DocumentStorageError(f"Failed to transfer document ownership: {str(e)}", e)


class DocumentStorage:
    """Main class for S3 document storage operations."""
    
    def __init__(self, bucket_name=None, region=None):
        """
        Initialize DocumentStorage with bucket and region configuration.
        
        Args:
            bucket_name (str, optional): S3 bucket name (default: DEFAULT_BUCKET_NAME)
            region (str, optional): AWS region (default: DEFAULT_REGION)
        """
        self.bucket_name = bucket_name or DEFAULT_BUCKET_NAME
        self.region = region or DEFAULT_REGION
        
        # Ensure bucket exists
        ensure_bucket_exists(self.bucket_name, self.region)
        logger.info(f"DocumentStorage initialized", bucket=self.bucket_name, region=self.region)
    
    def store_document(self, document_id, content, user_id=None, session_id=None, 
                      content_type="text/plain", metadata=None):
        """
        Stores document content in S3.
        
        Args:
            document_id (str): Unique document identifier
            content (str): Document content to store
            user_id (str, optional): User ID for authenticated users
            session_id (str, optional): Session ID for anonymous users
            content_type (str): MIME type of the document
            metadata (dict, optional): Additional metadata for the document
            
        Returns:
            dict: Storage result with metadata
            
        Raises:
            DocumentStorageError: If storage operation fails
            ValueError: If validation fails
        """
        if not document_id:
            raise ValueError("Document ID is required")
        if not user_id and not session_id:
            raise ValueError("Either user_id or session_id must be provided")
        
        return store_document(
            document_id=document_id,
            content=content,
            user_id=user_id,
            session_id=session_id,
            content_type=content_type,
            metadata=metadata,
            bucket_name=self.bucket_name,
            region=self.region
        )
    
    def retrieve_document(self, document_id, user_id=None, session_id=None):
        """
        Retrieves document content from S3.
        
        Args:
            document_id (str): Unique document identifier
            user_id (str, optional): User ID for authenticated users
            session_id (str, optional): Session ID for anonymous users
            
        Returns:
            dict: Document content and metadata
            
        Raises:
            DocumentNotFoundError: If document not found
            DocumentStorageError: If retrieval operation fails
        """
        if not document_id:
            raise ValueError("Document ID is required")
        if not user_id and not session_id:
            raise ValueError("Either user_id or session_id must be provided")
        
        return retrieve_document(
            document_id=document_id,
            user_id=user_id,
            session_id=session_id,
            bucket_name=self.bucket_name,
            region=self.region
        )
    
    def store_document_version(self, document_id, version_id, content, 
                              user_id=None, session_id=None, 
                              content_type="text/plain", metadata=None):
        """
        Stores a specific version of document content in S3.
        
        Args:
            document_id (str): Unique document identifier
            version_id (str): Unique version identifier
            content (str): Document content to store
            user_id (str, optional): User ID for authenticated users
            session_id (str, optional): Session ID for anonymous users
            content_type (str): MIME type of the document
            metadata (dict, optional): Additional metadata for the document
            
        Returns:
            dict: Storage result with metadata
            
        Raises:
            DocumentStorageError: If storage operation fails
            ValueError: If validation fails
        """
        if not document_id:
            raise ValueError("Document ID is required")
        if not version_id:
            raise ValueError("Version ID is required")
        if not user_id and not session_id:
            raise ValueError("Either user_id or session_id must be provided")
        
        return store_document_version(
            document_id=document_id,
            version_id=version_id,
            content=content,
            user_id=user_id,
            session_id=session_id,
            content_type=content_type,
            metadata=metadata,
            bucket_name=self.bucket_name,
            region=self.region
        )
    
    def retrieve_document_version(self, document_id, version_id, user_id=None, session_id=None):
        """
        Retrieves a specific version of document content from S3.
        
        Args:
            document_id (str): Unique document identifier
            version_id (str): Unique version identifier
            user_id (str, optional): User ID for authenticated users
            session_id (str, optional): Session ID for anonymous users
            
        Returns:
            dict: Document version content and metadata
            
        Raises:
            DocumentNotFoundError: If document version not found
            DocumentStorageError: If retrieval operation fails
        """
        if not document_id:
            raise ValueError("Document ID is required")
        if not version_id:
            raise ValueError("Version ID is required")
        if not user_id and not session_id:
            raise ValueError("Either user_id or session_id must be provided")
        
        return retrieve_document_version(
            document_id=document_id,
            version_id=version_id,
            user_id=user_id,
            session_id=session_id,
            bucket_name=self.bucket_name,
            region=self.region
        )
    
    def delete_document(self, document_id, user_id=None, session_id=None):
        """
        Deletes a document and all its versions from S3.
        
        Args:
            document_id (str): Unique document identifier
            user_id (str, optional): User ID for authenticated users
            session_id (str, optional): Session ID for anonymous users
            
        Returns:
            bool: Success status of deletion operation
            
        Raises:
            DocumentStorageError: If deletion operation fails
        """
        if not document_id:
            raise ValueError("Document ID is required")
        if not user_id and not session_id:
            raise ValueError("Either user_id or session_id must be provided")
        
        return delete_document(
            document_id=document_id,
            user_id=user_id,
            session_id=session_id,
            bucket_name=self.bucket_name,
            region=self.region
        )
    
    def delete_document_version(self, document_id, version_id, user_id=None, session_id=None):
        """
        Deletes a specific version of a document from S3.
        
        Args:
            document_id (str): Unique document identifier
            version_id (str): Unique version identifier
            user_id (str, optional): User ID for authenticated users
            session_id (str, optional): Session ID for anonymous users
            
        Returns:
            bool: Success status of deletion operation
            
        Raises:
            DocumentStorageError: If deletion operation fails
        """
        if not document_id:
            raise ValueError("Document ID is required")
        if not version_id:
            raise ValueError("Version ID is required")
        if not user_id and not session_id:
            raise ValueError("Either user_id or session_id must be provided")
        
        return delete_document_version(
            document_id=document_id,
            version_id=version_id,
            user_id=user_id,
            session_id=session_id,
            bucket_name=self.bucket_name,
            region=self.region
        )
    
    def create_download_url(self, document_id, user_id=None, session_id=None, expiration=None):
        """
        Creates a pre-signed URL for downloading a document.
        
        Args:
            document_id (str): Unique document identifier
            user_id (str, optional): User ID for authenticated users
            session_id (str, optional): Session ID for anonymous users
            expiration (int, optional): URL expiration in seconds (default: URL_EXPIRATION)
            
        Returns:
            str: Pre-signed URL for document download
            
        Raises:
            DocumentStorageError: If URL creation fails
        """
        if not document_id:
            raise ValueError("Document ID is required")
        if not user_id and not session_id:
            raise ValueError("Either user_id or session_id must be provided")
        
        return create_document_download_url(
            document_id=document_id,
            user_id=user_id,
            session_id=session_id,
            expiration=expiration,
            bucket_name=self.bucket_name
        )
    
    def create_upload_url(self, document_id, user_id=None, session_id=None, 
                         content_type="text/plain", expiration=None):
        """
        Creates a pre-signed URL for uploading a document.
        
        Args:
            document_id (str): Unique document identifier
            user_id (str, optional): User ID for authenticated users
            session_id (str, optional): Session ID for anonymous users
            content_type (str): MIME type of the document
            expiration (int, optional): URL expiration in seconds (default: URL_EXPIRATION)
            
        Returns:
            str: Pre-signed URL for document upload
            
        Raises:
            DocumentStorageError: If URL creation fails
        """
        if not document_id:
            raise ValueError("Document ID is required")
        if not user_id and not session_id:
            raise ValueError("Either user_id or session_id must be provided")
        
        return create_document_upload_url(
            document_id=document_id,
            user_id=user_id,
            session_id=session_id,
            content_type=content_type,
            expiration=expiration,
            bucket_name=self.bucket_name
        )
    
    def list_versions(self, document_id, user_id=None, session_id=None):
        """
        Lists all versions of a document stored in S3.
        
        Args:
            document_id (str): Unique document identifier
            user_id (str, optional): User ID for authenticated users
            session_id (str, optional): Session ID for anonymous users
            
        Returns:
            list: List of version keys and metadata
            
        Raises:
            DocumentStorageError: If list operation fails
        """
        if not document_id:
            raise ValueError("Document ID is required")
        if not user_id and not session_id:
            raise ValueError("Either user_id or session_id must be provided")
        
        return list_document_versions(
            document_id=document_id,
            user_id=user_id,
            session_id=session_id,
            bucket_name=self.bucket_name,
            region=self.region
        )
    
    def document_exists(self, document_id, user_id=None, session_id=None):
        """
        Checks if a document exists in S3.
        
        Args:
            document_id (str): Unique document identifier
            user_id (str, optional): User ID for authenticated users
            session_id (str, optional): Session ID for anonymous users
            
        Returns:
            bool: True if document exists, False otherwise
        """
        if not document_id:
            raise ValueError("Document ID is required")
        if not user_id and not session_id:
            raise ValueError("Either user_id or session_id must be provided")
        
        return check_document_exists(
            document_id=document_id,
            user_id=user_id,
            session_id=session_id,
            bucket_name=self.bucket_name,
            region=self.region
        )
    
    def transfer_ownership(self, document_id, session_id, user_id):
        """
        Transfers document ownership from session to user.
        
        This is used when converting an anonymous document to a user-owned document.
        
        Args:
            document_id (str): Unique document identifier
            session_id (str): Session ID for anonymous user
            user_id (str): User ID to transfer ownership to
            
        Returns:
            bool: Success status of transfer operation
            
        Raises:
            DocumentNotFoundError: If document not found
            DocumentStorageError: If transfer operation fails
        """
        if not document_id:
            raise ValueError("Document ID is required")
        if not session_id:
            raise ValueError("Session ID is required")
        if not user_id:
            raise ValueError("User ID is required")
        
        return transfer_document_ownership(
            document_id=document_id,
            session_id=session_id,
            user_id=user_id,
            bucket_name=self.bucket_name,
            region=self.region
        )