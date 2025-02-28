"""
Redis-based session storage implementation for managing anonymous and authenticated user sessions
with expiration and TTL capabilities.

This module provides a SessionStore class that handles Redis-based session storage
for both anonymous and authenticated users. It includes functionality for creating,
retrieving, updating, and deleting sessions, as well as session upgrade from anonymous
to authenticated status.
"""

import json
import uuid
import time
from redis import Redis

from core.utils.logger import get_logger
from .connection import get_session_store_connection

# Constants
SESSION_PREFIX = "session:"
ANONYMOUS_SESSION_TTL = 86400  # 24 hours in seconds
AUTHENTICATED_SESSION_TTL = 7200  # 2 hours in seconds

# Initialize logger
logger = get_logger(__name__)


class SessionStore:
    """
    Handles Redis-based session storage for both anonymous and authenticated users with TTL management.
    
    This class provides methods for creating, retrieving, updating, and deleting sessions,
    as well as managing session expiration and transitioning between anonymous and authenticated states.
    """

    def __init__(self, prefix=None):
        """
        Initializes the SessionStore with Redis connection and prefix.
        
        Args:
            prefix (str, optional): Custom prefix for Redis keys. Defaults to SESSION_PREFIX.
        """
        self._redis_client = get_session_store_connection()
        self._prefix = prefix if prefix else SESSION_PREFIX
        logger.info(f"SessionStore initialized with prefix '{self._prefix}'")

    def create_session(self, data=None, user_id=None, is_authenticated=False):
        """
        Creates a new session in Redis with optional user_id for authenticated users.
        
        Args:
            data (dict, optional): Initial session data. Defaults to empty dict.
            user_id (str, optional): User ID for authenticated sessions. Defaults to None.
            is_authenticated (bool): Flag indicating if session is authenticated. Defaults to False.
            
        Returns:
            str: Session ID of the created session
        """
        # Generate a unique session ID
        session_id = str(uuid.uuid4())
        
        # Determine appropriate TTL
        ttl = AUTHENTICATED_SESSION_TTL if is_authenticated else ANONYMOUS_SESSION_TTL
        
        # Ensure data is a dictionary
        if data is None:
            data = {}
        
        # Add metadata to the session
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "is_authenticated": is_authenticated,
            "creation_time": int(time.time()),
            **data
        }
        
        # Serialize and store in Redis
        redis_key = f"{self._prefix}{session_id}"
        serialized_data = json.dumps(session_data)
        self._redis_client.setex(redis_key, ttl, serialized_data)
        
        logger.info(f"Created new {'authenticated' if is_authenticated else 'anonymous'} "
                   f"session with ID {session_id}")
        
        return session_id

    def get_session(self, session_id):
        """
        Retrieves session data from Redis by session ID.
        
        Args:
            session_id (str): The session ID to retrieve
            
        Returns:
            dict: Session data or None if not found
        """
        redis_key = f"{self._prefix}{session_id}"
        data = self._redis_client.get(redis_key)
        
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode session data for {session_id}: {e}")
                return None
        else:
            logger.debug(f"Session not found with ID {session_id}")
            return None

    def update_session(self, session_id, data):
        """
        Updates existing session data in Redis.
        
        Args:
            session_id (str): The session ID to update
            data (dict): New data to merge with existing session data
            
        Returns:
            bool: True if successful, False if session not found
        """
        # Check if session exists
        current_data = self.get_session(session_id)
        if not current_data:
            logger.warning(f"Attempted to update non-existent session with ID {session_id}")
            return False
        
        # Get current TTL
        redis_key = f"{self._prefix}{session_id}"
        ttl = self._redis_client.ttl(redis_key)
        if ttl < 0:
            # If the key exists but has no TTL (-1) or doesn't exist (-2)
            ttl = AUTHENTICATED_SESSION_TTL if current_data.get("is_authenticated") else ANONYMOUS_SESSION_TTL
        
        # Merge new data with existing data
        current_data.update(data)
        
        # Save updated data
        serialized_data = json.dumps(current_data)
        self._redis_client.setex(redis_key, ttl, serialized_data)
        
        logger.debug(f"Updated session with ID {session_id}")
        return True

    def delete_session(self, session_id):
        """
        Deletes a session from Redis.
        
        Args:
            session_id (str): The session ID to delete
            
        Returns:
            bool: True if session was deleted, False if not found
        """
        redis_key = f"{self._prefix}{session_id}"
        result = self._redis_client.delete(redis_key)
        
        if result:
            logger.info(f"Deleted session with ID {session_id}")
            return True
        else:
            logger.debug(f"Attempted to delete non-existent session with ID {session_id}")
            return False

    def extend_session(self, session_id, ttl=None):
        """
        Extends the TTL of an existing session.
        
        Args:
            session_id (str): The session ID to extend
            ttl (int, optional): New TTL in seconds. If not provided, uses the default
                                based on authentication status.
                                
        Returns:
            bool: True if extended, False if session not found
        """
        redis_key = f"{self._prefix}{session_id}"
        
        # Check if session exists
        if not self._redis_client.exists(redis_key):
            logger.warning(f"Attempted to extend non-existent session with ID {session_id}")
            return False
        
        # If TTL not provided, determine based on session type
        if ttl is None:
            session_data = self.get_session(session_id)
            if not session_data:
                return False
            
            ttl = AUTHENTICATED_SESSION_TTL if session_data.get("is_authenticated") else ANONYMOUS_SESSION_TTL
        
        # Extend expiration
        self._redis_client.expire(redis_key, ttl)
        logger.debug(f"Extended session with ID {session_id} by {ttl} seconds")
        return True

    def create_anonymous_session(self, data=None):
        """
        Creates an anonymous user session with default TTL.
        
        Args:
            data (dict, optional): Initial session data. Defaults to empty dict.
            
        Returns:
            str: Session ID of the created anonymous session
        """
        return self.create_session(data=data, user_id=None, is_authenticated=False)

    def create_authenticated_session(self, user_id, data=None):
        """
        Creates an authenticated user session with user ID.
        
        Args:
            user_id (str): User ID for the authenticated session
            data (dict, optional): Initial session data. Defaults to empty dict.
            
        Returns:
            str: Session ID of the created authenticated session
        """
        if not user_id:
            logger.error("Cannot create authenticated session without user_id")
            return None
        
        return self.create_session(data=data, user_id=user_id, is_authenticated=True)

    def get_session_ttl(self, session_id):
        """
        Gets the remaining TTL of a session in seconds.
        
        Args:
            session_id (str): The session ID to check
            
        Returns:
            int: Remaining TTL in seconds or -1 if expired, -2 if not found
        """
        redis_key = f"{self._prefix}{session_id}"
        ttl = self._redis_client.ttl(redis_key)
        return ttl

    def upgrade_session(self, anonymous_session_id, user_id):
        """
        Upgrades an anonymous session to an authenticated session.
        
        Args:
            anonymous_session_id (str): The anonymous session ID to upgrade
            user_id (str): User ID for the new authenticated session
            
        Returns:
            str: New authenticated session ID or None if upgrade failed
        """
        if not user_id:
            logger.error("Cannot upgrade session without user_id")
            return None
        
        # Get anonymous session data
        anonymous_data = self.get_session(anonymous_session_id)
        if not anonymous_data:
            logger.warning(f"Attempted to upgrade non-existent session with ID {anonymous_session_id}")
            return None
        
        # Check if already authenticated
        if anonymous_data.get("is_authenticated"):
            logger.warning(f"Session with ID {anonymous_session_id} is already authenticated")
            
            # Update user_id if it's different
            if anonymous_data.get("user_id") != user_id:
                anonymous_data["user_id"] = user_id
                self.update_session(anonymous_session_id, {"user_id": user_id})
                
            return anonymous_session_id
        
        # Remove any sensitive or temporary data that shouldn't
        # be carried over to the authenticated session
        if "is_authenticated" in anonymous_data:
            del anonymous_data["is_authenticated"]
        if "user_id" in anonymous_data:
            del anonymous_data["user_id"]
        if "session_id" in anonymous_data:
            del anonymous_data["session_id"]
        
        # Create new authenticated session with data from anonymous session
        authenticated_session_id = self.create_authenticated_session(
            user_id=user_id,
            data=anonymous_data
        )
        
        # Delete the anonymous session
        self.delete_session(anonymous_session_id)
        
        logger.info(f"Upgraded anonymous session {anonymous_session_id} to authenticated session {authenticated_session_id}")
        return authenticated_session_id