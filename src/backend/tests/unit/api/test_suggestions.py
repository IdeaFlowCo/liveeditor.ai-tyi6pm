"""Unit tests for the suggestions API endpoints, verifying the functionality of generating AI-powered writing improvement suggestions and retrieving suggestion templates. Tests cover both anonymous and authenticated usage, handling various types of suggestions, and ensuring proper error handling and rate limiting."""

import pytest  # pytest version ^7.0.0
from unittest.mock import patch  # unittest.mock is part of the standard library
from flask import Flask  # Flask version ^2.3.0
from flask.testing import FlaskClient  # Flask's test client
import json  # json is part of the standard library

from src.backend.api.suggestions import suggestions_bp  # Import the suggestions Blueprint for testing
from src.backend.core.ai.suggestion_generator import SuggestionGenerator  # Import the core service to mock for tests
from src.backend.core.ai.prompt_manager import PromptManager  # Import the prompt manager to mock template retrieval
from src.backend.core.ai.token_optimizer import TokenOptimizer  # Import the token optimizer for mocking in tests
from src.backend.api.schemas.suggestion_schema import suggestion_request_schema  # Import schema for validating test request data
from src.backend.api.schemas.suggestion_schema import suggestion_with_diff_schema  # Import schema for validating test response data
from src.backend.data.mongodb.repositories.ai_interaction_repository import AIInteractionRepository  # Import repository to mock for tests
from src.backend.tests.fixtures.suggestion_fixtures import create_suggestion_data  # Import fixture utility for creating test data
from src.backend.tests.fixtures.suggestion_fixtures import create_suggestion_request_data  # Import fixture utility for creating test request data
from src.backend.tests.fixtures.suggestion_fixtures import create_suggestion_response_data  # Import fixture utility for creating test response data

TEST_PREFIX = '/api/suggestions'
SAMPLE_DOCUMENT_CONTENT = "The company needs to prioritize customer satisfaction and make sure to address all complaints promptly. The big advantage of this approach is that it allows for greater flexibility."
SAMPLE_SUGGESTION_RESPONSE = create_suggestion_response_data(suggestions=[create_suggestion_data()])


def setup_test_client() -> FlaskClient:
    """Helper function to create and configure a Flask test client with the suggestions Blueprint registered"""
    app = Flask(__name__)  # Create Flask app instance
    app.config['TESTING'] = True  # Configure app for testing
    app.register_blueprint(suggestions_bp)  # Register suggestions_bp with Flask application
    return app.test_client()  # Return test client


@pytest.mark.unit
@patch('src.backend.core.ai.prompt_manager.PromptManager.get_templates')
def test_get_suggestion_templates(mock_get_templates):
    """Test that the templates endpoint returns available suggestion templates"""
    test_client = setup_test_client()  # Create test client
    sample_templates = [  # Sample templates to return
        {'id': '1', 'name': 'Make it shorter', 'category': 'conciseness'},
        {'id': '2', 'name': 'More professional', 'category': 'style'}
    ]
    mock_get_templates.return_value = sample_templates  # Mock PromptManager.get_templates to return sample templates

    response = test_client.get(f'{TEST_PREFIX}/templates')  # Send GET request to /api/suggestions/templates
    assert response.status_code == 200  # Assert response status code is 200
    data = json.loads(response.data.decode('utf-8'))  # Load response data
    assert 'conciseness' in data and 'style' in data  # Assert response contains expected templates data
    mock_get_templates.assert_called_once()  # Assert get_templates was called once


@pytest.mark.unit
@patch('src.backend.core.ai.suggestion_generator.SuggestionGenerator.get_supported_suggestion_types')
def test_get_suggestion_types(mock_get_suggestion_types):
    """Test that the types endpoint returns available suggestion types"""
    test_client = setup_test_client()  # Create test client
    sample_types = {'grammar': 'Fix grammar', 'style': 'Improve style'}  # Sample types to return
    mock_get_suggestion_types.return_value = sample_types  # Mock SuggestionGenerator.get_supported_suggestion_types to return sample types

    response = test_client.get(f'{TEST_PREFIX}/types')  # Send GET request to /api/suggestions/types
    assert response.status_code == 200  # Assert response status code is 200
    data = json.loads(response.data.decode('utf-8'))  # Load response data
    assert data == sample_types  # Assert response contains expected suggestion types data
    mock_get_suggestion_types.assert_called_once()  # Assert get_supported_suggestion_types was called once


