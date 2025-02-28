"""Defines the Flask Blueprint for AI-powered writing suggestion endpoints, enabling users to request contextual improvements for their documents with support for template-based prompts and custom requests. Provides routes for generating suggestions, retrieving templates, and integrates with track changes functionality."""

import time  # Measuring processing time for metrics
import uuid  # Generate unique identifiers for requests

from flask import Blueprint, request, jsonify, g  # Flask framework
from src.backend.core.ai.suggestion_generator import SuggestionGenerator  # Core service that generates AI suggestions
from src.backend.core.ai.prompt_manager import PromptManager  # Manages prompt templates for suggestions
from src.backend.core.ai.token_optimizer import TokenOptimizer  # Optimizes content to reduce token usage
from src.backend.data.mongodb.repositories.ai_interaction_repository import AIInteractionRepository  # Stores AI interaction data for analytics
from src.backend.api.schemas.suggestion_schema import suggestion_request_schema, suggestion_with_diff_schema  # Validates suggestion requests
from src.backend.api.middleware.auth_middleware import auth_required, get_current_user_id, is_anonymous_session  # Authentication middleware
from src.backend.api.middleware.rate_limiter import rate_limit  # Rate limits API calls
from src.backend.core.utils.logger import get_logger  # Configures logging for API endpoints

# Create a Blueprint for suggestion routes
suggestions_bp = Blueprint('suggestions', __name__, url_prefix='/api/suggestions')

# Initialize logger
logger = get_logger(__name__)

# Initialize core services
suggestion_generator = SuggestionGenerator()
prompt_manager = PromptManager()
token_optimizer = TokenOptimizer()
ai_interaction_repo = AIInteractionRepository()

# Define rate limits for anonymous and authenticated users
AI_SUGGESTION_ANONYMOUS_LIMIT = 10
AI_SUGGESTION_AUTHENTICATED_LIMIT = 50


@suggestions_bp.route('/templates', methods=['GET'])
@auth_required(allow_anonymous=True)
def get_suggestion_templates():
    """Retrieves available suggestion templates for the client"""
    # Get user ID from auth context or anonymous session ID
    user_id = get_current_user_id() if not is_anonymous_session() else "anonymous"

    # Log request for template retrieval
    logger.info(f"Request for suggestion templates from user: {user_id}")

    # Retrieve available templates from prompt_manager
    templates = prompt_manager.get_templates()

    # Organize templates by category for better client presentation
    templates_by_category = {}
    for template in templates:
        category = template.get('category', 'uncategorized')
        if category not in templates_by_category:
            templates_by_category[category] = []
        templates_by_category[category].append(template)

    # Add metadata about frequently used templates if user has history
    # TODO: Implement usage tracking and add metadata

    # Return the templates as a JSON response
    return jsonify(templates_by_category)


@suggestions_bp.route('/types', methods=['GET'])
@auth_required(allow_anonymous=True)
def get_suggestion_types():
    """Retrieves available suggestion types and their descriptions"""
    # Log request for suggestion types
    logger.info("Request for suggestion types")

    # Retrieve supported suggestion types from suggestion_generator
    suggestion_types = suggestion_generator.get_supported_suggestion_types()

    # Format types with descriptions and examples
    # TODO: Add examples to suggestion types

    # Return types dictionary as JSON response
    return jsonify(suggestion_types)


