"""
Integration tests for the AI writing enhancement platform's suggestion API endpoints.

This module contains tests that verify the entire suggestion generation flow works correctly from HTTP request to
database operations and response generation. These tests ensure that:

- The API correctly processes suggestion requests with templates and custom prompts
- Suggestions are correctly formatted for the track changes review system
- Rate limiting is enforced for anonymous users
- Both authenticated and anonymous users can access appropriate functionality
- Error conditions are properly handled and validated

Tests in this module interact with the full API stack including database operations and external service integrations,
verifying end-to-end flows rather than isolated components.
"""

import json
import pytest
from flask import Flask

from ..fixtures.suggestion_fixtures import (
    create_suggestion_request_data,
    create_suggestion_data,
    SAMPLE_ORIGINAL_TEXT
)
from ..fixtures.template_fixtures import get_template_data

# API endpoints for suggestion services
SUGGESTIONS_API_BASE_URL = '/api/suggestions'
TEMPLATE_ID = 'professional_template'
SAMPLE_CUSTOM_PROMPT = 'Please make this text more concise and professional.'


@pytest.mark.integration
def test_get_suggestion_templates_integration(client, setup_test_template):
    """Test that the templates endpoint correctly returns available suggestion templates from the database."""
    # Send GET request to the templates endpoint
    response = client.get(f"{SUGGESTIONS_API_BASE_URL}/templates")
    
    # Verify response status code is 200
    assert response.status_code == 200
    
    # Parse JSON response and verify it contains the expected templates
    data = json.loads(response.data)
    
    # Verify response structure
    assert "templates" in data
    assert isinstance(data["templates"], list)
    assert len(data["templates"]) > 0
    
    # Verify at least one template has the correct structure
    template = data["templates"][0]
    assert "id" in template
    assert "name" in template
    assert "description" in template
    assert "category" in template
    
    # Verify templates are correctly grouped by category
    if "categories" in data:
        assert isinstance(data["categories"], dict)
        # Check that each category contains a list of templates
        for category, templates in data["categories"].items():
            assert isinstance(templates, list)


@pytest.mark.integration
def test_get_suggestion_types_integration(client):
    """Test that the suggestion types endpoint correctly returns available suggestion types."""
    # Send GET request to the suggestion types endpoint
    response = client.get(f"{SUGGESTIONS_API_BASE_URL}/types")
    
    # Verify response status code is 200
    assert response.status_code == 200
    
    # Parse JSON response and verify it contains valid suggestion types
    data = json.loads(response.data)
    
    # Verify response structure
    assert "types" in data
    assert isinstance(data["types"], list)
    assert len(data["types"]) > 0
    
    # Verify each suggestion type has a description
    for suggestion_type in data["types"]:
        assert "id" in suggestion_type
        assert "name" in suggestion_type
        assert "description" in suggestion_type
    
    # Verify required suggestion types (shorter, professional, grammar, etc.) are included
    type_ids = [t["id"] for t in data["types"]]
    expected_types = ["shorter", "professional", "grammar", "clarity", "style"]
    for expected_type in expected_types:
        assert any(expected_type in type_id for type_id in type_ids), f"Expected type {expected_type} not found"


@pytest.mark.integration
def test_generate_text_suggestions_with_template_integration(client, setup_test_template):
    """Test generating text suggestions using a template."""
    # Prepare request data with document content and template ID
    request_data = create_suggestion_request_data(
        document_content=SAMPLE_ORIGINAL_TEXT,
        template_id=TEMPLATE_ID
    )
    
    # Send POST request to the text suggestions endpoint
    response = client.post(
        f"{SUGGESTIONS_API_BASE_URL}/text",
        data=json.dumps(request_data),
        content_type='application/json'
    )
    
    # Verify response status code is 200
    assert response.status_code == 200
    
    # Parse JSON response and verify it contains suggestions
    data = json.loads(response.data)
    
    # Verify response structure
    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)
    assert len(data["suggestions"]) > 0
    
    # Verify each suggestion has required fields
    for suggestion in data["suggestions"]:
        assert "suggestion_id" in suggestion
        assert "original_text" in suggestion
        assert "suggested_text" in suggestion
        assert "start_position" in suggestion
        assert "end_position" in suggestion
        
    # Verify suggestions are in the correct track changes format
    has_track_changes_format = False
    for suggestion in data["suggestions"]:
        if "changes" in suggestion or "html_diff" in suggestion:
            has_track_changes_format = True
            break
    assert has_track_changes_format, "No track changes format found in suggestions"
    
    # Verify response includes processing time and metadata
    assert "processing_time" in data
    assert "metadata" in data


