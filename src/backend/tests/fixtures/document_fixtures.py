"""
Provides pytest fixtures for generating standardized document data to be used in tests
for the AI writing enhancement platform.

This module contains fixtures for documents in various states including basic documents,
user-owned documents, anonymous documents, documents with version history, and documents
with AI suggestions. These fixtures ensure consistent test data across the test suite.

Available fixtures:
- basic_document: Minimal document data
- user_document: Document owned by a specific user
- anonymous_document: Document associated with an anonymous session
- document_with_tags: Document with categorization tags
- archived_document: Document marked as archived
- document_with_versions: Document with version history
- document_with_suggestions: Document with AI improvement suggestions
- document_version: Single document version data
- ai_suggestion: Single AI suggestion data
- document_list: List of multiple documents for pagination tests
- large_document: Document with large content for performance testing
"""

import pytest
from datetime import datetime, timedelta
from bson import ObjectId  # pymongo ~=4.3.0
import uuid

from .user_fixtures import generate_user_id, generate_session_id

# Default values for document data
DEFAULT_DOCUMENT_TITLE = "Sample Document"
DEFAULT_DOCUMENT_CONTENT = "This is a sample document content for testing purposes. It contains multiple sentences to simulate a realistic document that would be processed by the AI writing enhancement system."
DEFAULT_VERSION_CONTENT = "This is a sample document version content. It represents a specific version of the document that can be used for testing the track changes and versioning system."
DOCUMENT_WITH_SUGGESTIONS_CONTENT = "This document contains content that will be analyzed by the AI system. The system will suggest improvements to enhance the writing quality, fix grammatical errors, and improve the overall structure."

# Sample IDs for testing
SAMPLE_USER_ID = "user123"
SAMPLE_SESSION_ID = "session456"


def generate_document_id():
    """Generate a unique document ID in the format of MongoDB ObjectID."""
    return str(ObjectId())


def generate_version_id():
    """Generate a unique version ID for document versions."""
    return str(ObjectId())


def get_document_data(title=None, content=None, description=None, document_id=None,
                     user_id=None, session_id=None, tags=None, is_archived=None,
                     current_version_id=None):
    """
    Creates a document data dictionary with customizable fields.
    
    Args:
        title (str): Document title
        content (str): Document content
        description (str): Document description
        document_id (str): Document ID
        user_id (str): User ID for document ownership
        session_id (str): Session ID for anonymous documents
        tags (list): List of tags for document categorization
        is_archived (bool): Whether the document is archived
        current_version_id (str): ID of the current document version
        
    Returns:
        dict: Document data dictionary with all necessary fields
    """
    now = datetime.utcnow()
    
    document = {
        "_id": document_id or generate_document_id(),
        "title": title or DEFAULT_DOCUMENT_TITLE,
        "content": content or DEFAULT_DOCUMENT_CONTENT,
        "description": description,
        "userId": user_id,
        "sessionId": session_id,
        "tags": tags or [],
        "isArchived": is_archived if is_archived is not None else False,
        "createdAt": now,
        "updatedAt": now,
        "lastAccessedAt": now,
        "currentVersionId": current_version_id
    }
    
    return document


def get_document_version_data(document_id, version_id=None, version_number=None, 
                             content=None, created_by=None, version_type=None,
                             change_description=None, previous_version_id=None,
                             metadata=None):
    """
    Creates a document version data dictionary with customizable fields.
    
    Args:
        document_id (str): ID of the parent document
        version_id (str): Version ID
        version_number (int): Version number (incremental)
        content (str): Version content
        created_by (str): User ID of version creator
        version_type (int): Version type (0=MAJOR, 1=MINOR, 2=AUTO_SAVE)
        change_description (str): Description of changes in this version
        previous_version_id (str): ID of previous version
        metadata (dict): Additional metadata for the version
        
    Returns:
        dict: Document version data dictionary
    """
    version = {
        "_id": version_id or generate_version_id(),
        "documentId": document_id,
        "versionNumber": version_number or 1,
        "content": content or DEFAULT_VERSION_CONTENT,
        "createdAt": datetime.utcnow(),
        "createdBy": created_by,
        "versionType": version_type or 0,  # Default to MAJOR version
        "changeDescription": change_description,
        "previousVersionId": previous_version_id,
        "metadata": metadata or {}
    }
    
    return version


def get_ai_suggestion_data(document_id, suggestion_id=None, original_text=None, 
                          suggested_text=None, prompt_type=None, start_position=None,
                          end_position=None, explanation=None, is_accepted=None,
                          is_rejected=None):
    """
    Creates an AI suggestion data dictionary with customizable fields.
    
    Args:
        document_id (str): ID of the parent document
        suggestion_id (str): Suggestion ID
        original_text (str): Original text to be replaced
        suggested_text (str): Suggested replacement text
        prompt_type (str): Type of improvement prompt used
        start_position (int): Start position in document
        end_position (int): End position in document
        explanation (str): Explanation for the suggestion
        is_accepted (bool): Whether suggestion is accepted
        is_rejected (bool): Whether suggestion is rejected
        
    Returns:
        dict: AI suggestion data dictionary
    """
    original_text = original_text or "original sample text"
    suggested_text = suggested_text or "improved sample text"
    
    suggestion = {
        "_id": suggestion_id or str(uuid.uuid4()),
        "documentId": document_id,
        "originalText": original_text,
        "suggestedText": suggested_text,
        "promptType": prompt_type or "improve_grammar",
        "startPosition": start_position or 0,
        "endPosition": end_position or len(original_text),
        "explanation": explanation,
        "isAccepted": is_accepted if is_accepted is not None else False,
        "isRejected": is_rejected if is_rejected is not None else False,
        "createdAt": datetime.utcnow()
    }
    
    return suggestion


