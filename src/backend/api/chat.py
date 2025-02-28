# flask v2.3.0 - Web framework for creating web applications and APIs
from flask import Blueprint, current_app
# flask_restful 0.3.9 - Extension for building RESTful APIs with Flask
from flask_restful import Api

# Internal imports
from .resources.chat_resource import ChatResource  # RESTful resource for chat functionality
from ..core.ai.chat_processor import ChatProcessor  # Core service for processing chat interactions
from ..core.ai.openai_service import OpenAIService  # Service for interacting with OpenAI API
from ..core.ai.context_manager import ContextManager  # Manages conversation context for AI interactions
from ..core.ai.prompt_manager import PromptManager  # Manages prompt templates and formatting
from ..core.ai.token_optimizer import TokenOptimizer  # Optimizes token usage for AI requests
from ..data.mongodb.repositories.ai_interaction_repository import AIInteractionRepository  # Repository for storing AI interaction data
from ..data.redis.rate_limiter import RateLimiter  # Rate limiting service for API requests
from ..core.utils.logger import get_logger  # Configure logging for the chat API module

# Create a Flask Blueprint for the chat API
chat_bp = Blueprint('chat', __name__)
# Create a Flask-RESTful API instance
chat_api = Api(chat_bp)
# Configure logger
logger = get_logger(__name__)


def initialize_dependencies() -> dict:
    """Initializes and configures all dependencies required for the chat API

    Returns:
        dict: Dictionary of initialized service instances
    """
    # Initialize OpenAIService with configuration from current_app
    openai_service = OpenAIService(
        api_key=current_app.config['OPENAI_API_KEY'],
        default_model=current_app.config['OPENAI_DEFAULT_MODEL'],
        fallback_model=current_app.config['OPENAI_FALLBACK_MODEL'],
        max_tokens=current_app.config['OPENAI_MAX_TOKENS'],
        temperature=current_app.config['OPENAI_TEMPERATURE'],
        request_timeout=current_app.config['OPENAI_REQUEST_TIMEOUT'],
        use_cache=current_app.config['OPENAI_USE_CACHE']
    )
    # Initialize ContextManager for conversation context
    context_manager = ContextManager()
    # Initialize TokenOptimizer for efficient token usage
    token_optimizer = TokenOptimizer()
    # Initialize PromptManager with templates
    prompt_manager = PromptManager()
    # Initialize AIInteractionRepository for storing interactions
    ai_interaction_repository = AIInteractionRepository()
    # Initialize RateLimiter for request rate limiting
    rate_limiter = RateLimiter()
    # Initialize ChatProcessor with all related services
    chat_processor = ChatProcessor(
        openai_service=openai_service,
        context_manager=context_manager,
        token_optimizer=token_optimizer,
        prompt_manager=prompt_manager,
        repository=ai_interaction_repository
    )

    # Return dictionary containing all initialized services
    return {
        "chat_processor": chat_processor,
        "ai_interaction_repository": ai_interaction_repository,
        "rate_limiter": rate_limiter
    }


def register_routes(services: dict) -> None:
    """Registers all chat-related routes with the API

    Args:
        services (dict): Dictionary of initialized service instances
    """
    # Extract required services from services dictionary
    chat_processor = services["chat_processor"]
    ai_interaction_repository = services["ai_interaction_repository"]
    rate_limiter = services["rate_limiter"]

    # Initialize ChatResource with services
    chat_resource = ChatResource(
        chat_processor=chat_processor,
        ai_interaction_repository=ai_interaction_repository,
        rate_limiter=rate_limiter
    )

    # Register ChatResource with chat_api at '/chat' endpoint
    chat_api.add_resource(chat_resource, '/chat')
    # Register streaming endpoint at '/chat/stream'
    chat_api.add_resource(chat_resource, '/chat/stream')
    # Register history endpoint at '/chat/history'
    chat_api.add_resource(chat_resource, '/chat/history')

    # Log successful route registration
    logger.info("Chat API routes registered successfully")


# Export the Flask Blueprint for chat API routes
__all__ = ['chat_bp']