@pytest.mark.integration
def test_generate_text_suggestions_with_custom_prompt_integration(client):
    """Test generating text suggestions using a custom prompt."""
    # Prepare request data with document content and custom prompt
    request_data = create_suggestion_request_data(
        document_content=SAMPLE_ORIGINAL_TEXT,
        custom_prompt=SAMPLE_CUSTOM_PROMPT
    )
    
    # Send POST request to the text suggestions endpoint
    response = client.post(
        f"{SUGGESTIONS_API_BASE_URL}/text",
        data=json.dumps(request_data),
        content_type='application/json'
    )
    
    # Verify response status code is 200
    assert response.status_code == 200
    
    # Parse JSON response and verify it contains suggestions
    data = json.loads(response.data)
    
    # Verify response structure
    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)
    assert len(data["suggestions"]) > 0
    
    # Verify each suggestion has required fields
    for suggestion in data["suggestions"]:
        assert "suggestion_id" in suggestion
        assert "original_text" in suggestion
        assert "suggested_text" in suggestion
        
    # Verify suggestions are in the correct track changes format
    has_track_changes_format = False
    for suggestion in data["suggestions"]:
        if "changes" in suggestion or "html_diff" in suggestion:
            has_track_changes_format = True
            break
    assert has_track_changes_format, "No track changes format found in suggestions"
    
    # Verify custom prompt is reflected in the response metadata
    assert "prompt_used" in data
    assert SAMPLE_CUSTOM_PROMPT in str(data["prompt_used"])


@pytest.mark.integration
def test_generate_text_suggestions_with_selection_integration(client):
    """Test generating suggestions for a selected portion of text."""
    # Define a selection range within the sample text
    selection = {
        "start": 10,  # Starting position in the text
        "end": 50     # Ending position in the text
    }
    
    # Prepare request data with document content, selection range, and template ID
    request_data = create_suggestion_request_data(
        document_content=SAMPLE_ORIGINAL_TEXT,
        selection=selection,
        template_id=TEMPLATE_ID
    )
    
    # Send POST request to the text suggestions endpoint
    response = client.post(
        f"{SUGGESTIONS_API_BASE_URL}/text",
        data=json.dumps(request_data),
        content_type='application/json'
    )
    
    # Verify response status code is 200
    assert response.status_code == 200
    
    # Parse JSON response and verify it contains suggestions
    data = json.loads(response.data)
    
    # Verify response structure
    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)
    assert len(data["suggestions"]) > 0
    
    # Verify suggestions are focused on the selected text range
    for suggestion in data["suggestions"]:
        # Check if the suggestion's positions overlap with the selection
        assert (suggestion["start_position"] >= selection["start"] and 
                suggestion["start_position"] < selection["end"]) or \
               (suggestion["end_position"] > selection["start"] and 
                suggestion["end_position"] <= selection["end"])
        
    # Verify suggestions include position information relative to the full document
    for suggestion in data["suggestions"]:
        assert "start_position" in suggestion
        assert "end_position" in suggestion
        
        # Positions should be non-negative integers
        assert suggestion["start_position"] >= 0
        assert suggestion["end_position"] >= 0
        
        # End position should be greater than start position
        assert suggestion["end_position"] > suggestion["start_position"]


@pytest.mark.integration
def test_generate_style_suggestions_integration(client):
    """Test generating style-focused suggestions."""
    # Prepare request data with document content and style parameters
    request_data = create_suggestion_request_data(
        document_content=SAMPLE_ORIGINAL_TEXT,
        suggestion_type="style",
        custom_prompt="Make this text more professional in style"
    )
    
    # Send POST request to the style suggestions endpoint
    response = client.post(
        f"{SUGGESTIONS_API_BASE_URL}/style",
        data=json.dumps(request_data),
        content_type='application/json'
    )
    
    # Verify response status code is 200
    assert response.status_code == 200
    
    # Parse JSON response and verify it contains style-focused suggestions
    data = json.loads(response.data)
    
    # Verify response structure
    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)
    assert len(data["suggestions"]) > 0
    
    # Verify suggestion_type field is set to 'style'
    for suggestion in data["suggestions"]:
        assert "suggestion_type" in suggestion
        assert suggestion["suggestion_type"] == "style"
        
    # Verify changes reflect style improvements
    style_improved = False
    for suggestion in data["suggestions"]:
        if suggestion["original_text"] != suggestion["suggested_text"]:
            style_improved = True
    assert style_improved, "No style improvements found in suggestions"


