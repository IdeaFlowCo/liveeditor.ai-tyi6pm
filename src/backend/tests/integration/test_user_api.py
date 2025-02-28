"""
Integration tests for the user management API endpoints in the AI writing enhancement platform.
Tests cover profile retrieval, updates, user preferences management, and account deletion functionality for both anonymous and authenticated users.
"""
# pytest==7.3.1
import pytest
# json - standard library
import json
# copy - standard library
import copy

from ..conftest import app, client, db, setup_test_db, auth_header, setup_test_user
from ..fixtures.user_fixtures import regular_user_data, verified_user_data, user_with_preferences

PROFILE_ENDPOINT = '/api/users/profile'
PREFERENCES_ENDPOINT = '/api/users/preferences'

class UserApiTestHelpers:
    """Helper methods for user API tests"""

    def __init__(self):
        """Initialize with common test data and utilities"""
        pass

    def get_user_from_db(self, db, user_id: str) -> dict:
        """Helper to retrieve user from database by ID

        Args:
            db: MongoDB database instance
            user_id: User ID

        Returns:
            User data from database
        """
        # Query users collection by ID
        user = db.users.find_one({'_id': user_id})
        # Return user document or None if not found
        return user

    def create_profile_update(self) -> dict:
        """Creates profile update data for testing

        Returns:
            Profile update data
        """
        # Create dictionary with first_name and last_name
        update_data = {
            'first_name': 'Updated',
            'last_name': 'User'
        }
        # Return update data dictionary
        return update_data

    def create_preferences_update(self) -> dict:
        """Creates preference update data for testing

        Returns:
            Preferences update data
        """
        # Create dictionary with theme, font_size, and notification settings
        preferences_data = {
            'theme': 'light',
            'font_size': 12,
            'notification_settings': {
                'email_notifications': False
            }
        }
        # Return preferences data dictionary
        return preferences_data

@pytest.mark.integration
def test_get_profile_success(client, db, setup_test_user, auth_header):
    """Test successful retrieval of user profile information"""
    # Send GET request to PROFILE_ENDPOINT with auth header
    response = client.get(PROFILE_ENDPOINT, headers=auth_header)
    # Assert response status code is 200
    assert response.status_code == 200
    # Parse JSON response and validate structure
    data = json.loads(response.data)
    assert 'email' in data
    # Verify response contains expected user data (email, first_name, last_name)
    assert data['email'] == setup_test_user['email']
    assert data['first_name'] == setup_test_user['firstName']
    assert data['last_name'] == setup_test_user['lastName']
    # Assert sensitive fields like password_hash are not included in response
    assert 'password_hash' not in data

@pytest.mark.integration
def test_get_profile_unauthenticated(client):
    """Test profile retrieval without authentication"""
    # Send GET request to PROFILE_ENDPOINT without auth header
    response = client.get(PROFILE_ENDPOINT)
    # Assert response status code is 401
    assert response.status_code == 401
    # Parse JSON response and verify it contains an error message
    data = json.loads(response.data)
    assert 'error' in data
    # Assert error message indicates authentication is required
    assert data['error'] == 'unauthorized'

@pytest.mark.integration
def test_update_profile_success(client, db, setup_test_user, auth_header):
    """Test successful update of user profile information"""
    helpers = UserApiTestHelpers()
    # Create updated profile data with new first_name and last_name
    update_data = helpers.create_profile_update()
    # Send PUT request to PROFILE_ENDPOINT with auth header and updated data
    response = client.put(PROFILE_ENDPOINT, headers=auth_header, json=update_data)
    # Assert response status code is 200
    assert response.status_code == 200
    # Parse JSON response and validate structure
    data = json.loads(response.data)
    assert 'email' in data
    # Verify response contains updated profile information
    assert data['first_name'] == update_data['first_name']
    assert data['last_name'] == update_data['last_name']
    # Query database to confirm updates were persisted
    updated_user = helpers.get_user_from_db(db, setup_test_user['_id'])
    assert updated_user['firstName'] == update_data['first_name']
    assert updated_user['lastName'] == update_data['last_name']