@suggestions_bp.route('/text', methods=['POST'])
@auth_required(allow_anonymous=True)
@rate_limit(limit_anonymous=AI_SUGGESTION_ANONYMOUS_LIMIT, limit_authenticated=AI_SUGGESTION_AUTHENTICATED_LIMIT)
def generate_text_suggestions():
    """Processes document content and generates text improvement suggestions"""
    # Start timing for performance metrics
    start_time = time.time()

    # Log suggestion request
    logger.info("Request for text suggestions")

    # Validate request data using suggestion_request_schema
    try:
        request_data = suggestion_request_schema.load(request.get_json())
    except Exception as e:
        logger.warning(f"Invalid request data: {str(e)}")
        return jsonify({"error": "invalid_request", "message": str(e)}), 400

    # Extract user ID from auth context or anonymous session ID
    user_id = get_current_user_id() if not is_anonymous_session() else "anonymous"

    # Extract document content, selection range, and prompt information
    document_content = request_data.get('document_content', '')
    selection = request_data.get('selection')
    template_id = request_data.get('template_id')
    custom_prompt = request_data.get('custom_prompt')
    suggestion_type = request_data.get('suggestion_type', 'general')
    session_id = request_data.get('session_id', str(uuid.uuid4()))

    # Optimize token usage with token_optimizer if needed
    # TODO: Implement token optimization

    # Generate request ID for tracking
    request_id = str(uuid.uuid4())

    # Call suggestion_generator.generate_suggestions with parameters
    try:
        suggestions = suggestion_generator.generate_suggestions(
            document_content=document_content,
            prompt_type=suggestion_type,
            options={'template_id': template_id, 'custom_prompt': custom_prompt, 'selection': selection},
            session_id=session_id
        )
    except Exception as e:
        logger.error(f"Error generating suggestions: {str(e)}")
        return jsonify({"error": "ai_error", "message": str(e)}), 500

    # Format suggestions with track changes information using suggestion_with_diff_schema
    try:
        formatted_suggestions = suggestion_with_diff_schema.dump(suggestions)
    except Exception as e:
        logger.error(f"Error formatting suggestions: {str(e)}")
        return jsonify({"error": "formatting_error", "message": str(e)}), 500

    # Log interaction data to ai_interaction_repo for analytics
    try:
        ai_interaction_repo.log_suggestion_interaction(
            session_id=session_id,
            user_id=user_id,
            document_id=request_data.get('document_id'),
            prompt_type=suggestion_type,
            custom_prompt=custom_prompt,
            suggestion_count=len(suggestions.get('suggestions', [])),
            processing_time=time.time() - start_time,
            metadata={'request_id': request_id}
        )
    except Exception as e:
        logger.warning(f"Error logging interaction: {str(e)}")

    # Calculate and log processing time
    processing_time = time.time() - start_time
    logger.info(f"Generated text suggestions in {processing_time:.4f} seconds", request_id=request_id)

    # Return formatted suggestions as JSON response with metadata
    return jsonify(formatted_suggestions)


@suggestions_bp.route('/style', methods=['POST'])
@auth_required(allow_anonymous=True)
@rate_limit(limit_anonymous=AI_SUGGESTION_ANONYMOUS_LIMIT, limit_authenticated=AI_SUGGESTION_AUTHENTICATED_LIMIT)
def generate_style_suggestions():
    """Processes document content and generates style-focused improvement suggestions"""
    # Start timing for performance metrics
    start_time = time.time()

    # Log style suggestion request
    logger.info("Request for style suggestions")

    # Validate request data using suggestion_request_schema
    try:
        request_data = suggestion_request_schema.load(request.get_json())
    except Exception as e:
        logger.warning(f"Invalid request data: {str(e)}")
        return jsonify({"error": "invalid_request", "message": str(e)}), 400

    # Extract user ID from auth context or anonymous session ID
    user_id = get_current_user_id() if not is_anonymous_session() else "anonymous"

    # Extract document content, selection range, and style parameters
    document_content = request_data.get('document_content', '')
    selection = request_data.get('selection')
    template_id = request_data.get('template_id')
    custom_prompt = request_data.get('custom_prompt')
    suggestion_type = request_data.get('suggestion_type', 'style')
    session_id = request_data.get('session_id', str(uuid.uuid4()))

    # Optimize token usage with token_optimizer if needed
    # TODO: Implement token optimization

    # Generate request ID for tracking
    request_id = str(uuid.uuid4())

    # Call suggestion_generator.generate_suggestions with style focus
    try:
        suggestions = suggestion_generator.generate_suggestions(
            document_content=document_content,
            prompt_type=suggestion_type,
            options={'template_id': template_id, 'custom_prompt': custom_prompt, 'selection': selection},
            session_id=session_id
        )
    except Exception as e:
        logger.error(f"Error generating style suggestions: {str(e)}")
        return jsonify({"error": "ai_error", "message": str(e)}), 500

    # Format suggestions with track changes information
    try:
        formatted_suggestions = suggestion_with_diff_schema.dump(suggestions)
    except Exception as e:
        logger.error(f"Error formatting style suggestions: {str(e)}")
        return jsonify({"error": "formatting_error", "message": str(e)}), 500

    # Log interaction data to ai_interaction_repo for analytics
    try:
        ai_interaction_repo.log_suggestion_interaction(
            session_id=session_id,
            user_id=user_id,
            document_id=request_data.get('document_id'),
            prompt_type=suggestion_type,
            custom_prompt=custom_prompt,
            suggestion_count=len(suggestions.get('suggestions', [])),
            processing_time=time.time() - start_time,
            metadata={'request_id': request_id}
        )
    except Exception as e:
        logger.warning(f"Error logging style interaction: {str(e)}")

    # Calculate and log processing time
    processing_time = time.time() - start_time
    logger.info(f"Generated style suggestions in {processing_time:.4f} seconds", request_id=request_id)

    # Return formatted style suggestions as JSON response with metadata
    return jsonify(formatted_suggestions)


