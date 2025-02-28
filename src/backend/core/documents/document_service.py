"""
High-level service that coordinates document operations in the AI writing enhancement platform,
providing a clean API for client code to perform document management, version control, and
AI suggestion integration. Handles business logic for both anonymous and authenticated users
with appropriate access controls.
"""

from typing import Dict, List, Tuple, Optional, Union
from datetime import datetime

from .document_manager import DocumentManager, DocumentManagerError, DocumentAccessError
from .version_manager import VersionManager, VersionManagerError, VersionNotFoundError
from .diff_service import DiffService
from ..ai.suggestion_generator import SuggestionGenerator, SuggestionGenerationError
from ..utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Define rate limits for anonymous users
ANONYMOUS_RATE_LIMIT_DOCUMENTS = 10
ANONYMOUS_RATE_LIMIT_PERIOD_HOURS = 24


class DocumentServiceError(Exception):
    """Base exception class for document service errors"""

    def __init__(self, message: str, original_error: Exception = None):
        """Initialize the document service error

        Args:
            message (str): Error message
            original_error (Exception): The original exception that caused this error
        """
        super().__init__(message)
        self.original_error = original_error


class DocumentAccessError(Exception):
    """Exception for document access permission errors"""

    def __init__(self, document_id: str, message: str):
        """Initialize the document access error

        Args:
            document_id (str): The document ID
            message (str): Error message
        """
        super().__init__(message)
        self.document_id = document_id


class AnonymousRateLimitError(Exception):
    """Exception for anonymous user rate limit exceeded"""

    def __init__(self, session_id: str, limit: int, period_hours: int):
        """Initialize the rate limit error

        Args:
            session_id (str): The session ID
            limit (int): The rate limit
            period_hours (int): The rate limit period in hours
        """
        message = f"Anonymous user with session {session_id} exceeded rate limit of {limit} documents per {period_hours} hours"
        super().__init__(message)
        self.session_id = session_id
        self.limit = limit
        self.period_hours = period_hours


