import pytest  # pytest==^7.0.0
from unittest.mock import patch  # unittest.mock standard library
from flask import Flask  # flask==^2.3.0
from flask.testing import FlaskClient  # flask==^2.3.0
from flask_restful import Api  # flask_restful==^0.3.10
import json  # json standard library

from src.backend.api.documents import DocumentResource, DocumentsResource, DocumentVersionResource, DocumentVersionsResource, DocumentCompareResource, DocumentExportResource, DocumentImportResource  # src/backend/api/documents.py
from src.backend.core.documents.document_service import DocumentService, DocumentAccessError, AnonymousRateLimitError  # src/backend/core/documents/document_service.py
from src.backend.api.schemas.document_schema import DocumentCreateSchema, DocumentUpdateSchema, DocumentResponseSchema, DocumentExportSchema, DocumentImportSchema, DocumentCompareSchema  # src/backend/api/schemas/document_schema.py
from src.backend.tests.fixtures.document_fixtures import get_document_data, get_document_version_data, generate_document_id, generate_version_id  # src/backend/tests/fixtures/document_fixtures.py
from src.backend.api.middleware.auth_middleware import get_current_user_id, is_anonymous_session  # src/backend/api/middleware/auth_middleware.py

TEST_PREFIX = '/api/documents'
USER_ID = 'user123'
SESSION_ID = 'session456'


def setup_test_client(DocumentService):
    """Helper function to create and configure a Flask test client for document API testing"""
    # Create Flask app instance
    app = Flask(__name__)
    # Configure app for testing
    app.config['TESTING'] = True
    # Register document endpoints with Flask-RESTful
    api = Api(app)
    api.add_resource(DocumentsResource, f'{TEST_PREFIX}/', resource_class_kwargs={'document_service': DocumentService})
    api.add_resource(DocumentResource, f'{TEST_PREFIX}/<string:document_id>', resource_class_kwargs={'document_service': DocumentService})
    api.add_resource(DocumentVersionResource, f'{TEST_PREFIX}/<string:document_id>/versions/<string:version_id>', resource_class_kwargs={'document_service': DocumentService})
    api.add_resource(DocumentVersionsResource, f'{TEST_PREFIX}/<string:document_id>/versions', resource_class_kwargs={'document_service': DocumentService})
    api.add_resource(DocumentCompareResource, f'{TEST_PREFIX}/<string:document_id>/compare', resource_class_kwargs={'document_service': DocumentService})
    api.add_resource(DocumentExportResource, f'{TEST_PREFIX}/<string:document_id>/export', resource_class_kwargs={'document_service': DocumentService})
    api.add_resource(DocumentImportResource, f'{TEST_PREFIX}/import', resource_class_kwargs={'document_service': DocumentService})
    # Return test client
    return app.test_client()


@pytest.mark.unit
@patch('src.backend.api.middleware.auth_middleware.get_current_user_id')
@patch('src.backend.api.middleware.auth_middleware.is_anonymous_session')
def test_create_document_authenticated(mock_is_anonymous_session, mock_get_current_user_id):
    """Test that authenticated users can create documents successfully"""
    # Mock get_current_user_id to return USER_ID
    mock_get_current_user_id.return_value = USER_ID
    # Mock is_anonymous_session to return False
    mock_is_anonymous_session.return_value = False
    # Create DocumentService mock with create_document method
    document_service_mock = pytest.helpers.Mock()
    document_service_mock.create_document.return_value = get_document_data(document_id=generate_document_id())
    # Create test client with mocked service
    test_client = setup_test_client(document_service_mock)
    # Prepare valid document data
    document_data = {'title': 'Test Document', 'content': 'Test Content'}
    # Send POST request to /api/documents
    response = test_client.post(f'{TEST_PREFIX}/', json=document_data)
    # Assert response status code is 201
    assert response.status_code == 201
    # Assert response contains document ID and other metadata
    response_data = json.loads(response.data.decode('utf-8'))
    assert 'id' in response_data
    assert response_data['title'] == 'Test Document'
    # Assert Location header contains document URL
    assert f'/documents/{response_data["id"]}' in response.headers['Location']
    # Assert DocumentService.create_document was called with correct arguments
    document_service_mock.create_document.assert_called_once_with(document_data, USER_ID, None)