@pytest.mark.integration
def test_update_profile_invalid_data(client, db, setup_test_user, auth_header):
    """Test profile update with invalid data"""
    helpers = UserApiTestHelpers()
    # Create invalid profile data (e.g., too long first_name)
    invalid_data = {'first_name': 'a' * 100}
    # Send PUT request to PROFILE_ENDPOINT with auth header and invalid data
    response = client.put(PROFILE_ENDPOINT, headers=auth_header, json=invalid_data)
    # Assert response status code is 400
    assert response.status_code == 400
    # Verify response contains validation error message
    data = json.loads(response.data)
    assert 'error' in data
    # Query database to confirm data was not updated
    original_user = helpers.get_user_from_db(db, setup_test_user['_id'])
    assert original_user['firstName'] == setup_test_user['firstName']

@pytest.mark.integration
def test_update_profile_unauthenticated(client):
    """Test profile update without authentication"""
    # Create valid profile update data
    update_data = {'first_name': 'Updated'}
    # Send PUT request to PROFILE_ENDPOINT without auth header
    response = client.put(PROFILE_ENDPOINT, json=update_data)
    # Assert response status code is 401
    assert response.status_code == 401
    # Verify response contains error about missing authentication
    data = json.loads(response.data)
    assert 'error' in data

@pytest.mark.integration
def test_delete_user_account_success(client, db, setup_test_user, auth_header):
    """Test successful deletion of user account"""
    helpers = UserApiTestHelpers()
    # Send DELETE request to PROFILE_ENDPOINT with auth header
    response = client.delete(PROFILE_ENDPOINT, headers=auth_header)
    # Assert response status code is 200
    assert response.status_code == 200
    # Parse JSON response and validate success message
    data = json.loads(response.data)
    assert 'message' in data
    # Query database to confirm user has been deleted
    deleted_user = helpers.get_user_from_db(db, setup_test_user['_id'])
    assert deleted_user is None
    # Send another request with the same auth token
    response = client.get(PROFILE_ENDPOINT, headers=auth_header)
    # Verify the token is now invalid after account deletion
    assert response.status_code == 401

@pytest.mark.integration
def test_delete_user_account_unauthenticated(client):
    """Test account deletion without authentication"""
    # Send DELETE request to PROFILE_ENDPOINT without auth header
    response = client.delete(PROFILE_ENDPOINT)
    # Assert response status code is 401
    assert response.status_code == 401
    # Verify response contains error about missing authentication
    data = json.loads(response.data)
    assert 'error' in data

@pytest.mark.integration
def test_get_preferences_success(client, db, user_with_preferences, auth_header):
    """Test successful retrieval of user preferences"""
    # Insert user_with_preferences into test database
    db.users.insert_one(user_with_preferences)
    # Send GET request to PREFERENCES_ENDPOINT with auth header
    response = client.get(PREFERENCES_ENDPOINT, headers=auth_header)
    # Assert response status code is 200
    assert response.status_code == 200
    # Parse JSON response and validate structure
    data = json.loads(response.data)
    assert 'theme' in data
    assert 'font_size' in data
    # Verify response contains expected preference fields (theme, font_size, etc.)
    assert data['theme'] == user_with_preferences['preferences']['theme']
    assert data['font_size'] == user_with_preferences['preferences']['fontSize']
    # Assert preferences match those defined in user_with_preferences fixture
    db.users.delete_one({'_id': user_with_preferences['_id']})

