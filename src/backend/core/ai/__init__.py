"""
Initialization file for the AI module that exposes the core AI components for the writing enhancement platform,
including OpenAI integration, token optimization, context management, prompt handling, chat processing, and suggestion generation.
"""

import typing  # Type hints for improved code documentation - typing standard library

from .openai_service import OpenAIService  # Provides integration with the OpenAI API for AI processing
from .token_optimizer import TokenOptimizer  # Optimizes token usage for AI requests to reduce costs and improve performance
from .prompt_manager import PromptManager  # Manages predefined and custom prompts for AI interactions
from .context_manager import ContextManager  # Maintains document context during AI processing
from .chat_processor import ChatProcessor  # Processes chat interactions between users and the AI assistant
from .suggestion_generator import SuggestionGenerator  # Generates document improvement suggestions based on AI analysis
from ...core.utils.logger import get_logger  # For logging AI module operations

__version__ = "0.1.0"  # Version information for the AI module
DEFAULT_MODEL = "gpt-4"  # Default AI model to use (gpt-4)
FALLBACK_MODEL = "gpt-3.5-turbo"  # Fallback AI model when primary is unavailable (gpt-3.5-turbo)

logger = get_logger(__name__)  # Initialize logger for this module

__all__ = [  # Exported items
    "OpenAIService",  # Core service for interacting with OpenAI API
    "TokenOptimizer",  # Optimizes token usage for efficient AI interactions
    "PromptManager",  # Manages AI prompts and templates for various improvement types
    "ContextManager",  # Maintains document and conversation context for AI interactions
    "ChatProcessor",  # Processes chat interactions between users and the AI assistant
    "SuggestionGenerator",  # Generates document improvement suggestions
    "DEFAULT_MODEL",  # Default AI model to use (gpt-4)
    "FALLBACK_MODEL",  # Fallback AI model when primary is unavailable (gpt-3.5-turbo)
    "__version__"  # Version information for the AI module
]