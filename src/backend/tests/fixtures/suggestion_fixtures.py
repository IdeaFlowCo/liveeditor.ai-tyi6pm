"""
Provides pytest fixtures for generating standardized AI writing suggestions data to be used in tests.

This module contains fixtures for individual suggestions, suggestion responses, track changes
format data, and suggestion requests with various attributes for comprehensive testing of the
AI suggestion system.

Available fixtures:
- single_suggestion: Standard single suggestion for testing
- multiple_suggestions: Multiple suggestions for testing batch processing
- suggestion_with_diff: Suggestion with diff information for track changes
- suggestion_response: Full suggestion response with metadata
- accepted_suggestion: Accepted suggestion for testing
- rejected_suggestion: Rejected suggestion for testing
- track_changes_data: Sample data for track changes testing
- suggestion_request: Standard suggestion request
- suggestion_request_with_template: Template-based suggestion request
- suggestion_request_with_custom_prompt: Custom prompt suggestion request
- anonymous_suggestion_request: Anonymous suggestion request
- authenticated_suggestion_request: Authenticated suggestion request
- suggestion_with_selection: Suggestion request with text selection
- bulk_suggestion_response: Response with multiple suggestions
- suggestion_feedback: User feedback on a suggestion
- suggestion_batch_request: Batch of suggestion requests
"""

import pytest  # pytest ^7.0.0
from datetime import datetime  # standard library
import uuid  # standard library
from bson import ObjectId  # bson ^0.5.10
import copy  # standard library

from .document_fixtures import generate_document_id
from .template_fixtures import get_template_data
from .user_fixtures import generate_user_id, generate_session_id
from ...api.schemas.suggestion_schema import SUGGESTION_TYPES, OPERATION_TYPES

# Sample text for testing suggestions
SAMPLE_ORIGINAL_TEXT = "The company needs to prioritize customer satisfaction and make sure to address all complaints promptly. The big advantage of this approach is that it allows for greater flexibility."
SAMPLE_SUGGESTION_TEXT = "The company should prioritize customer satisfaction and ensure all complaints are addressed promptly. The significant advantage of this approach is that it allows for greater flexibility."
SAMPLE_EXPLANATION = "These changes improve the professionalism of the text by using more concise and definitive language. \"Should\" is more decisive than \"needs to\" and \"ensure\" is more concise than \"make sure to\". \"Significant\" is more professional than \"big\"."

# Track changes format specification
TRACK_CHANGES_FORMAT = {
    "deletion_prefix": "[-",
    "deletion_suffix": "-]",
    "addition_prefix": "{+",
    "addition_suffix": "+}"
}

# Default custom prompt for tests
DEFAULT_CUSTOM_PROMPT = "Please improve this text to be more professional and concise."


def generate_suggestion_id():
    """Generate a unique suggestion ID in the format of MongoDB ObjectID."""
    return str(ObjectId())


def create_suggestion_data(suggestion_id=None, document_id=None, original_text=None,
                          suggested_text=None, explanation=None, start_position=None,
                          end_position=None, suggestion_type=None, is_accepted=None,
                          is_rejected=None):
    """
    Create a suggestion data dictionary with customizable fields.
    
    Args:
        suggestion_id (str): Unique identifier for the suggestion
        document_id (str): ID of the document this suggestion belongs to
        original_text (str): Original text before suggestion
        suggested_text (str): Improved text suggested by AI
        explanation (str): Explanation for the suggestion
        start_position (int): Starting position in the document
        end_position (int): Ending position in the document
        suggestion_type (str): Type of suggestion (grammar, style, etc.)
        is_accepted (bool): Whether the suggestion has been accepted
        is_rejected (bool): Whether the suggestion has been rejected
        
    Returns:
        dict: Dictionary containing suggestion data
    """
    # Default values
    suggestion_id = suggestion_id or generate_suggestion_id()
    document_id = document_id or generate_document_id()
    original_text = original_text or SAMPLE_ORIGINAL_TEXT
    suggested_text = suggested_text or SAMPLE_SUGGESTION_TEXT
    start_position = 0 if start_position is None else start_position
    end_position = len(original_text) if end_position is None else end_position
    suggestion_type = suggestion_type or SUGGESTION_TYPES[0]
    
    # Validate suggestion type
    if suggestion_type not in SUGGESTION_TYPES:
        raise ValueError(f"Invalid suggestion type: {suggestion_type}. Must be one of: {', '.join(SUGGESTION_TYPES)}")
    
    suggestion = {
        "suggestion_id": suggestion_id,
        "document_id": document_id,
        "original_text": original_text,
        "suggested_text": suggested_text,
        "explanation": explanation,
        "start_position": start_position,
        "end_position": end_position,
        "suggestion_type": suggestion_type,
        "is_accepted": is_accepted if is_accepted is not None else False,
        "is_rejected": is_rejected if is_rejected is not None else False,
        "created_at": datetime.utcnow()
    }
    
    return suggestion


