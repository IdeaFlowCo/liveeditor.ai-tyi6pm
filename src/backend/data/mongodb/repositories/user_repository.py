"""
MongoDB repository implementation for user data management in the AI writing enhancement platform.
Handles CRUD operations for both authenticated and anonymous users, providing persistent
storage for user profiles, authentication data, and preferences.
"""

from datetime import datetime
import pymongo
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
import typing
import uuid
import re

from ..connection import get_collection, str_to_object_id, object_id_to_str
from ...core.utils.logger import get_logger
from ...core.utils.validators import validate_object_id, is_valid_email

# Configure logger
logger = get_logger(__name__)

# Time-to-live for anonymous users (24 hours in seconds)
DEFAULT_ANONYMOUS_TTL = 86400  # 24 hours in seconds


class UserNotFoundError(Exception):
    """Exception raised when a user cannot be found"""
    
    def __init__(self, user_id: str, message: str = None):
        """Initializes the user not found error
        
        Args:
            user_id: ID of the user that wasn't found
            message: Optional custom error message
        """
        if message is None:
            message = f"User with ID {user_id} not found"
        super().__init__(message)
        self.user_id = user_id


class DuplicateEmailError(Exception):
    """Exception raised when attempting to use an email that already exists"""
    
    def __init__(self, email: str, message: str = None):
        """Initializes the duplicate email error
        
        Args:
            email: Email address that caused the conflict
            message: Optional custom error message
        """
        if message is None:
            message = f"User with email {email} already exists"
        super().__init__(message)
        self.email = email


