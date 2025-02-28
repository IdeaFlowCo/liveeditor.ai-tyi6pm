"""
Flask-RESTful resource classes implementing API endpoints for user management in the AI writing enhancement platform.
Provides routes for user profile operations, preferences management, and account-related functionality while supporting
both anonymous and authenticated users.
"""

from flask_restful import Resource
from flask import request
from http import HTTPStatus
from marshmallow import ValidationError

from ...core.auth.user_service import UserService
from ..schemas.user_schema import (
    UserResponseSchema, UserUpdateSchema, UserPreferencesSchema,
    UserPreferencesUpdateSchema, ChangePasswordSchema
)
from ..middleware.auth_middleware import jwt_required, get_current_user, get_current_user_id
from ..middleware.error_handler import create_error_response

# Configure logger
from ...core.utils.logger import get_logger
logger = get_logger(__name__)


class UserResource(Resource):
    """Resource for managing individual user profiles with CRUD operations"""
    
    def __init__(self, user_service: UserService):
        """Initialize the user resource with required services"""
        self._user_service = user_service
        self._user_schema = UserResponseSchema()
        self._update_schema = UserUpdateSchema()
    
    @jwt_required()
    def get(self, user_id: str):
        """Get user profile information by ID"""
        # Check authorization - users can only access their own profile
        current_user_id = get_current_user_id()
        if current_user_id != user_id:
            return create_error_response(
                "You can only access your own profile", 
                HTTPStatus.FORBIDDEN
            )
        
        try:
            user = self._user_service.get_user_by_id(user_id)
            return self._user_schema.dump(user), HTTPStatus.OK
        except Exception as e:
            logger.error(f"Error retrieving user {user_id}: {str(e)}")
            return create_error_response(
                "Error retrieving user profile", 
                HTTPStatus.INTERNAL_SERVER_ERROR
            )
    
    @jwt_required()
    def put(self, user_id: str):
        """Update user profile information"""
        # Check authorization - users can only update their own profile
        current_user_id = get_current_user_id()
        if current_user_id != user_id:
            return create_error_response(
                "You can only update your own profile", 
                HTTPStatus.FORBIDDEN
            )
        
        try:
            # Validate request data
            json_data = request.get_json()
            if not json_data:
                return create_error_response(
                    "No data provided for update", 
                    HTTPStatus.BAD_REQUEST
                )
                
            update_data = self._update_schema.load(json_data)
            
            # Update the user profile
            updated_user = self._user_service.update_user_profile(user_id, update_data)
            
            return self._user_schema.dump(updated_user), HTTPStatus.OK
        except ValidationError as e:
            return create_error_response(
                "Invalid update data", 
                HTTPStatus.BAD_REQUEST,
                e.messages
            )
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {str(e)}")
            return create_error_response(
                "Error updating user profile", 
                HTTPStatus.INTERNAL_SERVER_ERROR
            )
    
    @jwt_required()
    def delete(self, user_id: str):
        """Delete a user account"""
        # Check authorization - users can only delete their own account
        current_user_id = get_current_user_id()
        if current_user_id != user_id:
            return create_error_response(
                "You can only delete your own account", 
                HTTPStatus.FORBIDDEN
            )
        
        try:
            # Delete the user account
            result = self._user_service.delete_user(user_id)
            return {"message": "User account deleted successfully"}, HTTPStatus.OK
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {str(e)}")
            return create_error_response(
                "Error deleting user account", 
                HTTPStatus.INTERNAL_SERVER_ERROR
            )