@pytest.mark.unit
@patch('src.backend.api.middleware.auth_middleware.get_current_user_id')
@patch('src.backend.api.middleware.auth_middleware.is_anonymous_session')
def test_create_document_anonymous(mock_is_anonymous_session, mock_get_current_user_id):
    """Test that anonymous users can create documents successfully"""
    # Mock get_current_user_id to return None
    mock_get_current_user_id.return_value = None
    # Mock is_anonymous_session to return True with SESSION_ID
    mock_is_anonymous_session.return_value = True
    # Create DocumentService mock with create_document method
    document_service_mock = pytest.helpers.Mock()
    document_service_mock.create_document.return_value = get_document_data(document_id=generate_document_id())
    # Create test client with mocked service
    test_client = setup_test_client(document_service_mock)
    # Prepare valid document data
    document_data = {'title': 'Test Document', 'content': 'Test Content'}
    # Send POST request to /api/documents
    with test_client.session_transaction() as sess:
        sess['anonymous_session'] = SESSION_ID
    response = test_client.post(f'{TEST_PREFIX}/', json=document_data, environ_base={'HTTP_COOKIE': f'anonymous_session={SESSION_ID}'})
    # Assert response status code is 201
    assert response.status_code == 201
    # Assert response contains document ID and other metadata
    response_data = json.loads(response.data.decode('utf-8'))
    assert 'id' in response_data
    assert response_data['title'] == 'Test Document'
    # Assert DocumentService.create_document was called with session_id instead of user_id
    document_service_mock.create_document.assert_called_once_with(document_data, None, SESSION_ID)


@pytest.mark.unit
@patch('src.backend.api.middleware.auth_middleware.get_current_user_id')
def test_create_document_validation_error(mock_get_current_user_id):
    """Test that creating documents with invalid data returns validation errors"""
    # Mock get_current_user_id to return USER_ID
    mock_get_current_user_id.return_value = USER_ID
    # Create DocumentService mock
    document_service_mock = pytest.helpers.Mock()
    # Create test client with mocked service
    test_client = setup_test_client(document_service_mock)
    # Prepare invalid document data (missing required fields)
    document_data = {'content': 'Test Content'}
    # Send POST request to /api/documents
    response = test_client.post(f'{TEST_PREFIX}/', json=document_data)
    # Assert response status code is 400
    assert response.status_code == 400
    # Assert response contains validation error messages
    response_data = json.loads(response.data.decode('utf-8'))
    assert 'error' in response_data
    assert 'message' in response_data
    # Assert DocumentService.create_document was not called
    assert document_service_mock.create_document.call_count == 0


@pytest.mark.unit
@patch('src.backend.api.middleware.auth_middleware.get_current_user_id')
@patch('src.backend.api.middleware.auth_middleware.is_anonymous_session')
def test_create_document_anonymous_rate_limit(mock_is_anonymous_session, mock_get_current_user_id):
    """Test that anonymous users are rate limited for document creation"""
    # Mock get_current_user_id to return None
    mock_get_current_user_id.return_value = None
    # Mock is_anonymous_session to return True with SESSION_ID
    mock_is_anonymous_session.return_value = True
    # Create DocumentService mock with create_document method
    document_service_mock = pytest.helpers.Mock()
    document_service_mock.create_document.side_effect = AnonymousRateLimitError(SESSION_ID, 5, 24)
    # Create test client with mocked service
    test_client = setup_test_client(document_service_mock)
    # Prepare valid document data
    document_data = {'title': 'Test Document', 'content': 'Test Content'}
    # Send POST request to /api/documents
    with test_client.session_transaction() as sess:
        sess['anonymous_session'] = SESSION_ID
    response = test_client.post(f'{TEST_PREFIX}/', json=document_data, environ_base={'HTTP_COOKIE': f'anonymous_session={SESSION_ID}'})
    # Assert response status code is 429
    assert response.status_code == 429
    # Assert response contains rate limit exceeded message
    response_data = json.loads(response.data.decode('utf-8'))
    assert 'error' in response_data
    assert response_data['error'] == 'rate_limit_exceeded'
    # Assert DocumentService.create_document was called with session_id
    document_service_mock.create_document.assert_called_once_with(document_data, None, SESSION_ID)