def create_document_with_versions(version_count=3, user_id=None):
    """
    Creates a document with multiple versions.
    
    Args:
        version_count (int): Number of versions to create
        user_id (str): User ID for document ownership
        
    Returns:
        dict: Document data with version history
    """
    document_id = generate_document_id()
    versions = []
    previous_version_id = None
    
    for i in range(1, version_count + 1):
        version_id = generate_version_id()
        version = get_document_version_data(
            document_id=document_id,
            version_id=version_id,
            version_number=i,
            content=f"Version {i} content. {DEFAULT_VERSION_CONTENT}",
            created_by=user_id,
            previous_version_id=previous_version_id,
            change_description=f"Changes for version {i}"
        )
        versions.append(version)
        previous_version_id = version_id
    
    # Set the latest version as current
    current_version_id = versions[-1]["_id"] if versions else None
    
    document = get_document_data(
        document_id=document_id,
        user_id=user_id,
        current_version_id=current_version_id,
        content=versions[-1]["content"] if versions else DEFAULT_DOCUMENT_CONTENT
    )
    
    document["versions"] = versions
    return document


def create_document_with_suggestions(suggestion_count=3, user_id=None):
    """
    Creates a document with multiple AI suggestions.
    
    Args:
        suggestion_count (int): Number of suggestions to create
        user_id (str): User ID for document ownership
        
    Returns:
        dict: Document data with AI suggestions
    """
    document_id = generate_document_id()
    suggestions = []
    
    # Sample suggestion data - in real tests this would be more varied
    suggestion_samples = [
        {"original": "will analyze", "suggested": "analyzes", "prompt": "make_concise", "pos": 15},
        {"original": "fix grammatical errors", "suggested": "correct grammar", "prompt": "improve_style", "pos": 80},
        {"original": "improve the overall", "suggested": "enhance the", "prompt": "make_professional", "pos": 110},
        {"original": "system will suggest", "suggested": "system suggests", "prompt": "make_concise", "pos": 45}
    ]
    
    for i in range(min(suggestion_count, len(suggestion_samples))):
        sample = suggestion_samples[i]
        suggestion = get_ai_suggestion_data(
            document_id=document_id,
            original_text=sample["original"],
            suggested_text=sample["suggested"],
            prompt_type=sample["prompt"],
            start_position=sample["pos"],
            end_position=sample["pos"] + len(sample["original"]),
            explanation=f"This suggestion improves the {sample['prompt'].replace('_', ' ')}"
        )
        suggestions.append(suggestion)
    
    document = get_document_data(
        document_id=document_id,
        user_id=user_id,
        content=DOCUMENT_WITH_SUGGESTIONS_CONTENT
    )
    
    document["suggestions"] = suggestions
    return document


@pytest.fixture
def basic_document():
    """Fixture providing basic document data with minimal fields."""
    return get_document_data()


@pytest.fixture
def user_document():
    """Fixture providing document data owned by a user."""
    return get_document_data(user_id=SAMPLE_USER_ID)


@pytest.fixture
def anonymous_document():
    """Fixture providing document data associated with an anonymous session."""
    return get_document_data(session_id=SAMPLE_SESSION_ID)


@pytest.fixture
def document_with_tags():
    """Fixture providing document data with tags."""
    return get_document_data(tags=["business", "report", "draft"])


@pytest.fixture
def archived_document():
    """Fixture providing archived document data."""
    return get_document_data(is_archived=True)


@pytest.fixture
def document_with_versions():
    """Fixture providing document data with version history."""
    return create_document_with_versions()


@pytest.fixture
def document_with_suggestions():
    """Fixture providing document data with AI suggestions."""
    return create_document_with_suggestions()


@pytest.fixture
def document_version():
    """Fixture providing a single document version."""
    document_id = generate_document_id()
    return get_document_version_data(document_id=document_id)


@pytest.fixture
def ai_suggestion():
    """Fixture providing a single AI suggestion."""
    document_id = generate_document_id()
    return get_ai_suggestion_data(document_id=document_id)


@pytest.fixture
def document_list():
    """Fixture providing a list of multiple documents for pagination tests."""
    documents = []
    for i in range(10):
        is_even = i % 2 == 0
        document = get_document_data(
            title=f"Document {i}",
            user_id=SAMPLE_USER_ID if is_even else None,  
            session_id=None if is_even else f"session_{i}",
            tags=[f"tag{i}"] if i > 5 else [],
            is_archived=i >= 8
        )
        # Adjust the timestamps to create a time sequence
        created_date = datetime.utcnow() - timedelta(days=i)
        document["createdAt"] = created_date
        document["updatedAt"] = created_date + timedelta(hours=i)
        documents.append(document)
    return documents


@pytest.fixture
def large_document():
    """Fixture providing a document with large content for performance tests."""
    # Create content with ~5000 words for performance testing
    large_content = " ".join(["The quick brown fox jumps over the lazy dog."] * 500)
    return get_document_data(content=large_content)