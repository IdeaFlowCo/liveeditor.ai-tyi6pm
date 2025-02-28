"""
Core service that manages document versioning for the AI writing enhancement platform,
handling version creation, retrieval, comparison, and lifecycle management. Supports
different version types including major (user saves), minor (auto-saves), and AI suggestions
with appropriate retention policies. Integrates with the track changes system to enable
reviewing and accepting/rejecting AI-generated improvements.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import uuid

from ...data.mongodb.repositories.version_repository import (
    VersionRepository, 
    VersionType, 
    VersionNotFoundError, 
    VersionAccessError
)
from .diff_service import DiffService
from ..utils.logger import get_logger

# Configure logger
logger = get_logger(__name__)

# Retention policy settings (None = keep forever)
MAJOR_VERSION_RETENTION_DAYS = None  # Major versions are kept indefinitely
MINOR_VERSION_RETENTION_HOURS = 24  # Minor versions (auto-save) kept for 24 hours
AI_SUGGESTION_RETENTION_DAYS = 30  # AI suggestions kept for 30 days


class VersionManagerError(Exception):
    """Base exception class for version manager errors"""
    
    def __init__(self, message, original_error=None):
        """
        Initialize the version manager error
        
        Args:
            message: Error message
            original_error: Original exception that caused this error
        """
        super().__init__(message)
        self.original_error = original_error


class VersionManager:
    """
    Manages document versioning operations including creation, retrieval, comparison,
    and lifecycle management
    """
    
    def __init__(self, version_repository: VersionRepository, diff_service: DiffService):
        """
        Initializes the version manager with required dependencies
        
        Args:
            version_repository: Repository for version storage and retrieval
            diff_service: Service for comparing text and generating differences
        """
        self._version_repository = version_repository
        self._diff_service = diff_service
        logger.info("Initialized VersionManager")
    
    def create_version(self, document_id: str, content: str, user_id: str = None, 
                      session_id: str = None, change_description: str = None) -> Dict[str, Any]:
        """
        Creates a new major version of a document
        
        Args:
            document_id: Document ID
            content: Document content
            user_id: User ID (required for authenticated users)
            session_id: Session ID (required for anonymous users)
            change_description: Optional description of changes
            
        Returns:
            Created version metadata
            
        Raises:
            VersionManagerError: If version creation fails
        """
        # Validate user has access (either user_id or session_id must be provided)
        if not user_id and not session_id:
            raise VersionManagerError("Either user_id or session_id must be provided")
        
        try:
            # Prepare version data
            version_data = {
                "documentId": document_id,
                "content": content,
                "type": VersionType.MAJOR.value,
                "metadata": {}
            }
            
            # Add user ID or session ID
            if user_id:
                version_data["userId"] = user_id
            if session_id:
                version_data["sessionId"] = session_id
                
            # Add change description if provided
            if change_description:
                version_data["metadata"]["changeDescription"] = change_description
            
            # Create version in repository
            version = self._version_repository.create_version(version_data)
            
            # Schedule cleanup of older minor versions
            self._version_repository.cleanup_minor_versions(document_id, MINOR_VERSION_RETENTION_HOURS)
            
            logger.info(f"Created major version {version.get('versionNumber')} for document {document_id}")
            
            return version
            
        except Exception as e:
            logger.error(f"Failed to create version: {str(e)}")
            raise VersionManagerError(f"Failed to create version: {str(e)}", e)
    
    def create_auto_save_version(self, document_id: str, content: str, user_id: str = None, 
                              session_id: str = None) -> Dict[str, Any]:
        """
        Creates a minor auto-save version of a document
        
        Args:
            document_id: Document ID
            content: Document content
            user_id: User ID (required for authenticated users)
            session_id: Session ID (required for anonymous users)
            
        Returns:
            Created auto-save version metadata
            
        Raises:
            VersionManagerError: If version creation fails
        """
        # Validate user has access (either user_id or session_id must be provided)
        if not user_id and not session_id:
            raise VersionManagerError("Either user_id or session_id must be provided")
        
        try:
            # Prepare version data
            version_data = {
                "documentId": document_id,
                "content": content,
                "type": VersionType.MINOR.value,
                "metadata": {
                    "isAutoSave": True,
                    "autoSaveTimestamp": datetime.utcnow().isoformat()
                }
            }
            
            # Add user ID or session ID
            if user_id:
                version_data["userId"] = user_id
            if session_id:
                version_data["sessionId"] = session_id
            
            # Create version in repository
            version = self._version_repository.create_version(version_data)
            
            logger.info(f"Created auto-save version {version.get('versionNumber')} for document {document_id}")
            
            return version
            
        except Exception as e:
            logger.error(f"Failed to create auto-save version: {str(e)}")
            raise VersionManagerError(f"Failed to create auto-save version: {str(e)}", e)
    
    def create_ai_suggestion_version(self, document_id: str, original_content: str,
                                  suggested_content: str, suggestion_metadata: Dict[str, Any],
                                  user_id: str = None, session_id: str = None) -> Dict[str, Any]:
        """
        Creates a version containing AI-suggested improvements
        
        Args:
            document_id: Document ID
            original_content: Original document content
            suggested_content: AI-suggested content
            suggestion_metadata: Metadata about the suggestion (prompt, model, etc.)
            user_id: User ID (required for authenticated users)
            session_id: Session ID (required for anonymous users)
            
        Returns:
            Created AI suggestion version metadata
            
        Raises:
            VersionManagerError: If version creation fails
        """
        # Validate user has access (either user_id or session_id must be provided)
        if not user_id and not session_id:
            raise VersionManagerError("Either user_id or session_id must be provided")
        
        try:
            # Generate diff between original and suggested content
            diff_result = self._diff_service.compare_texts(original_content, suggested_content)
            
            # Prepare version data
            version_data = {
                "documentId": document_id,
                "content": suggested_content,
                "type": VersionType.AI_SUGGESTION.value,
                "metadata": {
                    "suggestionType": suggestion_metadata.get("type", "general"),
                    "model": suggestion_metadata.get("model", "unknown"),
                    "prompt": suggestion_metadata.get("prompt", ""),
                    "status": "pending",
                    "diff": diff_result,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            # Merge any additional metadata
            version_data["metadata"].update(suggestion_metadata)
            
            # Add user ID or session ID
            if user_id:
                version_data["userId"] = user_id
            if session_id:
                version_data["sessionId"] = session_id
            
            # Create version in repository
            version = self._version_repository.create_version(version_data)
            
            logger.info(f"Created AI suggestion version {version.get('versionNumber')} for document {document_id}")
            
            return version
            
        except Exception as e:
            logger.error(f"Failed to create AI suggestion version: {str(e)}")
            raise VersionManagerError(f"Failed to create AI suggestion version: {str(e)}", e)
    
    def get_version(self, version_id: str, user_id: str = None, session_id: str = None) -> Dict[str, Any]:
        """
        Retrieves a specific document version by its ID
        
        Args:
            version_id: Version ID
            user_id: User ID for access validation
            session_id: Session ID for access validation
            
        Returns:
            Version data and content
            
        Raises:
            VersionNotFoundError: If version not found
            VersionAccessError: If user doesn't have access to the version
        """
        try:
            # Get version from repository
            version = self._version_repository.get_version(version_id)
            
            # Verify user has access
            self._verify_version_access(version, user_id, session_id)
            
            logger.debug(f"Retrieved version {version_id}")
            
            return version
            
        except VersionNotFoundError as e:
            logger.warning(f"Version not found: {version_id}")
            raise
        except VersionAccessError as e:
            logger.warning(f"Access denied to version {version_id}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving version {version_id}: {str(e)}")
            raise VersionManagerError(f"Error retrieving version: {str(e)}", e)
    
    def get_latest_version(self, document_id: str, user_id: str = None, 
                          session_id: str = None, version_type: VersionType = None) -> Optional[Dict[str, Any]]:
        """
        Retrieves the latest version of a document
        
        Args:
            document_id: Document ID
            user_id: User ID for access validation
            session_id: Session ID for access validation
            version_type: Optional filter for version type
            
        Returns:
            Latest version data with content, or None if no versions exist
        """
        try:
            # Get latest version from repository
            version = self._version_repository.get_latest_version(document_id, version_type)
            
            # If no version found, return None
            if not version:
                return None
            
            # Verify user has access
            self._verify_version_access(version, user_id, session_id)
            
            logger.debug(f"Retrieved latest version for document {document_id}")
            
            return version
            
        except VersionAccessError as e:
            logger.warning(f"Access denied to latest version of document {document_id}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving latest version for document {document_id}: {str(e)}")
            raise VersionManagerError(f"Error retrieving latest version: {str(e)}", e)
    
    def get_version_history(self, document_id: str, user_id: str = None, session_id: str = None,
                          limit: int = 10, skip: int = 0, 
                          version_type: VersionType = None) -> Tuple[List[Dict[str, Any]], int]:
        """
        Retrieves version history for a document
        
        Args:
            document_id: Document ID
            user_id: User ID for access validation
            session_id: Session ID for access validation
            limit: Maximum number of versions to return
            skip: Number of versions to skip (for pagination)
            version_type: Optional filter for version type
            
        Returns:
            Tuple of (List of versions, total count)
        """
        try:
            # Get version history from repository
            versions, total_count = self._version_repository.get_version_history(
                document_id, limit, skip, version_type
            )
            
            # Filter versions to ensure user has access
            accessible_versions = []
            for version in versions:
                try:
                    self._verify_version_access(version, user_id, session_id)
                    accessible_versions.append(version)
                except VersionAccessError:
                    # Skip versions the user doesn't have access to
                    pass
            
            logger.debug(f"Retrieved version history for document {document_id}")
            
            return accessible_versions, total_count
            
        except Exception as e:
            logger.error(f"Error retrieving version history for document {document_id}: {str(e)}")
            raise VersionManagerError(f"Error retrieving version history: {str(e)}", e)
    
    def compare_versions(self, base_version_id: str, comparison_version_id: str,
                       user_id: str = None, session_id: str = None, 
                       format: str = "track_changes", diff_options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Compares two document versions and returns differences
        
        Args:
            base_version_id: Base version ID to compare from
            comparison_version_id: Version ID to compare to
            user_id: User ID for access validation
            session_id: Session ID for access validation
            format: Output format (track_changes, inline, unified)
            diff_options: Options for diff generation
            
        Returns:
            Differences between versions in requested format
        """
        try:
            # Get both versions
            base_version = self.get_version(base_version_id, user_id, session_id)
            comparison_version = self.get_version(comparison_version_id, user_id, session_id)
            
            # Extract content from versions
            base_content = base_version.get("content", "")
            comparison_content = comparison_version.get("content", "")
            
            # Generate diff
            diff_result = self._diff_service.compare_texts(base_content, comparison_content, 
                                                         options=diff_options)
            
            # Format diff according to requested output format
            formatted_diff = self._diff_service.format_for_display(diff_result, format)
            
            logger.info(f"Compared versions {base_version_id} and {comparison_version_id}")
            
            return formatted_diff
            
        except VersionNotFoundError as e:
            logger.warning(f"Version not found during comparison: {str(e)}")
            raise
        except VersionAccessError as e:
            logger.warning(f"Access denied during version comparison: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error comparing versions: {str(e)}")
            raise VersionManagerError(f"Error comparing versions: {str(e)}", e)
    
    def get_ai_suggestions(self, document_id: str, user_id: str = None, 
                         session_id: str = None, status: str = None) -> List[Dict[str, Any]]:
        """
        Retrieves AI suggestion versions for a document
        
        Args:
            document_id: Document ID
            user_id: User ID for access validation
            session_id: Session ID for access validation
            status: Optional filter by suggestion status (pending, accepted, rejected)
            
        Returns:
            List of AI suggestion versions
        """
        try:
            # Get AI suggestions from repository
            suggestions = self._version_repository.get_ai_suggestion_versions(document_id, status)
            
            # Filter suggestions to ensure user has access
            accessible_suggestions = []
            for suggestion in suggestions:
                try:
                    self._verify_version_access(suggestion, user_id, session_id)
                    accessible_suggestions.append(suggestion)
                except VersionAccessError:
                    # Skip suggestions the user doesn't have access to
                    pass
            
            logger.debug(f"Retrieved AI suggestions for document {document_id}")
            
            return accessible_suggestions
            
        except Exception as e:
            logger.error(f"Error retrieving AI suggestions for document {document_id}: {str(e)}")
            raise VersionManagerError(f"Error retrieving AI suggestions: {str(e)}", e)
    
    def accept_ai_suggestion(self, document_id: str, suggestion_id: str, 
                          user_id: str = None, session_id: str = None) -> Dict[str, Any]:
        """
        Accepts an AI suggestion and applies it to create a new document version
        
        Args:
            document_id: Document ID
            suggestion_id: Suggestion version ID
            user_id: User ID for access validation
            session_id: Session ID for access validation
            
        Returns:
            Newly created document version with accepted changes
        """
        try:
            # Get suggestion version
            suggestion = self.get_version(suggestion_id, user_id, session_id)
            
            # Validate suggestion belongs to document
            if str(suggestion.get("documentId")) != str(document_id):
                raise VersionManagerError(f"Suggestion {suggestion_id} does not belong to document {document_id}")
            
            # Get latest major version as base
            base_version = self.get_latest_version(document_id, user_id, session_id, VersionType.MAJOR)
            
            if not base_version:
                raise VersionManagerError(f"No base version found for document {document_id}")
            
            # Create new major version with suggested content
            new_version = self.create_version(
                document_id=document_id,
                content=suggestion.get("content", ""),
                user_id=user_id,
                session_id=session_id,
                change_description=f"Accepted AI suggestion {suggestion_id}"
            )
            
            # Mark suggestion as accepted
            self._version_repository.mark_suggestion_status(suggestion_id, "accepted")
            
            logger.info(f"Accepted AI suggestion {suggestion_id} for document {document_id}")
            
            return new_version
            
        except VersionNotFoundError as e:
            logger.warning(f"Version not found during suggestion acceptance: {str(e)}")
            raise
        except VersionAccessError as e:
            logger.warning(f"Access denied during suggestion acceptance: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error accepting AI suggestion: {str(e)}")
            raise VersionManagerError(f"Error accepting AI suggestion: {str(e)}", e)
    
    def reject_ai_suggestion(self, document_id: str, suggestion_id: str, 
                          user_id: str = None, session_id: str = None) -> bool:
        """
        Rejects an AI suggestion without applying changes
        
        Args:
            document_id: Document ID
            suggestion_id: Suggestion version ID
            user_id: User ID for access validation
            session_id: Session ID for access validation
            
        Returns:
            True if rejection was successful
        """
        try:
            # Get suggestion version
            suggestion = self.get_version(suggestion_id, user_id, session_id)
            
            # Validate suggestion belongs to document
            if str(suggestion.get("documentId")) != str(document_id):
                raise VersionManagerError(f"Suggestion {suggestion_id} does not belong to document {document_id}")
            
            # Mark suggestion as rejected
            result = self._version_repository.mark_suggestion_status(suggestion_id, "rejected")
            
            # Schedule cleanup of rejected suggestion
            if result and AI_SUGGESTION_RETENTION_DAYS is not None:
                self._version_repository.cleanup_ai_suggestions(document_id, AI_SUGGESTION_RETENTION_DAYS)
            
            logger.info(f"Rejected AI suggestion {suggestion_id} for document {document_id}")
            
            return result
            
        except VersionNotFoundError as e:
            logger.warning(f"Version not found during suggestion rejection: {str(e)}")
            raise
        except VersionAccessError as e:
            logger.warning(f"Access denied during suggestion rejection: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error rejecting AI suggestion: {str(e)}")
            raise VersionManagerError(f"Error rejecting AI suggestion: {str(e)}", e)
    
    def partially_accept_ai_suggestion(self, document_id: str, suggestion_id: str, 
                                    selected_change_ids: List[str], 
                                    user_id: str = None, session_id: str = None) -> Dict[str, Any]:
        """
        Accepts only selected changes from an AI suggestion
        
        Args:
            document_id: Document ID
            suggestion_id: Suggestion version ID
            selected_change_ids: IDs of specific changes to accept
            user_id: User ID for access validation
            session_id: Session ID for access validation
            
        Returns:
            Newly created document version with selected changes
        """
        try:
            # Get suggestion version
            suggestion = self.get_version(suggestion_id, user_id, session_id)
            
            # Validate suggestion belongs to document
            if str(suggestion.get("documentId")) != str(document_id):
                raise VersionManagerError(f"Suggestion {suggestion_id} does not belong to document {document_id}")
            
            # Get latest major version as base
            base_version = self.get_latest_version(document_id, user_id, session_id, VersionType.MAJOR)
            
            if not base_version:
                raise VersionManagerError(f"No base version found for document {document_id}")
            
            # Get diff data from suggestion metadata
            diff_data = suggestion.get("metadata", {}).get("diff", {})
            
            if not diff_data:
                raise VersionManagerError(f"No diff data found in suggestion {suggestion_id}")
            
            # Get base content
            base_content = base_version.get("content", "")
            
            # Apply selected changes
            modified_content = self._diff_service.apply_selected_changes(
                base_content, diff_data, selected_change_ids
            )
            
            # Create new major version with selectively modified content
            new_version = self.create_version(
                document_id=document_id,
                content=modified_content,
                user_id=user_id,
                session_id=session_id,
                change_description=f"Partially accepted AI suggestion {suggestion_id}"
            )
            
            # Mark suggestion as partially accepted
            self._version_repository.mark_suggestion_status(suggestion_id, "partially_accepted")
            
            logger.info(f"Partially accepted AI suggestion {suggestion_id} for document {document_id}")
            
            return new_version
            
        except VersionNotFoundError as e:
            logger.warning(f"Version not found during partial suggestion acceptance: {str(e)}")
            raise
        except VersionAccessError as e:
            logger.warning(f"Access denied during partial suggestion acceptance: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error partially accepting AI suggestion: {str(e)}")
            raise VersionManagerError(f"Error partially accepting AI suggestion: {str(e)}", e)
    
    def cleanup_versions(self, document_id: str) -> Dict[str, int]:
        """
        Performs cleanup of document versions based on retention policies
        
        Args:
            document_id: Document ID
            
        Returns:
            Counts of versions cleaned up by type
        """
        try:
            cleanup_results = {
                "minor_versions": 0,
                "ai_suggestions": 0
            }
            
            # Cleanup minor versions
            if MINOR_VERSION_RETENTION_HOURS is not None:
                minor_count = self._version_repository.cleanup_minor_versions(
                    document_id, MINOR_VERSION_RETENTION_HOURS
                )
                cleanup_results["minor_versions"] = minor_count
            
            # Cleanup rejected AI suggestions
            if AI_SUGGESTION_RETENTION_DAYS is not None:
                ai_count = self._version_repository.cleanup_ai_suggestions(
                    document_id, AI_SUGGESTION_RETENTION_DAYS
                )
                cleanup_results["ai_suggestions"] = ai_count
            
            logger.info(f"Cleaned up versions for document {document_id}: {cleanup_results}")
            
            return cleanup_results
            
        except Exception as e:
            logger.error(f"Error cleaning up versions for document {document_id}: {str(e)}")
            raise VersionManagerError(f"Error cleaning up versions: {str(e)}", e)
    
    def transfer_anonymous_versions(self, document_id: str, session_id: str, user_id: str) -> int:
        """
        Transfers ownership of document versions from anonymous session to registered user
        
        Args:
            document_id: Document ID
            session_id: Anonymous session ID to transfer from
            user_id: User ID to transfer ownership to
            
        Returns:
            Number of versions transferred
        """
        try:
            # Transfer version ownership in repository
            count = self._version_repository.transfer_version_ownership(
                document_id, session_id, user_id
            )
            
            logger.info(f"Transferred {count} versions for document {document_id} from session {session_id} to user {user_id}")
            
            return count
            
        except Exception as e:
            logger.error(f"Error transferring version ownership: {str(e)}")
            raise VersionManagerError(f"Error transferring version ownership: {str(e)}", e)
    
    def get_version_differences(self, suggestion_id: str, format: str = "track_changes",
                              user_id: str = None, session_id: str = None) -> Dict[str, Any]:
        """
        Gets the differences between original document content and suggestion
        
        Args:
            suggestion_id: Suggestion version ID
            format: Output format (track_changes, inline, unified)
            user_id: User ID for access validation
            session_id: Session ID for access validation
            
        Returns:
            Formatted differences between original and suggested content
        """
        try:
            # Get suggestion version
            suggestion = self.get_version(suggestion_id, user_id, session_id)
            
            # Verify it's an AI suggestion
            if suggestion.get("type") != VersionType.AI_SUGGESTION.value:
                raise VersionManagerError(f"Version {suggestion_id} is not an AI suggestion")
            
            # Get diff data from metadata
            diff_data = suggestion.get("metadata", {}).get("diff", {})
            
            if not diff_data:
                raise VersionManagerError(f"No diff data found in suggestion {suggestion_id}")
            
            # Format diff according to requested output format
            formatted_diff = self._diff_service.format_for_display(diff_data, format)
            
            logger.debug(f"Retrieved version differences for suggestion {suggestion_id}")
            
            return formatted_diff
            
        except VersionNotFoundError as e:
            logger.warning(f"Version not found when getting differences: {str(e)}")
            raise
        except VersionAccessError as e:
            logger.warning(f"Access denied when getting differences: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error getting version differences: {str(e)}")
            raise VersionManagerError(f"Error getting version differences: {str(e)}", e)
    
    def _verify_version_access(self, version: Dict[str, Any], user_id: str = None, session_id: str = None) -> bool:
        """
        Verifies user has access to a specific version
        
        Args:
            version: Version data to check
            user_id: User ID for access validation
            session_id: Session ID for access validation
            
        Returns:
            True if user has access
            
        Raises:
            VersionAccessError: If user doesn't have access to the version
        """
        version_user_id = version.get("userId")
        version_session_id = version.get("sessionId")
        
        # Grant access if version has no owner
        if not version_user_id and not version_session_id:
            return True
        
        # Check user ID match
        if user_id and version_user_id and str(user_id) == str(version_user_id):
            return True
        
        # Check session ID match
        if session_id and version_session_id and session_id == version_session_id:
            return True
        
        # No access match found
        raise VersionAccessError(
            version_id=version.get("_id", ""),
            user_id=user_id,
            session_id=session_id,
            message="User does not have access to this version"
        )