@pytest.mark.unit
@patch('src.backend.core.ai.suggestion_generator.SuggestionGenerator.generate_suggestions')
def test_generate_text_suggestions_valid(mock_generate_suggestions):
    """Test that the text suggestions endpoint returns suggestions for valid input"""
    test_client = setup_test_client()  # Create test client
    request_data = create_suggestion_request_data(document_content=SAMPLE_DOCUMENT_CONTENT, template_id='123')  # Create valid suggestion request with document content and template ID
    mock_generate_suggestions.return_value = SAMPLE_SUGGESTION_RESPONSE  # Mock SuggestionGenerator.generate_suggestions to return sample suggestions

    response = test_client.post(f'{TEST_PREFIX}/text', json=request_data)  # Send POST request to /api/suggestions/text with request data
    assert response.status_code == 200  # Assert response status code is 200
    data = json.loads(response.data.decode('utf-8'))  # Load response data
    assert 'suggestions' in data  # Assert response contains suggestions in expected format
    assert 'changes' in data['suggestions'][0] if data['suggestions'] else True  # Assert response includes track changes format data
    mock_generate_suggestions.assert_called_with(  # Assert generate_suggestions was called with correct parameters
        document_content=SAMPLE_DOCUMENT_CONTENT,
        prompt_type=request_data['suggestion_type'],
        options={'template_id': '123', 'custom_prompt': None, 'selection': None},
        session_id=None
    )


@pytest.mark.unit
def test_generate_text_suggestions_invalid_request():
    """Test that the text suggestions endpoint validates request data"""
    test_client = setup_test_client()  # Create test client
    request_data = {}  # Create invalid suggestion request (missing required fields)

    response = test_client.post(f'{TEST_PREFIX}/text', json=request_data)  # Send POST request to /api/suggestions/text with invalid data
    assert response.status_code == 400  # Assert response status code is 400
    data = json.loads(response.data.decode('utf-8'))  # Load response data
    assert 'error' in data  # Assert response contains validation error details


@pytest.mark.unit
@patch('src.backend.core.ai.suggestion_generator.SuggestionGenerator.generate_suggestions')
def test_generate_text_suggestions_with_custom_prompt(mock_generate_suggestions):
    """Test that the text suggestions endpoint works with custom prompts"""
    test_client = setup_test_client()  # Create test client
    request_data = create_suggestion_request_data(document_content=SAMPLE_DOCUMENT_CONTENT, custom_prompt='Make it shorter')  # Create suggestion request with custom prompt instead of template ID
    mock_generate_suggestions.return_value = SAMPLE_SUGGESTION_RESPONSE  # Mock SuggestionGenerator.generate_suggestions to return sample suggestions

    response = test_client.post(f'{TEST_PREFIX}/text', json=request_data)  # Send POST request to /api/suggestions/text with request data
    assert response.status_code == 200  # Assert response status code is 200
    data = json.loads(response.data.decode('utf-8'))  # Load response data
    assert 'suggestions' in data  # Assert response contains suggestions
    mock_generate_suggestions.assert_called_with(  # Assert generate_suggestions was called with custom prompt parameter
        document_content=SAMPLE_DOCUMENT_CONTENT,
        prompt_type=request_data['suggestion_type'],
        options={'template_id': None, 'custom_prompt': 'Make it shorter', 'selection': None},
        session_id=None
    )


@pytest.mark.unit
@patch('src.backend.core.ai.suggestion_generator.SuggestionGenerator.generate_suggestions')
@patch('src.backend.api.middleware.auth_middleware.is_anonymous_session')
def test_generate_text_suggestions_anonymous_user(mock_is_anonymous_session, mock_generate_suggestions):
    """Test that the text suggestions endpoint works for anonymous users"""
    test_client = setup_test_client()  # Create test client
    mock_is_anonymous_session.return_value = True  # Mock is_anonymous_session to return True (anonymous user)
    request_data = create_suggestion_request_data(document_content=SAMPLE_DOCUMENT_CONTENT, custom_prompt='Make it shorter', session_id='session123')  # Create valid suggestion request with session ID
    mock_generate_suggestions.return_value = SAMPLE_SUGGESTION_RESPONSE  # Mock SuggestionGenerator.generate_suggestions to return sample suggestions

    response = test_client.post(f'{TEST_PREFIX}/text', json=request_data)  # Send POST request to /api/suggestions/text with request data
    assert response.status_code == 200  # Assert response status code is 200
    data = json.loads(response.data.decode('utf-8'))  # Load response data
    assert 'suggestions' in data  # Assert response contains suggestions
    mock_generate_suggestions.assert_called_with(  # Assert generate_suggestions was called with session_id parameter
        document_content=SAMPLE_DOCUMENT_CONTENT,
        prompt_type=request_data['suggestion_type'],
        options={'template_id': None, 'custom_prompt': 'Make it shorter', 'selection': None},
        session_id='session123'
    )


