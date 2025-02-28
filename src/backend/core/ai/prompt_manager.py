"""
Core module that manages the creation, formatting, and optimization of prompts for AI interactions in the writing enhancement platform.
Handles both predefined template prompts and custom user prompts, ensuring optimal token usage and effective context management for high-quality AI suggestions.
"""

import json  # JSON serialization/deserialization for prompt data
import re  # Regular expressions for prompt processing
import time  # Performance timing for prompt operations
from typing import Dict, List, Optional  # Type hints for improved code documentation

from .context_manager import ContextManager  # Manage document and conversation context for AI prompts
from .token_optimizer import TokenOptimizer  # Optimize token usage in prompts and manage context windows
from ..templates.template_service import TemplateService  # Retrieve and manage prompt templates
from ...core.utils.logger import get_logger  # Configure logging for the prompt manager
from ...core.utils import validators  # Validate prompt inputs
from ...data.redis.caching_service import cache_set, cache_get, get_content_hash_key  # Caching formatted prompts to improve performance

# Constants
DEFAULT_SYSTEM_PROMPT = "You are an AI writing assistant that helps improve written content. Your suggestions should be clear, concise, and improve the overall quality of the text while maintaining the author's voice and intent."
IMPROVEMENT_INSTRUCTION = "Provide improvements in a track changes format. Use [-original text-] for deletions and {+suggested text+} for additions."
TRACK_CHANGES_FORMAT = "Use track changes format: [-deleted text-]{+added text+}"
DEFAULT_MAX_TOKENS = 4000
PROMPT_CACHE_TTL = 3600
PROMPT_CACHE_PREFIX = "prompt_manager:"

# Initialize logger
logger = get_logger(__name__)


def generate_cache_key(template_id: str, parameters: Dict) -> str:
    """Generates a cache key for storing and retrieving formatted prompts

    Args:
        template_id (str): Template identifier
        parameters (dict): Parameters used to format the template

    Returns:
        str: Unique cache key for the prompt
    """
    # Use get_content_hash_key to generate a hash of the template_id and parameters
    content_hash = get_content_hash_key(template_id + json.dumps(parameters, sort_keys=True))
    # Prefix with PROMPT_CACHE_PREFIX for namespacing
    cache_key = f"{PROMPT_CACHE_PREFIX}{content_hash}"
    # Return the formatted cache key
    return cache_key


def format_variable_placeholder(variable_name: str) -> str:
    """Formats a variable placeholder for insertion into a template

    Args:
        variable_name (str): Name of the variable

    Returns:
        str: Formatted placeholder string
    """
    # Return the variable name wrapped in curly braces with format specifier
    return f'{{{variable_name}}}'


def extract_variables_from_template(template_text: str) -> List[str]:
    """Extracts variable placeholders from a template string

    Args:
        template_text (str): Template string

    Returns:
        list: List of variable names found in the template
    """
    # Use regular expression to find all placeholders in the template
    placeholders = re.findall(r'\{(.*?)\}', template_text)
    # Extract variable names from the matches
    variable_names = [match.strip() for match in placeholders]
    # Return list of unique variable names
    return list(set(variable_names))


def sanitize_prompt_parameters(parameters: Dict) -> Dict:
    """Sanitizes user-provided parameters for safe insertion into prompts

    Args:
        parameters (dict): Dictionary of parameters

    Returns:
        dict: Sanitized parameters
    """
    # Create a copy of the parameters dictionary
    sanitized_parameters = parameters.copy()
    # Sanitize each parameter to prevent prompt injection
    for key, value in sanitized_parameters.items():
        if isinstance(value, str):
            # Remove any potentially dangerous sequences
            sanitized_value = value.replace("{{", "").replace("}}", "")
            sanitized_parameters[key] = sanitized_value
    # Return sanitized parameter dictionary
    return sanitized_parameters


