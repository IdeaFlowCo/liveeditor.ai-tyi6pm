"""
Core service that generates AI-powered writing improvement suggestions by orchestrating prompt creation,
context management, and OpenAI interactions. Produces contextually relevant suggestions in a track-changes
format that can be presented to users for review and acceptance.
"""

import re  # Regular expressions for text processing
import time  # Performance timing and measuring processing duration
import typing  # Type annotations for better code documentation
import uuid  # Generate unique identifiers for suggestions
import json  # JSON handling for structured data

from .context_manager import ContextManager  # Manage document context for AI processing
from .openai_service import OpenAIService  # Interface with OpenAI API to generate suggestions
from .prompt_manager import PromptManager  # Create and format prompts for AI suggestions
from .token_optimizer import TokenOptimizer  # Optimize token usage for efficient AI interactions
from ..documents.diff_service import DiffService  # Generate track changes format diffs between original and suggested text
from ...data.mongodb.repositories.ai_interaction_repository import AIInteractionRepository  # Log AI suggestion interactions for analytics and improvement
from ...core.utils.logger import get_logger  # Configure logging for the suggestion generator

# Constants
SUGGESTION_TYPES = {
    "shorter": "Make the text more concise",
    "professional": "Use more professional language",
    "grammar": "Fix grammar and spelling issues",
    "clarity": "Improve clarity and readability",
    "examples": "Add relevant examples",
    "academic": "Use academic writing style",
    "creative": "Make the writing more engaging"
}
MAX_CONCURRENCY = 5
DEFAULT_MAX_TOKENS = 4000
DEFAULT_RESERVED_TOKENS = 800
DEFAULT_SUGGESTION_COUNT = 10
DIFF_ALGORITHM = "diff_match_patch"
TRACK_CHANGES_FORMAT = {
    "deletion_prefix": "[-",
    "deletion_suffix": "-]",
    "addition_prefix": "{+",
    "addition_suffix": "+}"
}

# Initialize logger
logger = get_logger(__name__)


def parse_ai_response(response_text: str, original_text: str) -> list:
    """Parses the raw AI response text into structured suggestion objects

    Args:
        response_text (str): Raw AI response text
        original_text (str): Original text

    Returns:
        list: List of structured suggestion objects
    """
    # Extract suggestion segments using regex pattern matching for track changes format
    pattern = re.compile(r'(\[-.*?-\]|\{+.*?+\})')
    segments = pattern.split(response_text)

    suggestions = []
    position = 0
    for segment in segments:
        if not segment:
            continue

        # Identify the original and suggested text portions
        deletion_match = re.match(r'\\[-(.*?)-\\]', segment)
        addition_match = re.match(r'\\{+(.*?)+\\}', segment)

        if deletion_match:
            original_snippet = deletion_match.group(1)
            suggested_snippet = ""
        elif addition_match:
            original_snippet = ""
            suggested_snippet = addition_match.group(1)
        else:
            original_snippet = segment
            suggested_snippet = segment

        # Find the position of each suggestion in the original document
        start_index = original_text.find(original_snippet, position)
        if start_index == -1:
            logger.warning(f"Could not find snippet in original text: {original_snippet}")
            continue

        # Create structured suggestion objects with positions and content
        suggestion = {
            "original_text": original_snippet,
            "suggested_text": suggested_snippet,
            "position": start_index
        }
        position = start_index + len(original_snippet)

        # Generate unique suggestion IDs
        suggestion_id = generate_suggestion_id(original_snippet, suggested_snippet, start_index)
        suggestion["id"] = suggestion_id

        suggestions.append(suggestion)

    # Return list of parsed suggestions
    return suggestions


def validate_suggestions(suggestions: list, original_text: str) -> list:
    """Validates generated suggestions for quality and correctness

    Args:
        suggestions (list): List of suggestions
        original_text (str): Original text

    Returns:
        list: Filtered list of valid suggestions
    """
    # Remove duplicate suggestions
    unique_suggestions = []
    seen = set()
    for suggestion in suggestions:
        suggestion_tuple = (suggestion["original_text"], suggestion["suggested_text"], suggestion["position"])
        if suggestion_tuple not in seen:
            unique_suggestions.append(suggestion)
            seen.add(suggestion_tuple)

    # Filter out suggestions where original text doesn't match document at specified position
    valid_suggestions = []
    for suggestion in unique_suggestions:
        start_index = suggestion["position"]
        original_snippet = suggestion["original_text"]
        if original_text[start_index:start_index + len(original_snippet)] == original_snippet:
            valid_suggestions.append(suggestion)
        else:
            logger.warning(f"Suggestion validation failed: original text mismatch at position {start_index}")

    # Filter out suggestions with minimal or no changes
    meaningful_suggestions = [s for s in valid_suggestions if s["original_text"] != s["suggested_text"]]

    # Filter out suggestions that would create invalid document structure
    # (e.g., unbalanced brackets, invalid HTML)
    # TODO: Implement structural validation

    # Log validation statistics
    total_suggestions = len(suggestions)
    valid_count = len(meaningful_suggestions)
    logger.info(f"Suggestion validation: {valid_count}/{total_suggestions} valid suggestions")

    # Return filtered list of valid suggestions
    return meaningful_suggestions