class DocumentService:
    """
    Primary service that coordinates document operations and business logic in the application
    """

    def __init__(
        self,
        document_manager: DocumentManager,
        version_manager: VersionManager,
        diff_service: DiffService,
        suggestion_generator: SuggestionGenerator,
    ):
        """Initialize the document service with required dependencies

        Args:
            document_manager (DocumentManager): Document manager instance
            version_manager (VersionManager): Version manager instance
            diff_service (DiffService): Diff service instance
            suggestion_generator (SuggestionGenerator): Suggestion generator instance
        """
        self._document_manager = document_manager
        self._version_manager = version_manager
        self._diff_service = diff_service
        self._suggestion_generator = suggestion_generator
        self.logger = logger
        logger.info("Initialized DocumentService")

    def create_document(self, document_data: dict, user_id: str = None, session_id: str = None) -> dict:
        """Creates a new document with metadata and content

        Args:
            document_data (dict): Document data
            user_id (str): User ID
            session_id (str): Session ID

        Returns:
            dict: Created document metadata
        """
        try:
            # Validate user has permission to create document
            # Check anonymous rate limits if applicable
            if session_id and self._check_anonymous_rate_limit(session_id):
                raise AnonymousRateLimitError(session_id, ANONYMOUS_RATE_LIMIT_DOCUMENTS, ANONYMOUS_RATE_LIMIT_PERIOD_HOURS)

            # Delegate to document_manager.create_document
            document = self._document_manager.create_document(document_data, user_id, session_id)

            # Log document creation with masked ID
            logger.info(f"Created document: {document['_id'][:8]}...", user_id=user_id, session_id=session_id)

            # Return created document metadata
            return document
        except DocumentManagerError as e:
            logger.error(f"Failed to create document: {str(e)}", exc_info=True)
            raise
        except AnonymousRateLimitError as e:
            logger.error(f"Anonymous rate limit exceeded: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Failed to create document: {str(e)}", exc_info=True)
            raise DocumentServiceError(f"Failed to create document: {str(e)}", e)

    def get_document(self, document_id: str, user_id: str = None, session_id: str = None, include_content: bool = True) -> dict:
        """Retrieves a document by ID with access control

        Args:
            document_id (str): Document ID
            user_id (str): User ID
            session_id (str): Session ID
            include_content (bool): Include content

        Returns:
            dict: Document data
        """
        try:
            # Ensure either user_id or session_id is provided
            if not user_id and not session_id:
                raise ValueError("Either user_id or session_id must be provided")

            # Delegate to document_manager.get_document
            document = self._document_manager.get_document(document_id, user_id, session_id, include_content)

            # Log document retrieval with masked ID
            logger.info(f"Retrieved document: {document_id[:8]}...", user_id=user_id, session_id=session_id)

            # Return document with metadata and optional content
            return document
        except DocumentManagerError as e:
            logger.error(f"Failed to get document: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Failed to get document: {str(e)}", exc_info=True)
            raise DocumentServiceError(f"Failed to get document: {str(e)}", e)

    def update_document(self, document_id: str, document_data: dict, user_id: str = None, session_id: str = None, create_version: bool = False) -> dict:
        """Updates an existing document

        Args:
            document_id (str): Document ID
            document_data (dict): Document data
            user_id (str): User ID
            session_id (str): Session ID
            create_version (bool): Create version

        Returns:
            dict: Updated document metadata
        """
        try:
            # Ensure either user_id or session_id is provided
            if not user_id and not session_id:
                raise ValueError("Either user_id or session_id must be provided")

            # Delegate to document_manager.update_document
            document = self._document_manager.update_document(document_id, document_data, user_id, session_id, create_version)

            # Log document update with masked ID
            logger.info(f"Updated document: {document_id[:8]}...", user_id=user_id, session_id=session_id)

            # Return updated document metadata
            return document
        except DocumentManagerError as e:
            logger.error(f"Failed to update document: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Failed to update document: {str(e)}", exc_info=True)
            raise DocumentServiceError(f"Failed to update document: {str(e)}", e)

    def delete_document(self, document_id: str, user_id: str = None, session_id: str = None) -> bool:
        """Deletes a document

        Args:
            document_id (str): Document ID
            user_id (str): User ID
            session_id (str): Session ID

        Returns:
            bool: Success status
        """
        try:
            # Ensure either user_id or session_id is provided
            if not user_id and not session_id:
                raise ValueError("Either user_id or session_id must be provided")

            # Delegate to document_manager.delete_document
            success = self._document_manager.delete_document(document_id, user_id, session_id)

            # Log document deletion with masked ID
            logger.info(f"Deleted document: {document_id[:8]}...", user_id=user_id, session_id=session_id)

            # Return success status
            return success
        except DocumentManagerError as e:
            logger.error(f"Failed to delete document: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Failed to delete document: {str(e)}", exc_info=True)
            raise DocumentServiceError(f"Failed to delete document: {str(e)}", e)

    def list_documents(self, user_id: str = None, session_id: str = None, filters: dict = None, skip: int = 0, limit: int = 20) -> Tuple[List[dict], int]:
        """Lists documents for a user or session

        Args:
            user_id (str): User ID
            session_id (str): Session ID
            filters (dict): Filters
            skip (int): Skip
            limit (int): Limit

        Returns:
            Tuple[List[dict], int]: List of documents and total count
        """
        try:
            # Ensure either user_id or session_id is provided
            if not user_id and not session_id:
                raise ValueError("Either user_id or session_id must be provided")

            # Call document_manager.get_user_documents or document_manager.get_session_documents
            documents, total_count = self._document_manager.list_documents(user_id, session_id, filters, skip, limit)

            # Log document list retrieval with masked ID
            logger.info(f"Retrieved {len(documents)} documents", user_id=user_id, session_id=session_id)

            # Return tuple with document list and total count
            return documents, total_count
        except DocumentManagerError as e:
            logger.error(f"Failed to list documents: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Failed to list documents: {str(e)}", exc_info=True)
            raise DocumentServiceError(f"Failed to list documents: {str(e)}", e)

    def get_document_versions(self, document_id: str, user_id: str = None, session_id: str = None, limit: int = 10, skip: int = 0) -> Tuple[List[dict], int]:
        """Retrieves version history for a document

        Args:
            document_id (str): Document ID
            user_id (str): User ID
            session_id (str): Session ID
            limit (int): Limit
            skip (int): Skip

        Returns:
            Tuple[List[dict], int]: List of versions and total count
        """
        try:
            # Ensure either user_id or session_id is provided
            if not user_id and not session_id:
                raise ValueError("Either user_id or session_id must be provided")

            # Delegate to version_manager.get_version_history
            versions, total_count = self._version_manager.get_document_versions(document_id, user_id, session_id, limit, skip)

            # Log version history retrieval
            logger.info(f"Retrieved version history for document {document_id}", user_id=user_id, session_id=session_id)

            # Return tuple with versions list and total count
            return versions, total_count
        except VersionManagerError as e:
            logger.error(f"Failed to get document versions: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Failed to get document versions: {str(e)}", exc_info=True)
            raise DocumentServiceError(f"Failed to get document versions: {str(e)}", e)

    def get_document_version(self, document_id: str, version_id: str, user_id: str = None, session_id: str = None) -> dict:
        """Retrieves a specific version of a document

        Args:
            document_id (str): Document ID
            version_id (str): Version ID
            user_id (str): User ID
            session_id (str): Session ID

        Returns:
            dict: Version data
        """
        try:
            # Ensure either user_id or session_id is provided
            if not user_id and not session_id:
                raise ValueError("Either user_id or session_id must be provided")

            # Delegate to version_manager.get_version
            version = self._version_manager.get_document_version(document_id, version_id, user_id, session_id)

            # Log version retrieval
            logger.info(f"Retrieved version {version_id} for document {document_id}", user_id=user_id, session_id=session_id)

            # Return version data
            return version
        except VersionManagerError as e:
            logger.error(f"Failed to get document version: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Failed to get document version: {str(e)}", exc_info=True)
            raise DocumentServiceError(f"Failed to get document version: {str(e)}", e)

    def compare_document_versions(self, document_id: str, base_version_id: str, comparison_version_id: str, user_id: str = None, session_id: str = None, format: str = "track_changes") -> dict:
        """Compares two document versions and returns differences

        Args:
            document_id (str): Document ID
            base_version_id (str): Base version ID
            comparison_version_id (str): Comparison version ID
            user_id (str): User ID
            session_id (str): Session ID
            format (str): Format

        Returns:
            dict: Differences between versions
        """
        try:
            # Ensure either user_id or session_id is provided
            if not user_id and not session_id:
                raise ValueError("Either user_id or session_id must be provided")

            # Delegate to version_manager.compare_versions
            diff = self._version_manager.compare_document_versions(document_id, base_version_id, comparison_version_id, user_id, session_id, format)

            # Log comparison operation
            logger.info(f"Compared versions {base_version_id} and {comparison_version_id} for document {document_id}", user_id=user_id, session_id=session_id)

            # Return formatted diff result
            return diff
        except VersionManagerError as e:
            logger.error(f"Failed to compare document versions: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Failed to compare document versions: {str(e)}", exc_info=True)
            raise DocumentServiceError(f"Failed to compare document versions: {str(e)}", e)

    def import_document(self, content: str, format: str, title: str, user_id: str = None, session_id: str = None, metadata: dict = None) -> dict:
        """Imports a document from external content

        Args:
            content (str): Document content
            format (str): Document format
            title (str): Document title
            user_id (str): User ID
            session_id (str): Session ID
            metadata (dict): Metadata

        Returns:
            dict: Created document metadata
        """
        try:
            # Ensure either user_id or session_id is provided
            if not user_id and not session_id:
                raise ValueError("Either user_id or session_id must be provided")

            # Check anonymous rate limits if applicable
            if session_id and self._check_anonymous_rate_limit(session_id):
                raise AnonymousRateLimitError(session_id, ANONYMOUS_RATE_LIMIT_DOCUMENTS, ANONYMOUS_RATE_LIMIT_PERIOD_HOURS)

            # Delegate to document_manager.import_document
            document = self._document_manager.import_document(content, format, title, user_id, session_id, metadata)

            # Log document import with format information
            logger.info(f"Imported document: {document['title'][:20]}...", user_id=user_id, session_id=session_id, format=format)

            # Return created document metadata
            return document
        except DocumentManagerError as e:
            logger.error(f"Failed to import document: {str(e)}", exc_info=True)
            raise
        except AnonymousRateLimitError as e:
            logger.error(f"Anonymous rate limit exceeded: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Failed to import document: {str(e)}", exc_info=True)
            raise DocumentServiceError(f"Failed to import document: {str(e)}", e)

    def export_document(self, document_id: str, format: str, user_id: str = None, session_id: str = None, options: dict = None) -> dict:
        """Exports a document to a specified format

        Args:
            document_id (str): Document ID
            format (str): Document format
            user_id (str): User ID
            session_id (str): Session ID
            options (dict): Options

        Returns:
            dict: Export data
        """
        try:
            # Ensure either user_id or session_id is provided
            if not user_id and not session_id:
                raise ValueError("Either user_id or session_id must be provided")

            # Delegate to document_manager.export_document
            data = self._document_manager.export_document(document_id, format, user_id, session_id, options)

            # Log document export with format information
            logger.info(f"Exported document: {document_id[:8]}...", user_id=user_id, session_id=session_id, format=format)

            # Return export data
            return data
        except DocumentManagerError as e:
            logger.error(f"Failed to export document: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Failed to export document: {str(e)}", exc_info=True)
            raise DocumentServiceError(f"Failed to export document: {str(e)}", e)

    def generate_suggestions(self, document_id: str, prompt_type: str, user_id: str = None, session_id: str = None, options: dict = None) -> dict:
        """Generates AI-powered suggestions for document improvement

        Args:
            document_id (str): Document ID
            prompt_type (str): Prompt type
            user_id (str): User ID
            session_id (str): Session ID
            options (dict): Options

        Returns:
            dict: Generated suggestions
        """
        try:
            # Ensure either user_id or session_id is provided
            if not user_id and not session_id:
                raise ValueError("Either user_id or session_id must be provided")

            # Delegate to suggestion_generator.generate_suggestions
            suggestions = self._suggestion_generator.generate_suggestions(document_id, prompt_type, options, session_id)

            # Log suggestion generation with statistics
            logger.info(f"Generated suggestions for document {document_id}", user_id=user_id, session_id=session_id)

            # Return formatted suggestions with metadata
            return suggestions
        except SuggestionGenerationError as e:
            logger.error(f"Failed to generate suggestions: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Failed to generate suggestions: {str(e)}", exc_info=True)
            raise DocumentServiceError(f"Failed to generate suggestions: {str(e)}", e)

    def get_ai_suggestions(self, document_id: str, user_id: str = None, session_id: str = None, status: str = None) -> list:
        """Retrieves AI suggestions for a document

        Args:
            document_id (str): Document ID
            user_id (str): User ID
            session_id (str): Session ID
            status (str): Status

        Returns:
            list: List of AI suggestion versions
        """
        try:
            # Ensure either user_id or session_id is provided
            if not user_id and not session_id:
                raise ValueError("Either user_id or session_id must be provided")

            # Delegate to version_manager.get_ai_suggestions
            suggestions = self._version_manager.get_ai_suggestions(document_id, user_id, session_id, status)

            # Log AI suggestions retrieval
            logger.info(f"Retrieved AI suggestions for document {document_id}", user_id=user_id, session_id=session_id)

            # Return list of suggestion versions
            return suggestions
        except VersionManagerError as e:
            logger.error(f"Failed to get AI suggestions: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Failed to get AI suggestions: {str(e)}", exc_info=True)
            raise DocumentServiceError(f"Failed to get AI suggestions: {str(e)}", e)

    def accept_ai_suggestion(self, document_id: str, suggestion_id: str, user_id: str = None, session_id: str = None) -> dict:
        """Accepts an AI suggestion and applies it to create a new document version

        Args:
            document_id (str): Document ID
            suggestion_id (str): Suggestion ID
            user_id (str): User ID
            session_id (str): Session ID

        Returns:
            dict: Newly created document version
        """
        try:
            # Ensure either user_id or session_id is provided
            if not user_id and not session_id:
                raise ValueError("Either user_id or session_id must be provided")

            # Delegate to version_manager.accept_ai_suggestion
            version = self._version_manager.accept_ai_suggestion(document_id, suggestion_id, user_id, session_id)

            # Log suggestion acceptance
            logger.info(f"Accepted AI suggestion {suggestion_id} for document {document_id}", user_id=user_id, session_id=session_id)

            # Return new document version
            return version
        except VersionManagerError as e:
            logger.error(f"Failed to accept AI suggestion: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Failed to accept AI suggestion: {str(e)}", exc_info=True)
            raise DocumentServiceError(f"Failed to accept AI suggestion: {str(e)}", e)

    def reject_ai_suggestion(self, document_id: str, suggestion_id: str, user_id: str = None, session_id: str = None) -> bool:
        """Rejects an AI suggestion without applying changes

        Args:
            document_id (str): Document ID
            suggestion_id (str): Suggestion ID
            user_id (str): User ID
            session_id (str): Session ID

        Returns:
            bool: Success status
        """
        try:
            # Ensure either user_id or session_id is provided
            if not user_id and not session_id:
                raise ValueError("Either user_id or session_id must be provided")

            # Delegate to version_manager.reject_ai_suggestion
            success = self._version_manager.reject_ai_suggestion(document_id, suggestion_id, user_id, session_id)

            # Log suggestion rejection
            logger.info(f"Rejected AI suggestion {suggestion_id} for document {document_id}", user_id=user_id, session_id=session_id)

            # Return success status
            return success
        except VersionManagerError as e:
            logger.error(f"Failed to reject AI suggestion: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Failed to reject AI suggestion: {str(e)}", exc_info=True)
            raise DocumentServiceError(f"Failed to reject AI suggestion: {str(e)}", e)

    def partially_accept_ai_suggestion(self, document_id: str, suggestion_id: str, selected_change_ids: List[str], user_id: str = None, session_id: str = None) -> dict:
        """Partially accepts an AI suggestion

        Args:
            document_id (str): Document ID
            suggestion_id (str): Suggestion ID
            selected_change_ids (List[str]): Selected change IDs
            user_id (str): User ID
            session_id (str): Session ID

        Returns:
            dict: Newly created document version
        """
        try:
            # Ensure either user_id or session_id is provided
            if not user_id and not session_id:
                raise ValueError("Either user_id or session_id must be provided")

            # Delegate to version_manager.partially_accept_ai_suggestion
            version = self._version_manager.partially_accept_ai_suggestion(document_id, suggestion_id, selected_change_ids, user_id, session_id)

            # Log partial suggestion acceptance
            logger.info(f"Partially accepted AI suggestion {suggestion_id} for document {document_id}", user_id=user_id, session_id=session_id)

            # Return new document version
            return version
        except VersionManagerError as e:
            logger.error(f"Failed to partially accept AI suggestion: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Failed to partially accept AI suggestion: {str(e)}", exc_info=True)
            raise DocumentServiceError(f"Failed to partially accept AI suggestion: {str(e)}", e)

    def get_suggestion_difference(self, document_id: str, suggestion_id: str, format: str, user_id: str = None, session_id: str = None) -> dict:
        """Gets formatted differences between original content and AI suggestion

        Args:
            document_id (str): Document ID
            suggestion_id (str): Suggestion ID
            format (str): Format
            user_id (str): User ID
            session_id (str): Session ID

        Returns:
            dict: Formatted differences
        """
        try:
            # Ensure either user_id or session_id is provided
            if not user_id and not session_id:
                raise ValueError("Either user_id or session_id must be provided")

            # Delegate to version_manager.get_version_differences
            diff = self._version_manager.get_suggestion_difference(document_id, suggestion_id, format, user_id, session_id)

            # Log difference retrieval operation
            logger.info(f"Retrieved differences for suggestion {suggestion_id} for document {document_id}", user_id=user_id, session_id=session_id)

            # Return formatted differences
            return diff
        except VersionManagerError as e:
            logger.error(f"Failed to get suggestion difference: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Failed to get suggestion difference: {str(e)}", exc_info=True)
            raise DocumentServiceError(f"Failed to get suggestion difference: {str(e)}", e)

    def get_supported_suggestion_types(self) -> dict:
        """Returns the list of supported suggestion types

        Returns:
            dict: Dictionary of suggestion types
        """
        try:
            # Delegate to suggestion_generator.get_supported_suggestion_types
            types = self._suggestion_generator.get_supported_suggestion_types()

            # Return supported suggestion types dictionary
            return types
        except Exception as e:
            logger.error(f"Failed to get supported suggestion types: {str(e)}", exc_info=True)
            raise DocumentServiceError(f"Failed to get supported suggestion types: {str(e)}", e)

    def transfer_anonymous_documents(self, session_id: str, user_id: str) -> int:
        """Transfers all documents from an anonymous session to a registered user

        Args:
            session_id (str): Session ID
            user_id (str): User ID

        Returns:
            int: Number of documents transferred
        """
        try:
            # Validate session_id and user_id parameters
            if not session_id or not user_id:
                raise ValueError("session_id and user_id must be provided")

            # Delegate to document_manager.transfer_all_anonymous_documents
            count = self._document_manager.transfer_all_anonymous_documents(session_id, user_id)

            # Log transfer operation with count
            logger.info(f"Transferred {count} anonymous documents to user: {user_id[:8]}...", session_id=session_id)

            # Return count of transferred documents
            return count
        except DocumentManagerError as e:
            logger.error(f"Failed to transfer anonymous documents: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Failed to transfer anonymous documents: {str(e)}", exc_info=True)
            raise DocumentServiceError(f"Failed to transfer anonymous documents: {str(e)}", e)

    def _check_anonymous_rate_limit(self, session_id: str) -> bool:
        """Internal method to check if anonymous user has exceeded rate limits

        Args:
            session_id (str): Session ID

        Returns:
            bool: True if rate limit is exceeded
        """
        # If no session_id provided, return False (not applicable)
        if not session_id:
            return False

        # Count documents created by this session in the rate limit period
        # Compare count to ANONYMOUS_RATE_LIMIT_DOCUMENTS
        # If exceeded, log rate limit event
        # Return True if limit exceeded, False otherwise
        return False