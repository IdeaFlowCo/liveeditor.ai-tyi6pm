"""
Manages anonymous user sessions for the AI writing enhancement application, providing 
functionality to create, retrieve, and upgrade anonymous sessions to authenticated ones.
Implements session-based tracking for users who want to use the system without logging in.
"""

import uuid  # standard library
import time  # standard library
from typing import Dict, List, Optional, Any, Tuple  # standard library

from flask import request, current_app  # Flask ~=2.3.0

from ../../core/utils/logger import get_logger
from ../../data/redis/session_store import SessionStore
from ../../core/utils/validators import is_valid_uuid

# Anonymous session constants
ANONYMOUS_SESSION_COOKIE_NAME = 'anonymous_session'
ANONYMOUS_SESSION_TTL = 86400  # 24 hours in seconds
SESSION_EXTENSION_THRESHOLD = 3600  # 1 hour in seconds

# Initialize logger and session store
logger = get_logger(__name__)
_session_store = SessionStore()


def create_anonymous_session(initial_data: Dict = None) -> str:
    """
    Creates a new anonymous session with a unique identifier.
    
    Args:
        initial_data: Optional initial data for the session
        
    Returns:
        Anonymous session identifier
    """
    session_id = str(uuid.uuid4())
    
    if initial_data is None:
        initial_data = {}
    
    # Ensure required fields are present
    if 'documents' not in initial_data:
        initial_data['documents'] = []
    
    # Add creation timestamp
    initial_data['creation_timestamp'] = int(time.time())
    
    # Create the session
    _session_store.create_anonymous_session(initial_data)
    
    # Log session creation with partially masked ID for security
    masked_id = session_id[:8] + "..." + session_id[-4:]
    logger.info(f"Created anonymous session {masked_id}")
    
    return session_id


def get_anonymous_session(session_id: str) -> Optional[Dict]:
    """
    Retrieves an anonymous session by session ID.
    
    Args:
        session_id: The session ID to retrieve
        
    Returns:
        Session data or None if not found or expired
    """
    if not is_valid_uuid(session_id):
        logger.warning(f"Invalid session ID format: {session_id}")
        return None
    
    session_data = _session_store.get_session(session_id)
    
    if not session_data:
        logger.debug(f"Session not found: {session_id[:8]}...")
        return None
    
    # Check if session is close to expiration and extend if needed
    now = int(time.time())
    creation_time = session_data.get('creation_timestamp', now)
    time_elapsed = now - creation_time
    
    if time_elapsed > (ANONYMOUS_SESSION_TTL - SESSION_EXTENSION_THRESHOLD):
        # Session is close to expiration, extend it
        extend_session_ttl(session_id)
        logger.debug(f"Extended TTL for session approaching expiration: {session_id[:8]}...")
    
    return session_data


def update_anonymous_session(session_id: str, data: Dict) -> bool:
    """
    Updates an existing anonymous session with new data.
    
    Args:
        session_id: The session ID to update
        data: New data to merge with existing session data
        
    Returns:
        True if session was updated, False if not found
    """
    if not is_valid_uuid(session_id):
        logger.warning(f"Invalid session ID format: {session_id}")
        return False
    
    # Get existing session
    existing_session = get_anonymous_session(session_id)
    if not existing_session:
        logger.warning(f"Attempted to update non-existent session: {session_id[:8]}...")
        return False
    
    # Update last modified timestamp
    data['last_updated_timestamp'] = int(time.time())
    
    # Update the session
    result = _session_store.update_session(session_id, data)
    
    if result:
        logger.debug(f"Updated anonymous session {session_id[:8]}...")
    else:
        logger.warning(f"Failed to update anonymous session {session_id[:8]}...")
    
    return result


def delete_anonymous_session(session_id: str) -> bool:
    """
    Deletes an anonymous session.
    
    Args:
        session_id: The session ID to delete
        
    Returns:
        True if session was deleted, False if not found
    """
    if not is_valid_uuid(session_id):
        logger.warning(f"Invalid session ID format: {session_id}")
        return False
    
    result = _session_store.delete_session(session_id)
    
    if result:
        logger.info(f"Deleted anonymous session {session_id[:8]}...")
    else:
        logger.debug(f"Attempted to delete non-existent session: {session_id[:8]}...")
    
    return result


