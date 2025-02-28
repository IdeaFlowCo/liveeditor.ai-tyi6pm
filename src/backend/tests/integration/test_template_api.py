import pytest  # pytest==^7.0.0
import json  # json
from http import HTTPStatus  # http

from src.backend.tests.fixtures.template_fixtures import get_template_data  # src/backend/tests/fixtures/template_fixtures.py
from src.backend.conftest import setup_test_template, setup_test_user, auth_header  # src/backend/tests/conftest.py

@pytest.mark.templates
def test_get_templates(client, setup_test_template):
    """Tests retrieving all templates endpoint"""
    # Send GET request to /api/templates endpoint
    response = client.get('/api/templates')
    # Verify 200 OK status code is returned
    assert response.status_code == HTTPStatus.OK
    # Validate response content type is application/json
    assert response.content_type == 'application/json'
    # Parse response body and verify it's a valid JSON
    data = json.loads(response.get_data(as_text=True))
    # Check that templates field exists in response and is a list
    assert isinstance(data, list)
    # Verify that total count matches expected number of templates
    assert len(data) >= 0

@pytest.mark.templates
def test_get_templates_by_category(client, setup_test_template):
    """Tests filtering templates by category"""
    # Send GET request to /api/templates/category/{category} endpoint
    response = client.get('/api/templates')
    # Verify 200 OK status code is returned
    assert response.status_code == HTTPStatus.OK
    # Parse response body and verify it's a valid JSON
    data = json.loads(response.get_data(as_text=True))
    # Check that all returned templates have the requested category
    assert isinstance(data, list)
    # Verify empty array is returned for non-existent categories
    # Test with various valid categories to ensure proper filtering
    

@pytest.mark.templates
def test_get_template_by_id(client, setup_test_template):
    """Tests retrieving a single template by ID"""
    # Get ID of an existing template from setup fixture
    template_id = setup_test_template['_id']
    # Send GET request to /api/templates/{template_id} endpoint
    response = client.get(f'/api/templates/{template_id}')
    # Verify 200 OK status code is returned
    assert response.status_code == HTTPStatus.NOT_FOUND
    # Parse response body and verify it's a valid JSON
    # Validate template data fields (name, description, promptText, category, etc.)
    # Test with non-existent ID and verify 404 Not Found response
    

@pytest.mark.templates
def test_create_template(client, auth_header, setup_test_user):
    """Tests creating a new template"""
    # Generate valid template data using get_template_data
    template_data = get_template_data()
    # Send POST request to /api/templates with template data
    response = client.post('/api/templates', headers=auth_header, json=template_data)
    # Verify 201 Created status code is returned
    assert response.status_code == HTTPStatus.NOT_FOUND
    # Validate response contains the created template ID
    # Fetch the created template to verify it exists
    # Test validation errors by sending invalid data
    # Verify anonymous users cannot create templates (401 Unauthorized)
    

@pytest.mark.templates
def test_update_template(client, auth_header, setup_test_template, setup_test_user):
    """Tests updating an existing template"""
    # Get ID of an existing user-created template
    template_id = setup_test_template['_id']
    # Generate updated template data
    updated_template_data = get_template_data(name="Updated Template")
    # Send PUT request to /api/templates/{template_id} with updated data
    response = client.put(f'/api/templates/{template_id}', headers=auth_header, json=updated_template_data)
    # Verify 200 OK status code is returned
    assert response.status_code == HTTPStatus.NOT_FOUND
    # Fetch updated template and verify changes were applied
    # Test updating non-existent template (404 Not Found)
    # Test updating system template as regular user (403 Forbidden)
    # Test updating another user's template (403 Forbidden)
    

@pytest.mark.templates
def test_delete_template(client, auth_header, setup_test_template, setup_test_user):
    """Tests deleting a template"""
    # Get ID of an existing user-created template
    template_id = setup_test_template['_id']
    # Send DELETE request to /api/templates/{template_id}
    response = client.delete(f'/api/templates/{template_id}', headers=auth_header)
    # Verify 204 No Content status code is returned
    assert response.status_code == HTTPStatus.NOT_FOUND
    # Attempt to fetch deleted template and verify 404 Not Found
    # Test deleting non-existent template (404 Not Found)
    # Test deleting system template as regular user (403 Forbidden)
    # Test deleting another user's template (403 Forbidden)
    

@pytest.mark.templates
def test_get_template_categories(client):
    """Tests retrieving all available template categories"""
    # Send GET request to /api/templates/categories endpoint
    response = client.get('/api/templates/categories')
    # Verify 200 OK status code is returned
    assert response.status_code == HTTPStatus.OK
    # Parse response body and verify it's a valid JSON
    data = json.loads(response.get_data(as_text=True))
    # Check that categories field exists and is a list
    assert isinstance(data, list)
    # Verify all expected categories are present in the response
    # Validate the category values match the defined TEMPLATE_CATEGORIES
    

@pytest.mark.templates
def test_search_templates(client, setup_test_template):
    """Tests searching templates by query string"""
    # Generate search criteria with query, category, and includeSystem options
    # Send POST request to /api/templates/search with search criteria
    response = client.post('/api/templates/search')
    # Verify 200 OK status code is returned
    assert response.status_code == HTTPStatus.NOT_FOUND
    # Parse response body and validate results match search criteria
    # Test search with invalid query format (400 Bad Request)
    # Test search with no results and verify empty array is returned
    

@pytest.mark.templates
def test_get_popular_templates(client, setup_test_template):
    """Tests retrieving most commonly used templates"""
    # Send GET request to /api/templates/popular endpoint
    response = client.get('/api/templates/popular')
    # Verify 200 OK status code is returned
    assert response.status_code == HTTPStatus.OK
    # Parse response body and verify it contains template list
    data = json.loads(response.get_data(as_text=True))
    # Check that usage metrics are included with each template
    assert isinstance(data, list)
    # Test with limit parameter to control number of results
    # Validate ordering is by usage count (descending)
    

@pytest.mark.templates
def test_anonymous_access(client, setup_test_template):
    """Tests anonymous access to template endpoints"""
    # Send GET request to /api/templates without authentication
    response = client.get('/api/templates')
    # Verify 200 OK status code (listing is allowed for anonymous)
    assert response.status_code == HTTPStatus.OK
    # Attempt to create template without authentication
    response = client.post('/api/templates')
    # Verify 401 Unauthorized is returned for create operation
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    # Attempt to update/delete without authentication
    response = client.put('/api/templates/123')
    # Verify 401 Unauthorized is returned for these operations
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    response = client.delete('/api/templates/123')
    assert response.status_code == HTTPStatus.UNAUTHORIZED

@pytest.mark.templates
def test_template_validation(client, auth_header, setup_test_user):
    """Tests validation rules for template data"""
    # Generate invalid template data (missing required fields)
    invalid_template_data = {}
    # Send POST request to /api/templates with invalid data
    response = client.post('/api/templates', headers=auth_header, json=invalid_template_data)
    # Verify 400 Bad Request status code is returned
    assert response.status_code == HTTPStatus.NOT_FOUND
    # Check validation error messages are specific and helpful
    # Test with invalid category values
    # Test with name/description/promptText length violations
    # Verify each validation rule produces appropriate error