@suggestions_bp.route('/grammar', methods=['POST'])
@auth_required(allow_anonymous=True)
@rate_limit(limit_anonymous=AI_SUGGESTION_ANONYMOUS_LIMIT, limit_authenticated=AI_SUGGESTION_AUTHENTICATED_LIMIT)
def generate_grammar_suggestions():
    """Processes document content and generates grammar-focused improvement suggestions"""
    # Start timing for performance metrics
    start_time = time.time()

    # Log grammar suggestion request
    logger.info("Request for grammar suggestions")

    # Validate request data using suggestion_request_schema
    try:
        request_data = suggestion_request_schema.load(request.get_json())
    except Exception as e:
        logger.warning(f"Invalid request data: {str(e)}")
        return jsonify({"error": "invalid_request", "message": str(e)}), 400

    # Extract user ID from auth context or anonymous session ID
    user_id = get_current_user_id() if not is_anonymous_session() else "anonymous"

    # Extract document content, selection range, and language preferences
    document_content = request_data.get('document_content', '')
    selection = request_data.get('selection')
    template_id = request_data.get('template_id')
    custom_prompt = request_data.get('custom_prompt')
    suggestion_type = request_data.get('suggestion_type', 'grammar')
    session_id = request_data.get('session_id', str(uuid.uuid4()))

    # Optimize token usage with token_optimizer if needed
    # TODO: Implement token optimization

    # Generate request ID for tracking
    request_id = str(uuid.uuid4())

    # Call suggestion_generator.generate_suggestions with grammar focus
    try:
        suggestions = suggestion_generator.generate_suggestions(
            document_content=document_content,
            prompt_type=suggestion_type,
            options={'template_id': template_id, 'custom_prompt': custom_prompt, 'selection': selection},
            session_id=session_id
        )
    except Exception as e:
        logger.error(f"Error generating grammar suggestions: {str(e)}")
        return jsonify({"error": "ai_error", "message": str(e)}), 500

    # Format suggestions with track changes information
    try:
        formatted_suggestions = suggestion_with_diff_schema.dump(suggestions)
    except Exception as e:
        logger.error(f"Error formatting grammar suggestions: {str(e)}")
        return jsonify({"error": "formatting_error", "message": str(e)}), 500

    # Log interaction data to ai_interaction_repo for analytics
    try:
        ai_interaction_repo.log_suggestion_interaction(
            session_id=session_id,
            user_id=user_id,
            document_id=request_data.get('document_id'),
            prompt_type=suggestion_type,
            custom_prompt=custom_prompt,
            suggestion_count=len(suggestions.get('suggestions', [])),
            processing_time=time.time() - start_time,
            metadata={'request_id': request_id}
        )
    except Exception as e:
        logger.warning(f"Error logging grammar interaction: {str(e)}")

    # Calculate and log processing time
    processing_time = time.time() - start_time
    logger.info(f"Generated grammar suggestions in {processing_time:.4f} seconds", request_id=request_id)

    # Return formatted grammar suggestions as JSON response with metadata
    return jsonify(formatted_suggestions)


@suggestions_bp.errorhandler(Exception)
def handle_error(error):
    """Error handler for the suggestions blueprint"""
    # Log the error details with contextual information
    logger.error(f"Unhandled exception: {str(error)}", exc_info=True)

    # Determine appropriate status code based on error type
    status_code = 500
    if isinstance(error, ValueError):
        status_code = 400
    # TODO: Add more specific error handling for different exception types

    # Format user-friendly error message
    error_message = "An unexpected error occurred"
    if hasattr(error, 'message'):
        error_message = error.message

    # For validation errors, include specific field issues
    error_details = {}
    if hasattr(error, 'errors'):
        error_details = error.errors

    # For AI service errors, provide appropriate fallback message
    # TODO: Implement AI service error handling

    # Include request ID if available for tracking
    request_id = getattr(g, 'request_id', 'N/A')

    # Return error response as JSON with status code
    return jsonify({
        "error": "server_error",
        "message": error_message,
        "details": error_details,
        "request_id": request_id
    }), status_code