def add_document_to_session(session_id: str, document_id: str, document_title: str) -> bool:
    """
    Adds a document reference to an anonymous session.
    
    Args:
        session_id: The session ID
        document_id: ID of the document to add
        document_title: Title of the document
        
    Returns:
        True if document was added, False if session not found
    """
    # Get existing session
    session_data = get_anonymous_session(session_id)
    if not session_data:
        logger.warning(f"Attempted to add document to non-existent session: {session_id[:8]}...")
        return False
    
    # Get or initialize documents list
    documents = session_data.get('documents', [])
    
    # Create document entry
    document_entry = {
        'id': document_id,
        'title': document_title,
        'timestamp': int(time.time())
    }
    
    # Append to list
    documents.append(document_entry)
    
    # Update session
    update_data = {'documents': documents}
    result = update_anonymous_session(session_id, update_data)
    
    if result:
        logger.info(f"Added document {document_id[:8]}... to session {session_id[:8]}...")
    
    return result


def get_session_documents(session_id: str) -> List:
    """
    Retrieves the list of documents associated with an anonymous session.
    
    Args:
        session_id: The session ID
        
    Returns:
        List of document references or empty list if none or session not found
    """
    # Get existing session
    session_data = get_anonymous_session(session_id)
    if not session_data:
        logger.debug(f"Attempted to get documents from non-existent session: {session_id[:8]}...")
        return []
    
    # Get documents list or empty list if not found
    documents = session_data.get('documents', [])
    return documents


def extend_session_ttl(session_id: str) -> bool:
    """
    Extends the time-to-live of an anonymous session.
    
    Args:
        session_id: The session ID
        
    Returns:
        True if session TTL was extended, False if not found
    """
    if not is_valid_uuid(session_id):
        logger.warning(f"Invalid session ID format: {session_id}")
        return False
    
    result = _session_store.extend_session(session_id, ANONYMOUS_SESSION_TTL)
    
    if result:
        logger.debug(f"Extended TTL for session {session_id[:8]}...")
    else:
        logger.warning(f"Failed to extend TTL for non-existent session: {session_id[:8]}...")
    
    return result


def upgrade_to_authenticated(anonymous_session_id: str, user_id: str) -> Optional[str]:
    """
    Upgrades an anonymous session to an authenticated session.
    
    Args:
        anonymous_session_id: The anonymous session ID to upgrade
        user_id: User ID to associate with the authenticated session
        
    Returns:
        New authenticated session ID or None if upgrade failed
    """
    if not is_valid_uuid(anonymous_session_id):
        logger.warning(f"Invalid session ID format: {anonymous_session_id}")
        return None
    
    # Get anonymous session
    session_data = get_anonymous_session(anonymous_session_id)
    if not session_data:
        logger.warning(f"Attempted to upgrade non-existent session: {anonymous_session_id[:8]}...")
        return None
    
    # Upgrade the session
    authenticated_session_id = _session_store.upgrade_session(anonymous_session_id, user_id)
    
    if authenticated_session_id:
        masked_user_id = user_id[:4] + "..." if len(user_id) > 8 else user_id
        logger.info(f"Upgraded anonymous session {anonymous_session_id[:8]}... to authenticated session for user {masked_user_id}")
    else:
        logger.error(f"Failed to upgrade anonymous session {anonymous_session_id[:8]}...")
    
    return authenticated_session_id


def get_current_session_id() -> Optional[str]:
    """
    Gets the current anonymous session ID from cookie or request.
    
    Returns:
        Current session ID or None if not found
    """
    # Try to get from cookie
    session_id = None
    
    try:
        if hasattr(request, 'cookies'):
            session_id = request.cookies.get(ANONYMOUS_SESSION_COOKIE_NAME)
        
        # If not in cookie, try to get from header
        if not session_id and hasattr(request, 'headers'):
            session_id = request.headers.get('X-Anonymous-Session-ID')
        
        # Validate UUID format
        if session_id and not is_valid_uuid(session_id):
            logger.warning(f"Invalid session ID format in request: {session_id}")
            return None
        
        return session_id
    except Exception as e:
        logger.error(f"Error getting session ID from request: {str(e)}")
        return None