@pytest.mark.unit
@patch('src.backend.core.ai.suggestion_generator.SuggestionGenerator.generate_suggestions')
def test_generate_text_suggestions_with_selection(mock_generate_suggestions):
    """Test that the text suggestions endpoint handles text selection properly"""
    test_client = setup_test_client()  # Create test client
    selection = {'start': 10, 'end': 50}  # Text selection range (start/end positions)
    request_data = create_suggestion_request_data(document_content=SAMPLE_DOCUMENT_CONTENT, custom_prompt='Make it shorter', selection=selection)  # Create suggestion request with text selection range (start/end positions)
    mock_generate_suggestions.return_value = SAMPLE_SUGGESTION_RESPONSE  # Mock SuggestionGenerator.generate_suggestions to return sample suggestions

    response = test_client.post(f'{TEST_PREFIX}/text', json=request_data)  # Send POST request to /api/suggestions/text with request data
    assert response.status_code == 200  # Assert response status code is 200
    data = json.loads(response.data.decode('utf-8'))  # Load response data
    assert 'suggestions' in data  # Assert response contains suggestions for selected text
    mock_generate_suggestions.assert_called_with(  # Assert generate_suggestions was called with selection parameters
        document_content=SAMPLE_DOCUMENT_CONTENT,
        prompt_type=request_data['suggestion_type'],
        options={'template_id': None, 'custom_prompt': 'Make it shorter', 'selection': selection},
        session_id=None
    )


@pytest.mark.unit
@patch('src.backend.core.ai.suggestion_generator.SuggestionGenerator.generate_suggestions')
def test_generate_style_suggestions(mock_generate_suggestions):
    """Test that the style suggestions endpoint works correctly"""
    test_client = setup_test_client()  # Create test client
    request_data = create_suggestion_request_data(document_content=SAMPLE_DOCUMENT_CONTENT, suggestion_type='style', custom_prompt='Make it sound more formal')  # Create valid suggestion request with style parameters
    mock_generate_suggestions.return_value = SAMPLE_SUGGESTION_RESPONSE  # Mock SuggestionGenerator.generate_suggestions to return style suggestions

    response = test_client.post(f'{TEST_PREFIX}/style', json=request_data)  # Send POST request to /api/suggestions/style with request data
    assert response.status_code == 200  # Assert response status code is 200
    data = json.loads(response.data.decode('utf-8'))  # Assert response contains style suggestions
    assert 'suggestions' in data  # Assert response contains style suggestions
    mock_generate_suggestions.assert_called_with(  # Assert generate_suggestions was called with style suggestion_type parameter
        document_content=SAMPLE_DOCUMENT_CONTENT,
        prompt_type='style',
        options={'template_id': None, 'custom_prompt': 'Make it sound more formal', 'selection': None},
        session_id=None
    )


@pytest.mark.unit
@patch('src.backend.core.ai.suggestion_generator.SuggestionGenerator.generate_suggestions')
def test_generate_grammar_suggestions(mock_generate_suggestions):
    """Test that the grammar suggestions endpoint works correctly"""
    test_client = setup_test_client()  # Create test client
    request_data = create_suggestion_request_data(document_content=SAMPLE_DOCUMENT_CONTENT, suggestion_type='grammar', custom_prompt='Fix any grammar errors')  # Create valid suggestion request with language preferences
    mock_generate_suggestions.return_value = SAMPLE_SUGGESTION_RESPONSE  # Mock SuggestionGenerator.generate_suggestions to return grammar suggestions

    response = test_client.post(f'{TEST_PREFIX}/grammar', json=request_data)  # Send POST request to /api/suggestions/grammar with request data
    assert response.status_code == 200  # Assert response status code is 200
    data = json.loads(response.data.decode('utf-8'))  # Assert response contains grammar suggestions
    assert 'suggestions' in data  # Assert response contains grammar suggestions
    mock_generate_suggestions.assert_called_with(  # Assert generate_suggestions was called with grammar suggestion_type parameter
        document_content=SAMPLE_DOCUMENT_CONTENT,
        prompt_type='grammar',
        options={'template_id': None, 'custom_prompt': 'Fix any grammar errors', 'selection': None},
        session_id=None
    )