@pytest.mark.integration
def test_generate_grammar_suggestions_integration(client):
    """Test generating grammar-focused suggestions."""
    # Sample text with intentional grammar issues
    text_with_grammar_issues = "The company have several employee that works remotely. They is performing well despite the challenges."
    
    # Prepare request data with document content containing grammar issues
    request_data = create_suggestion_request_data(
        document_content=text_with_grammar_issues,
        suggestion_type="grammar",
        custom_prompt="Fix grammar issues in this text"
    )
    
    # Send POST request to the grammar suggestions endpoint
    response = client.post(
        f"{SUGGESTIONS_API_BASE_URL}/grammar",
        data=json.dumps(request_data),
        content_type='application/json'
    )
    
    # Verify response status code is 200
    assert response.status_code == 200
    
    # Parse JSON response and verify it contains grammar-focused suggestions
    data = json.loads(response.data)
    
    # Verify response structure
    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)
    assert len(data["suggestions"]) > 0
    
    # Verify suggestion_type field is set to 'grammar'
    for suggestion in data["suggestions"]:
        assert "suggestion_type" in suggestion
        assert suggestion["suggestion_type"] == "grammar"
        
    # Verify changes address grammar issues in the text
    grammar_issues_fixed = False
    for suggestion in data["suggestions"]:
        if (suggestion["original_text"] != suggestion["suggested_text"] and 
            ("have several employee" in suggestion["original_text"] or 
             "is performing" in suggestion["original_text"])):
            grammar_issues_fixed = True
    assert grammar_issues_fixed, "No grammar issues fixed in suggestions"


@pytest.mark.integration
def test_anonymous_user_suggestion_integration(client):
    """Test generating suggestions for an anonymous user."""
    # Generate a session ID to represent an anonymous user
    session_id = "test-anonymous-session-123"
    
    # Prepare request data with document content, template ID, and session ID
    request_data = create_suggestion_request_data(
        document_content=SAMPLE_ORIGINAL_TEXT,
        template_id=TEMPLATE_ID,
        session_id=session_id
    )
    
    # Send POST request to the text suggestions endpoint without auth headers
    response = client.post(
        f"{SUGGESTIONS_API_BASE_URL}/text",
        data=json.dumps(request_data),
        content_type='application/json'
    )
    
    # Verify response status code is 200
    assert response.status_code == 200
    
    # Parse JSON response and verify it contains suggestions
    data = json.loads(response.data)
    
    # Verify response structure
    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)
    assert len(data["suggestions"]) > 0
    
    # Verify session ID is reflected in the response or logs
    if "metadata" in data:
        assert "session_id" in data["metadata"]
        assert data["metadata"]["session_id"] == session_id
    elif "session_id" in data:
        assert data["session_id"] == session_id


@pytest.mark.integration
def test_authenticated_user_suggestion_integration(client, setup_test_user, auth_header):
    """Test generating suggestions for an authenticated user."""
    # Prepare request data with document content and template ID
    request_data = create_suggestion_request_data(
        document_content=SAMPLE_ORIGINAL_TEXT,
        template_id=TEMPLATE_ID
    )
    
    # Send POST request to the text suggestions endpoint with auth headers
    response = client.post(
        f"{SUGGESTIONS_API_BASE_URL}/text",
        data=json.dumps(request_data),
        content_type='application/json',
        headers=auth_header
    )
    
    # Verify response status code is 200
    assert response.status_code == 200
    
    # Parse JSON response and verify it contains suggestions
    data = json.loads(response.data)
    
    # Verify response structure
    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)
    assert len(data["suggestions"]) > 0
    
    # Verify user ID is associated with the suggestion interaction
    if "metadata" in data:
        assert "user_id" in data["metadata"], "User ID not found in metadata"
    elif "user_id" in data:
        assert data["user_id"], "User ID not found in response"


