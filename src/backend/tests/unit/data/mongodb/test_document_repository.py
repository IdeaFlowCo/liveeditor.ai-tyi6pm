import pytest  # pytest==7.x
from unittest.mock import MagicMock  # unittest.mock - part of standard library
from bson import ObjectId  # bson - part of pymongo

# Assuming pymongo is used, but using mongomock for testing
import mongomock  # mongomock==4.x

from src.backend.data.mongodb.repositories.document_repository import DocumentRepository  # src/backend/data/mongodb/repositories/document_repository.py
from src.backend.tests.fixtures.document_fixtures import sample_document, sample_documents  # src/backend/tests/fixtures/document_fixtures.py
from src.backend.tests.conftest import mongodb_connection  # src/backend/tests/conftest.py

@pytest.mark.unit
def test_document_repository_init():
    """Tests the initialization of the DocumentRepository class"""
    # Create a mock MongoDB client
    mock_client = MagicMock()

    # Initialize DocumentRepository with the mock client
    repo = DocumentRepository()
    repo._collection = mock_client  # Directly assign the mock

    # Assert that the repository has the correct database and collection
    assert repo._collection == mock_client

@pytest.mark.unit
def test_find_by_id(sample_document):
    """Tests the find_by_id method of DocumentRepository"""
    # Create a mock MongoDB client
    mock_client = MagicMock()

    # Set up the mock to return a specific document when find_one is called
    mock_client.find_one.return_value = sample_document

    # Initialize DocumentRepository with the mock client
    repo = DocumentRepository()
    repo._collection = mock_client  # Directly assign the mock

    # Call find_by_id with a test document ID
    document_id = "some_document_id"
    document = repo.get_by_id(document_id)

    # Assert that the returned document matches the expected document
    assert document == sample_document

@pytest.mark.unit
def test_find_by_id_not_found():
    """Tests the find_by_id method when document is not found"""
    # Create a mock MongoDB client
    mock_client = MagicMock()

    # Set up the mock to return None when find_one is called
    mock_client.find_one.return_value = None

    # Initialize DocumentRepository with the mock client
    repo = DocumentRepository()
    repo._collection = mock_client  # Directly assign the mock

    # Call find_by_id with a test document ID
    document_id = "non_existent_document_id"
    document = repo.get_by_id(document_id)

    # Assert that None is returned
    assert document is None

@pytest.mark.unit
def test_find_by_user_id(sample_documents):
    """Tests the find_by_user_id method of DocumentRepository"""
    # Create a mock MongoDB client
    mock_client = MagicMock()

    # Set up the mock to return a list of documents when find is called
    mock_client.find.return_value = sample_documents

    # Initialize DocumentRepository with the mock client
    repo = DocumentRepository()
    repo._collection = mock_client  # Directly assign the mock

    # Call find_by_user_id with a test user ID
    user_id = "test_user_id"
    documents, _ = repo.find_by_user(user_id)

    # Assert that the returned documents match the expected documents
    assert documents == sample_documents

@pytest.mark.unit
def test_create():
    """Tests the create method of DocumentRepository"""
    # Create a mock MongoDB client
    mock_client = MagicMock()

    # Set up the mock to return an insert result with a generated ID
    mock_insert_result = MagicMock()
    mock_insert_result.inserted_id = ObjectId()
    mock_client.insert_one.return_value = mock_insert_result

    # Initialize DocumentRepository with the mock client
    repo = DocumentRepository()
    repo._collection = mock_client  # Directly assign the mock

    # Call create with a test document
    document_data = {"title": "Test Document", "content": "Test Content"}
    document = repo.create(document_data, user_id="test_user_id")

    # Assert that the insert_one method was called with the correct document
    mock_client.insert_one.assert_called_once()
    call_args = mock_client.insert_one.call_args
    assert call_args is not None
    args, kwargs = call_args
    assert len(args) == 1
    inserted_document = args[0]
    assert inserted_document["title"] == "Test Document"
    assert inserted_document["content"] == "Test Content"
    assert inserted_document["userId"] == "test_user_id"

    # Assert that the returned document has the correct ID
    assert document["_id"] == str(mock_insert_result.inserted_id)