def extract_suggestion_explanation(response_text: str, original_snippet: str, suggested_snippet: str) -> str:
    """Extracts explanation for a specific suggestion from AI response

    Args:
        response_text (str): Full AI response text
        original_snippet (str): Original text snippet
        suggested_snippet (str): Suggested text snippet

    Returns:
        str: Explanation text for the suggestion
    """
    # Look for explicit explanation in response using regex patterns
    pattern = re.compile(f".*{re.escape(original_snippet)}.*{re.escape(suggested_snippet)}.*Explanation:(.*)", re.DOTALL)
    match = pattern.search(response_text)

    if match:
        # Extract and return the explanation
        explanation = match.group(1).strip()
        return explanation

    # If not found, generate a generic explanation based on the changes
    explanation = f"The text was changed from '{original_snippet}' to '{suggested_snippet}' to improve the writing."
    return explanation


def generate_suggestion_id(original_text: str, suggested_text: str, position: int) -> str:
    """Generates a unique identifier for a suggestion

    Args:
        original_text (str): Original text
        suggested_text (str): Suggested text
        position (int): Position of the suggestion in the document

    Returns:
        str: Unique suggestion identifier
    """
    # Create a hash of the original text, suggested text, and position
    hash_input = f"{original_text}-{suggested_text}-{position}"
    hash_value = uuid.uuid5(uuid.NAMESPACE_DNS, hash_input).hex

    # Combine with a UUID to ensure uniqueness
    suggestion_id = f"suggestion-{hash_value}"

    # Return formatted suggestion ID
    return suggestion_id


def get_suggestion_type_description(suggestion_type: str) -> str:
    """Returns the description for a suggestion type

    Args:
        suggestion_type (str): Suggestion type

    Returns:
        str: Description of the suggestion type
    """
    # Look up suggestion type in SUGGESTION_TYPES dictionary
    if suggestion_type in SUGGESTION_TYPES:
        return SUGGESTION_TYPES[suggestion_type]

    # Return a default description if not found
    return "Improve the writing"


class SuggestionGenerationError(Exception):
    """Exception raised when suggestion generation fails"""

    def __init__(self, message: str, error_type: str):
        """Initialize the exception with error details

        Args:
            message (str): Error message
            error_type (str): Type of error
        """
        # Call parent Exception constructor with message
        super().__init__(message)
        # Store error_type for categorization
        self.error_type = error_type