def create_change_data(change_id=None, operation_type=None, original_text=None,
                      new_text=None, start_position=None, end_position=None):
    """
    Create a change data dictionary for a track changes operation.
    
    Args:
        change_id (str): Unique identifier for the change
        operation_type (str): Type of operation (addition, deletion, modification)
        original_text (str): Original text being changed
        new_text (str): New text being proposed
        start_position (int): Starting position of the change
        end_position (int): Ending position of the change
        
    Returns:
        dict: Dictionary containing change data
    """
    # Default values
    change_id = change_id or str(uuid.uuid4())
    operation_type = operation_type or "modification"
    
    # Validate operation type
    if operation_type not in OPERATION_TYPES:
        raise ValueError(f"Invalid operation type: {operation_type}. Must be one of: {', '.join(OPERATION_TYPES)}")
    
    # Set appropriate default texts based on operation type
    if operation_type == "deletion":
        original_text = original_text or "text to be deleted"
        new_text = None
    elif operation_type == "addition":
        original_text = None
        new_text = new_text or "text to be added"
    else:  # modification
        original_text = original_text or "original text"
        new_text = new_text or "modified text"
    
    start_position = 0 if start_position is None else start_position
    end_position = (len(original_text) if original_text else 0) if end_position is None else end_position
    
    change = {
        "change_id": change_id,
        "operation_type": operation_type,
        "original_text": original_text,
        "new_text": new_text,
        "start_position": start_position,
        "end_position": end_position
    }
    
    return change


def create_track_changes_data(original_text=None, suggestions=None):
    """
    Create track changes data with original and modified text.
    
    Args:
        original_text (str): Original document text
        suggestions (list): List of suggestion dictionaries
        
    Returns:
        dict: Dictionary with track changes formatted text
    """
    original_text = original_text or SAMPLE_ORIGINAL_TEXT
    suggestions = suggestions or []
    
    # In a real implementation, this would apply the suggestions to the original text
    # and generate the track changes format. For the fixture, we'll use a simplified approach.
    modified_text = SAMPLE_SUGGESTION_TEXT
    
    # Create track changes text by applying the deletion/addition markers
    # This is a simplified example - a real implementation would be more complex
    track_changes_text = original_text
    track_changes_text = track_changes_text.replace("needs to", f"{TRACK_CHANGES_FORMAT['deletion_prefix']}needs to{TRACK_CHANGES_FORMAT['deletion_suffix']}{TRACK_CHANGES_FORMAT['addition_prefix']}should{TRACK_CHANGES_FORMAT['addition_suffix']}")
    track_changes_text = track_changes_text.replace("make sure to", f"{TRACK_CHANGES_FORMAT['deletion_prefix']}make sure to{TRACK_CHANGES_FORMAT['deletion_suffix']}{TRACK_CHANGES_FORMAT['addition_prefix']}ensure{TRACK_CHANGES_FORMAT['addition_suffix']}")
    track_changes_text = track_changes_text.replace("big", f"{TRACK_CHANGES_FORMAT['deletion_prefix']}big{TRACK_CHANGES_FORMAT['deletion_suffix']}{TRACK_CHANGES_FORMAT['addition_prefix']}significant{TRACK_CHANGES_FORMAT['addition_suffix']}")
    
    return {
        "original_text": original_text,
        "modified_text": modified_text,
        "track_changes_text": track_changes_text
    }