def set_session_cookie(session_id: str, response) -> Any:
    """
    Sets the anonymous session ID cookie in the response.
    
    Args:
        session_id: The session ID to set in the cookie
        response: Flask response object
        
    Returns:
        Flask response object with cookie set
    """
    if not is_valid_uuid(session_id):
        logger.warning(f"Invalid session ID format: {session_id}")
        return response
    
    # Set the cookie with appropriate security settings
    max_age = ANONYMOUS_SESSION_TTL
    secure = current_app.config.get('SESSION_COOKIE_SECURE', False)
    httponly = True
    samesite = 'Lax'
    
    response.set_cookie(
        ANONYMOUS_SESSION_COOKIE_NAME,
        session_id,
        max_age=max_age,
        secure=secure,
        httponly=httponly,
        samesite=samesite
    )
    
    return response


class AnonymousSessionManager:
    """
    Class for managing anonymous user sessions with integrated Flask support.
    """
    
    def __init__(self, session_store=None):
        """
        Initialize the anonymous session manager.
        
        Args:
            session_store: Optional session store instance (uses global by default)
        """
        self._session_store = session_store or _session_store
        self._logger = logger
    
    def initialize_session(self) -> Tuple[str, Dict, bool]:
        """
        Creates a new anonymous session or retrieves existing one from request.
        
        Returns:
            Tuple of (session_id, session_data, is_new_session)
        """
        # Try to get existing session ID
        session_id = get_current_session_id()
        is_new_session = False
        
        if session_id:
            # Retrieve existing session
            session_data = get_anonymous_session(session_id)
            if session_data:
                self._logger.debug(f"Retrieved existing anonymous session {session_id[:8]}...")
                return session_id, session_data, is_new_session
        
        # Create new session if no valid session was found
        is_new_session = True
        session_id = create_anonymous_session()
        session_data = get_anonymous_session(session_id)
        
        self._logger.info(f"Created new anonymous session {session_id[:8]}...")
        return session_id, session_data, is_new_session
    
    def get_session(self) -> Optional[Dict]:
        """
        Gets the current anonymous session data.
        
        Returns:
            Current session data or None if no valid session
        """
        session_id = get_current_session_id()
        if session_id:
            return get_anonymous_session(session_id)
        return None
    
    def create_session(self, initial_data: Dict = None) -> str:
        """
        Creates a new anonymous session with optional initial data.
        
        Args:
            initial_data: Optional initial data for the session
            
        Returns:
            New anonymous session ID
        """
        return create_anonymous_session(initial_data)
    
    def update_session(self, data: Dict) -> bool:
        """
        Updates the current anonymous session with new data.
        
        Args:
            data: New data to merge with existing session data
            
        Returns:
            True if session was updated, False otherwise
        """
        session_id = get_current_session_id()
        if session_id:
            return update_anonymous_session(session_id, data)
        return False
    
    def clear_session(self) -> bool:
        """
        Deletes the current anonymous session.
        
        Returns:
            True if session was cleared, False otherwise
        """
        session_id = get_current_session_id()
        if session_id:
            return delete_anonymous_session(session_id)
        return False
    
    def add_document_to_current_session(self, document_id: str, document_title: str) -> bool:
        """
        Adds document to the current session.
        
        Args:
            document_id: ID of the document to add
            document_title: Title of the document
            
        Returns:
            True if document was added, False otherwise
        """
        session_id = get_current_session_id()
        if session_id:
            return add_document_to_session(session_id, document_id, document_title)
        return False
    
    def get_current_session_documents(self) -> List:
        """
        Gets documents from the current session.
        
        Returns:
            List of document references in current session
        """
        session_id = get_current_session_id()
        if session_id:
            return get_session_documents(session_id)
        return []
    
    def apply_session_to_response(self, response, session_id: str = None) -> Any:
        """
        Applies the session cookie to an HTTP response.
        
        Args:
            response: Flask response object
            session_id: Optional session ID (gets current session ID if not provided)
            
        Returns:
            Modified response with session cookie
        """
        if not session_id:
            session_id = get_current_session_id()
        
        if session_id:
            return set_session_cookie(session_id, response)
        return response
    
    def upgrade_to_authenticated_user(self, user_id: str) -> Optional[str]:
        """
        Upgrades anonymous session to authenticated user session.
        
        Args:
            user_id: User ID to associate with the authenticated session
            
        Returns:
            New authenticated session ID or None if failed
        """
        session_id = get_current_session_id()
        if session_id:
            return upgrade_to_authenticated(session_id, user_id)
        return None