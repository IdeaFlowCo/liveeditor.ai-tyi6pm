"""
Core manager component that coordinates document operations in the AI writing enhancement platform.
It serves as a bridge between the higher-level document service and the lower-level data repositories,
handling create, read, update, delete operations as well as versioning, format conversion, and
anonymous/authenticated access control.
"""

import io  # standard library
from typing import Union, Dict, List, Tuple, Any  # typing standard library

from .version_manager import VersionManager  # Internal import
from .format_converter import FormatConverter  # Internal import
from ..utils.logger import get_logger  # Internal import
from ..utils.validators import validate_document_data  # Internal import
from ...data.mongodb.repositories.document_repository import (  # Internal import
    DocumentRepository,
    DocumentNotFoundError,
    DocumentAccessError
)
from ...data.s3.document_storage import DocumentStorage, DocumentNotFoundError as S3DocumentNotFoundError  # Internal import

# Initialize logger
logger = get_logger(__name__)

# Define default format
DEFAULT_FORMAT = "html"


class DocumentManagerError(Exception):
    """Base exception class for document manager errors"""

    def __init__(self, message: str, original_error: Exception = None):
        """Initialize the document manager error

        Args:
            message (str): Error message
            original_error (Exception): The original exception that caused this error
        """
        super().__init__(message)
        self.original_error = original_error


class DocumentFormatError(Exception):
    """Exception for document format errors during import/export"""

    def __init__(self, format: str, operation: str, message: str = None):
        """Initialize the document format error

        Args:
            format (str): The format that caused the error
            operation (str): The operation being performed (import/export)
            message (str): Error message
        """
        if not message:
            message = f"Document format error during {operation} for format {format}"
        super().__init__(message)
        self.format = format
        self.operation = operation


class DocumentVersionError(Exception):
    """Exception for document versioning errors"""

    def __init__(self, document_id: str, message: str = None):
        """Initialize the document version error

        Args:
            document_id (str): The document ID that caused the error
            message (str): Error message
        """
        if not message:
            message = f"Document version error for document {document_id}"
        super().__init__(message)
        self.document_id = document_id