@pytest.mark.unit
@patch('src.backend.api.middleware.auth_middleware.get_current_user_id')
@patch('src.backend.api.middleware.auth_middleware.is_anonymous_session')
def test_get_document_authenticated(mock_is_anonymous_session, mock_get_current_user_id):
    """Test that authenticated users can retrieve their documents"""
    # Mock get_current_user_id to return USER_ID
    mock_get_current_user_id.return_value = USER_ID
    # Mock is_anonymous_session to return False
    mock_is_anonymous_session.return_value = False
    # Create DocumentService mock with get_document method
    document_service_mock = pytest.helpers.Mock()
    document_id = generate_document_id()
    document_service_mock.get_document.return_value = get_document_data(document_id=document_id)
    # Create test client with mocked service
    test_client = setup_test_client(document_service_mock)
    # Send GET request to /api/documents/{document_id}
    response = test_client.get(f'{TEST_PREFIX}/{document_id}')
    # Assert response status code is 200
    assert response.status_code == 200
    # Assert response contains document data
    response_data = json.loads(response.data.decode('utf-8'))
    assert response_data['id'] == document_id
    # Assert DocumentService.get_document was called with correct document_id and user_id
    document_service_mock.get_document.assert_called_once_with(document_id, USER_ID, None, include_content=True)


@pytest.mark.unit
@patch('src.backend.api.middleware.auth_middleware.get_current_user_id')
@patch('src.backend.api.middleware.auth_middleware.is_anonymous_session')
def test_get_document_anonymous(mock_is_anonymous_session, mock_get_current_user_id):
    """Test that anonymous users can retrieve their session documents"""
    # Mock get_current_user_id to return None
    mock_get_current_user_id.return_value = None
    # Mock is_anonymous_session to return True with SESSION_ID
    mock_is_anonymous_session.return_value = True
    # Create DocumentService mock with get_document method
    document_service_mock = pytest.helpers.Mock()
    document_id = generate_document_id()
    document_service_mock.get_document.return_value = get_document_data(document_id=document_id)
    # Create test client with mocked service
    test_client = setup_test_client(document_service_mock)
    # Send GET request to /api/documents/{document_id}
    with test_client.session_transaction() as sess:
        sess['anonymous_session'] = SESSION_ID
    response = test_client.get(f'{TEST_PREFIX}/{document_id}', environ_base={'HTTP_COOKIE': f'anonymous_session={SESSION_ID}'})
    # Assert response status code is 200
    assert response.status_code == 200
    # Assert response contains document data
    response_data = json.loads(response.data.decode('utf-8'))
    assert response_data['id'] == document_id
    # Assert DocumentService.get_document was called with session_id instead of user_id
    document_service_mock.get_document.assert_called_once_with(document_id, None, SESSION_ID, include_content=True)


@pytest.mark.unit
@patch('src.backend.api.middleware.auth_middleware.get_current_user_id')
def test_get_document_not_found(mock_get_current_user_id):
    """Test that retrieving a non-existent document returns 404"""
    # Mock get_current_user_id to return USER_ID
    mock_get_current_user_id.return_value = USER_ID
    # Create DocumentService mock with get_document method
    document_service_mock = pytest.helpers.Mock()
    document_id = generate_document_id()
    document_service_mock.get_document.return_value = None
    # Create test client with mocked service
    test_client = setup_test_client(document_service_mock)
    # Send GET request to /api/documents/{document_id}
    response = test_client.get(f'{TEST_PREFIX}/{document_id}')
    # Assert response status code is 404
    assert response.status_code == 404
    # Assert response contains appropriate error message
    response_data = json.loads(response.data.decode('utf-8'))
    assert 'error' in response_data
    assert response_data['error'] == 'document_not_found'
    # Assert DocumentService.get_document was called with correct document_id
    document_service_mock.get_document.assert_called_once_with(document_id, USER_ID, None, include_content=True)


