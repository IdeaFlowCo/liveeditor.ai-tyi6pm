"""
API endpoints for user profile management and preferences, including CRUD operations for user accounts
in the AI writing enhancement platform. Supports both anonymous and authenticated users with appropriate
permission checks.
"""

from flask import Blueprint, request, jsonify
from http import HTTPStatus
from marshmallow import ValidationError

from ..core.auth.user_service import UserService, UserNotFoundError
from .middleware.auth_middleware import auth_required, get_current_user_id
from .schemas.user_schema import UserUpdateSchema, UserPreferencesUpdateSchema, UserResponseSchema
from .middleware.error_handler import create_error_response
from ..core.utils.validators import validate_object_id

# Create blueprint for user routes
users_blueprint = Blueprint('users', __name__)


@users_blueprint.route('/profile', methods=['GET'])
@auth_required(allow_anonymous=False)
def get_user_profile():
    """
    Retrieves the profile information for the currently authenticated user.
    
    Returns:
        JSON response with user profile data and HTTP status code
    """
    try:
        # Get current user ID from authentication context
        user_id = get_current_user_id()
        
        # Retrieve user data from the UserService
        from flask import current_app
        user_service = current_app.user_service
        user_data = user_service.get_user_by_id(user_id)
        
        # Serialize user profile data using UserResponseSchema
        user_schema = UserResponseSchema()
        result = user_schema.dump(user_data)
        
        # Return user profile as JSON response with 200 OK status
        return jsonify(result), HTTPStatus.OK
        
    except UserNotFoundError as e:
        return create_error_response(
            message=f"User not found: {str(e)}",
            status_code=HTTPStatus.NOT_FOUND
        )
    except Exception as e:
        return create_error_response(
            message=f"Failed to retrieve user profile: {str(e)}",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )


@users_blueprint.route('/profile', methods=['PUT'])
@auth_required(allow_anonymous=False)
def update_user_profile():
    """
    Updates the profile information for the currently authenticated user.
    
    Returns:
        JSON response with updated user profile and HTTP status code
    """
    try:
        # Get current user ID from authentication context
        user_id = get_current_user_id()
        
        # Parse and validate request JSON data with UserUpdateSchema
        request_data = request.get_json()
        if not request_data:
            return create_error_response(
                message="No update data provided",
                status_code=HTTPStatus.BAD_REQUEST
            )
        
        schema = UserUpdateSchema()
        validated_data = schema.load(request_data)
        
        # Call UserService.update_user_profile with validated data
        from flask import current_app
        user_service = current_app.user_service
        updated_user = user_service.update_user_profile(user_id, validated_data)
        
        # Serialize updated user profile with UserResponseSchema
        response_schema = UserResponseSchema()
        result = response_schema.dump(updated_user)
        
        # Return updated profile as JSON response with 200 OK status
        return jsonify(result), HTTPStatus.OK
        
    except ValidationError as e:
        # Handle validation errors with 400 Bad Request response
        return create_error_response(
            message="Invalid update data",
            status_code=HTTPStatus.BAD_REQUEST,
            details=e.messages
        )
    except UserNotFoundError as e:
        # Handle UserNotFoundError with 404 Not Found response
        return create_error_response(
            message=f"User not found: {str(e)}",
            status_code=HTTPStatus.NOT_FOUND
        )
    except Exception as e:
        return create_error_response(
            message=f"Failed to update user profile: {str(e)}",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )


@users_blueprint.route('/profile', methods=['DELETE'])
@auth_required(allow_anonymous=False)
def delete_user_account():
    """
    Deletes the account of the currently authenticated user.
    
    Returns:
        JSON response confirming deletion and HTTP status code
    """
    try:
        # Get current user ID from authentication context
        user_id = get_current_user_id()
        
        # Call UserService.delete_user to delete the account
        from flask import current_app
        user_service = current_app.user_service
        user_service.delete_user(user_id)
        
        # Return success message as JSON response with 200 OK status
        return jsonify({
            "message": "User account deleted successfully"
        }), HTTPStatus.OK
        
    except UserNotFoundError as e:
        # Handle UserNotFoundError with 404 Not Found response
        return create_error_response(
            message=f"User not found: {str(e)}",
            status_code=HTTPStatus.NOT_FOUND
        )
    except Exception as e:
        return create_error_response(
            message=f"Failed to delete user account: {str(e)}",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )


@users_blueprint.route('/preferences', methods=['GET'])
@auth_required(allow_anonymous=False)
def get_user_preferences():
    """
    Retrieves the preferences for the currently authenticated user.
    
    Returns:
        JSON response with user preferences and HTTP status code
    """
    try:
        # Get current user ID from authentication context
        user_id = get_current_user_id()
        
        # Call UserService.get_user_by_id to retrieve user data
        from flask import current_app
        user_service = current_app.user_service
        user_data = user_service.get_user_by_id(user_id)
        
        # Extract preferences from user data
        preferences = user_data.get('preferences', {})
        
        # Return preferences as JSON response with 200 OK status
        return jsonify(preferences), HTTPStatus.OK
        
    except UserNotFoundError as e:
        # Handle UserNotFoundError with 404 Not Found response
        return create_error_response(
            message=f"User not found: {str(e)}",
            status_code=HTTPStatus.NOT_FOUND
        )
    except Exception as e:
        return create_error_response(
            message=f"Failed to retrieve user preferences: {str(e)}",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )


@users_blueprint.route('/preferences', methods=['PUT'])
@auth_required(allow_anonymous=False)
def update_user_preferences():
    """
    Updates the preferences for the currently authenticated user.
    
    Returns:
        JSON response with updated preferences and HTTP status code
    """
    try:
        # Get current user ID from authentication context
        user_id = get_current_user_id()
        
        # Parse and validate request JSON data with UserPreferencesUpdateSchema
        request_data = request.get_json()
        if not request_data:
            return create_error_response(
                message="No preferences data provided",
                status_code=HTTPStatus.BAD_REQUEST
            )
        
        schema = UserPreferencesUpdateSchema()
        validated_data = schema.load(request_data)
        
        # Call UserService.update_user_preferences with validated data
        from flask import current_app
        user_service = current_app.user_service
        updated_preferences = user_service.update_user_preferences(user_id, validated_data)
        
        # Return updated preferences as JSON response with 200 OK status
        return jsonify(updated_preferences), HTTPStatus.OK
        
    except ValidationError as e:
        # Handle validation errors with 400 Bad Request response
        return create_error_response(
            message="Invalid preferences data",
            status_code=HTTPStatus.BAD_REQUEST,
            details=e.messages
        )
    except UserNotFoundError as e:
        # Handle UserNotFoundError with 404 Not Found response
        return create_error_response(
            message=f"User not found: {str(e)}",
            status_code=HTTPStatus.NOT_FOUND
        )
    except Exception as e:
        return create_error_response(
            message=f"Failed to update user preferences: {str(e)}",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )