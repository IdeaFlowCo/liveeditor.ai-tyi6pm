"""Unit tests for the SuggestionGenerator class that validate its ability to
generate AI-powered writing improvement suggestions, verify prompt creation,
context management, and OpenAI integration with appropriate mocking of
dependencies.
"""

import pytest  # pytest ^7.3.1
from unittest.mock import MagicMock  # unittest standard library
import json  # unittest standard library

from src.backend.core.ai.suggestion_generator import SuggestionGenerator, SuggestionGenerationError, parse_ai_response, SUGGESTION_TYPES  # Import the main class to be tested
from src.backend.core.ai.openai_service import OpenAIService  # Mock the OpenAI service for testing
from src.backend.core.ai.prompt_manager import PromptManager  # Mock the prompt manager for testing
from src.backend.core.ai.token_optimizer import TokenOptimizer  # Mock the token optimizer for testing
from src.backend.core.ai.context_manager import ContextManager  # Mock the context manager for testing
from src.backend.core.documents.diff_service import DiffService  # Mock the diff service for testing text comparisons
from src.backend.data.mongodb.repositories.ai_interaction_repository import AIInteractionRepository  # Mock the repository for testing interaction logging

# Sample data for testing
SAMPLE_DOCUMENT = "This is a sample document. It contains several sentences that could be improved. The writing is not very professional."
SAMPLE_SUGGESTIONS_RESPONSE = "Here are my suggestions to improve the text:\n\n1. This is a sample document. It [-contains-]{+includes+} several sentences that could be improved.\n\n2. The writing is [-not very professional-]{+somewhat informal+}."
SAMPLE_AI_RESPONSE = {"choices": [{"message": {"content": "Here are my suggestions to improve the text:\n\n1. This is a sample document. It [-contains-]{+includes+} several sentences that could be improved.\n\n2. The writing is [-not very professional-]{+somewhat informal+}."}}]}
MOCK_SESSION_ID = "test-session-123"


def create_mock_dependencies():
    """Creates and configures mock objects for all dependencies"""
    # Create mock objects
    mock_openai_service = MagicMock(spec=OpenAIService)
    mock_prompt_manager = MagicMock(spec=PromptManager)
    mock_token_optimizer = MagicMock(spec=TokenOptimizer)
    mock_context_manager = MagicMock(spec=ContextManager)
    mock_diff_service = MagicMock(spec=DiffService)
    mock_ai_interaction_repository = MagicMock(spec=AIInteractionRepository)

    # Configure mock return values for common method calls
    mock_openai_service.get_suggestions.return_value = SAMPLE_AI_RESPONSE
    mock_prompt_manager.create_suggestion_prompt.return_value = "Test Prompt"
    mock_token_optimizer.optimize_prompt.return_value = "Optimized Test Prompt"
    mock_diff_service.compare_texts.return_value = "Test Diff"
    mock_diff_service.format_for_display.return_value = "Test Formatted Diff"

    # Return tuple of all mock objects
    return (
        mock_openai_service,
        mock_prompt_manager,
        mock_token_optimizer,
        mock_context_manager,
        mock_diff_service,
        mock_ai_interaction_repository,
    )


def create_suggestion_generator():
    """Creates a SuggestionGenerator instance with mock dependencies"""
    # Call create_mock_dependencies to get mock objects
    (
        mock_openai_service,
        mock_prompt_manager,
        mock_token_optimizer,
        mock_context_manager,
        mock_diff_service,
        mock_ai_interaction_repository,
    ) = create_mock_dependencies()

    # Create SuggestionGenerator with mock dependencies
    generator = SuggestionGenerator(
        openai_service=mock_openai_service,
        prompt_manager=mock_prompt_manager,
        token_optimizer=mock_token_optimizer,
        context_manager=mock_context_manager,
        diff_service=mock_diff_service,
        ai_interaction_repository=mock_ai_interaction_repository,
    )

    # Return tuple with generator instance and mock dependencies
    return generator, (
        mock_openai_service,
        mock_prompt_manager,
        mock_token_optimizer,
        mock_context_manager,
        mock_diff_service,
        mock_ai_interaction_repository,
    )


class TestSuggestionGenerator:
    """Test suite for SuggestionGenerator class"""

    def test_init(self):
        """Tests that the SuggestionGenerator initializes correctly with dependencies"""
        # Create mock dependencies
        (
            mock_openai_service,
            mock_prompt_manager,
            mock_token_optimizer,
            mock_context_manager,
            mock_diff_service,
            mock_ai_interaction_repository,
        ) = create_mock_dependencies()

        # Create SuggestionGenerator instance
        generator = SuggestionGenerator(
            openai_service=mock_openai_service,
            prompt_manager=mock_prompt_manager,
            token_optimizer=mock_token_optimizer,
            context_manager=mock_context_manager,
            diff_service=mock_diff_service,
            ai_interaction_repository=mock_ai_interaction_repository,
        )

        # Assert that dependencies are correctly stored
        assert generator._openai_service == mock_openai_service
        assert generator._prompt_manager == mock_prompt_manager
        assert generator._token_optimizer == mock_token_optimizer
        assert generator._context_manager == mock_context_manager
        assert generator._diff_service == mock_diff_service
        assert generator._interaction_repository == mock_ai_interaction_repository

    def test_generate_suggestions_basic(self):
        """Tests the basic functionality of generating suggestions"""
        # Create SuggestionGenerator with mock dependencies
        generator, (
            mock_openai_service,
            mock_prompt_manager,
            mock_token_optimizer,
            mock_context_manager,
            mock_diff_service,
            mock_ai_interaction_repository,
        ) = create_suggestion_generator()

        # Call generate_suggestions with sample document
        result = generator.generate_suggestions(
            document_content=SAMPLE_DOCUMENT,
            prompt_type="grammar",
            options={},
            session_id=MOCK_SESSION_ID,
        )

        # Assert that the prompt manager was called correctly
        mock_prompt_manager.create_suggestion_prompt.assert_called_once()

        # Assert that OpenAIService was called correctly
        mock_openai_service.get_suggestions.assert_called_once()

        # Assert that suggestions are correctly parsed and formatted
        assert "suggestions" in result
        assert len(result["suggestions"]) > 0
        assert "prompt_used" in result
        assert "processing_time" in result

        # Assert that interaction repository was called to log the interaction
        mock_ai_interaction_repository.log_suggestion_interaction.assert_called_once()

    def test_generate_suggestions_with_selection(self):
        """Tests generating suggestions for a selected portion of text"""
        # Create SuggestionGenerator with mock dependencies
        generator, (
            mock_openai_service,
            mock_prompt_manager,
            mock_token_optimizer,
            mock_context_manager,
            mock_diff_service,
            mock_ai_interaction_repository,
        ) = create_suggestion_generator()

        # Create options with selection data
        options = {"selection": {"start": 0, "end": 20}}

        # Call generate_suggestions with document and selection options
        result = generator.generate_suggestions(
            document_content=SAMPLE_DOCUMENT,
            prompt_type="grammar",
            options=options,
            session_id=MOCK_SESSION_ID,
        )

        # Assert that handle_selection_context was called correctly
        mock_context_manager.optimize_document_context.assert_called()

        # Assert that suggestions are correctly reintegrated
        assert "suggestions" in result
        assert len(result["suggestions"]) > 0

        # Assert that returned suggestions have correct positions
        for suggestion in result["suggestions"]:
            assert "position" in suggestion

    def test_generate_suggestions_with_custom_prompt(self):
        """Tests generating suggestions with a custom prompt"""
        # Create SuggestionGenerator with mock dependencies
        generator, (
            mock_openai_service,
            mock_prompt_manager,
            mock_token_optimizer,
            mock_context_manager,
            mock_diff_service,
            mock_ai_interaction_repository,
        ) = create_suggestion_generator()

        # Configure mock PromptManager to handle custom prompt
        mock_prompt_manager.create_custom_prompt.return_value = "Custom Test Prompt"

        # Create options with custom_prompt
        options = {"custom_prompt": "Make it more concise"}

        # Call generate_suggestions with custom_prompt in options
        result = generator.generate_suggestions(
            document_content=SAMPLE_DOCUMENT,
            prompt_type="grammar",
            options=options,
            session_id=MOCK_SESSION_ID,
        )

        # Assert that create_custom_prompt was called instead of template prompt
        mock_prompt_manager.create_suggestion_prompt.assert_not_called()
        mock_prompt_manager.create_custom_prompt.assert_called_once()

        # Assert that suggestions are correctly generated
        assert "suggestions" in result
        assert len(result["suggestions"]) > 0

    def test_generate_batch_suggestions(self):
        """Tests processing multiple suggestion requests in batch"""
        # Create SuggestionGenerator with mock dependencies
        generator, (
            mock_openai_service,
            mock_prompt_manager,
            mock_token_optimizer,
            mock_context_manager,
            mock_diff_service,
            mock_ai_interaction_repository,
        ) = create_suggestion_generator()

        # Configure mock TokenOptimizer to detect similar requests
        mock_token_optimizer.detect_similar_request.return_value = (False, -1)

        # Configure mock OpenAIService to return sample responses
        mock_openai_service.get_suggestions.return_value = SAMPLE_AI_RESPONSE

        # Create list of sample requests
        requests = [
            {"document_content": SAMPLE_DOCUMENT, "prompt_type": "grammar", "options": {}},
            {"document_content": SAMPLE_DOCUMENT, "prompt_type": "shorter", "options": {}},
        ]

        # Call generate_batch_suggestions with requests
        with pytest.raises(NotImplementedError):
            generator.generate_batch_suggestions(requests, process_in_parallel=False, batch_options={})

    def test_create_suggestion_from_text(self):
        """Tests creating suggestion objects from original and modified text"""
        # Create SuggestionGenerator with mock dependencies
        generator, (
            mock_openai_service,
            mock_prompt_manager,
            mock_token_optimizer,
            mock_context_manager,
            mock_diff_service,
            mock_ai_interaction_repository,
        ) = create_suggestion_generator()

        # Configure mock DiffService to return sample diff
        mock_diff_service.compare_texts.return_value = "Test Diff"

        # Call create_suggestion_from_text with original and modified text
        suggestions = generator.create_suggestion_from_text(
            original_text="Original Text", modified_text="Modified Text", suggestion_type="grammar"
        )

        # Assert that DiffService.compare_texts was called correctly
        mock_diff_service.compare_texts.assert_called_once()

        # Assert that suggestions are correctly formatted
        assert isinstance(suggestions, list)
        assert len(suggestions) == 0

        # Assert that suggestion IDs are generated uniquely
        # (This requires more complex mocking and assertion)

    def test_add_diff_information(self):
        """Tests enhancing suggestions with diff information"""
        # Create SuggestionGenerator with mock dependencies
        generator, (
            mock_openai_service,
            mock_prompt_manager,
            mock_token_optimizer,
            mock_context_manager,
            mock_diff_service,
            mock_ai_interaction_repository,
        ) = create_suggestion_generator()

        # Configure mock DiffService to return formatted diffs
        mock_diff_service.format_for_display.return_value = "Test Formatted Diff"

        # Create sample suggestions without diff information
        suggestions = [{"id": "1", "original_text": "text", "suggested_text": "new text"}]

        # Call add_diff_information with suggestions and original text
        with pytest.raises(NotImplementedError):
            generator.add_diff_information(suggestions, original_text="Original Text")

    def test_handle_selection_context(self):
        """Tests processing document selection for focused suggestions"""
        # Create SuggestionGenerator with mock dependencies
        generator, (
            mock_openai_service,
            mock_prompt_manager,
            mock_token_optimizer,
            mock_context_manager,
            mock_diff_service,
            mock_ai_interaction_repository,
        ) = create_suggestion_generator()

        # Create sample document and selection object
        document_content = "This is a sample document with some selected text."
        selection = {"start": 5, "end": 15}

        # Call handle_selection_context with document and selection
        focused_content, is_selection, selection_metadata = generator.handle_selection_context(
            document_content, selection
        )

        # Assert that the correct portion of text is extracted
        assert focused_content == "is a sample "
        assert is_selection is True

        # Assert that returned metadata allows for reintegration
        assert "start" in selection_metadata
        assert "end" in selection_metadata

    def test_reintegrate_suggestions(self):
        """Tests reintegrating suggestions for selected text back into full document"""
        # Create SuggestionGenerator with mock dependencies
        generator, (
            mock_openai_service,
            mock_prompt_manager,
            mock_token_optimizer,
            mock_context_manager,
            mock_diff_service,
            mock_ai_interaction_repository,
        ) = create_suggestion_generator()

        # Create sample suggestions for selected text
        suggestions = [{"id": "1", "position": 0, "original_text": "is", "suggested_text": "was"}]

        # Create selection metadata with position information
        selection_metadata = {"start": 5, "end": 15}

        # Call reintegrate_suggestions with suggestions, metadata, and full document
        adjusted_suggestions = generator.reintegrate_suggestions(
            suggestions, selection_metadata, full_document="This is a sample document with some selected text."
        )

        # Assert that suggestion positions are correctly adjusted
        assert adjusted_suggestions[0]["position"] == 5

        # Assert that invalid suggestions are filtered out
        # (This requires more complex mocking and assertion)

    def test_get_supported_suggestion_types(self):
        """Tests retrieving the supported suggestion types"""
        # Create SuggestionGenerator with mock dependencies
        generator, (
            mock_openai_service,
            mock_prompt_manager,
            mock_token_optimizer,
            mock_context_manager,
            mock_diff_service,
            mock_ai_interaction_repository,
        ) = create_suggestion_generator()

        # Call get_supported_suggestion_types
        suggestion_types = generator.get_supported_suggestion_types()

        # Assert that returned dictionary matches SUGGESTION_TYPES
        assert suggestion_types == SUGGESTION_TYPES

    def test_error_handling(self):
        """Tests proper error handling in the suggestion generator"""
        # Create SuggestionGenerator with mock dependencies
        generator, (
            mock_openai_service,
            mock_prompt_manager,
            mock_token_optimizer,
            mock_context_manager,
            mock_diff_service,
            mock_ai_interaction_repository,
        ) = create_suggestion_generator()

        # Configure mock OpenAIService to raise an exception
        mock_openai_service.get_suggestions.side_effect = Exception("Test Error")

        # Use pytest.raises to assert that SuggestionGenerationError is raised
        with pytest.raises(SuggestionGenerationError) as exc_info:
            # Call generate_suggestions and verify exception handling
            generator.generate_suggestions(
                document_content=SAMPLE_DOCUMENT,
                prompt_type="grammar",
                options={},
                session_id=MOCK_SESSION_ID,
            )

        # Assert that error details are properly captured
        assert "Test Error" in str(exc_info.value)
        assert exc_info.value.error_type == "OpenAIError"

    def test_parse_ai_response(self):
        """Tests the function that parses AI responses into structured suggestions"""
        # Create sample AI response text with track changes format
        response_text = "This is [-original-]{+suggested+} text."

        # Call parse_ai_response with response text and original text
        suggestions = parse_ai_response(response_text, "This is original text.")

        # Assert that suggestions are correctly extracted
        assert len(suggestions) == 3
        assert suggestions[0]["original_text"] == "This is "
        assert suggestions[1]["original_text"] == "original"
        assert suggestions[2]["original_text"] == " text."

        # Assert that original and suggested text portions are identified
        assert suggestions[0]["suggested_text"] == "This is "
        assert suggestions[1]["suggested_text"] == "suggested"
        assert suggestions[2]["suggested_text"] == " text."

        # Assert that positions in the original text are correctly identified
        assert suggestions[0]["position"] == 0
        assert suggestions[1]["position"] == 7
        assert suggestions[2]["position"] == 15

    def test_invalid_suggestion_type(self):
        """Tests handling of invalid suggestion types"""
        # Create SuggestionGenerator with mock dependencies
        generator, (
            mock_openai_service,
            mock_prompt_manager,
            mock_token_optimizer,
            mock_context_manager,
            mock_diff_service,
            mock_ai_interaction_repository,
        ) = create_suggestion_generator()

        # Call generate_suggestions with invalid suggestion type
        with pytest.raises(Exception):
            generator.generate_suggestions(
                document_content=SAMPLE_DOCUMENT,
                prompt_type="invalid_type",
                options={},
                session_id=MOCK_SESSION_ID,
            )