class UserRepository:
    """MongoDB repository for user data operations with support for both authenticated and anonymous users"""
    
    COLLECTION_NAME = 'users'
    
    def __init__(self):
        """Initializes the user repository with MongoDB collection"""
        # Get collection reference
        self._collection = get_collection(self.COLLECTION_NAME)
        
        # Ensure indexes exist
        self._create_indexes()
        
        logger.info(f"UserRepository initialized with collection '{self.COLLECTION_NAME}'")
    
    def _create_indexes(self):
        """Creates necessary indexes for the users collection"""
        # Email must be unique to prevent duplicate registrations
        try:
            self._collection.create_index('email', unique=True, sparse=True)
            
            # Session ID index for anonymous users
            self._collection.create_index('sessionId', sparse=True)
            
            # Indexes for common query patterns
            self._collection.create_index('createdAt')
            self._collection.create_index('lastLogin')
            
            # Index for querying expired anonymous users
            self._collection.create_index([('isAnonymous', pymongo.ASCENDING), ('expiresAt', pymongo.ASCENDING)])
            
            # Index for account status queries
            self._collection.create_index('accountStatus')
            
            logger.info("User collection indexes created")
        except Exception as e:
            logger.error(f"Error creating user collection indexes: {str(e)}")
            raise
    
    def create_user(self, user_data: dict) -> dict:
        """Creates a new user with email, password hash, and profile data
        
        Args:
            user_data: Dictionary containing user information including email and password_hash
            
        Returns:
            Created user document with generated ID and metadata
            
        Raises:
            DuplicateEmailError: If email already exists
            ValueError: If required fields are missing
        """
        # Validate required fields
        if 'email' not in user_data or 'password_hash' not in user_data:
            raise ValueError("Email and password_hash are required fields")
        
        # Validate email format
        email = user_data['email']
        if not is_valid_email(email):
            raise ValueError(f"Invalid email format: {email}")
        
        # Check if email already exists
        existing_user = self.get_by_email(email)
        if existing_user:
            logger.warning(f"Attempted to create user with existing email: {email}")
            raise DuplicateEmailError(email)
        
        # Prepare the user document
        now = datetime.utcnow()
        user_doc = {
            'email': email,
            'passwordHash': user_data['password_hash'],
            'firstName': user_data.get('first_name', ''),
            'lastName': user_data.get('last_name', ''),
            'createdAt': now,
            'lastLogin': now,
            'isAnonymous': False,
            'emailVerified': False,
            'accountStatus': user_data.get('account_status', 'active'),
            'preferences': user_data.get('preferences', {})
        }
        
        try:
            # Insert the user document
            result = self._collection.insert_one(user_doc)
            user_id = result.inserted_id
            
            # Retrieve the created user
            created_user = self.get_by_id(str(user_id))
            
            logger.info(f"Created new user with ID: {user_id}, email: {email}")
            return created_user
        except DuplicateKeyError:
            # This can happen in rare race conditions
            logger.warning(f"Duplicate key error when creating user with email: {email}")
            raise DuplicateEmailError(email)
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise
    
    def create_anonymous_user(self, session_id: str) -> dict:
        """Creates a new anonymous user with session ID
        
        Args:
            session_id: Browser session identifier
            
        Returns:
            Created anonymous user document with generated ID
            
        Raises:
            ValueError: If session_id is not provided
        """
        if not session_id:
            raise ValueError("Session ID is required for anonymous users")
        
        # Prepare the anonymous user document
        now = datetime.utcnow()
        expires_at = datetime.utcfromtimestamp(now.timestamp() + DEFAULT_ANONYMOUS_TTL)
        
        user_doc = {
            'sessionId': session_id,
            'isAnonymous': True,
            'createdAt': now,
            'expiresAt': expires_at,
            'preferences': {}
        }
        
        try:
            # Insert the anonymous user document
            result = self._collection.insert_one(user_doc)
            user_id = result.inserted_id
            
            # Retrieve the created user
            created_user = self.get_by_id(str(user_id))
            
            logger.info(f"Created new anonymous user with ID: {user_id}, session: {session_id}")
            return created_user
        except Exception as e:
            logger.error(f"Error creating anonymous user: {str(e)}")
            raise
    
    def get_by_id(self, user_id: str, include_password_hash: bool = False) -> dict:
        """Retrieves a user by their ID
        
        Args:
            user_id: User's ID string
            include_password_hash: Whether to include the password hash in the result
            
        Returns:
            User document if found, None otherwise
        """
        try:
            # Validate user_id format
            validate_object_id(user_id)
            
            # Convert string ID to ObjectId
            obj_id = str_to_object_id(user_id)
            
            # Define projection to exclude password hash if not requested
            projection = None if include_password_hash else {'passwordHash': 0}
            
            # Find the user by ID
            user = self._collection.find_one({'_id': obj_id}, projection)
            
            if not user:
                logger.debug(f"User not found with ID: {user_id}")
                return None
            
            # Convert ObjectId to string and format dates
            user['_id'] = object_id_to_str(user['_id'])
            
            # Format dates for serialization
            if 'createdAt' in user:
                user['createdAt'] = user['createdAt'].isoformat()
            if 'lastLogin' in user:
                user['lastLogin'] = user['lastLogin'].isoformat()
            if 'expiresAt' in user:
                user['expiresAt'] = user['expiresAt'].isoformat()
            
            logger.debug(f"Retrieved user by ID: {user_id}")
            return user
        except Exception as e:
            logger.error(f"Error retrieving user by ID {user_id}: {str(e)}")
            return None
    
    def get_by_email(self, email: str, include_password_hash: bool = False) -> dict:
        """Retrieves a user by their email address
        
        Args:
            email: User's email address
            include_password_hash: Whether to include the password hash in the result
            
        Returns:
            User document if found, None otherwise
        """
        if not is_valid_email(email):
            logger.warning(f"Invalid email format in get_by_email: {email}")
            return None
        
        try:
            # Define projection to exclude password hash if not requested
            projection = None if include_password_hash else {'passwordHash': 0}
            
            # Find the user by email (case-insensitive)
            user = self._collection.find_one({'email': {'$regex': f'^{re.escape(email)}$', '$options': 'i'}}, projection)
            
            if not user:
                logger.debug(f"User not found with email: {email}")
                return None
            
            # Convert ObjectId to string and format dates
            user['_id'] = object_id_to_str(user['_id'])
            
            # Format dates for serialization
            if 'createdAt' in user:
                user['createdAt'] = user['createdAt'].isoformat()
            if 'lastLogin' in user:
                user['lastLogin'] = user['lastLogin'].isoformat()
            if 'expiresAt' in user:
                user['expiresAt'] = user['expiresAt'].isoformat()
            
            logger.debug(f"Retrieved user by email: {email}")
            return user
        except Exception as e:
            logger.error(f"Error retrieving user by email {email}: {str(e)}")
            return None
    
    def get_by_session(self, session_id: str) -> dict:
        """Retrieves a user by their session ID (for anonymous users)
        
        Args:
            session_id: Browser session identifier
            
        Returns:
            User document if found, None otherwise
        """
        if not session_id:
            logger.warning("Empty session_id provided to get_by_session")
            return None
        
        try:
            # Find the user by session ID
            user = self._collection.find_one({'sessionId': session_id})
            
            if not user:
                logger.debug(f"User not found with session ID: {session_id}")
                return None
            
            # Check if anonymous user has expired
            if user.get('isAnonymous', False) and 'expiresAt' in user:
                if user['expiresAt'] < datetime.utcnow():
                    # User has expired, delete and return None
                    self._collection.delete_one({'_id': user['_id']})
                    logger.info(f"Deleted expired anonymous user with session ID: {session_id}")
                    return None
            
            # Convert ObjectId to string and format dates
            user['_id'] = object_id_to_str(user['_id'])
            
            # Format dates for serialization
            if 'createdAt' in user:
                user['createdAt'] = user['createdAt'].isoformat()
            if 'lastLogin' in user:
                user['lastLogin'] = user['lastLogin'].isoformat()
            if 'expiresAt' in user:
                user['expiresAt'] = user['expiresAt'].isoformat()
            
            logger.debug(f"Retrieved user by session ID: {session_id}")
            return user
        except Exception as e:
            logger.error(f"Error retrieving user by session ID {session_id}: {str(e)}")
            return None
    
    def update_user(self, user_id: str, update_data: dict) -> dict:
        """Updates user profile information
        
        Args:
            user_id: User's ID string
            update_data: Dictionary containing fields to update
            
        Returns:
            Updated user document
            
        Raises:
            UserNotFoundError: If user doesn't exist
            ValueError: If user_id is invalid
        """
        try:
            # Validate user_id format
            validate_object_id(user_id)
            
            # Convert string ID to ObjectId
            obj_id = str_to_object_id(user_id)
            
            # Ensure user exists
            existing_user = self._collection.find_one({'_id': obj_id})
            if not existing_user:
                logger.warning(f"Attempted to update non-existent user with ID: {user_id}")
                raise UserNotFoundError(user_id)
            
            # Filter update_data to prevent updating restricted fields
            safe_update = {}
            allowed_fields = {
                'firstName', 'lastName', 'preferences', 'accountStatus'
            }
            
            for field, value in update_data.items():
                if field in allowed_fields:
                    safe_update[field] = value
            
            # Don't update if no valid fields
            if not safe_update:
                logger.warning(f"No valid fields to update for user {user_id}")
                return self.get_by_id(user_id)
            
            # Update the user
            result = self._collection.update_one(
                {'_id': obj_id},
                {'$set': safe_update}
            )
            
            if result.modified_count == 0:
                logger.warning(f"No changes made when updating user {user_id}")
            
            # Get and return the updated user
            updated_user = self.get_by_id(user_id)
            logger.info(f"Updated user {user_id}: {', '.join(safe_update.keys())}")
            
            return updated_user
        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {str(e)}")
            raise
    
    def update_email(self, user_id: str, new_email: str) -> dict:
        """Updates a user's email address
        
        Args:
            user_id: User's ID string
            new_email: New email address
            
        Returns:
            Updated user document
            
        Raises:
            UserNotFoundError: If user doesn't exist
            DuplicateEmailError: If email is already used by another user
            ValueError: If email format is invalid
        """
        # Validate user_id and email format
        validate_object_id(user_id)
        
        if not is_valid_email(new_email):
            raise ValueError(f"Invalid email format: {new_email}")
        
        # Check if email is already used by a different user
        existing = self.get_by_email(new_email)
        if existing and existing['_id'] != user_id:
            raise DuplicateEmailError(new_email)
        
        try:
            obj_id = str_to_object_id(user_id)
            
            # Update email and set emailVerified to false
            result = self._collection.update_one(
                {'_id': obj_id},
                {'$set': {
                    'email': new_email,
                    'emailVerified': False
                }}
            )
            
            if result.matched_count == 0:
                raise UserNotFoundError(user_id)
            
            # Get and return the updated user
            updated_user = self.get_by_id(user_id)
            logger.info(f"Updated email for user {user_id} to {new_email}")
            
            return updated_user
        except DuplicateKeyError:
            # This can happen in race conditions
            logger.warning(f"Duplicate key error when updating email to: {new_email}")
            raise DuplicateEmailError(new_email)
        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating email for user {user_id}: {str(e)}")
            raise
    
    def update_password(self, user_id: str, password_hash: str) -> bool:
        """Updates a user's password hash
        
        Args:
            user_id: User's ID string
            password_hash: New password hash
            
        Returns:
            True if updated successfully, False otherwise
            
        Raises:
            UserNotFoundError: If user doesn't exist
            ValueError: If user_id is invalid
        """
        try:
            # Validate user_id format
            validate_object_id(user_id)
            
            # Convert string ID to ObjectId
            obj_id = str_to_object_id(user_id)
            
            # Update the password hash
            result = self._collection.update_one(
                {'_id': obj_id},
                {'$set': {'passwordHash': password_hash}}
            )
            
            if result.matched_count == 0:
                logger.warning(f"Attempted to update password for non-existent user: {user_id}")
                raise UserNotFoundError(user_id)
            
            logger.info(f"Updated password for user {user_id}")
            return True
        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating password for user {user_id}: {str(e)}")
            return False
    
    def delete_user(self, user_id: str) -> bool:
        """Deletes a user account
        
        Args:
            user_id: User's ID string
            
        Returns:
            True if deleted successfully, False otherwise
            
        Raises:
            ValueError: If user_id is invalid
        """
        try:
            # Validate user_id format
            validate_object_id(user_id)
            
            # Convert string ID to ObjectId
            obj_id = str_to_object_id(user_id)
            
            # Delete the user
            result = self._collection.delete_one({'_id': obj_id})
            
            if result.deleted_count == 0:
                logger.warning(f"Attempted to delete non-existent user: {user_id}")
                return False
            
            logger.info(f"Deleted user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {str(e)}")
            return False
    
    def verify_email(self, user_id: str) -> bool:
        """Marks a user's email as verified
        
        Args:
            user_id: User's ID string
            
        Returns:
            True if updated successfully, False otherwise
            
        Raises:
            UserNotFoundError: If user doesn't exist
            ValueError: If user_id is invalid
        """
        try:
            # Validate user_id format
            validate_object_id(user_id)
            
            # Convert string ID to ObjectId
            obj_id = str_to_object_id(user_id)
            
            # Mark email as verified
            result = self._collection.update_one(
                {'_id': obj_id},
                {'$set': {'emailVerified': True}}
            )
            
            if result.matched_count == 0:
                logger.warning(f"Attempted to verify email for non-existent user: {user_id}")
                raise UserNotFoundError(user_id)
            
            logger.info(f"Verified email for user {user_id}")
            return True
        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error verifying email for user {user_id}: {str(e)}")
            return False
    
    def update_last_login(self, user_id: str) -> bool:
        """Updates a user's last login timestamp
        
        Args:
            user_id: User's ID string
            
        Returns:
            True if updated successfully, False otherwise
            
        Raises:
            UserNotFoundError: If user doesn't exist
            ValueError: If user_id is invalid
        """
        try:
            # Validate user_id format
            validate_object_id(user_id)
            
            # Convert string ID to ObjectId
            obj_id = str_to_object_id(user_id)
            
            # Update last login timestamp
            result = self._collection.update_one(
                {'_id': obj_id},
                {'$set': {'lastLogin': datetime.utcnow()}}
            )
            
            if result.matched_count == 0:
                logger.warning(f"Attempted to update last login for non-existent user: {user_id}")
                raise UserNotFoundError(user_id)
            
            logger.debug(f"Updated last login timestamp for user {user_id}")
            return True
        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating last login for user {user_id}: {str(e)}")
            return False
    
    def store_verification_token(self, user_id: str, token: str, expiry: datetime) -> bool:
        """Stores an email verification token for a user
        
        Args:
            user_id: User's ID string
            token: Verification token
            expiry: Token expiration timestamp
            
        Returns:
            True if stored successfully, False otherwise
            
        Raises:
            UserNotFoundError: If user doesn't exist
            ValueError: If user_id is invalid
        """
        try:
            # Validate user_id format
            validate_object_id(user_id)
            
            # Convert string ID to ObjectId
            obj_id = str_to_object_id(user_id)
            
            # Store verification token and expiry
            result = self._collection.update_one(
                {'_id': obj_id},
                {'$set': {
                    'verificationToken': token,
                    'verificationTokenExpiry': expiry
                }}
            )
            
            if result.matched_count == 0:
                logger.warning(f"Attempted to store verification token for non-existent user: {user_id}")
                raise UserNotFoundError(user_id)
            
            logger.info(f"Stored verification token for user {user_id}, expires: {expiry.isoformat()}")
            return True
        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error storing verification token for user {user_id}: {str(e)}")
            return False
    
    def store_reset_token(self, user_id: str, token: str, expiry: datetime) -> bool:
        """Stores a password reset token for a user
        
        Args:
            user_id: User's ID string
            token: Reset token
            expiry: Token expiration timestamp
            
        Returns:
            True if stored successfully, False otherwise
            
        Raises:
            UserNotFoundError: If user doesn't exist
            ValueError: If user_id is invalid
        """
        try:
            # Validate user_id format
            validate_object_id(user_id)
            
            # Convert string ID to ObjectId
            obj_id = str_to_object_id(user_id)
            
            # Store reset token and expiry
            result = self._collection.update_one(
                {'_id': obj_id},
                {'$set': {
                    'resetToken': token,
                    'resetTokenExpiry': expiry
                }}
            )
            
            if result.matched_count == 0:
                logger.warning(f"Attempted to store reset token for non-existent user: {user_id}")
                raise UserNotFoundError(user_id)
            
            logger.info(f"Stored password reset token for user {user_id}, expires: {expiry.isoformat()}")
            return True
        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error storing reset token for user {user_id}: {str(e)}")
            return False
    
    def clear_reset_token(self, user_id: str) -> bool:
        """Clears a password reset token after use
        
        Args:
            user_id: User's ID string
            
        Returns:
            True if cleared successfully, False otherwise
            
        Raises:
            UserNotFoundError: If user doesn't exist
            ValueError: If user_id is invalid
        """
        try:
            # Validate user_id format
            validate_object_id(user_id)
            
            # Convert string ID to ObjectId
            obj_id = str_to_object_id(user_id)
            
            # Clear reset token and expiry
            result = self._collection.update_one(
                {'_id': obj_id},
                {'$unset': {
                    'resetToken': '',
                    'resetTokenExpiry': ''
                }}
            )
            
            if result.matched_count == 0:
                logger.warning(f"Attempted to clear reset token for non-existent user: {user_id}")
                raise UserNotFoundError(user_id)
            
            logger.info(f"Cleared password reset token for user {user_id}")
            return True
        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error clearing reset token for user {user_id}: {str(e)}")
            return False
    
    def convert_anonymous_to_registered(self, session_id: str, user_data: dict) -> dict:
        """Converts an anonymous user to a registered user
        
        Args:
            session_id: Session ID of the anonymous user
            user_data: Registration data including email and password_hash
            
        Returns:
            Updated user document
            
        Raises:
            UserNotFoundError: If anonymous user doesn't exist
            DuplicateEmailError: If email is already used by another user
            ValueError: If required fields are missing or invalid
        """
        # Validate required fields
        if not session_id:
            raise ValueError("Session ID is required")
        
        if 'email' not in user_data or 'password_hash' not in user_data:
            raise ValueError("Email and password_hash are required fields")
        
        email = user_data['email']
        if not is_valid_email(email):
            raise ValueError(f"Invalid email format: {email}")
        
        # Check if email already exists
        existing_user = self.get_by_email(email)
        if existing_user:
            logger.warning(f"Attempted to convert anonymous user to existing email: {email}")
            raise DuplicateEmailError(email)
        
        try:
            # Find the anonymous user
            anonymous_user = self._collection.find_one({'sessionId': session_id, 'isAnonymous': True})
            
            if not anonymous_user:
                logger.warning(f"Anonymous user not found with session ID: {session_id}")
                raise UserNotFoundError(session_id, f"Anonymous user with session ID {session_id} not found")
            
            # Prepare update data
            now = datetime.utcnow()
            update_data = {
                'email': email,
                'passwordHash': user_data['password_hash'],
                'firstName': user_data.get('first_name', ''),
                'lastName': user_data.get('last_name', ''),
                'isAnonymous': False,
                'emailVerified': False,
                'accountStatus': 'active',
                'lastLogin': now
            }
            
            # Remove anonymous-specific fields
            unset_data = {
                'sessionId': '',
                'expiresAt': ''
            }
            
            # Update the user
            result = self._collection.update_one(
                {'_id': anonymous_user['_id']},
                {
                    '$set': update_data,
                    '$unset': unset_data
                }
            )
            
            if result.modified_count == 0:
                logger.warning(f"Failed to convert anonymous user with session ID: {session_id}")
                return None
            
            # Get and return the updated user
            updated_user = self.get_by_id(str(anonymous_user['_id']))
            logger.info(f"Converted anonymous user to registered user: {updated_user['_id']}, email: {email}")
            
            return updated_user
        except DuplicateKeyError:
            # This can happen in race conditions
            logger.warning(f"Duplicate key error when converting anonymous user to email: {email}")
            raise DuplicateEmailError(email)
        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error converting anonymous user with session ID {session_id}: {str(e)}")
            raise
    
    def find_users(self, filters: dict = None, skip: int = 0, limit: int = 20) -> typing.Tuple[list, int]:
        """Finds users based on filter criteria with pagination
        
        Args:
            filters: Dictionary of filter criteria
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (list of users, total count)
        """
        try:
            # Prepare query
            query = {}
            
            if filters:
                # Apply filters
                if 'email' in filters and filters['email']:
                    query['email'] = {'$regex': filters['email'], '$options': 'i'}
                
                if 'account_status' in filters and filters['account_status']:
                    query['accountStatus'] = filters['account_status']
                
                if 'is_anonymous' in filters:
                    query['isAnonymous'] = bool(filters['is_anonymous'])
                
                if 'is_email_verified' in filters:
                    query['emailVerified'] = bool(filters['is_email_verified'])
            
            # Get total count
            total_count = self._collection.count_documents(query)
            
            # Get paginated results
            cursor = self._collection.find(
                query,
                {'passwordHash': 0}  # Exclude password hash
            ).sort('createdAt', pymongo.DESCENDING).skip(skip).limit(limit)
            
            # Format users
            users = []
            for user in cursor:
                # Convert ObjectId to string and format dates
                user['_id'] = object_id_to_str(user['_id'])
                
                # Format dates for serialization
                if 'createdAt' in user:
                    user['createdAt'] = user['createdAt'].isoformat()
                if 'lastLogin' in user:
                    user['lastLogin'] = user['lastLogin'].isoformat()
                if 'expiresAt' in user:
                    user['expiresAt'] = user['expiresAt'].isoformat()
                
                users.append(user)
            
            logger.debug(f"Found {len(users)} users with total count {total_count}")
            return users, total_count
        except Exception as e:
            logger.error(f"Error finding users: {str(e)}")
            return [], 0
    
    def cleanup_expired_anonymous(self) -> int:
        """Removes expired anonymous users
        
        Returns:
            Number of users cleaned up
        """
        try:
            # Current time for expiration check
            now = datetime.utcnow()
            
            # Find and delete expired anonymous users
            result = self._collection.delete_many({
                'isAnonymous': True,
                'expiresAt': {'$lt': now}
            })
            
            deleted_count = result.deleted_count
            logger.info(f"Cleaned up {deleted_count} expired anonymous users")
            
            return deleted_count
        except Exception as e:
            logger.error(f"Error cleaning up expired anonymous users: {str(e)}")
            return 0
    
    def update_user_preferences(self, user_id: str, preferences: dict) -> dict:
        """Updates a user's preferences
        
        Args:
            user_id: User's ID string
            preferences: Dictionary of preference settings
            
        Returns:
            Updated preferences
            
        Raises:
            UserNotFoundError: If user doesn't exist
            ValueError: If user_id is invalid
        """
        try:
            # Validate user_id format
            validate_object_id(user_id)
            
            # Convert string ID to ObjectId
            obj_id = str_to_object_id(user_id)
            
            # Update preferences
            result = self._collection.update_one(
                {'_id': obj_id},
                {'$set': {'preferences': preferences}}
            )
            
            if result.matched_count == 0:
                logger.warning(f"Attempted to update preferences for non-existent user: {user_id}")
                raise UserNotFoundError(user_id)
            
            # Get updated user
            updated_user = self._collection.find_one(
                {'_id': obj_id},
                {'preferences': 1}
            )
            
            if not updated_user:
                raise UserNotFoundError(user_id)
            
            logger.info(f"Updated preferences for user {user_id}")
            return updated_user.get('preferences', {})
        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating preferences for user {user_id}: {str(e)}")
            raise