@pytest.mark.unit
def test_update():
    """Tests the update method of DocumentRepository"""
    # Create a mock MongoDB client
    mock_client = MagicMock()

    # Set up the mock to return an update result indicating success
    mock_update_result = MagicMock()
    mock_update_result.modified_count = 1
    mock_client.update_one.return_value = mock_update_result

    # Initialize DocumentRepository with the mock client
    repo = DocumentRepository()
    repo._collection = mock_client  # Directly assign the mock

    # Call update with a test document ID and updated data
    document_id = "test_document_id"
    update_data = {"title": "Updated Title", "content": "Updated Content"}
    success = repo.update(document_id, update_data)

    # Assert that the update_one method was called with the correct document ID and update data
    mock_client.update_one.assert_called_once()
    call_args = mock_client.update_one.call_args
    assert call_args is not None
    args, kwargs = call_args
    assert len(args) == 2
    query, update = args
    assert query["_id"] == document_id
    assert "$set" in update
    assert update["$set"]["title"] == "Updated Title"
    assert update["$set"]["content"] == "Updated Content"

    # Assert that the method returns True indicating success
    assert success is True

@pytest.mark.unit
def test_update_failure():
    """Tests the update method when the update fails"""
    # Create a mock MongoDB client
    mock_client = MagicMock()

    # Set up the mock to return an update result indicating failure
    mock_update_result = MagicMock()
    mock_update_result.modified_count = 0
    mock_client.update_one.return_value = mock_update_result

    # Initialize DocumentRepository with the mock client
    repo = DocumentRepository()
    repo._collection = mock_client  # Directly assign the mock

    # Call update with a test document ID and updated data
    document_id = "test_document_id"
    update_data = {"title": "Updated Title", "content": "Updated Content"}
    success = repo.update(document_id, update_data)

    # Assert that the method returns False indicating failure
    assert success is False

@pytest.mark.unit
def test_delete():
    """Tests the delete method of DocumentRepository"""
    # Create a mock MongoDB client
    mock_client = MagicMock()

    # Set up the mock to return a delete result indicating success
    mock_delete_result = MagicMock()
    mock_delete_result.deleted_count = 1
    mock_client.delete_one.return_value = mock_delete_result

    # Initialize DocumentRepository with the mock client
    repo = DocumentRepository()
    repo._collection = mock_client  # Directly assign the mock

    # Call delete with a test document ID
    document_id = "test_document_id"
    success = repo.delete(document_id)

    # Assert that the delete_one method was called with the correct document ID
    mock_client.delete_one.assert_called_once_with({"_id": document_id})

    # Assert that the method returns True indicating success
    assert success is True

@pytest.mark.unit
def test_delete_failure():
    """Tests the delete method when the delete fails"""
    # Create a mock MongoDB client
    mock_client = MagicMock()

    # Set up the mock to return a delete result indicating failure
    mock_delete_result = MagicMock()
    mock_delete_result.deleted_count = 0
    mock_client.delete_one.return_value = mock_delete_result

    # Initialize DocumentRepository with the mock client
    repo = DocumentRepository()
    repo._collection = mock_client  # Directly assign the mock

    # Call delete with a test document ID
    document_id = "test_document_id"
    success = repo.delete(document_id)

    # Assert that the method returns False indicating failure
    assert success is False

@pytest.mark.unit
def test_find_all():
    """Tests the find_all method of DocumentRepository"""
    # Create a mock MongoDB client
    mock_client = MagicMock()

    # Set up the mock to return a list of all documents when find is called
    mock_client.find.return_value = []

    # Initialize DocumentRepository with the mock client
    repo = DocumentRepository()
    repo._collection = mock_client  # Directly assign the mock

    # Call find_all
    documents, _ = repo.find_all()

    # Assert that the returned documents match the expected documents
    assert documents == []