class DocumentManager:
    """
    Core manager class for document operations that bridges higher-level services with data repositories
    """

    def __init__(
        self,
        document_repository: DocumentRepository,
        version_manager: VersionManager,
        document_storage: DocumentStorage,
        format_converter: FormatConverter,
    ):
        """Initializes the document manager with required dependencies

        Args:
            document_repository (DocumentRepository): Repository for document metadata
            version_manager (VersionManager): Manager for document versions
            document_storage (DocumentStorage): Storage for document content
            format_converter (FormatConverter): Converter for document formats
        """
        self._document_repository = document_repository
        self._version_manager = version_manager
        self._document_storage = document_storage
        self._format_converter = format_converter
        logger.info("Initialized DocumentManager")

    def create_document(self, document_data: dict, user_id: str = None, session_id: str = None) -> dict:
        """Creates a new document with metadata and content

        Args:
            document_data (dict): Document data including title, content, etc.
            user_id (str): User ID for authenticated users
            session_id (str): Session ID for anonymous users

        Returns:
            dict: Created document metadata with ID
        """
        try:
            # Validate document_data
            validate_document_data(document_data)

            # Ensure either user_id or session_id is provided
            if not user_id and not session_id:
                raise ValueError("Either user_id or session_id must be provided")

            # Extract content from document_data if present
            content = document_data.get("content")

            # Create document metadata in repository
            document = self._document_repository.create(document_data, user_id, session_id)
            document_id = document["_id"]

            # If content provided, store in document storage
            if content:
                self._document_storage.store_document(document_id, content, user_id, session_id)

                # Create initial version
                version = self._version_manager.create_version(
                    document_id=document_id,
                    content=content,
                    user_id=user_id,
                    session_id=session_id,
                    change_description="Initial version",
                )

                # Update document with current version ID if versioned
                self._document_repository.update_current_version(document_id, version["_id"])

            logger.info(f"Created document: {document_id[:8]}...", user_id=user_id, session_id=session_id)
            return document
        except Exception as e:
            logger.error(f"Failed to create document: {str(e)}", exc_info=True)
            raise DocumentManagerError(f"Failed to create document: {str(e)}", e)

    def get_document(self, document_id: str, user_id: str = None, session_id: str = None, include_content: bool = True) -> dict:
        """Retrieves a document by ID with access control

        Args:
            document_id (str): ID of the document to retrieve
            user_id (str): User ID for authenticated users
            session_id (str): Session ID for anonymous users
            include_content (bool): Whether to include document content in the response

        Returns:
            dict: Document data with optional content
        """
        try:
            # Ensure either user_id or session_id is provided
            if not user_id and not session_id:
                raise ValueError("Either user_id or session_id must be provided")

            # Retrieve document metadata from repository
            document = self._document_repository.get_by_id(document_id, user_id, session_id, include_content)

            # Check user has permission to access document
            if not document:
                raise DocumentNotFoundError(document_id)

            # If include_content is True, retrieve content from storage
            if include_content:
                try:
                    content_data = self._document_storage.retrieve_document(document_id, user_id, session_id)
                    document["content"] = content_data["content"]
                except S3DocumentNotFoundError:
                    # If content not found but versions exist, get latest version content
                    latest_version = self._version_manager.get_latest_version(document_id, user_id, session_id)
                    if latest_version:
                        document["content"] = latest_version["content"]
                    else:
                        document["content"] = ""  # No content and no versions

            logger.info(f"Retrieved document: {document_id[:8]}...", user_id=user_id, session_id=session_id)
            return document
        except Exception as e:
            logger.error(f"Failed to get document: {str(e)}", exc_info=True)
            raise DocumentManagerError(f"Failed to get document: {str(e)}", e)

    def update_document(self, document_id: str, document_data: dict, user_id: str = None, session_id: str = None, create_version: bool = False) -> dict:
        """Updates an existing document with new metadata and/or content

        Args:
            document_id (str): ID of the document to update
            document_data (dict): New data to apply to the document
            user_id (str): User ID for authenticated users
            session_id (str): Session ID for anonymous users
            create_version (bool): Whether to create a new version if content changes

        Returns:
            dict: Updated document metadata
        """
        try:
            # Ensure either user_id or session_id is provided
            if not user_id and not session_id:
                raise ValueError("Either user_id or session_id must be provided")

            # Validate document_data schema and values
            validate_document_data(document_data)

            # Retrieve current document to check permissions
            current_document = self.get_document(document_id, user_id, session_id, include_content=False)

            # Extract content from document_data if present
            content = document_data.get("content")

            # If create_version is True and content changes, create new version
            if create_version and content and content != current_document.get("content"):
                self._version_manager.create_version(
                    document_id=document_id,
                    content=content,
                    user_id=user_id,
                    session_id=session_id,
                    change_description="User update",
                )

            # Update document metadata in repository
            updated_document = self._document_repository.update(document_id, document_data, user_id, session_id)

            # If content provided, update content in storage
            if content:
                self._document_storage.store_document(document_id, content, user_id, session_id)

            logger.info(f"Updated document: {document_id[:8]}...", user_id=user_id, session_id=session_id)
            return updated_document
        except Exception as e:
            logger.error(f"Failed to update document: {str(e)}", exc_info=True)
            raise DocumentManagerError(f"Failed to update document: {str(e)}", e)

    def delete_document(self, document_id: str, user_id: str = None, session_id: str = None) -> bool:
        """Deletes a document and all associated data

        Args:
            document_id (str): ID of the document to delete
            user_id (str): User ID for authenticated users
            session_id (str): Session ID for anonymous users

        Returns:
            bool: Success status of deletion operation
        """
        try:
            # Ensure either user_id or session_id is provided
            if not user_id and not session_id:
                raise ValueError("Either user_id or session_id must be provided")

            # Retrieve document to check permissions
            self.get_document(document_id, user_id, session_id, include_content=False)

            # Delete document content from storage
            self._document_storage.delete_document(document_id, user_id, session_id)

            # Delete document metadata from repository
            success = self._document_repository.delete(document_id, user_id, session_id)

            logger.info(f"Deleted document: {document_id[:8]}...", user_id=user_id, session_id=session_id)
            return success
        except Exception as e:
            logger.error(f"Failed to delete document: {str(e)}", exc_info=True)
            raise DocumentManagerError(f"Failed to delete document: {str(e)}", e)

    def get_user_documents(self, user_id: str, filters: dict = None, skip: int = 0, limit: int = 20) -> Tuple[List[dict], int]:
        """Retrieves all documents owned by a specific user

        Args:
            user_id (str): User ID to find documents for
            filters (dict): Additional query filters
            skip (int): Number of documents to skip for pagination
            limit (int): Maximum number of documents to return

        Returns:
            Tuple[List[dict], int]: (List of document metadata, total count)
        """
        try:
            # Validate user_id parameter
            if not user_id:
                raise ValueError("User ID must be provided")

            # Call document repository to find user's documents
            documents, total_count = self._document_repository.find_by_user(user_id, filters, skip, limit)

            logger.info(f"Retrieved {len(documents)} documents for user: {user_id[:8]}...", user_id=user_id)
            return documents, total_count
        except Exception as e:
            logger.error(f"Failed to get user documents: {str(e)}", exc_info=True)
            raise DocumentManagerError(f"Failed to get user documents: {str(e)}", e)

    def get_session_documents(self, session_id: str, filters: dict = None, skip: int = 0, limit: int = 20) -> Tuple[List[dict], int]:
        """Retrieves all documents associated with an anonymous session

        Args:
            session_id (str): Session ID to find documents for
            filters (dict): Additional query filters
            skip (int): Number of documents to skip for pagination
            limit (int): Maximum number of documents to return

        Returns:
            Tuple[List[dict], int]: (List of document metadata, total count)
        """
        try:
            # Validate session_id parameter
            if not session_id:
                raise ValueError("Session ID must be provided")

            # Call document repository to find session's documents
            documents, total_count = self._document_repository.find_by_session(session_id, filters, skip, limit)

            logger.info(f"Retrieved {len(documents)} documents for session: {session_id[:8]}...", session_id=session_id)
            return documents, total_count
        except Exception as e:
            logger.error(f"Failed to get session documents: {str(e)}", exc_info=True)
            raise DocumentManagerError(f"Failed to get session documents: {str(e)}", e)

    def create_document_version(self, document_id: str, content: str, user_id: str = None, session_id: str = None, change_description: str = None, is_auto_save: bool = False) -> dict:
        """Creates a new version of an existing document

        Args:
            document_id (str): ID of the document
            content (str): Content of the new version
            user_id (str): User ID for authenticated users
            session_id (str): Session ID for anonymous users
            change_description (str): Description of the changes in this version
            is_auto_save (bool): Whether this version is an auto-save

        Returns:
            dict: Created version metadata
        """
        try:
            # Ensure either user_id or session_id is provided
            if not user_id and not session_id:
                raise ValueError("Either user_id or session_id must be provided")

            # Retrieve document to check permissions
            self.get_document(document_id, user_id, session_id, include_content=False)

            # Create the document version
            version = self._version_manager.create_version(
                document_id=document_id,
                content=content,
                user_id=user_id,
                session_id=session_id,
                change_description=change_description,
            )

            logger.info(f"Created version for document: {document_id[:8]}...", user_id=user_id, session_id=session_id)
            return version
        except Exception as e:
            logger.error(f"Failed to create document version: {str(e)}", exc_info=True)
            raise DocumentManagerError(f"Failed to create document version: {str(e)}", e)

    def import_document(self, content: Union[str, bytes], source_format: str = None, title: str = "Imported Document", user_id: str = None, session_id: str = None, metadata: dict = None) -> dict:
        """Imports a document from external content with format conversion

        Args:
            content (Union[str, bytes]): Document content
            source_format (str): Source format (e.g., "txt", "html", "docx")
            title (str): Title of the document
            user_id (str): User ID for authenticated users
            session_id (str): Session ID for anonymous users
            metadata (dict): Additional metadata

        Returns:
            dict: Created document metadata
        """
        try:
            # Ensure either user_id or session_id is provided
            if not user_id and not session_id:
                raise ValueError("Either user_id or session_id must be provided")

            # If source_format not provided, detect format using format_converter
            if not source_format:
                source_format = self._format_converter.detect_format(content)

            # Convert content to HTML format if not already HTML
            if source_format != "html":
                content = self._format_converter.convert(content, source_format, "html")

            # Prepare document_data with title and metadata
            document_data = {"title": title, "content": content}
            if metadata:
                document_data.update(metadata)

            # Call create_document to create the document
            document = self.create_document(document_data, user_id, session_id)

            logger.info(f"Imported document: {document['title'][:20]}...", user_id=user_id, session_id=session_id, format=source_format)
            return document
        except Exception as e:
            logger.error(f"Failed to import document: {str(e)}", exc_info=True)
            raise DocumentManagerError(f"Failed to import document: {str(e)}", e)

    def export_document(self, document_id: str, target_format: str, user_id: str = None, session_id: str = None, conversion_options: dict = None) -> dict:
        """Exports a document to a specified format

        Args:
            document_id (str): ID of the document to export
            target_format (str): Target format (e.g., "txt", "html", "docx", "pdf")
            user_id (str): User ID for authenticated users
            session_id (str): Session ID for anonymous users
            conversion_options (dict): Options for the format conversion

        Returns:
            dict: Export data with content and format info
        """
        try:
            # Ensure either user_id or session_id is provided
            if not user_id and not session_id:
                raise ValueError("Either user_id or session_id must be provided")

            # Retrieve document with content to check permissions
            document = self.get_document(document_id, user_id, session_id, include_content=True)

            # If content not found, retrieve latest version content
            content = document.get("content")
            if not content:
                latest_version = self._version_manager.get_latest_version(document_id, user_id, session_id)
                if latest_version:
                    content = latest_version["content"]
                else:
                    raise ValueError("Document has no content and no versions")

            # Validate target_format against supported formats
            if target_format not in self._format_converter._export_formats:
                raise DocumentFormatError(target_format, "export", "Unsupported export format")

            # If document is already in target format, return as is
            if target_format == DEFAULT_FORMAT:
                return {"content": content, "format": DEFAULT_FORMAT, "metadata": document}

            # Use format_converter to convert to target format
            converted_content = self._format_converter.convert(content, DEFAULT_FORMAT, target_format, conversion_options)

            # Prepare export data with content, format and metadata
            export_data = {"content": converted_content, "format": target_format, "metadata": document}

            logger.info(f"Exported document: {document_id[:8]}...", user_id=user_id, session_id=session_id, format=target_format)
            return export_data
        except Exception as e:
            logger.error(f"Failed to export document: {str(e)}", exc_info=True)
            raise DocumentManagerError(f"Failed to export document: {str(e)}", e)

    def transfer_anonymous_document(self, document_id: str, session_id: str, user_id: str) -> bool:
        """Transfers ownership of a document from anonymous session to registered user

        Args:
            document_id (str): ID of the document to transfer
            session_id (str): Session ID of the anonymous user
            user_id (str): User ID of the registered user

        Returns:
            bool: Success status of transfer operation
        """
        try:
            # Validate document_id, session_id, and user_id parameters
            if not document_id or not session_id or not user_id:
                raise ValueError("document_id, session_id, and user_id must be provided")

            # Verify document belongs to specified session
            document = self.get_document(document_id, user_id=None, session_id=session_id, include_content=False)
            if not document:
                raise DocumentNotFoundError(document_id)

            # Call document repository to transfer document ownership
            success = self._document_repository.transfer_anonymous_document(document_id, session_id, user_id)

            # Call document storage to transfer content ownership
            self._document_storage.transfer_ownership(document_id, session_id, user_id)

            # Call version manager to transfer version ownership
            self._version_manager.transfer_anonymous_versions(document_id, session_id, user_id)

            logger.info(f"Transferred anonymous document: {document_id[:8]}...", session_id=session_id, user_id=user_id)
            return success
        except Exception as e:
            logger.error(f"Failed to transfer anonymous document: {str(e)}", exc_info=True)
            raise DocumentManagerError(f"Failed to transfer anonymous document: {str(e)}", e)

    def transfer_all_anonymous_documents(self, session_id: str, user_id: str) -> int:
        """Transfers all documents from an anonymous session to a registered user

        Args:
            session_id (str): Session ID of the anonymous user
            user_id (str): User ID of the registered user

        Returns:
            int: Number of documents transferred
        """
        try:
            # Validate session_id and user_id parameters
            if not session_id or not user_id:
                raise ValueError("session_id and user_id must be provided")

            # Retrieve list of documents for specified session
            documents, _ = self.get_session_documents(session_id)

            # For each document, call transfer_anonymous_document
            transferred_count = 0
            for document in documents:
                try:
                    if self.transfer_anonymous_document(document["_id"], session_id, user_id):
                        transferred_count += 1
                except Exception as e:
                    logger.warning(f"Failed to transfer document {document['_id'][:8]}...: {str(e)}", exc_info=True)

            logger.info(f"Transferred {transferred_count} anonymous documents to user: {user_id[:8]}...", session_id=session_id)
            return transferred_count
        except Exception as e:
            logger.error(f"Failed to transfer all anonymous documents: {str(e)}", exc_info=True)
            raise DocumentManagerError(f"Failed to transfer all anonymous documents: {str(e)}", e)

    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Returns the list of supported document formats for import/export

        Returns:
            Dict[str, List[str]]: Dictionary with import_formats and export_formats lists
        """
        try:
            # Call format_converter to get supported formats
            formats = self._format_converter.get_supported_formats()

            logger.debug("Retrieved supported formats")
            return formats
        except Exception as e:
            logger.error(f"Failed to get supported formats: {str(e)}", exc_info=True)
            raise DocumentManagerError(f"Failed to get supported formats: {str(e)}", e)