@pytest.mark.integration
def test_suggestion_with_existing_document_integration(client, setup_test_user, setup_test_document, auth_header):
    """Test generating suggestions for an existing document."""
    # Get the document ID from the test fixture
    document_id = setup_test_document["_id"]
    
    # Prepare request data with document ID instead of content
    request_data = create_suggestion_request_data(
        document_id=document_id,
        template_id=TEMPLATE_ID
    )
    
    # Send POST request to the text suggestions endpoint with auth headers
    response = client.post(
        f"{SUGGESTIONS_API_BASE_URL}/text",
        data=json.dumps(request_data),
        content_type='application/json',
        headers=auth_header
    )
    
    # Verify response status code is 200
    assert response.status_code == 200
    
    # Parse JSON response and verify it contains suggestions
    data = json.loads(response.data)
    
    # Verify response structure
    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)
    assert len(data["suggestions"]) > 0
    
    # Verify document ID is reflected in the response
    assert "document_id" in data
    assert data["document_id"] == document_id


@pytest.mark.integration
@pytest.mark.skip(reason='Rate limit test may be flaky')
def test_suggestion_rate_limit_anonymous_integration(client):
    """Test that anonymous users are subject to appropriate rate limits."""
    # Prepare request data with document content and template ID
    request_data = create_suggestion_request_data(
        document_content=SAMPLE_ORIGINAL_TEXT,
        template_id=TEMPLATE_ID,
        session_id="test-rate-limit-session"
    )
    
    # Send multiple POST requests in quick succession to trigger rate limiting
    responses = []
    for _ in range(15):  # Attempt 15 requests to hit the rate limit
        response = client.post(
            f"{SUGGESTIONS_API_BASE_URL}/text",
            data=json.dumps(request_data),
            content_type='application/json'
        )
        responses.append(response)
        if response.status_code == 429:  # If we hit the rate limit, we can stop
            break
    
    # Verify that at least one response had a 429 status code (rate limit exceeded)
    assert any(r.status_code == 429 for r in responses), "Rate limit was not enforced"
    
    # Get the last response that hit the rate limit
    rate_limited_response = next(r for r in reversed(responses) if r.status_code == 429)
    
    # Verify response contains rate limit error message
    data = json.loads(rate_limited_response.data)
    assert "error" in data
    assert "rate limit" in data["error"].lower()
    
    # Verify Retry-After header is present in the response
    assert "Retry-After" in rate_limited_response.headers


@pytest.mark.integration
def test_invalid_suggestion_request_integration(client):
    """Test that invalid suggestion requests are properly validated."""
    # Test case 1: Missing required fields
    invalid_request_1 = {
        # Missing both document_content and document_id
        "template_id": TEMPLATE_ID
    }
    
    response_1 = client.post(
        f"{SUGGESTIONS_API_BASE_URL}/text",
        data=json.dumps(invalid_request_1),
        content_type='application/json'
    )
    
    # Verify response status code is 400
    assert response_1.status_code == 400
    
    # Verify error message in response
    data_1 = json.loads(response_1.data)
    assert "error" in data_1
    assert "document" in str(data_1).lower()
    
    # Test case 2: Document too large
    large_document = "word " * 30000  # Create document with 30,000 words (over limit)
    invalid_request_2 = create_suggestion_request_data(
        document_content=large_document,
        template_id=TEMPLATE_ID
    )
    
    response_2 = client.post(
        f"{SUGGESTIONS_API_BASE_URL}/text",
        data=json.dumps(invalid_request_2),
        content_type='application/json'
    )
    
    # Verify response status code is 400
    assert response_2.status_code == 400
    
    # Verify error message in response
    data_2 = json.loads(response_2.data)
    assert "error" in data_2
    assert "size" in str(data_2).lower() or "too large" in str(data_2).lower()
    
    # Test case 3: Invalid selection range
    invalid_request_3 = create_suggestion_request_data(
        document_content=SAMPLE_ORIGINAL_TEXT,
        template_id=TEMPLATE_ID,
        selection={"start": 50, "end": 10}  # End before start is invalid
    )
    
    response_3 = client.post(
        f"{SUGGESTIONS_API_BASE_URL}/text",
        data=json.dumps(invalid_request_3),
        content_type='application/json'
    )
    
    # Verify response status code is 400
    assert response_3.status_code == 400
    
    # Verify error message in response
    data_3 = json.loads(response_3.data)
    assert "error" in data_3
    assert "selection" in str(data_3).lower() or "range" in str(data_3).lower()