class CurrentUserResource(Resource):
    """Resource for managing the current authenticated user"""
    
    def __init__(self, user_service: UserService):
        """Initialize the current user resource with required services"""
        self._user_service = user_service
        self._user_schema = UserResponseSchema()
        self._update_schema = UserUpdateSchema()
    
    @jwt_required()
    def get(self):
        """Get current user profile information"""
        user_id = get_current_user_id()
        if not user_id:
            return create_error_response(
                "Authentication required", 
                HTTPStatus.UNAUTHORIZED
            )
        
        try:
            user = self._user_service.get_user_by_id(user_id)
            return self._user_schema.dump(user), HTTPStatus.OK
        except Exception as e:
            logger.error(f"Error retrieving current user {user_id}: {str(e)}")
            return create_error_response(
                "Error retrieving user profile", 
                HTTPStatus.INTERNAL_SERVER_ERROR
            )
    
    @jwt_required()
    def put(self):
        """Update current user profile information"""
        user_id = get_current_user_id()
        if not user_id:
            return create_error_response(
                "Authentication required", 
                HTTPStatus.UNAUTHORIZED
            )
        
        try:
            # Validate request data
            json_data = request.get_json()
            if not json_data:
                return create_error_response(
                    "No data provided for update", 
                    HTTPStatus.BAD_REQUEST
                )
                
            update_data = self._update_schema.load(json_data)
            
            # Update the user profile
            updated_user = self._user_service.update_user_profile(user_id, update_data)
            
            return self._user_schema.dump(updated_user), HTTPStatus.OK
        except ValidationError as e:
            return create_error_response(
                "Invalid update data", 
                HTTPStatus.BAD_REQUEST,
                e.messages
            )
        except Exception as e:
            logger.error(f"Error updating current user {user_id}: {str(e)}")
            return create_error_response(
                "Error updating user profile", 
                HTTPStatus.INTERNAL_SERVER_ERROR
            )


class UserPreferencesResource(Resource):
    """Resource for managing user preferences"""
    
    def __init__(self, user_service: UserService):
        """Initialize the user preferences resource with required services"""
        self._user_service = user_service
        self._preferences_schema = UserPreferencesSchema()
        self._preferences_update_schema = UserPreferencesUpdateSchema()
    
    @jwt_required()
    def get(self, user_id: str):
        """Get user preferences"""
        # Check authorization - users can only access their own preferences
        current_user_id = get_current_user_id()
        if current_user_id != user_id:
            return create_error_response(
                "You can only access your own preferences", 
                HTTPStatus.FORBIDDEN
            )
        
        try:
            user = self._user_service.get_user_by_id(user_id)
            preferences = user.get('preferences', {})
            return self._preferences_schema.dump(preferences), HTTPStatus.OK
        except Exception as e:
            logger.error(f"Error retrieving preferences for user {user_id}: {str(e)}")
            return create_error_response(
                "Error retrieving user preferences", 
                HTTPStatus.INTERNAL_SERVER_ERROR
            )
    
    @jwt_required()
    def put(self, user_id: str):
        """Update user preferences"""
        # Check authorization - users can only update their own preferences
        current_user_id = get_current_user_id()
        if current_user_id != user_id:
            return create_error_response(
                "You can only update your own preferences", 
                HTTPStatus.FORBIDDEN
            )
        
        try:
            # Validate request data
            json_data = request.get_json()
            if not json_data:
                return create_error_response(
                    "No preference data provided", 
                    HTTPStatus.BAD_REQUEST
                )
                
            preferences_data = self._preferences_update_schema.load(json_data)
            
            # Update the user preferences
            updated_preferences = self._user_service.update_user_preferences(user_id, preferences_data)
            
            return self._preferences_schema.dump(updated_preferences), HTTPStatus.OK
        except ValidationError as e:
            return create_error_response(
                "Invalid preferences data", 
                HTTPStatus.BAD_REQUEST,
                e.messages
            )
        except Exception as e:
            logger.error(f"Error updating preferences for user {user_id}: {str(e)}")
            return create_error_response(
                "Error updating user preferences", 
                HTTPStatus.INTERNAL_SERVER_ERROR
            )