@pytest.mark.unit
@patch('src.backend.api.middleware.auth_middleware.get_current_user_id')
def test_get_document_access_denied(mock_get_current_user_id):
    """Test that retrieving another user's document returns 403"""
    # Mock get_current_user_id to return USER_ID
    mock_get_current_user_id.return_value = USER_ID
    # Create DocumentService mock with get_document method
    document_service_mock = pytest.helpers.Mock()
    document_id = generate_document_id()
    document_service_mock.get_document.side_effect = DocumentAccessError(document_id, 'other_user')
    # Create test client with mocked service
    test_client = setup_test_client(document_service_mock)
    # Send GET request to /api/documents/{document_id}
    response = test_client.get(f'{TEST_PREFIX}/{document_id}')
    # Assert response status code is 403
    assert response.status_code == 403
    # Assert response contains appropriate error message
    response_data = json.loads(response.data.decode('utf-8'))
    assert 'error' in response_data
    assert response_data['error'] == 'access_denied'
    # Assert DocumentService.get_document was called with correct document_id
    document_service_mock.get_document.assert_called_once_with(document_id, USER_ID, None, include_content=True)


@pytest.mark.unit
@patch('src.backend.api.middleware.auth_middleware.get_current_user_id')
def test_update_document(mock_get_current_user_id):
    """Test that users can update their documents"""
    # Mock get_current_user_id to return USER_ID
    mock_get_current_user_id.return_value = USER_ID
    # Create DocumentService mock with update_document method
    document_service_mock = pytest.helpers.Mock()
    document_id = generate_document_id()
    document_service_mock.update_document.return_value = get_document_data(document_id=document_id, title='Updated Title', content='Updated Content')
    # Create test client with mocked service
    test_client = setup_test_client(document_service_mock)
    # Prepare update data with new title and content
    update_data = {'title': 'Updated Title', 'content': 'Updated Content'}
    # Send PUT request to /api/documents/{document_id}
    response = test_client.put(f'{TEST_PREFIX}/{document_id}', json=update_data)
    # Assert response status code is 200
    assert response.status_code == 200
    # Assert response contains updated document data
    response_data = json.loads(response.data.decode('utf-8'))
    assert response_data['id'] == document_id
    assert response_data['title'] == 'Updated Title'
    assert response_data['content'] == 'Updated Content'
    # Assert DocumentService.update_document was called with correct arguments
    document_service_mock.update_document.assert_called_once_with(document_id, update_data, USER_ID, None, create_version=False)


@pytest.mark.unit
@patch('src.backend.api.middleware.auth_middleware.get_current_user_id')
def test_update_document_validation_error(mock_get_current_user_id):
    """Test that updating documents with invalid data returns validation errors"""
    # Mock get_current_user_id to return USER_ID
    mock_get_current_user_id.return_value = USER_ID
    # Create DocumentService mock
    document_service_mock = pytest.helpers.Mock()
    document_id = generate_document_id()
    # Create test client with mocked service
    test_client = setup_test_client(document_service_mock)
    # Prepare invalid update data (e.g., empty title)
    update_data = {'title': ''}
    # Send PUT request to /api/documents/{document_id}
    response = test_client.put(f'{TEST_PREFIX}/{document_id}', json=update_data)
    # Assert response status code is 400
    assert response.status_code == 400
    # Assert response contains validation error messages
    response_data = json.loads(response.data.decode('utf-8'))
    assert 'error' in response_data
    assert 'message' in response_data
    # Assert DocumentService.update_document was not called
    assert document_service_mock.update_document.call_count == 0


@pytest.mark.unit
@patch('src.backend.api.middleware.auth_middleware.get_current_user_id')
def test_delete_document(mock_get_current_user_id):
    """Test that users can delete their documents"""
    # Mock get_current_user_id to return USER_ID
    mock_get_current_user_id.return_value = USER_ID
    # Create DocumentService mock with delete_document method
    document_service_mock = pytest.helpers.Mock()
    document_id = generate_document_id()
    document_service_mock.delete_document.return_value = True
    # Create test client with mocked service
    test_client = setup_test_client(document_service_mock)
    # Send DELETE request to /api/documents/{document_id}
    response = test_client.delete(f'{TEST_PREFIX}/{document_id}')
    # Assert response status code is 204
    assert response.status_code == 204
    # Assert response body is empty
    assert response.data.decode('utf-8') == ''
    # Assert DocumentService.delete_document was called with correct document_id and user_id
    document_service_mock.delete_document.assert_called_once_with(document_id, USER_ID, None)


