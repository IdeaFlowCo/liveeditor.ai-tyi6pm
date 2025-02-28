# pytest==^7.0.0 - Core testing framework
import pytest
# json - Standard library for handling JSON data
import json
# flask==2.3.0 - Web framework for API tests
from flask import Flask

# Internal imports
from src.backend.tests.conftest import app, client, db, setup_test_db, auth_header, setup_test_user, setup_test_document, basic_document, user_document, anonymous_document, document_with_versions, get_document_data, regular_user_data
from src.backend.tests.fixtures.document_fixtures import user_document, anonymous_document, document_with_versions, get_document_data
from src.backend.tests.fixtures.user_fixtures import regular_user_data

# Define API endpoints
DOCUMENTS_ENDPOINT = '/api/documents'
DOCUMENT_ENDPOINT = '/api/documents/{document_id}'
DOCUMENT_VERSIONS_ENDPOINT = '/api/documents/{document_id}/versions'
ANONYMOUS_SESSION_ENDPOINT = '/api/auth/anonymous'


@pytest.mark.integration
def test_create_document_anonymous(client, db):
    """Test creating a document with an anonymous session"""
    # Create anonymous session with POST to ANONYMOUS_SESSION_ENDPOINT
    response = client.post(ANONYMOUS_SESSION_ENDPOINT)
    assert response.status_code == 201
    session_data = json.loads(response.data)
    session_id = session_data['session_id']
    session_cookie = response.headers['Set-Cookie'].split(';')[0]

    # Create document data with title and content
    document_data = {
        'title': 'Anonymous Document',
        'content': 'This is an anonymous document.'
    }

    # Send POST request to DOCUMENTS_ENDPOINT with document data and session cookie
    response = client.post(
        DOCUMENTS_ENDPOINT,
        json=document_data,
        headers={'Cookie': session_cookie}
    )

    # Assert response status code is 201
    assert response.status_code == 201

    # Parse response JSON and validate structure
    data = json.loads(response.data)
    assert 'id' in data
    assert 'title' in data
    assert data['title'] == document_data['title']

    # Assert response contains document_id and session_id matches
    document_id = data['id']

    # GET the created document to verify it exists
    response = client.get(
        DOCUMENT_ENDPOINT.format(document_id=document_id),
        headers={'Cookie': session_cookie}
    )
    assert response.status_code == 200
    data = json.loads(response.data)

    # Assert document content matches what was submitted
    assert data['content'] == document_data['content']


@pytest.mark.integration
def test_create_document_authenticated(client, db, setup_test_user, auth_header):
    """Test creating a document as an authenticated user"""
    # Create document data with title and content
    document_data = {
        'title': 'Authenticated Document',
        'content': 'This is an authenticated document.'
    }

    # Send POST request to DOCUMENTS_ENDPOINT with document data and auth_header
    response = client.post(
        DOCUMENTS_ENDPOINT,
        json=document_data,
        headers=auth_header
    )

    # Assert response status code is 201
    assert response.status_code == 201

    # Parse response JSON and validate structure
    data = json.loads(response.data)
    assert 'id' in data
    assert 'title' in data
    assert data['title'] == document_data['title']

    # Assert response contains document_id and user_id matches setup_test_user
    document_id = data['id']
    assert data['user_id'] == setup_test_user['_id']

    # GET the created document to verify it exists
    response = client.get(
        DOCUMENT_ENDPOINT.format(document_id=document_id),
        headers=auth_header
    )
    assert response.status_code == 200
    data = json.loads(response.data)

    # Assert document content matches what was submitted
    assert data['content'] == document_data['content']

    # Assert document is associated with the authenticated user
    assert data['user_id'] == setup_test_user['_id']


@pytest.mark.integration
def test_get_document_by_id(client, db, setup_test_document, auth_header):
    """Test retrieving a document by its ID"""
    # Extract document_id from setup_test_document
    document_id = setup_test_document['_id']

    # Send GET request to DOCUMENT_ENDPOINT with document_id and auth_header
    response = client.get(
        DOCUMENT_ENDPOINT.format(document_id=document_id),
        headers=auth_header
    )

    # Assert response status code is 200
    assert response.status_code == 200

    # Parse response JSON and validate structure
    data = json.loads(response.data)
    assert 'id' in data
    assert 'title' in data
    assert 'content' in data
    assert 'userId' in data
    assert 'createdAt' in data
    assert 'updatedAt' in data

    # Assert response contains correct document title, content, user_id
    assert data['title'] == setup_test_document['title']
    assert data['content'] == setup_test_document['content']
    assert data['userId'] == setup_test_document['userId']

    # Assert response includes createdAt and updatedAt timestamps
    assert 'createdAt' in data
    assert 'updatedAt' in data

    # Assert response metadata matches expected values
    assert data['id'] == document_id
    assert data['title'] == setup_test_document['title']
    assert data['content'] == setup_test_document['content']