def create_suggestion_request_data(document_content=None, document_id=None,
                                 selection=None, template_id=None, custom_prompt=None,
                                 suggestion_type=None, session_id=None):
    """
    Create a suggestion request data dictionary.
    
    Args:
        document_content (str): Raw document content to analyze
        document_id (str): ID of stored document to analyze
        selection (dict): Text selection range for targeted suggestions
        template_id (str): ID of predefined suggestion template to use
        custom_prompt (str): Custom improvement prompt
        suggestion_type (str): Type of suggestion
        session_id (str): Session identifier for anonymous users
        
    Returns:
        dict: Dictionary containing suggestion request data
    """
    # Input validation
    if document_content and document_id:
        raise ValueError("Cannot provide both document_content and document_id")
    if not document_content and not document_id:
        document_content = SAMPLE_ORIGINAL_TEXT
    
    if template_id and custom_prompt:
        raise ValueError("Cannot provide both template_id and custom_prompt")
    if not template_id and not custom_prompt:
        custom_prompt = DEFAULT_CUSTOM_PROMPT
    
    suggestion_type = suggestion_type or "professional"
    
    request = {
        "request_id": str(uuid.uuid4()),
        "suggestion_type": suggestion_type,
        "created_at": datetime.utcnow()
    }
    
    # Set document source
    if document_content:
        request["document_content"] = document_content
    if document_id:
        request["document_id"] = document_id
    
    # Set prompt source
    if template_id:
        request["template_id"] = template_id
    if custom_prompt:
        request["custom_prompt"] = custom_prompt
    
    # Optional fields
    if selection:
        request["selection"] = selection
    if session_id:
        request["session_id"] = session_id
    
    return request


def create_suggestion_response_data(suggestions=None, document_id=None, request_id=None,
                                   prompt_used=None, metadata=None, processing_time=None):
    """
    Create a suggestion response data dictionary.
    
    Args:
        suggestions (list): List of suggestion dictionaries
        document_id (str): ID of the document
        request_id (str): ID of the original request
        prompt_used (str): The prompt that was used to generate suggestions
        metadata (dict): Additional metadata about the suggestions
        processing_time (float): Time taken to process the suggestions
        
    Returns:
        dict: Dictionary containing suggestion response data
    """
    # Default values
    document_id = document_id or generate_document_id()
    request_id = request_id or str(uuid.uuid4())
    prompt_used = prompt_used or DEFAULT_CUSTOM_PROMPT
    metadata = metadata or {"model": "gpt-4", "temperature": 0.7}
    processing_time = processing_time or 1.5  # seconds
    
    # If no suggestions provided, create a default one
    if suggestions is None:
        suggestions = [create_suggestion_data(document_id=document_id)]
    
    response = {
        "document_id": document_id,
        "request_id": request_id,
        "suggestions": suggestions,
        "prompt_used": prompt_used,
        "metadata": metadata,
        "processing_time": processing_time,
        "created_at": datetime.utcnow()
    }
    
    return response


@pytest.fixture
def single_suggestion():
    """
    Fixture providing a standard single suggestion for testing.
    
    Returns:
        dict: A single suggestion data dictionary
    """
    return create_suggestion_data()


@pytest.fixture
def multiple_suggestions():
    """
    Fixture providing multiple suggestions for testing batch processing.
    
    Returns:
        list: A list of suggestion data dictionaries
    """
    document_id = generate_document_id()
    
    suggestions = [
        create_suggestion_data(
            document_id=document_id,
            original_text="needs to prioritize",
            suggested_text="should prioritize",
            start_position=11,
            end_position=29,
            suggestion_type="professional"
        ),
        create_suggestion_data(
            document_id=document_id,
            original_text="make sure to address",
            suggested_text="ensure",
            start_position=67,
            end_position=87,
            suggestion_type="conciseness"
        ),
        create_suggestion_data(
            document_id=document_id,
            original_text="big advantage",
            suggested_text="significant advantage",
            start_position=124,
            end_position=137,
            suggestion_type="professional"
        )
    ]
    
    return suggestions


@pytest.fixture
def suggestion_with_diff():
    """
    Fixture providing a suggestion with diff information for track changes.
    
    Returns:
        dict: A suggestion with detailed diff information
    """
    suggestion = create_suggestion_data()
    
    # Create diff operations
    diff_operations = [
        {
            "operation": "delete",
            "text": "needs to",
            "position": 11
        },
        {
            "operation": "insert",
            "text": "should",
            "position": 11
        },
        {
            "operation": "equal",
            "text": " prioritize customer satisfaction and ",
            "position": 17
        },
        {
            "operation": "delete",
            "text": "make sure to ",
            "position": 55
        },
        {
            "operation": "insert",
            "text": "ensure ",
            "position": 55
        }
    ]
    
    return {
        "suggestion": suggestion,
        "diff_operations": diff_operations,
        "html_diff": "<span>The company <del>needs to</del><ins>should</ins> prioritize customer satisfaction and <del>make sure to</del><ins>ensure</ins> address all complaints promptly.</span>",
        "diff_statistics": {
            "words_added": 2,
            "words_deleted": 4,
            "total_changes": 6
        }
    }


@pytest.fixture
def suggestion_response():
    """
    Fixture providing a full suggestion response with metadata.
    
    Returns:
        dict: A suggestion response dictionary
    """
    return create_suggestion_response_data()