@pytest.mark.unit
@patch('src.backend.api.middleware.auth_middleware.get_current_user_id')
def test_list_documents(mock_get_current_user_id):
    """Test that users can list their documents with pagination"""
    # Mock get_current_user_id to return USER_ID
    mock_get_current_user_id.return_value = USER_ID
    # Create DocumentService mock with list_documents method
    document_service_mock = pytest.helpers.Mock()
    document_service_mock.list_documents.return_value = ([], 0)
    # Create test client with mocked service
    test_client = setup_test_client(document_service_mock)
    # Send GET request to /api/documents with pagination parameters
    response = test_client.get(f'{TEST_PREFIX}/?limit=10&skip=0')
    # Assert response status code is 200
    assert response.status_code == 200
    # Assert response contains items array and pagination metadata
    response_data = json.loads(response.data.decode('utf-8'))
    assert 'items' in response_data
    assert 'total' in response_data
    assert 'limit' in response_data
    assert 'skip' in response_data
    # Assert DocumentService.list_documents was called with correct arguments
    document_service_mock.list_documents.assert_called_once_with(USER_ID, None, filters={}, skip=0, limit=10)


@pytest.mark.unit
@patch('src.backend.api.middleware.auth_middleware.get_current_user_id')
def test_list_documents_with_filters(mock_get_current_user_id):
    """Test that users can list documents with filters like tags and search"""
    # Mock get_current_user_id to return USER_ID
    mock_get_current_user_id.return_value = USER_ID
    # Create DocumentService mock with list_documents method
    document_service_mock = pytest.helpers.Mock()
    document_service_mock.list_documents.return_value = ([], 0)
    # Create test client with mocked service
    test_client = setup_test_client(document_service_mock)
    # Send GET request to /api/documents with filter parameters
    response = test_client.get(f'{TEST_PREFIX}/?tags=tag1,tag2&search=keyword')
    # Assert response status code is 200
    assert response.status_code == 200
    # Prepare expected filters
    expected_filters = {'tags': 'tag1,tag2', 'search': 'keyword'}
    # Assert DocumentService.list_documents was called with correct filter arguments
    document_service_mock.list_documents.assert_called_once_with(USER_ID, None, filters=expected_filters, skip=0, limit=10)
    # Assert response contains only documents matching the filters
    response_data = json.loads(response.data.decode('utf-8'))
    assert 'items' in response_data


@pytest.mark.unit
@patch('src.backend.api.middleware.auth_middleware.get_current_user_id')
def test_get_document_versions(mock_get_current_user_id):
    """Test retrieving version history for a document"""
    # Mock get_current_user_id to return USER_ID
    mock_get_current_user_id.return_value = USER_ID
    # Create DocumentService mock with get_document_versions method
    document_service_mock = pytest.helpers.Mock()
    document_id = generate_document_id()
    document_service_mock.get_document_versions.return_value = ([], 0)
    # Create test client with mocked service
    test_client = setup_test_client(document_service_mock)
    # Send GET request to /api/documents/{document_id}/versions
    response = test_client.get(f'{TEST_PREFIX}/{document_id}/versions')
    # Assert response status code is 200
    assert response.status_code == 200
    # Assert response contains items array and pagination metadata
    response_data = json.loads(response.data.decode('utf-8'))
    assert 'items' in response_data
    assert 'total' in response_data
    assert 'limit' in response_data
    assert 'skip' in response_data
    # Assert DocumentService.get_document_versions was called with correct arguments
    document_service_mock.get_document_versions.assert_called_once_with(document_id, USER_ID, None, 10, 0)


@pytest.mark.unit
@patch('src.backend.api.middleware.auth_middleware.get_current_user_id')
def test_get_document_version(mock_get_current_user_id):
    """Test retrieving a specific version of a document"""
    # Mock get_current_user_id to return USER_ID
    mock_get_current_user_id.return_value = USER_ID
    # Create DocumentService mock with get_document_version method
    document_service_mock = pytest.helpers.Mock()
    document_id = generate_document_id()
    version_id = generate_version_id()
    document_service_mock.get_document_version.return_value = get_document_version_data(document_id=document_id, version_id=version_id)
    # Create test client with mocked service
    test_client = setup_test_client(document_service_mock)
    # Send GET request to /api/documents/{document_id}/versions/{version_id}
    response = test_client.get(f'{TEST_PREFIX}/{document_id}/versions/{version_id}')
    # Assert response status code is 200
    assert response.status_code == 200
    # Assert response contains version data including content
    response_data = json.loads(response.data.decode('utf-8'))
    assert response_data['id'] == version_id
    assert response_data['document_id'] == document_id
    assert 'content' in response_data
    # Assert DocumentService.get_document_version was called with correct arguments
    document_service_mock.get_document_version.assert_called_once_with(document_id, version_id, USER_ID, None)