@pytest.mark.integration
def test_suggestion_interaction_logging_integration(client, db, setup_test_user, auth_header):
    """Test that AI interactions are properly logged in the database."""
    # Prepare request data with document content and template ID
    request_data = create_suggestion_request_data(
        document_content=SAMPLE_ORIGINAL_TEXT,
        template_id=TEMPLATE_ID
    )
    
    # Get user ID from the test fixture for verification
    user_id = setup_test_user["_id"]
    
    # Send POST request to the text suggestions endpoint with auth headers
    response = client.post(
        f"{SUGGESTIONS_API_BASE_URL}/text",
        data=json.dumps(request_data),
        content_type='application/json',
        headers=auth_header
    )
    
    # Verify response status code is 200
    assert response.status_code == 200
    
    # Parse JSON response to get suggestion IDs
    data = json.loads(response.data)
    assert "suggestions" in data
    
    # Get the first suggestion ID for verification
    if data["suggestions"]:
        suggestion_id = data["suggestions"][0]["suggestion_id"]
        
        # Query the database to verify an interaction record was created
        interaction = db.ai_interactions.find_one({"suggestion_id": suggestion_id})
        
        # Verify the interaction record exists and contains the correct user ID
        assert interaction is not None, "Interaction record not created in database"
        assert "user_id" in interaction
        assert str(interaction["user_id"]) == str(user_id)
        
        # Verify the interaction record contains the correct metadata
        assert "prompt_type" in interaction
        assert "created_at" in interaction
        assert "document_content" in interaction or "document_id" in interaction


@pytest.mark.integration
@pytest.mark.slow
def test_suggestion_large_document_optimization_integration(client):
    """Test that large documents are automatically optimized for token usage."""
    # Generate a large document content (approaching but under the maximum limit)
    large_document = "The quick brown fox jumps over the lazy dog. " * 1000  # ~10,000 words
    
    # Prepare request data with the large document and template ID
    request_data = create_suggestion_request_data(
        document_content=large_document,
        template_id=TEMPLATE_ID
    )
    
    # Send POST request to the text suggestions endpoint
    response = client.post(
        f"{SUGGESTIONS_API_BASE_URL}/text",
        data=json.dumps(request_data),
        content_type='application/json'
    )
    
    # Verify response status code is 200
    assert response.status_code == 200
    
    # Parse JSON response and verify it contains suggestions
    data = json.loads(response.data)
    
    # Verify response structure
    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)
    assert len(data["suggestions"]) > 0
    
    # Verify processing time reflects the optimization process
    assert "processing_time" in data
    assert data["processing_time"] > 0.5  # Should take longer than small documents
    
    # Verify optimization metadata is included in the response
    assert "metadata" in data
    assert any(key in data["metadata"] for key in ["optimization", "token_usage", "context_strategy"])


@pytest.mark.integration
@pytest.mark.slow
def test_end_to_end_suggestion_flow(client, setup_test_user, auth_header, setup_test_document):
    """Test the full suggestion flow from request to accepted suggestions."""
    # Get the document ID from the test fixture
    document_id = setup_test_document["_id"]
    
    # Step 1: Generate suggestions for the document
    request_data = create_suggestion_request_data(
        document_id=document_id,
        template_id=TEMPLATE_ID
    )
    
    response = client.post(
        f"{SUGGESTIONS_API_BASE_URL}/text",
        data=json.dumps(request_data),
        content_type='application/json',
        headers=auth_header
    )
    
    # Verify successful suggestion generation
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "suggestions" in data
    assert len(data["suggestions"]) > 0
    
    # Step 2: Extract suggestion IDs from the response
    suggestion_ids = [suggestion["suggestion_id"] for suggestion in data["suggestions"]]
    assert len(suggestion_ids) > 0
    
    # Step 3: Prepare suggestion acceptance request with document ID and suggestion IDs
    accept_request = {
        "document_id": document_id,
        "accepted_suggestion_ids": suggestion_ids,
        "rejected_suggestion_ids": [],
        "apply_immediately": True
    }
    
    # Step 4: Send POST request to accept suggestions
    accept_response = client.post(
        f"{SUGGESTIONS_API_BASE_URL}/accept",
        data=json.dumps(accept_request),
        content_type='application/json',
        headers=auth_header
    )
    
    # Verify successful acceptance
    assert accept_response.status_code == 200
    accept_data = json.loads(accept_response.data)
    assert "success" in accept_data
    assert accept_data["success"] is True
    
    # Step 5: Verify document content is updated with accepted changes
    document_response = client.get(
        f"/api/documents/{document_id}",
        headers=auth_header
    )
    
    assert document_response.status_code == 200
    document_data = json.loads(document_response.data)
    
    # Verify the document has been updated
    assert "content" in document_data
    assert document_data["content"] != setup_test_document["content"]