class SuggestionGenerator:
    """Main service for generating AI-powered writing improvement suggestions"""

    def __init__(
        self,
        openai_service: OpenAIService,
        prompt_manager: PromptManager,
        token_optimizer: TokenOptimizer,
        context_manager: ContextManager,
        diff_service: DiffService,
        ai_interaction_repository: AIInteractionRepository
    ):
        """Initialize the suggestion generator with required dependencies

        Args:
            openai_service (OpenAIService): OpenAI service instance
            prompt_manager (PromptManager): Prompt manager instance
            token_optimizer (TokenOptimizer): Token optimizer instance
            context_manager (ContextManager): Context manager instance
            diff_service (DiffService): Diff service instance
            ai_interaction_repository (AIInteractionRepository): AI interaction repository instance
        """
        # Store service dependencies as instance variables
        self._openai_service = openai_service
        self._prompt_manager = prompt_manager
        self._token_optimizer = token_optimizer
        self._context_manager = context_manager
        self._diff_service = diff_service
        self._interaction_repository = ai_interaction_repository
        # Initialize logger
        self.logger = logger
        # Validate required dependencies
        if not all([openai_service, prompt_manager, token_optimizer, context_manager, diff_service, ai_interaction_repository]):
            raise ValueError("All dependencies must be provided")

    def generate_suggestions(self, document_content: str, prompt_type: str, options: dict, session_id: str) -> dict:
        """Generates writing improvement suggestions for a document

        Args:
            document_content (str): Document text
            prompt_type (str): Suggestion type
            options (dict): Options
            session_id (str): Session ID

        Returns:
            dict: Response containing generated suggestions
        """
        # Start performance timer
        start_time = time.time()

        # Log suggestion request
        self.logger.info(f"Generating suggestions for prompt type: {prompt_type}")

        # Parse options for customizations (max_tokens, template_id, custom_prompt)
        max_tokens = options.get("max_tokens", DEFAULT_MAX_TOKENS)
        template_id = options.get("template_id")
        custom_prompt = options.get("custom_prompt")

        # Handle document selection if provided in options
        focused_content = document_content
        is_selection = False
        selection_metadata = {}
        if "selection" in options:
            focused_content, is_selection, selection_metadata = self.handle_selection_context(document_content, options["selection"])

        # Create appropriate prompt using prompt_manager
        prompt = self._prompt_manager.create_suggestion_prompt(
            document_content=focused_content,
            template_identifier=template_id,
            parameters={"custom_prompt": custom_prompt, "prompt_type": prompt_type}
        )

        # Optimize document context using context_manager if needed
        # (This might involve trimming the context or summarizing it)
        # optimized_content = self._context_manager.optimize_document_context(document_content)

        # Send request to OpenAI via openai_service
        try:
            ai_response = self._openai_service.get_suggestions(
                document_content=focused_content,
                prompt=prompt,
                parameters={"max_tokens": max_tokens}
            )
        except Exception as e:
            raise SuggestionGenerationError(str(e), "OpenAIError")

        # Parse AI response into structured suggestions
        suggestions = parse_ai_response(ai_response["choices"][0]["message"]["content"], focused_content)

        # Validate suggestions to ensure quality and correctness
        valid_suggestions = validate_suggestions(suggestions, focused_content)

        # Reintegrate suggestions for selected text back into the full document context
        if is_selection:
            valid_suggestions = self.reintegrate_suggestions(valid_suggestions, selection_metadata, document_content)

        # Apply diff processing to create track changes format
        diff_result = self._diff_service.compare_texts(focused_content, ai_response["choices"][0]["message"]["content"])
        formatted_suggestions = self._diff_service.format_for_display(diff_result, "track_changes")

        # Log interaction for analytics via interaction_repository
        processing_time = time.time() - start_time
        self._interaction_repository.log_suggestion_interaction(
            session_id=session_id,
            prompt_type=prompt_type,
            suggestion_count=len(valid_suggestions),
            processing_time=processing_time,
            metadata={"ai_model": ai_response["model"]}
        )

        # Calculate processing time
        processing_time = time.time() - start_time

        # Return formatted response with suggestions, metadata, and processing time
        return self.format_response(valid_suggestions, str(uuid.uuid4()), str(uuid.uuid4()), prompt, processing_time, {"ai_model": ai_response["model"]})

    def generate_batch_suggestions(self, requests: list, process_in_parallel: bool, batch_options: dict) -> list:
        """Processes multiple suggestion requests in batch for efficiency

        Args:
            requests (list): List of suggestion requests
            process_in_parallel (bool): Whether to process requests in parallel
            batch_options (dict): Batch processing options

        Returns:
            list: List of suggestion responses for each request
        """
        # Validate batch request parameters
        if not isinstance(requests, list):
            raise ValueError("Requests must be a list")

        if not isinstance(process_in_parallel, bool):
            raise ValueError("process_in_parallel must be a boolean")

        if not isinstance(batch_options, dict):
            raise ValueError("batch_options must be a dict")

        # Group similar requests using token_optimizer.detect_similar_request
        # Process each unique request or group
        # If process_in_parallel is True, use concurrent processing with MAX_CONCURRENCY limit
        # Otherwise process sequentially
        # For each grouped request, adapt the suggestions to each original request
        # Log batch processing statistics
        # Return list of responses corresponding to original requests
        raise NotImplementedError

    def create_suggestion_from_text(self, original_text: str, modified_text: str, suggestion_type: str) -> list:
        """Creates structured suggestion objects from original and modified text

        Args:
            original_text (str): Original text
            modified_text (str): Modified text
            suggestion_type (str): Suggestion type

        Returns:
            list: List of structured suggestion objects
        """
        # Generate diff between original and modified text using diff_service
        diff_result = self._diff_service.compare_texts(original_text, modified_text)

        # Convert diffs to suggestion format
        suggestions = self._diff_service.create_suggestion_from_diff(diff_result)

        # Add metadata like suggestion_type and explanations
        for suggestion in suggestions:
            suggestion["suggestion_type"] = suggestion_type
            suggestion["explanation"] = extract_suggestion_explanation(
                "", suggestion["original_text"], suggestion["suggested_text"]
            )

        # Generate unique IDs for each suggestion
        for suggestion in suggestions:
            suggestion["id"] = generate_suggestion_id(
                suggestion["original_text"], suggestion["suggested_text"], suggestion["position"]
            )

        # Return list of suggestion objects
        return suggestions

    def add_diff_information(self, suggestions: list, original_text: str) -> list:
        """Enhances suggestions with detailed diff information for track changes display

        Args:
            suggestions (list): List of suggestions
            original_text (str): Original text

        Returns:
            list: Enhanced suggestions with diff information
        """
        # For each suggestion, extract original and suggested text
        # Generate detailed diff using diff_service.compare_texts
        # Format diff for display using diff_service.format_for_display
        # Add diff information to suggestion objects
        # Return enhanced suggestions
        raise NotImplementedError

    def handle_selection_context(self, document_content: str, selection: dict) -> tuple:
        """Process document selection to focus suggestions on selected text

        Args:
            document_content (str): The entire document content
            selection (dict): Dictionary containing selection details (start, end)

        Returns:
            tuple: (focused_content, is_selection, selection_metadata)
        """
        # Check if selection parameters are provided
        if not selection or not isinstance(selection, dict):
            return document_content, False, {}

        start = selection.get("start")
        end = selection.get("end")

        # If selection exists, extract the selected portion of the document
        if start is not None and end is not None and isinstance(start, int) and isinstance(end, int):
            if start < 0 or end > len(document_content) or start >= end:
                self.logger.warning(f"Invalid selection range: start={start}, end={end}, document length={len(document_content)}")
                return document_content, False, {}

            selected_content = document_content[start:end]

            # Capture context around selection for better AI understanding
            context_before = document_content[:start][-100:]  # 100 characters before
            context_after = document_content[end:][:100]  # 100 characters after

            # Create metadata about selection for later reintegration
            selection_metadata = {
                "start": start,
                "end": end,
                "context_before": context_before,
                "context_after": context_after
            }

            # Return focused content and selection information
            return selected_content, True, selection_metadata

        return document_content, False, {}

    def reintegrate_suggestions(self, suggestions: list, selection_metadata: dict, full_document: str) -> list:
        """Reintegrates suggestions for selected text back into the full document context

        Args:
            suggestions (list): List of suggestions
            selection_metadata (dict): Metadata about the selection
            full_document (str): The full document content

        Returns:
            list: Suggestions with positions adjusted for the full document
        """
        # Adjust suggestion position offsets based on selection location in full document
        start_offset = selection_metadata.get("start", 0)

        adjusted_suggestions = []
        for suggestion in suggestions:
            original_snippet = suggestion["original_text"]
            adjusted_position = suggestion["position"] + start_offset

            # Verify suggestions still match original text at adjusted positions
            if full_document[adjusted_position:adjusted_position + len(original_snippet)] == original_snippet:
                suggestion["position"] = adjusted_position
                adjusted_suggestions.append(suggestion)
            else:
                self.logger.warning(f"Suggestion no longer matches original text after reintegration. Skipping suggestion.")

        # Filter out invalid suggestions that don't match after reintegration
        # Return adjusted suggestions
        return adjusted_suggestions

    def get_supported_suggestion_types(self) -> dict:
        """Returns the list of supported suggestion types

        Returns:
            dict: Dictionary of suggestion types and their descriptions
        """
        # Return the SUGGESTION_TYPES dictionary
        return SUGGESTION_TYPES

    def format_response(self, suggestions: list, request_id: str, document_id: str, prompt_used: str, processing_time: float, metadata: dict) -> dict:
        """Formats the suggestion results into a standardized response object

        Args:
            suggestions (list): List of suggestions
            request_id (str): Request identifier
            document_id (str): Document identifier
            prompt_used (str): Prompt used to generate suggestions
            processing_time (float): Processing time
            metadata (dict): Metadata

        Returns:
            dict: Formatted response object
        """
        # Create response dictionary with standard fields
        response = {
            "request_id": request_id,
            "document_id": document_id,
            "suggestions": suggestions,
            "prompt_used": prompt_used,
            "processing_time": processing_time,
            "metadata": metadata
        }

        # Add suggestions list
        # Add metadata about the request and processing
        # Add processing time
        # Return formatted response
        return response