@pytest.mark.unit
@patch('src.backend.api.middleware.auth_middleware.get_current_user_id')
def test_compare_document_versions(mock_get_current_user_id):
    """Test comparing two versions of a document"""
    # Mock get_current_user_id to return USER_ID
    mock_get_current_user_id.return_value = USER_ID
    # Create DocumentService mock with compare_document_versions method
    document_service_mock = pytest.helpers.Mock()
    document_id = generate_document_id()
    base_version_id = generate_version_id()
    comparison_version_id = generate_version_id()
    document_service_mock.compare_document_versions.return_value = {'diff': 'test diff'}
    # Create test client with mocked service
    test_client = setup_test_client(document_service_mock)
    # Prepare comparison request with base and comparison version IDs
    compare_data = {'base_version_id': base_version_id, 'comparison_version_id': comparison_version_id}
    # Send POST request to /api/documents/{document_id}/compare
    response = test_client.post(f'{TEST_PREFIX}/{document_id}/compare', json=compare_data)
    # Assert response status code is 200
    assert response.status_code == 200
    # Assert response contains difference data in requested format
    response_data = json.loads(response.data.decode('utf-8'))
    assert 'diff' in response_data
    # Assert DocumentService.compare_document_versions was called with correct arguments
    document_service_mock.compare_document_versions.assert_called_once_with(document_id, base_version_id, comparison_version_id, USER_ID, None, 'html')


@pytest.mark.unit
@patch('src.backend.api.middleware.auth_middleware.get_current_user_id')
def test_export_document(mock_get_current_user_id):
    """Test exporting a document to different formats"""
    # Mock get_current_user_id to return USER_ID
    mock_get_current_user_id.return_value = USER_ID
    # Create DocumentService mock with export_document method
    document_service_mock = pytest.helpers.Mock()
    document_id = generate_document_id()
    document_service_mock.export_document.return_value = {'content': 'exported content', 'format': 'text/plain'}
    # Create test client with mocked service
    test_client = setup_test_client(document_service_mock)
    # Prepare export request with format parameter
    export_data = {'format': 'txt'}
    # Send POST request to /api/documents/{document_id}/export
    response = test_client.post(f'{TEST_PREFIX}/{document_id}/export', json=export_data)
    # Assert response status code is 200
    assert response.status_code == 200
    # Assert response content type matches requested format
    assert response.content_type == 'text/plain'
    # Assert response contains exported content
    assert response.data.decode('utf-8') == 'exported content'
    # Assert DocumentService.export_document was called with correct arguments
    document_service_mock.export_document.assert_called_once_with(document_id, 'txt', USER_ID, None, {})


@pytest.mark.unit
@patch('src.backend.api.middleware.auth_middleware.get_current_user_id')
def test_import_document(mock_get_current_user_id):
    """Test importing a document from different formats"""
    # Mock get_current_user_id to return USER_ID
    mock_get_current_user_id.return_value = USER_ID
    # Create DocumentService mock with import_document method
    document_service_mock = pytest.helpers.Mock()
    document_service_mock.import_document.return_value = get_document_data(document_id=generate_document_id())
    # Create test client with mocked service
    test_client = setup_test_client(document_service_mock)
    # Prepare import request with content, format, and title
    import_data = {'content': 'import content', 'format': 'txt', 'title': 'Imported Title'}
    # Send POST request to /api/documents/import
    response = test_client.post(f'{TEST_PREFIX}/import', json=import_data)
    # Assert response status code is 201
    assert response.status_code == 201
    # Assert response contains document ID and metadata
    response_data = json.loads(response.data.decode('utf-8'))
    assert 'id' in response_data
    assert response_data['title'] == 'Imported Title'
    # Assert Location header contains document URL
    assert f'/documents/{response_data["id"]}' in response.headers['Location']
    # Assert DocumentService.import_document was called with correct arguments
    document_service_mock.import_document.assert_called_once_with('import content', 'txt', 'Imported Title', USER_ID, None)