"""
Central pytest configuration file for the AI writing enhancement platform's backend tests.
Defines fixtures, mocks, and test setup functions that are available across all test modules.
Provides test database initialization, application instance creation, and mock services for unit and integration testing.
"""
# pytest==^7.0.0 - Core testing framework
import pytest
# mongomock==^4.1.0 - Mock MongoDB client for unit tests
import mongomock
# unittest.mock - Standard library mocking tools
import unittest.mock
# fakeredis==^2.0.0 - Mock Redis client for unit tests
import fakeredis
# flask==^2.3.0 - Web framework for testing API endpoints
import flask
# botocore.stub==^1.31.0 - AWS service mocking for S3 storage tests
import botocore.stub
import os

from .fixtures.user_fixtures import regular_user_data, verified_user_data, admin_user_data, anonymous_user_data, user_with_reset_token, user_with_preferences, user_list
from .fixtures.document_fixtures import basic_document, user_document, document_with_suggestions, document_with_tags, archived_document, document_with_versions, document_version, ai_suggestion, document_list, large_document
from src.backend.api import create_app
from src.backend.data.mongodb.connection import reset_db_for_testing, get_database, get_collection

TEST_CONFIG = {"TESTING": True, "MONGODB_URI": "mongodb://localhost:27017/test_ai_writing", "REDIS_URI": "redis://localhost:6379/1", "S3_BUCKET": "test-ai-writing-bucket", "OPENAI_API_KEY": "test-api-key-not-real"}

@pytest.fixture(scope='session')
def setup_test_db():
    """Fixture that sets up and tears down test database with scope session"""
    # Setup: Reset the test database
    reset_db_for_testing()
    yield  # Provide the setup
    # Teardown: Reset the test database after all tests in the session are finished
    reset_db_for_testing()

@pytest.fixture
def setup_test_user(setup_test_db, regular_user_data):
    """Fixture that creates a test user in the database"""
    db = get_database()
    users_collection = get_collection('users')
    user = regular_user_data
    users_collection.insert_one(user)
    yield user
    users_collection.delete_one({'_id': user['_id']})

@pytest.fixture
def setup_test_document(setup_test_user, user_document):
    """Fixture that creates a test document in the database"""
    db = get_database()
    documents_collection = get_collection('documents')
    document = user_document
    documents_collection.insert_one(document)
    yield document
    documents_collection.delete_one({'_id': document['_id']})

@pytest.fixture
def setup_test_template(setup_test_db):
    """Fixture that creates test AI templates in the database"""
    db = get_database()
    templates_collection = get_collection('templates')
    template_data = {
        "name": "Test Template",
        "description": "A test template for pytest",
        "promptText": "Make the text shorter",
        "category": "length",
        "isSystem": True
    }
    templates_collection.insert_one(template_data)
    yield template_data
    templates_collection.delete_one({'name': template_data['name']})

@pytest.fixture
def app():
    """Fixture providing a configured Flask test client instance"""
    # Configure the Flask app for testing
    test_app = create_app(TEST_CONFIG)
    # Create a test client using Flask's test_client
    with test_app.test_client() as test_client:
        # Establish an application context
        with test_app.app_context():
            # Yield the test client for use in tests
            yield test_client

@pytest.fixture
def client(app):
    """Fixture providing a Flask test client for making requests"""
    # Return the test client for making requests
    return app

@pytest.fixture
def db():
    """Fixture providing a test database instance"""
    # Get the test database instance
    test_db = get_database()
    # Return the test database instance
    return test_db

@pytest.fixture
def mock_mongodb():
    """Fixture providing a mongomock instance for unit tests"""
    # Create a mock MongoDB client using mongomock
    mock_client = mongomock.MongoClient()
    # Return the mock client
    return mock_client

@pytest.fixture
def mock_redis():
    """Fixture providing a fakeredis instance for unit tests"""
    # Create a mock Redis client using fakeredis
    mock_server = fakeredis.FakeServer()
    mock_client = fakeredis.FakeRedis(server=mock_server)
    # Return the mock client
    return mock_client

@pytest.fixture
def mock_s3():
    """Fixture providing a mocked S3 client for unit tests"""
    # Create a mock S3 client using botocore.stub
    s3_stub = botocore.stub.Stubber(boto3.client('s3', region_name='us-east-1'))
    # Return the mock S3 client
    return s3_stub

@pytest.fixture
def mock_openai_service():
    """Fixture providing a mocked OpenAI service for AI tests"""
    # Create a mock OpenAI service using unittest.mock
    mock_service = unittest.mock.Mock()
    # Return the mock service
    return mock_service

@pytest.fixture
def auth_header(setup_test_user):
    """Fixture providing authentication headers for API tests"""
    # Generate a test token for the test user
    test_token = "test_auth_token"
    # Return the authentication header with the test token
    return {"Authorization": f"Bearer {test_token}"}

def pytest_configure(config):
    """Pytest hook that runs at the start of the test session to set up the environment"""
    # Set environment variables for testing mode
    os.environ['FLASK_ENV'] = 'testing'
    # Configure pytest markers for categorizing tests
    config.addinivalue_line("markers", "slow: mark test as slow to run")
    config.addinivalue_line("markers", "database: mark test as requiring a database")
    # Register additional hooks if needed
    # Setup logging for test execution
    print("Pytest is configuring the test environment...")

def pytest_collection_modifyitems(config, items):
    """Pytest hook that modifies the collected test items for better organization"""
    # Add 'slow' mark to tests with known long execution time
    for item in items:
        if "test_slow" in item.name:
            item.add_marker(pytest.mark.slow)
    # Add database markers based on test module path
        if "database" in str(item.fspath):
            item.add_marker(pytest.mark.database)
    # Skip certain tests in CI environment if needed
        if config.getoption("-m") == "skip_ci" and item.get_closest_marker("ci"):
            item.skip = True
    print("Pytest is modifying the collected test items...")