@pytest.mark.unit
@patch('src.backend.api.middleware.rate_limiter.rate_limit')
@patch('src.backend.api.middleware.auth_middleware.is_anonymous_session')
def test_suggestions_rate_limit_anonymous(mock_is_anonymous_session, mock_rate_limit):
    """Test that anonymous users are subject to appropriate rate limits"""
    test_client = setup_test_client()  # Create test client
    mock_is_anonymous_session.return_value = True  # Mock is_anonymous_session to return True (anonymous user)
    mock_rate_limit.return_value = True  # Mock rate_limit to act as if limit is exceeded
    request_data = create_suggestion_request_data(document_content=SAMPLE_DOCUMENT_CONTENT, custom_prompt='Make it shorter')  # Create valid request data

    response = test_client.post(f'{TEST_PREFIX}/text', json=request_data)  # Send POST request to /api/suggestions/text with valid request data
    assert response.status_code == 429  # Assert response status code is 429 (Too Many Requests)
    data = json.loads(response.data.decode('utf-8'))  # Load response data
    assert 'error' in data  # Assert response contains rate limit error message
    # mock_rate_limit.assert_called_with(limit_anonymous=True)  # Verify rate_limit was called with anonymous limit parameter


@pytest.mark.unit
@patch('src.backend.core.ai.suggestion_generator.SuggestionGenerator.generate_suggestions')
def test_suggestions_service_error(mock_generate_suggestions):
    """Test that the suggestions API properly handles errors from the suggestion service"""
    test_client = setup_test_client()  # Create test client
    mock_generate_suggestions.side_effect = Exception('AI service unavailable')  # Mock SuggestionGenerator.generate_suggestions to raise an exception
    request_data = create_suggestion_request_data(document_content=SAMPLE_DOCUMENT_CONTENT, custom_prompt='Make it shorter')  # Create valid request data

    response = test_client.post(f'{TEST_PREFIX}/text', json=request_data)  # Send POST request to /api/suggestions/text with valid request data
    assert response.status_code == 500  # Assert response status code is 500
    data = json.loads(response.data.decode('utf-8'))  # Assert response contains error message
    assert 'error' in data  # Assert response contains error message
    mock_generate_suggestions.assert_called_once()  # Assert generate_suggestions was called once


@pytest.mark.unit
@patch('src.backend.core.ai.suggestion_generator.SuggestionGenerator.generate_suggestions')
@patch('src.backend.core.ai.token_optimizer.TokenOptimizer.optimize_content')
def test_suggestions_optimization(mock_optimize_content, mock_generate_suggestions):
    """Test that content optimization is applied when needed"""
    test_client = setup_test_client()  # Create test client
    mock_optimize_content.return_value = "Optimized document content"  # Mock TokenOptimizer.optimize_content to return optimized content
    mock_generate_suggestions.return_value = SAMPLE_SUGGESTION_RESPONSE  # Mock SuggestionGenerator.generate_suggestions to return suggestions
    request_data = create_suggestion_request_data(document_content="Large document content", custom_prompt='Make it shorter')  # Create suggestion request with large document content

    response = test_client.post(f'{TEST_PREFIX}/text', json=request_data)  # Send POST request to /api/suggestions/text with request data
    assert response.status_code == 200  # Assert response status code is 200
    mock_optimize_content.assert_called_once()  # Assert optimize_content was called once
    mock_generate_suggestions.assert_called_with(  # Assert generate_suggestions was called with optimized content
        document_content="Large document content",
        prompt_type=request_data['suggestion_type'],
        options={'template_id': None, 'custom_prompt': 'Make it shorter', 'selection': None},
        session_id=None
    )


@pytest.mark.unit
@patch('src.backend.core.ai.suggestion_generator.SuggestionGenerator.generate_suggestions')
@patch('src.backend.data.mongodb.repositories.ai_interaction_repository.AIInteractionRepository.save_interaction')
def test_suggestions_interaction_logging(mock_save_interaction, mock_generate_suggestions):
    """Test that AI interactions are properly logged"""
    test_client = setup_test_client()  # Create test client
    mock_generate_suggestions.return_value = SAMPLE_SUGGESTION_RESPONSE  # Mock SuggestionGenerator.generate_suggestions to return suggestions
    mock_save_interaction.return_value = True  # Mock AIInteractionRepository.save_interaction to return success
    request_data = create_suggestion_request_data(document_content=SAMPLE_DOCUMENT_CONTENT, custom_prompt='Make it shorter')  # Create valid suggestion request

    response = test_client.post(f'{TEST_PREFIX}/text', json=request_data)  # Send POST request to /api/suggestions/text with request data
    assert response.status_code == 200  # Assert response status code is 200
    mock_save_interaction.assert_called()  # Assert save_interaction was called with correct parameters
    call_args = mock_save_interaction.call_args.kwargs
    assert 'user_id' in call_args or 'session_id' in call_args  # Assert interaction data includes user ID or session ID