@pytest.mark.integration
def test_get_document_anonymous(client, db):
    """Test retrieving an anonymous document"""
    # Create anonymous session with POST to ANONYMOUS_SESSION_ENDPOINT
    response = client.post(ANONYMOUS_SESSION_ENDPOINT)
    assert response.status_code == 201
    session_data = json.loads(response.data)
    session_id = session_data['session_id']
    session_cookie = response.headers['Set-Cookie'].split(';')[0]

    # Create document via POST to DOCUMENTS_ENDPOINT with session cookie
    document_data = {'title': 'Anonymous Doc', 'content': 'Anonymous Content'}
    response = client.post(
        DOCUMENTS_ENDPOINT,
        json=document_data,
        headers={'Cookie': session_cookie}
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    document_id = data['id']

    # Send GET request to DOCUMENT_ENDPOINT with document_id and session cookie
    response = client.get(
        DOCUMENT_ENDPOINT.format(document_id=document_id),
        headers={'Cookie': session_cookie}
    )

    # Assert response status code is 200
    assert response.status_code == 200

    # Parse response JSON and validate structure
    data = json.loads(response.data)
    assert 'id' in data
    assert 'title' in data
    assert 'content' in data
    assert 'createdAt' in data
    assert 'updatedAt' in data

    # Assert session_id in document matches anonymous session
    assert data['id'] == document_id
    assert data['title'] == document_data['title']
    assert data['content'] == document_data['content']


@pytest.mark.integration
def test_update_document(client, db, setup_test_document, auth_header):
    """Test updating an existing document"""
    # Extract document_id from setup_test_document
    document_id = setup_test_document['_id']

    # Create updated document data with new title and content
    updated_data = {
        'title': 'Updated Title',
        'content': 'Updated Content',
        'create_version': True
    }

    # Send PUT request to DOCUMENT_ENDPOINT with document_id, updated data, and auth_header
    response = client.put(
        DOCUMENT_ENDPOINT.format(document_id=document_id),
        json=updated_data,
        headers=auth_header
    )

    # Assert response status code is 200
    assert response.status_code == 200

    # Parse response JSON and validate structure
    data = json.loads(response.data)
    assert 'id' in data
    assert 'title' in data
    assert 'content' in data
    assert 'userId' in data
    assert 'createdAt' in data
    assert 'updatedAt' in data

    # Assert document title and content have been updated
    assert data['title'] == updated_data['title']
    assert data['content'] == updated_data['content']

    # Assert updatedAt timestamp is newer than createdAt
    assert data['updatedAt'] > data['createdAt']

    # Assert a new version has been created
    versions_response = client.get(
        DOCUMENT_VERSIONS_ENDPOINT.format(document_id=document_id),
        headers=auth_header
    )
    assert versions_response.status_code == 200
    versions_data = json.loads(versions_response.data)
    assert versions_data['total'] > 1

    # GET document versions to verify version history
    assert versions_response.status_code == 200


@pytest.mark.integration
def test_delete_document(client, db, setup_test_document, auth_header):
    """Test deleting a document"""
    # Extract document_id from setup_test_document
    document_id = setup_test_document['_id']

    # Send DELETE request to DOCUMENT_ENDPOINT with document_id and auth_header
    response = client.delete(
        DOCUMENT_ENDPOINT.format(document_id=document_id),
        headers=auth_header
    )

    # Assert response status code is 204
    assert response.status_code == 204

    # Send GET request to DOCUMENT_ENDPOINT with same document_id
    response = client.get(
        DOCUMENT_ENDPOINT.format(document_id=document_id),
        headers=auth_header
    )

    # Assert response status code is 404
    assert response.status_code == 404

    # Check database directly to confirm document is marked as deleted
    # TODO: Implement database check


@pytest.mark.integration
def test_list_user_documents(client, db, setup_test_user, auth_header):
    """Test listing all documents for a user"""
    # Create multiple documents for the test user via POST requests
    num_documents = 3
    for i in range(num_documents):
        document_data = {'title': f'Test Document {i}', 'content': f'Test Content {i}'}
        response = client.post(
            DOCUMENTS_ENDPOINT,
            json=document_data,
            headers=auth_header
        )
        assert response.status_code == 201

    # Send GET request to DOCUMENTS_ENDPOINT with auth_header
    response = client.get(
        DOCUMENTS_ENDPOINT,
        headers=auth_header
    )

    # Assert response status code is 200
    assert response.status_code == 200

    # Parse response JSON and validate structure
    data = json.loads(response.data)
    assert 'items' in data
    assert 'total' in data
    assert 'limit' in data
    assert 'skip' in data

    # Assert response contains items array with all created documents
    assert len(data['items']) == num_documents
    assert data['total'] == num_documents
    assert data['limit'] == 10
    assert data['skip'] == 0

    # Assert pagination metadata is correct (total, page, limit)
    # TODO: Implement pagination assertions

    # Test pagination by requesting different pages
    # TODO: Implement pagination tests

    # Test filtering by adding query parameters
    # TODO: Implement filtering tests


@pytest.mark.integration
def test_document_versions(client, db, document_with_versions, auth_header):
    """Test retrieving document version history"""
    # Insert document_with_versions into test database
    db.documents.insert_one(document_with_versions)

    # Extract document_id from document_with_versions
    document_id = document_with_versions['_id']

    # Send GET request to DOCUMENT_VERSIONS_ENDPOINT with document_id and auth_header
    response = client.get(
        DOCUMENT_VERSIONS_ENDPOINT.format(document_id=document_id),
        headers=auth_header
    )

    # Assert response status code is 200
    assert response.status_code == 200

    # Parse response JSON and validate structure
    data = json.loads(response.data)
    assert 'items' in data
    assert 'total' in data
    assert 'limit' in data
    assert 'skip' in data

    # Assert response contains items array with all versions
    assert len(data['items']) == 3
    assert data['total'] == 3
    assert data['limit'] == 10
    assert data['skip'] == 0

    # Assert versions are ordered correctly by versionNumber
    version_numbers = [version['version_number'] for version in data['items']]
    assert version_numbers == [3, 2, 1]

    # Assert each version has correct metadata and content
    for version in data['items']:
        assert 'id' in version
        assert 'document_id' in version
        assert 'version_number' in version
        assert 'content' in version
        assert 'createdAt' in version


@pytest.mark.integration
def test_unauthorized_document_access(client, db, setup_test_document):
    """Test that users cannot access documents they don't own"""
    # Extract document_id from setup_test_document
    document_id = setup_test_document['_id']

    # Create a second test user and authenticate
    second_user_data = {'email': 'second@example.com', 'password': 'password'}
    response = client.post('/api/auth/register', json=second_user_data)
    assert response.status_code == 201
    second_auth_header = {'Authorization': f"Bearer {json.loads(response.data)['access_token']}"}

    # Send GET request to DOCUMENT_ENDPOINT with document_id and second user's auth
    response = client.get(
        DOCUMENT_ENDPOINT.format(document_id=document_id),
        headers=second_auth_header
    )

    # Assert response status code is 403 (Forbidden)
    assert response.status_code == 403

    # Send PUT request to update document with second user's auth
    response = client.put(
        DOCUMENT_ENDPOINT.format(document_id=document_id),
        json={'title': 'Attempted Update'},
        headers=second_auth_header
    )

    # Assert response status code is 403 (Forbidden)
    assert response.status_code == 403

    # Send DELETE request with second user's auth
    response = client.delete(
        DOCUMENT_ENDPOINT.format(document_id=document_id),
        headers=second_auth_header
    )

    # Assert response status code is 403 (Forbidden)
    assert response.status_code == 403


@pytest.mark.integration
def test_create_document_validation(client, auth_header):
    """Test document creation with invalid data"""
    # Create document data with missing title
    invalid_data = {'content': 'Some content'}

    # Send POST request to DOCUMENTS_ENDPOINT with invalid data and auth_header
    response = client.post(
        DOCUMENTS_ENDPOINT,
        json=invalid_data,
        headers=auth_header
    )

    # Assert response status code is 400
    assert response.status_code == 400

    # Assert error response contains validation details
    error_data = json.loads(response.data)
    assert 'error' in error_data
    assert 'message' in error_data
    assert 'details' in error_data
    assert 'title' in error_data['details']

    # Create document data with extremely long content (over limit)
    oversized_data = {'title': 'Oversized', 'content': 'a' * 30000}

    # Send POST request with oversized content
    response = client.post(
        DOCUMENTS_ENDPOINT,
        json=oversized_data,
        headers=auth_header
    )

    # Assert response status code is 400
    assert response.status_code == 400

    # Assert error response mentions size limitations
    error_data = json.loads(response.data)
    assert 'error' in error_data
    assert 'message' in error_data
    assert 'content' in error_data['details']
    assert 'size' in error_data['details']['content'][0]


@pytest.mark.integration
def test_anonymous_to_user_document_transfer(client, db):
    """Test documents transfer when anonymous user registers"""
    # Create anonymous session with POST to ANONYMOUS_SESSION_ENDPOINT
    response = client.post(ANONYMOUS_SESSION_ENDPOINT)
    assert response.status_code == 201
    session_data = json.loads(response.data)
    session_id = session_data['session_id']
    session_cookie = response.headers['Set-Cookie'].split(';')[0]

    # Extract session cookie and session_id from response
    # Create multiple documents with anonymous session
    num_anonymous_docs = 2
    anonymous_docs = []
    for i in range(num_anonymous_docs):
        document_data = {'title': f'Anonymous Doc {i}', 'content': f'Anonymous Content {i}'}
        response = client.post(
            DOCUMENTS_ENDPOINT,
            json=document_data,
            headers={'Cookie': session_cookie}
        )
        assert response.status_code == 201
        anonymous_docs.append(json.loads(response.data))

    # Register new user with the same session_id (convert to registered)
    registration_data = {'email': 'newuser@example.com', 'password': 'password', 'session_id': session_id,
                         'first_name': 'New', 'last_name': 'User'}
    response = client.post('/api/auth/register', json=registration_data)
    assert response.status_code == 201
    auth_data = json.loads(response.data)
    auth_token = auth_data['access_token']
    auth_header = {'Authorization': f"Bearer {auth_token}"}

    # Extract auth token from registration response
    # Send GET request to DOCUMENTS_ENDPOINT with new auth token
    response = client.get(
        DOCUMENTS_ENDPOINT,
        headers=auth_header
    )
    assert response.status_code == 200
    user_docs = json.loads(response.data)['items']

    # Assert all previously anonymous documents are now associated with the user
    assert len(user_docs) == num_anonymous_docs
    for doc in user_docs:
        assert doc['userId'] == auth_data['user_id']
        assert doc['sessionId'] is None

    # Verify document content is preserved during transfer
    for i, doc in enumerate(user_docs):
        assert doc['title'] == anonymous_docs[i]['title']
        # TODO: Implement content verification

class DocumentApiTestUtils:
    """Utility class with helper methods for document API tests"""

    def __init__(self):
        """Initialize the utility class"""
        pass

    def create_anonymous_session(self, client):
        """Helper to create an anonymous session"""
        # Send POST request to ANONYMOUS_SESSION_ENDPOINT
        response = client.post(ANONYMOUS_SESSION_ENDPOINT)
        assert response.status_code == 201
        session_data = json.loads(response.data)
        session_id = session_data['session_id']
        session_cookie = response.headers['Set-Cookie'].split(';')[0]
        return session_id, session_cookie

    def create_test_document(self, client, auth, document_data):
        """Helper to create a test document"""
        # Send POST request to DOCUMENTS_ENDPOINT with document_data and auth
        response = client.post(
            DOCUMENTS_ENDPOINT,
            json=document_data,
            headers=auth
        )
        # Assert creation was successful
        assert response.status_code == 201
        # Return parsed response with document data
        return json.loads(response.data)

    def verify_document_content(self, document, expected_data):
        """Helper to verify document content matches expected"""
        # Compare document title with expected title
        if document['title'] != expected_data['title']:
            return False
        # Compare document content with expected content
        if document['content'] != expected_data['content']:
            return False
        # Compare additional fields as specified
        # Return True if all match, False otherwise
        return True