@pytest.mark.integration
def test_get_preferences_user_without_preferences(client, db, regular_user_data, auth_header):
    """Test preferences retrieval for user without defined preferences"""
    # Insert regular_user_data (without preferences) into test database
    db.users.insert_one(regular_user_data)
    # Send GET request to PREFERENCES_ENDPOINT with auth header
    response = client.get(PREFERENCES_ENDPOINT, headers=auth_header)
    # Assert response status code is 200
    assert response.status_code == 200
    # Parse JSON response and validate that it contains default preferences
    data = json.loads(response.data)
    assert 'theme' in data
    assert 'font_size' in data
    # Verify default theme and font_size are provided
    assert data['theme'] is not None
    assert data['font_size'] is not None
    db.users.delete_one({'_id': regular_user_data['_id']})

@pytest.mark.integration
def test_update_preferences_success(client, db, setup_test_user, auth_header):
    """Test successful update of user preferences"""
    helpers = UserApiTestHelpers()
    # Create preferences update data with theme, font_size, and other settings
    update_data = helpers.create_preferences_update()
    # Send PUT request to PREFERENCES_ENDPOINT with auth header and update data
    response = client.put(PREFERENCES_ENDPOINT, headers=auth_header, json=update_data)
    # Assert response status code is 200
    assert response.status_code == 200
    # Parse JSON response and validate structure
    data = json.loads(response.data)
    assert 'theme' in data
    assert 'font_size' in data
    # Verify response contains updated preference values
    assert data['theme'] == update_data['theme']
    assert data['font_size'] == update_data['font_size']
    # Query database to confirm preferences were persisted
    updated_user = UserApiTestHelpers().get_user_from_db(db, setup_test_user['_id'])
    assert updated_user['preferences']['theme'] == update_data['theme']
    assert updated_user['preferences']['font_size'] == update_data['font_size']

@pytest.mark.integration
def test_update_preferences_partial(client, db, user_with_preferences, auth_header):
    """Test partial update of user preferences"""
    helpers = UserApiTestHelpers()
    # Insert user_with_preferences into test database
    db.users.insert_one(user_with_preferences)
    # Create partial preferences update (only theme update)
    partial_update = {'theme': 'dark'}
    # Send PUT request to PREFERENCES_ENDPOINT with auth header and partial update
    response = client.put(PREFERENCES_ENDPOINT, headers=auth_header, json=partial_update)
    # Assert response status code is 200
    assert response.status_code == 200
    # Parse JSON response and validate that only specified fields were updated
    data = json.loads(response.data)
    assert data['theme'] == partial_update['theme']
    # Verify other preference fields remain unchanged
    updated_user = UserApiTestHelpers().get_user_from_db(db, user_with_preferences['_id'])
    assert updated_user['preferences']['theme'] == partial_update['theme']
    db.users.delete_one({'_id': user_with_preferences['_id']})

@pytest.mark.integration
def test_update_preferences_invalid_data(client, db, setup_test_user, auth_header):
    """Test preferences update with invalid data"""
    helpers = UserApiTestHelpers()
    # Create invalid preferences data (e.g., invalid theme value)
    invalid_data = {'theme': 'invalid'}
    # Send PUT request to PREFERENCES_ENDPOINT with auth header and invalid data
    response = client.put(PREFERENCES_ENDPOINT, headers=auth_header, json=invalid_data)
    # Assert response status code is 400
    assert response.status_code == 400
    # Verify response contains validation error message
    data = json.loads(response.data)
    assert 'error' in data
    # Query database to confirm preferences were not updated
    original_user = helpers.get_user_from_db(db, setup_test_user['_id'])
    assert 'preferences' not in original_user

@pytest.mark.integration
def test_update_preferences_unauthenticated(client):
    """Test preferences update without authentication"""
    # Create valid preferences update data
    update_data = {'theme': 'dark'}
    # Send PUT request to PREFERENCES_ENDPOINT without auth header
    response = client.put(PREFERENCES_ENDPOINT, json=update_data)
    # Assert response status code is 401
    assert response.status_code == 401
    # Verify response contains error about missing authentication
    data = json.loads(response.data)
    assert 'error' in data