class CurrentUserPreferencesResource(Resource):
    """Resource for managing current user's preferences"""
    
    def __init__(self, user_service: UserService):
        """Initialize the current user preferences resource with required services"""
        self._user_service = user_service
        self._preferences_schema = UserPreferencesSchema()
        self._preferences_update_schema = UserPreferencesUpdateSchema()
    
    @jwt_required()
    def get(self):
        """Get current user's preferences"""
        user_id = get_current_user_id()
        if not user_id:
            return create_error_response(
                "Authentication required", 
                HTTPStatus.UNAUTHORIZED
            )
        
        try:
            user = self._user_service.get_user_by_id(user_id)
            preferences = user.get('preferences', {})
            return self._preferences_schema.dump(preferences), HTTPStatus.OK
        except Exception as e:
            logger.error(f"Error retrieving preferences for current user {user_id}: {str(e)}")
            return create_error_response(
                "Error retrieving user preferences", 
                HTTPStatus.INTERNAL_SERVER_ERROR
            )
    
    @jwt_required()
    def put(self):
        """Update current user's preferences"""
        user_id = get_current_user_id()
        if not user_id:
            return create_error_response(
                "Authentication required", 
                HTTPStatus.UNAUTHORIZED
            )
        
        try:
            # Validate request data
            json_data = request.get_json()
            if not json_data:
                return create_error_response(
                    "No preference data provided", 
                    HTTPStatus.BAD_REQUEST
                )
                
            preferences_data = self._preferences_update_schema.load(json_data)
            
            # Update the user preferences
            updated_preferences = self._user_service.update_user_preferences(user_id, preferences_data)
            
            return self._preferences_schema.dump(updated_preferences), HTTPStatus.OK
        except ValidationError as e:
            return create_error_response(
                "Invalid preferences data", 
                HTTPStatus.BAD_REQUEST,
                e.messages
            )
        except Exception as e:
            logger.error(f"Error updating preferences for current user {user_id}: {str(e)}")
            return create_error_response(
                "Error updating user preferences", 
                HTTPStatus.INTERNAL_SERVER_ERROR
            )


class UserPasswordResource(Resource):
    """Resource for changing user password"""
    
    def __init__(self, user_service: UserService):
        """Initialize the user password resource with required services"""
        self._user_service = user_service
        self._password_schema = ChangePasswordSchema()
    
    @jwt_required()
    def put(self, user_id: str):
        """Change user password"""
        # Check authorization - users can only change their own password
        current_user_id = get_current_user_id()
        if current_user_id != user_id:
            return create_error_response(
                "You can only change your own password", 
                HTTPStatus.FORBIDDEN
            )
        
        try:
            # Validate request data
            json_data = request.get_json()
            if not json_data:
                return create_error_response(
                    "No password data provided", 
                    HTTPStatus.BAD_REQUEST
                )
                
            password_data = self._password_schema.load(json_data)
            
            # Change the password
            self._user_service.change_password(
                user_id, 
                password_data['current_password'], 
                password_data['new_password']
            )
            
            return {"message": "Password changed successfully"}, HTTPStatus.OK
        except ValidationError as e:
            return create_error_response(
                "Invalid password data", 
                HTTPStatus.BAD_REQUEST,
                e.messages
            )
        except Exception as e:
            logger.error(f"Error changing password for user {user_id}: {str(e)}")
            return create_error_response(
                "Error changing password", 
                HTTPStatus.INTERNAL_SERVER_ERROR
            )


class CurrentUserPasswordResource(Resource):
    """Resource for changing current user's password"""
    
    def __init__(self, user_service: UserService):
        """Initialize the current user password resource with required services"""
        self._user_service = user_service
        self._password_schema = ChangePasswordSchema()
    
    @jwt_required()
    def put(self):
        """Change current user's password"""
        user_id = get_current_user_id()
        if not user_id:
            return create_error_response(
                "Authentication required", 
                HTTPStatus.UNAUTHORIZED
            )
        
        try:
            # Validate request data
            json_data = request.get_json()
            if not json_data:
                return create_error_response(
                    "No password data provided", 
                    HTTPStatus.BAD_REQUEST
                )
                
            password_data = self._password_schema.load(json_data)
            
            # Change the password
            self._user_service.change_password(
                user_id, 
                password_data['current_password'], 
                password_data['new_password']
            )
            
            return {"message": "Password changed successfully"}, HTTPStatus.OK
        except ValidationError as e:
            return create_error_response(
                "Invalid password data", 
                HTTPStatus.BAD_REQUEST,
                e.messages
            )
        except Exception as e:
            logger.error(f"Error changing password for current user {user_id}: {str(e)}")
            return create_error_response(
                "Error changing password", 
                HTTPStatus.INTERNAL_SERVER_ERROR
            )