@pytest.fixture
def accepted_suggestion():
    """
    Fixture providing an accepted suggestion for testing.
    
    Returns:
        dict: A suggestion that has been accepted
    """
    return create_suggestion_data(is_accepted=True, is_rejected=False)


@pytest.fixture
def rejected_suggestion():
    """
    Fixture providing a rejected suggestion for testing.
    
    Returns:
        dict: A suggestion that has been rejected
    """
    return create_suggestion_data(is_accepted=False, is_rejected=True)


@pytest.fixture
def track_changes_data():
    """
    Fixture providing sample data for track changes testing.
    
    Returns:
        dict: Track changes data with original, modified, and marked-up text
    """
    return create_track_changes_data()


@pytest.fixture
def suggestion_request():
    """
    Fixture providing a basic suggestion request for testing.
    
    Returns:
        dict: A basic suggestion request dictionary
    """
    return create_suggestion_request_data()


@pytest.fixture
def suggestion_request_with_template():
    """
    Fixture providing a template-based suggestion request.
    
    Returns:
        dict: A suggestion request using a template
    """
    template = get_template_data(name="More Professional Tone", category="professional")
    return create_suggestion_request_data(
        document_content=SAMPLE_ORIGINAL_TEXT,
        template_id=str(template["_id"]),
        custom_prompt=None,
        suggestion_type="professional"
    )


@pytest.fixture
def suggestion_request_with_custom_prompt():
    """
    Fixture providing a custom prompt suggestion request.
    
    Returns:
        dict: A suggestion request using a custom prompt
    """
    return create_suggestion_request_data(
        document_content=SAMPLE_ORIGINAL_TEXT,
        template_id=None,
        custom_prompt="Improve this text to sound more professional and remove redundancy.",
        suggestion_type="custom"
    )


@pytest.fixture
def anonymous_suggestion_request():
    """
    Fixture providing an anonymous suggestion request.
    
    Returns:
        dict: A suggestion request for an anonymous user
    """
    return create_suggestion_request_data(
        document_content=SAMPLE_ORIGINAL_TEXT,
        session_id=generate_session_id()
    )


@pytest.fixture
def authenticated_suggestion_request():
    """
    Fixture providing an authenticated suggestion request.
    
    Returns:
        dict: A suggestion request for an authenticated user
    """
    document_id = generate_document_id()
    return create_suggestion_request_data(
        document_id=document_id,
        document_content=None,
        custom_prompt=DEFAULT_CUSTOM_PROMPT
    )


@pytest.fixture
def suggestion_with_selection():
    """
    Fixture providing a suggestion request with text selection.
    
    Returns:
        dict: A suggestion request with a specific text selection
    """
    selection = {
        "start": 11,
        "end": 137
    }
    return create_suggestion_request_data(
        document_content=SAMPLE_ORIGINAL_TEXT,
        selection=selection,
        custom_prompt=DEFAULT_CUSTOM_PROMPT
    )


@pytest.fixture
def bulk_suggestion_response():
    """
    Fixture providing a response with multiple suggestions.
    
    Returns:
        dict: A response with multiple suggestions
    """
    return create_suggestion_response_data(
        suggestions=multiple_suggestions(),
        metadata={
            "model": "gpt-4",
            "temperature": 0.7,
            "suggestion_count": 3,
            "document_word_count": 28
        },
        processing_time=2.3
    )


@pytest.fixture
def suggestion_feedback():
    """
    Fixture providing user feedback on a suggestion.
    
    Returns:
        dict: A suggestion feedback dictionary
    """
    return {
        "suggestion_id": generate_suggestion_id(),
        "quality_rating": 4,
        "feedback_text": "Good suggestion, but could have been more concise.",
        "improvement_reason": "Made the text more professional",
        "user_id": generate_user_id(),
        "created_at": datetime.utcnow()
    }


@pytest.fixture
def suggestion_batch_request():
    """
    Fixture providing a batch of suggestion requests.
    
    Returns:
        dict: A batch request containing multiple suggestion requests
    """
    requests = [
        create_suggestion_request_data(
            document_id=generate_document_id(),
            custom_prompt="Make more professional"
        ),
        create_suggestion_request_data(
            document_id=generate_document_id(),
            custom_prompt="Fix grammar issues"
        ),
        create_suggestion_request_data(
            document_id=generate_document_id(),
            custom_prompt="Make more concise"
        )
    ]
    
    return {
        "requests": requests,
        "process_in_parallel": True,
        "batch_options": {
            "priority": "normal",
            "timeout": 30
        }
    }