class PromptManager:
    """Manages the creation, formatting, and optimization of prompts for AI interactions"""

    def __init__(
        self,
        template_service: TemplateService,
        token_optimizer: TokenOptimizer,
        context_manager: ContextManager,
        use_cache: bool = True,
        cache_ttl: int = PROMPT_CACHE_TTL
    ):
        """Initializes the prompt manager with required dependencies

        Args:
            template_service (TemplateService): Service for retrieving templates
            token_optimizer (TokenOptimizer): Optimizer for managing token usage
            context_manager (ContextManager): Manages conversation context
            use_cache (bool): Whether to use caching for prompts
            cache_ttl (int): Time-to-live for cached prompts
        """
        # Store dependencies as instance variables
        self._template_service = template_service
        self._token_optimizer = token_optimizer
        self._context_manager = context_manager
        # Set caching preferences (default: True)
        self._use_cache = use_cache
        # Set cache TTL (default: PROMPT_CACHE_TTL)
        self._cache_ttl = cache_ttl
        # Initialize logger
        self.logger = get_logger(__name__)

    def create_system_prompt(self, custom_instruction: str = None) -> str:
        """Creates the system prompt that defines AI behavior

        Args:
            custom_instruction (str, optional): Custom instruction to append to the default system prompt. Defaults to None.

        Returns:
            str: Formatted system prompt
        """
        # Start with DEFAULT_SYSTEM_PROMPT
        system_prompt = DEFAULT_SYSTEM_PROMPT
        # Append custom instruction if provided
        if custom_instruction:
            system_prompt += f" {custom_instruction}"
        # Add TRACK_CHANGES_FORMAT instruction
        system_prompt += f" {TRACK_CHANGES_FORMAT}"
        # Return complete system prompt
        return system_prompt

    def create_template_prompt(self, template_identifier: str, parameters: Dict, by_id: bool = True) -> str:
        """Creates a prompt using a predefined template

        Args:
            template_identifier (str): Identifier of the template
            parameters (Dict): Parameters to format the template with
            by_id (bool): Whether to retrieve the template by ID or name

        Returns:
            str: Formatted prompt based on template
        """
        # Validate template_identifier is not empty
        if not template_identifier:
            raise ValueError("Template identifier cannot be empty")

        # Check cache for previously formatted prompt if caching enabled
        if self._use_cache:
            cached_prompt = self.get_cached_prompt(template_identifier, parameters)
            if cached_prompt:
                return cached_prompt

        try:
            # Retrieve template using template_service
            if by_id:
                template = self._template_service.get_template_by_id(template_identifier)
            else:
                template = self._template_service.get_template_by_name(template_identifier)

            # If template not found, raise TemplateNotFoundError
            if not template:
                raise PromptTemplateNotFoundError(template_identifier)

            # Extract template text from retrieved template
            template_text = template['promptText']

            # Sanitize parameters to prevent prompt injection
            sanitized_parameters = sanitize_prompt_parameters(parameters)

            # Format template with provided parameters
            formatted_prompt = template_text.format(**sanitized_parameters)

            # Cache formatted prompt if caching enabled
            if self._use_cache:
                self.cache_prompt(template_identifier, parameters, formatted_prompt)

            # Return formatted prompt
            return formatted_prompt
        except KeyError as e:
            raise PromptFormatError(missing_parameters=[str(e)], message="Missing parameters in template")
        except Exception as e:
            self.logger.error(f"Error creating template prompt: {str(e)}")
            raise

    def create_custom_prompt(self, prompt_text: str, parameters: Dict = None) -> str:
        """Creates a prompt from custom user input

        Args:
            prompt_text (str): User-provided prompt text
            parameters (Dict, optional): Parameters to format the prompt with. Defaults to None.

        Returns:
            str: Formatted custom prompt
        """
        # Validate prompt_text using validators.validate_prompt
        if not validators.validate_prompt(prompt_text):
            raise ValueError("Invalid prompt text")

        # Append TRACK_CHANGES_FORMAT instruction if not already present
        if TRACK_CHANGES_FORMAT not in prompt_text:
            prompt_text += f" {TRACK_CHANGES_FORMAT}"

        # Sanitize parameters to prevent prompt injection
        sanitized_parameters = sanitize_prompt_parameters(parameters or {})

        # Format prompt with provided parameters if any
        try:
            formatted_prompt = prompt_text.format(**sanitized_parameters)
        except KeyError as e:
             raise PromptFormatError(missing_parameters=[str(e)], message="Missing parameters in custom prompt")
        except Exception as e:
            self.logger.error(f"Error formatting custom prompt: {str(e)}")
            raise

        # Return formatted custom prompt
        return formatted_prompt

    def optimize_prompt_with_content(self, prompt: str, document_content: str, max_tokens: int = None, reserved_tokens: int = 0) -> str:
        """Optimizes a prompt with document content to fit within token limits

        Args:
            prompt (str): Prompt text
            document_content (str): Document content
            max_tokens (int, optional): Maximum tokens allowed. Defaults to None.
            reserved_tokens (int, optional): Tokens to reserve for the AI's response. Defaults to 0.

        Returns:
            str: Optimized prompt with content
        """
        # Set default max_tokens if not provided
        if max_tokens is None:
            max_tokens = DEFAULT_MAX_TOKENS

        # Count tokens in prompt to determine available space
        prompt_tokens = self._token_optimizer.count_tokens(prompt)

        # Use token_optimizer to optimize the prompt and document content together
        optimized_prompt = self._token_optimizer.optimize_prompt(
            prompt=prompt,
            content=document_content,
            max_tokens=max_tokens,
            reserved_tokens=reserved_tokens
        )

        # Return optimized prompt that fits within token limits
        return optimized_prompt

    def create_chat_prompt(self, messages: List, system_instruction: str = None, document_content: str = None) -> List:
        """Creates a prompt for chat interactions, incorporating conversation history

        Args:
            messages (List): List of previous messages in the conversation
            system_instruction (str, optional): Custom instruction for the AI. Defaults to None.
            document_content (str, optional): Document content to provide context. Defaults to None.

        Returns:
            List: Formatted chat messages array
        """
        # Create system message with default behavior and provided instruction
        system_message = self.create_system_prompt(system_instruction)

        # If document_content provided, optimize it using context_manager
        if document_content:
            document_content = self._context_manager.optimize_document_context(document_content)
            system_message += f"\n\nDocument Context: {document_content}"

        # Format user and assistant messages in OpenAI chat format
        chat_messages = [{"role": "system", "content": system_message}]
        for msg in messages:
            chat_messages.append({"role": msg["role"], "content": msg["content"]})

        # Check total token count and trim if necessary
        total_tokens = self._token_optimizer.count_tokens("".join([m["content"] for m in chat_messages]))
        if total_tokens > DEFAULT_MAX_TOKENS:
            self.logger.warning(f"Chat messages exceed token limit: {total_tokens} tokens")
            # Implement trimming logic here if needed

        # Return formatted chat messages array
        return chat_messages

    def create_suggestion_prompt(self, document_content: str, template_identifier: str = None, parameters: Dict = None, by_id: bool = True) -> str:
        """Creates a prompt specifically for generating writing improvement suggestions

        Args:
            document_content (str): Document content to improve
            template_identifier (str, optional): Identifier of the template to use. Defaults to None.
            parameters (Dict, optional): Parameters to format the template with. Defaults to None.
            by_id (bool): Whether to retrieve the template by ID or name

        Returns:
            str: Complete suggestion prompt
        """
        # Determine if using template or custom prompt
        if template_identifier:
            # If template_identifier provided, get template prompt
            prompt = self.create_template_prompt(template_identifier, parameters or {}, by_id=by_id)
        elif parameters and "custom_prompt" in parameters:
            # If parameters contains custom_prompt, use that instead
            prompt = self.create_custom_prompt(parameters["custom_prompt"], parameters)
        else:
            raise ValueError("Either template_identifier or custom_prompt must be provided")

        # Add improvement instructions if not already included
        if IMPROVEMENT_INSTRUCTION not in prompt:
            prompt += f" {IMPROVEMENT_INSTRUCTION}"

        # Optimize prompt with document content using token_optimizer
        optimized_prompt = self.optimize_prompt_with_content(prompt, document_content)

        # Return complete suggestion prompt optimized for token usage
        return optimized_prompt

    def get_cached_prompt(self, template_id: str, parameters: Dict) -> Optional[str]:
        """Retrieves a cached prompt if available

        Args:
            template_id (str): Template identifier
            parameters (Dict): Parameters used to format the template

        Returns:
            Optional[str]: Cached prompt or None if not found
        """
        # If caching disabled, return None
        if not self._use_cache:
            return None

        # Generate cache key from template_id and parameters
        cache_key = generate_cache_key(template_id, parameters)

        # Attempt to retrieve from cache
        cached_prompt = cache_get(cache_key)

        # Log cache hit/miss
        if cached_prompt:
            self.logger.debug(f"Cache hit for prompt: {cache_key}")
        else:
            self.logger.debug(f"Cache miss for prompt: {cache_key}")

        # Return cached prompt or None if not found
        return cached_prompt

    def cache_prompt(self, template_id: str, parameters: Dict, formatted_prompt: str) -> bool:
        """Caches a formatted prompt for future reuse

        Args:
            template_id (str): Template identifier
            parameters (Dict): Parameters used to format the template
            formatted_prompt (str): Formatted prompt to cache

        Returns:
            bool: Success status
        """
        # If caching disabled, return False
        if not self._use_cache:
            return False

        # Generate cache key from template_id and parameters
        cache_key = generate_cache_key(template_id, parameters)

        # Store prompt in cache with TTL
        success = cache_set(cache_key, formatted_prompt, self._cache_ttl)

        # Log caching operation
        if success:
            self.logger.debug(f"Cached prompt: {cache_key}")
        else:
            self.logger.warning(f"Failed to cache prompt: {cache_key}")

        # Return success status
        return success

    def estimate_tokens(self, prompt: str, document_content: str) -> Dict:
        """Estimates the token count for a prompt and document combination

        Args:
            prompt (str): Prompt text
            document_content (str): Document content

        Returns:
            Dict: Token count information including prompt, document, and total tokens
        """
        # Use token_optimizer to count tokens in prompt
        prompt_tokens = self._token_optimizer.count_tokens(prompt)
        # Use token_optimizer to count tokens in document_content
        document_tokens = self._token_optimizer.count_tokens(document_content)
        # Calculate total combined tokens
        total_tokens = prompt_tokens + document_tokens
        # Return dictionary with prompt_tokens, document_tokens, and total_tokens
        return {
            "prompt_tokens": prompt_tokens,
            "document_tokens": document_tokens,
            "total_tokens": total_tokens
        }

    def get_conversation_prompt(self, session_id: str, conversation_id: str, user_message: str, max_tokens: int = DEFAULT_MAX_TOKENS) -> Dict:
        """Formats a conversation with context for AI interactions

        Args:
            session_id (str): Session identifier
            conversation_id (str): Conversation identifier
            user_message (str): User's message
            max_tokens (int, optional): Maximum tokens allowed. Defaults to DEFAULT_MAX_TOKENS.

        Returns:
            Dict: Conversation context in AI-ready format
        """
        # Retrieve conversation context using context_manager
        context = self._context_manager.get_context(session_id, conversation_id)
        if not context:
            raise ContextNotFoundError(session_id, conversation_id)

        # Add user message to conversation context
        context = self._context_manager.add_message_to_context(session_id, conversation_id, "user", user_message)

        # Use context_manager.prepare_context_for_ai to format for AI service
        ai_messages = self._context_manager.prepare_context_for_ai(context, max_tokens)

        # Apply token optimization if needed
        # (This might involve trimming the context or summarizing it)

        # Return AI-ready conversation context
        return ai_messages


class PromptTemplateNotFoundError(Exception):
    """Exception raised when a prompt template cannot be found"""

    def __init__(self, template_identifier: str, message: str = None):
        """Initializes the exception with template identifier

        Args:
            template_identifier (str): Identifier of the template
            message (str, optional): Custom error message. Defaults to None.
        """
        # Set default message if none provided
        if message is None:
            message = f"Prompt template not found: {template_identifier}"
        # Call parent Exception constructor with message
        super().__init__(message)
        # Store template_identifier for reference
        self.template_identifier = template_identifier


class PromptFormatError(Exception):
    """Exception raised when a prompt cannot be properly formatted"""

    def __init__(self, missing_parameters: List[str], message: str = None):
        """Initializes the exception with formatting details

        Args:
            missing_parameters (List[str]): List of missing parameter names
            message (str, optional): Custom error message. Defaults to None.
        """
        # Set default message if none provided
        if message is None:
            message = f"Missing parameters in prompt format: {missing_parameters}"
        # Call parent Exception constructor with message
        super().__init__(message)
        # Store missing_parameters list for reference
        self.missing_parameters = missing_parameters