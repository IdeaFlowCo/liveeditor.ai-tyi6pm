"""
Core service that provides integration with OpenAI's API for AI-powered writing enhancements,
suggestion generation, and chat functionality. Implements intelligent request handling,
error management, performance monitoring, and token optimization to efficiently leverage
language models.
"""

import json
import time
import typing
import asyncio
import aiohttp
from typing import Any, Dict, List, Optional, Union, Generator, Tuple

import openai  # openai ^1.0.0

from .token_optimizer import TokenOptimizer, count_tokens, optimize_prompt
from ...core.utils.logger import get_logger
from ...core.utils.validators import validate_prompt
from ...data.redis.caching_service import cache_set, cache_get, get_content_hash_key

# Configuration constants
DEFAULT_MODEL = "gpt-4"
FALLBACK_MODEL = "gpt-3.5-turbo"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 4096
DEFAULT_REQUEST_TIMEOUT = 30
RETRY_ATTEMPTS = 3
RETRY_BACKOFF = 2.0
RESPONSE_CACHE_TTL = 3600  # 1 hour
CACHE_PREFIX = "openai:response:"
STREAMING_CHUNK_SIZE = 100

# Initialize logger
logger = get_logger(__name__)


def generate_cache_key(model: str, prompt: str, parameters: Dict) -> str:
    """
    Generates a cache key for storing and retrieving OpenAI API responses.
    
    Args:
        model: The model name
        prompt: The input prompt
        parameters: Additional parameters that affect the response
        
    Returns:
        A unique cache key for the combination of inputs
    """
    # Generate a hash based on the model, prompt, and parameters
    content_hash = get_content_hash_key(f"{model}:{prompt}:{json.dumps(parameters, sort_keys=True)}")
    return f"{CACHE_PREFIX}{content_hash}"


def handle_api_error(error: Exception) -> Tuple[str, bool]:
    """
    Handles and categorizes errors from the OpenAI API.
    
    Args:
        error: The exception raised during the API call
        
    Returns:
        A tuple of (error message, is_retriable)
    """
    error_message = str(error)
    is_retriable = False
    
    logger.error(f"OpenAI API error: {error_message}")
    
    # OpenAI API specific error handling
    if isinstance(error, openai.APIError):
        is_retriable = True
        return "OpenAI API returned an error. Please try again.", is_retriable
    elif isinstance(error, openai.APIConnectionError):
        is_retriable = True
        return "Connection to OpenAI API failed. Please check your internet connection and try again.", is_retriable
    elif isinstance(error, openai.RateLimitError):
        is_retriable = True
        return "Rate limit exceeded. Please try again later.", is_retriable
    elif isinstance(error, openai.APITimeoutError):
        is_retriable = True
        return "Request to OpenAI API timed out. Please try again.", is_retriable
    elif isinstance(error, openai.AuthenticationError):
        return "Authentication to OpenAI API failed. Please check your API key.", is_retriable
    elif isinstance(error, openai.BadRequestError):
        # Check for token limit errors
        if "maximum context length" in error_message.lower() or "token" in error_message.lower():
            is_retriable = True  # Might be retriable with token optimization
            return "The input was too long for the AI model. Try with a shorter text.", is_retriable
        return "Invalid request to OpenAI API. Please check your input.", is_retriable
    elif isinstance(error, openai.PermissionDeniedError):
        return "You don't have permission to use this OpenAI model or feature.", is_retriable
    elif isinstance(error, openai.NotFoundError):
        return "The requested OpenAI resource was not found.", is_retriable
    elif isinstance(error, asyncio.TimeoutError):
        is_retriable = True
        return "The request to OpenAI timed out. Please try again.", is_retriable
    else:
        return f"An unexpected error occurred: {error_message}", is_retriable


def sanitize_response(response: Dict) -> str:
    """
    Sanitizes and validates the response from OpenAI API.
    
    Args:
        response: The raw API response
        
    Returns:
        Cleaned and validated response text
    """
    try:
        # Extract the content from the response
        if "choices" in response and len(response["choices"]) > 0:
            if "message" in response["choices"][0]:
                # Handle chat completions
                message = response["choices"][0]["message"]
                if "content" in message and message["content"]:
                    return message["content"].strip()
            elif "text" in response["choices"][0]:
                # Handle completions
                return response["choices"][0]["text"].strip()
        
        # If we couldn't extract content in the expected format
        logger.warning(f"Unexpected response format from OpenAI API: {response}")
        
        # Attempt to extract any text from choices as a fallback
        if "choices" in response and len(response["choices"]) > 0:
            choice = response["choices"][0]
            for key in ["message", "text", "content"]:
                if key in choice:
                    value = choice[key]
                    if isinstance(value, dict) and "content" in value:
                        return value["content"].strip()
                    elif isinstance(value, str):
                        return value.strip()
        
        # If all else fails, return a default message
        return "Unable to extract a valid response from the AI model."
    
    except Exception as e:
        logger.error(f"Error sanitizing OpenAI response: {str(e)}")
        return "Error processing AI response."


class OpenAIService:
    """
    Service that interfaces with OpenAI API to provide AI capabilities for the writing enhancement platform.
    """
    
    def __init__(
        self,
        api_key: str,
        default_model: str = DEFAULT_MODEL,
        fallback_model: str = FALLBACK_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        request_timeout: int = DEFAULT_REQUEST_TIMEOUT,
        use_cache: bool = True
    ):
        """
        Initialize OpenAI service with configuration parameters.
        
        Args:
            api_key: OpenAI API key
            default_model: Default model to use
            fallback_model: Fallback model when primary is unavailable
            max_tokens: Maximum tokens for completions
            temperature: Randomness of completions (0.0 to 1.0)
            request_timeout: Timeout for API requests in seconds
            use_cache: Whether to cache responses
        """
        self._api_key = api_key
        self._default_model = default_model
        self._fallback_model = fallback_model
        self._default_max_tokens = max_tokens
        self._default_temperature = temperature
        self._request_timeout = request_timeout
        self._use_cache = use_cache
        
        # Initialize OpenAI client
        self._openai_client = openai.OpenAI(api_key=api_key)
        
        # Initialize token optimizer
        self._token_optimizer = TokenOptimizer(default_model, max_tokens, use_cache)
        
        # Initialize performance metrics
        self._performance_metrics = {
            "request_count": 0,
            "success_count": 0,
            "error_count": 0,
            "cache_hit_count": 0,
            "cache_miss_count": 0,
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_latency": 0,
            "errors": {},
            "models": {}
        }
        
        logger.info(f"OpenAIService initialized with model {default_model} (fallback: {fallback_model})")
        
        # Validate API key is set
        if not api_key:
            logger.warning("OpenAI API key is not set. AI features will not work.")
    
    def get_suggestions(
        self,
        document_content: str,
        prompt: str,
        parameters: Dict = None
    ) -> Dict:
        """
        Generates writing improvement suggestions based on document content and prompt.
        
        Args:
            document_content: The document text to improve
            prompt: The improvement instruction prompt
            parameters: Additional parameters for the API call
            
        Returns:
            OpenAI API response with suggestions
        """
        # Use empty dict if parameters is None
        parameters = parameters or {}
        
        # Validate inputs
        if not document_content:
            logger.error("Empty document content provided to get_suggestions")
            raise ValueError("Document content cannot be empty")
            
        if not prompt:
            logger.error("Empty prompt provided to get_suggestions")
            raise ValueError("Prompt cannot be empty")
        
        # Validate prompt format and safety
        if not validate_prompt(prompt):
            logger.warning(f"Invalid prompt format: {prompt}")
            raise ValueError("Invalid prompt format or content")
        
        # Check cache for similar requests
        if self._use_cache:
            model = parameters.get("model", self._default_model)
            cached_response = self.get_cached_response(model, prompt, parameters)
            if cached_response:
                logger.info("Using cached OpenAI response")
                self._performance_metrics["cache_hit_count"] += 1
                return cached_response
            else:
                self._performance_metrics["cache_miss_count"] += 1
        
        # Prepare parameters for API call
        api_params = {
            "model": parameters.get("model", self._default_model),
            "temperature": parameters.get("temperature", self._default_temperature),
            "max_tokens": parameters.get("max_tokens", self._default_max_tokens),
            "n": parameters.get("n", 1),
            "presence_penalty": parameters.get("presence_penalty", 0.0),
            "frequency_penalty": parameters.get("frequency_penalty", 0.0),
        }
        
        # Optimize the prompt with token considerations
        optimized_prompt = self._token_optimizer.optimize_prompt(
            prompt=prompt,
            content=document_content,
            max_tokens=api_params["max_tokens"],
            reserved_tokens=1000  # Reserve tokens for the completion
        )
        
        try:
            # Send request to OpenAI
            response = self.send_request(
                model=api_params["model"],
                prompt_or_messages=[{"role": "user", "content": optimized_prompt}],
                parameters=api_params,
                is_chat=True
            )
            
            # Cache successful response
            if self._use_cache:
                self.cache_response(api_params["model"], prompt, parameters, response)
            
            return response
            
        except Exception as e:
            error_message, is_retriable = handle_api_error(e)
            
            # Try fallback model if appropriate
            if is_retriable and api_params["model"] != self._fallback_model:
                logger.warning(f"Retrying with fallback model {self._fallback_model}")
                try:
                    # Update model to fallback
                    api_params["model"] = self._fallback_model
                    
                    # Re-optimize prompt for fallback model if needed
                    fallback_optimizer = TokenOptimizer(
                        self._fallback_model, 
                        api_params["max_tokens"],
                        self._use_cache
                    )
                    optimized_prompt = fallback_optimizer.optimize_prompt(
                        prompt=prompt,
                        content=document_content,
                        max_tokens=api_params["max_tokens"],
                        reserved_tokens=1000
                    )
                    
                    # Send request with fallback model
                    response = self.send_request(
                        model=self._fallback_model,
                        prompt_or_messages=[{"role": "user", "content": optimized_prompt}],
                        parameters=api_params,
                        is_chat=True
                    )
                    
                    # Cache successful fallback response
                    if self._use_cache:
                        self.cache_response(self._fallback_model, prompt, parameters, response)
                    
                    return response
                    
                except Exception as fallback_error:
                    # If fallback also fails, raise the original error
                    logger.error(f"Fallback model also failed: {str(fallback_error)}")
                    raise ValueError(error_message) from e
            else:
                # If not retriable or already using fallback, raise error
                raise ValueError(error_message) from e
    
    def get_chat_response(
        self,
        messages: List[Dict],
        parameters: Dict = None,
        streaming: bool = False
    ) -> Union[Dict, Generator]:
        """
        Generates a chat response for interactive conversations.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            parameters: Additional parameters for the API call
            streaming: Whether to stream the response
            
        Returns:
            Chat completion response or streaming generator
        """
        # Use empty dict if parameters is None
        parameters = parameters or {}
        
        # Validate inputs
        if not messages or not isinstance(messages, list):
            logger.error("Invalid messages provided to get_chat_response")
            raise ValueError("Messages must be a non-empty list")
        
        for msg in messages:
            if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
                logger.error(f"Invalid message format: {msg}")
                raise ValueError("Each message must be a dict with 'role' and 'content' keys")
        
        # Return streaming response if requested
        if streaming:
            return self.stream_response(messages, parameters)
        
        # Prepare parameters for API call
        api_params = {
            "model": parameters.get("model", self._default_model),
            "temperature": parameters.get("temperature", self._default_temperature),
            "max_tokens": parameters.get("max_tokens", self._default_max_tokens),
            "n": parameters.get("n", 1),
            "presence_penalty": parameters.get("presence_penalty", 0.0),
            "frequency_penalty": parameters.get("frequency_penalty", 0.0),
            "stream": False
        }
        
        try:
            # Send request to OpenAI
            response = self.send_request(
                model=api_params["model"],
                prompt_or_messages=messages,
                parameters=api_params,
                is_chat=True
            )
            
            return response
            
        except Exception as e:
            error_message, is_retriable = handle_api_error(e)
            
            # Try fallback model if appropriate
            if is_retriable and api_params["model"] != self._fallback_model:
                logger.warning(f"Retrying chat with fallback model {self._fallback_model}")
                try:
                    # Update model to fallback
                    api_params["model"] = self._fallback_model
                    
                    # Send request with fallback model
                    return self.send_request(
                        model=self._fallback_model,
                        prompt_or_messages=messages,
                        parameters=api_params,
                        is_chat=True
                    )
                    
                except Exception as fallback_error:
                    # If fallback also fails, raise the original error
                    logger.error(f"Fallback model also failed: {str(fallback_error)}")
                    raise ValueError(error_message) from e
            else:
                # If not retriable or already using fallback, raise error
                raise ValueError(error_message) from e
    
    def stream_response(
        self,
        messages: List[Dict],
        parameters: Dict = None
    ) -> Generator:
        """
        Creates a generator that streams the OpenAI response in chunks.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            parameters: Additional parameters for the API call
            
        Returns:
            Generator yielding response chunks
        """
        # Use empty dict if parameters is None
        parameters = parameters or {}
        
        # Prepare parameters for API call
        api_params = {
            "model": parameters.get("model", self._default_model),
            "temperature": parameters.get("temperature", self._default_temperature),
            "max_tokens": parameters.get("max_tokens", self._default_max_tokens),
            "n": parameters.get("n", 1),
            "presence_penalty": parameters.get("presence_penalty", 0.0),
            "frequency_penalty": parameters.get("frequency_penalty", 0.0),
            "stream": True
        }
        
        async def async_generator():
            try:
                # Get start time for metrics
                start_time = time.time()
                
                # Create async client
                async_client = openai.AsyncOpenAI(api_key=self._api_key)
                
                # Send streaming request
                stream = await async_client.chat.completions.create(
                    model=api_params["model"],
                    messages=messages,
                    temperature=api_params["temperature"],
                    max_tokens=api_params["max_tokens"],
                    n=api_params["n"],
                    presence_penalty=api_params["presence_penalty"],
                    frequency_penalty=api_params["frequency_penalty"],
                    stream=True
                )
                
                content_buffer = ""
                
                # Process each chunk
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                        content_piece = chunk.choices[0].delta.content
                        content_buffer += content_piece
                        
                        # Buffer chunks for more efficient transmission
                        if len(content_buffer) >= STREAMING_CHUNK_SIZE:
                            yield {"content": content_buffer, "done": False}
                            content_buffer = ""
                
                # Yield any remaining content
                if content_buffer:
                    yield {"content": content_buffer, "done": False}
                
                # Signal completion
                yield {"content": "", "done": True}
                
                # Update metrics
                duration = time.time() - start_time
                self._performance_metrics["request_count"] += 1
                self._performance_metrics["success_count"] += 1
                self._performance_metrics["total_latency"] += duration
                
                # Update model-specific metrics
                model = api_params["model"]
                if model not in self._performance_metrics["models"]:
                    self._performance_metrics["models"][model] = {
                        "request_count": 0,
                        "total_tokens": 0,
                        "total_latency": 0
                    }
                self._performance_metrics["models"][model]["request_count"] += 1
                self._performance_metrics["models"][model]["total_latency"] += duration
                
            except Exception as e:
                error_message, _ = handle_api_error(e)
                self._performance_metrics["error_count"] += 1
                
                # Add to error metrics
                error_type = type(e).__name__
                if error_type not in self._performance_metrics["errors"]:
                    self._performance_metrics["errors"][error_type] = 0
                self._performance_metrics["errors"][error_type] += 1
                
                # Yield error message
                yield {"error": error_message, "done": True}
        
        # Create a wrapper generator that runs the async generator
        def sync_generator():
            loop = asyncio.new_event_loop()
            async_gen = async_generator()
            
            try:
                while True:
                    try:
                        yield loop.run_until_complete(async_gen.__anext__())
                    except StopAsyncIteration:
                        break
            finally:
                loop.close()
        
        return sync_generator()
    
    def send_request(
        self,
        model: str,
        prompt_or_messages: Union[str, List[Dict]],
        parameters: Dict,
        is_chat: bool = True
    ) -> Dict:
        """
        Sends a request to the OpenAI API with retry logic.
        
        Args:
            model: The model to use
            prompt_or_messages: The prompt string or list of message dicts
            parameters: Additional parameters for the API call
            is_chat: Whether to use chat completions API
            
        Returns:
            The API response
        """
        # Track request metrics
        start_time = time.time()
        self._performance_metrics["request_count"] += 1
        
        # Initialize retry counter
        retry_count = 0
        last_error = None
        
        # Implement retry logic with exponential backoff
        while retry_count <= RETRY_ATTEMPTS:
            try:
                if retry_count > 0:
                    logger.info(f"Retrying OpenAI request (attempt {retry_count}/{RETRY_ATTEMPTS})")
                
                if is_chat:
                    # Use chat completions API
                    response = self._openai_client.chat.completions.create(
                        model=model,
                        messages=prompt_or_messages,
                        temperature=parameters.get("temperature", self._default_temperature),
                        max_tokens=parameters.get("max_tokens", self._default_max_tokens),
                        n=parameters.get("n", 1),
                        presence_penalty=parameters.get("presence_penalty", 0.0),
                        frequency_penalty=parameters.get("frequency_penalty", 0.0),
                        timeout=self._request_timeout,
                        stream=parameters.get("stream", False)
                    )
                else:
                    # Use completions API (legacy)
                    response = self._openai_client.completions.create(
                        model=model,
                        prompt=prompt_or_messages,
                        temperature=parameters.get("temperature", self._default_temperature),
                        max_tokens=parameters.get("max_tokens", self._default_max_tokens),
                        n=parameters.get("n", 1),
                        presence_penalty=parameters.get("presence_penalty", 0.0),
                        frequency_penalty=parameters.get("frequency_penalty", 0.0),
                        timeout=self._request_timeout,
                        stream=parameters.get("stream", False)
                    )
                
                # Convert response object to dict
                response_dict = response.model_dump()
                
                # Update performance metrics
                duration = time.time() - start_time
                self._performance_metrics["success_count"] += 1
                self._performance_metrics["total_latency"] += duration
                
                # Update token usage metrics
                if "usage" in response_dict:
                    prompt_tokens = response_dict["usage"].get("prompt_tokens", 0)
                    completion_tokens = response_dict["usage"].get("completion_tokens", 0)
                    total_tokens = response_dict["usage"].get("total_tokens", 0)
                    
                    self.update_token_metrics(model, prompt_tokens, completion_tokens, total_tokens)
                
                # Update model-specific metrics
                if model not in self._performance_metrics["models"]:
                    self._performance_metrics["models"][model] = {
                        "request_count": 0,
                        "total_tokens": 0,
                        "total_latency": 0
                    }
                self._performance_metrics["models"][model]["request_count"] += 1
                self._performance_metrics["models"][model]["total_latency"] += duration
                
                return response_dict
                
            except Exception as e:
                # Record error
                last_error = e
                self._performance_metrics["error_count"] += 1
                
                # Add to error metrics
                error_type = type(e).__name__
                if error_type not in self._performance_metrics["errors"]:
                    self._performance_metrics["errors"][error_type] = 0
                self._performance_metrics["errors"][error_type] += 1
                
                # Check if the error is retriable
                error_message, is_retriable = handle_api_error(e)
                
                if is_retriable and retry_count < RETRY_ATTEMPTS:
                    # Exponential backoff
                    backoff_time = RETRY_BACKOFF ** retry_count
                    logger.warning(f"Retriable error occurred: {error_message}. Retrying in {backoff_time}s")
                    time.sleep(backoff_time)
                    retry_count += 1
                else:
                    # Non-retriable error or max retries reached
                    break
        
        # If we get here, all retries failed
        if last_error:
            error_message, _ = handle_api_error(last_error)
            raise ValueError(f"OpenAI API request failed after {retry_count} retries: {error_message}") from last_error
        else:
            raise ValueError("OpenAI API request failed with an unknown error")
    
    def cache_response(
        self,
        model: str,
        prompt: str,
        parameters: Dict,
        response: Dict
    ) -> bool:
        """
        Caches OpenAI API response for future reuse.
        
        Args:
            model: The model used
            prompt: The input prompt
            parameters: Parameters used for the request
            response: The API response to cache
            
        Returns:
            True if successfully cached, False otherwise
        """
        if not self._use_cache:
            return False
        
        try:
            cache_key = generate_cache_key(model, prompt, parameters)
            
            # Only cache successful responses
            if "choices" in response and len(response["choices"]) > 0:
                cache_set(cache_key, response, RESPONSE_CACHE_TTL)
                logger.debug(f"Cached OpenAI response with key {cache_key}")
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Failed to cache OpenAI response: {str(e)}")
            return False
    
    def get_cached_response(
        self,
        model: str,
        prompt: str,
        parameters: Dict
    ) -> Optional[Dict]:
        """
        Retrieves cached response for a similar request.
        
        Args:
            model: The model name
            prompt: The input prompt
            parameters: Additional parameters
            
        Returns:
            Cached response or None if not found
        """
        if not self._use_cache:
            return None
        
        try:
            cache_key = generate_cache_key(model, prompt, parameters)
            cached_data = cache_get(cache_key)
            
            if cached_data:
                logger.debug(f"Cache hit for key {cache_key}")
                return cached_data
            
            logger.debug(f"Cache miss for key {cache_key}")
            return None
            
        except Exception as e:
            logger.warning(f"Error retrieving cached response: {str(e)}")
            return None
    
    def get_performance_metrics(self) -> Dict:
        """
        Returns performance metrics for OpenAI API usage.
        
        Returns:
            Dictionary of metrics including request counts, latencies, token usage, and error rates
        """
        metrics = self._performance_metrics.copy()
        
        # Calculate average latency
        if metrics["success_count"] > 0:
            metrics["average_latency"] = metrics["total_latency"] / metrics["success_count"]
        else:
            metrics["average_latency"] = 0
        
        # Calculate error rate
        if metrics["request_count"] > 0:
            metrics["error_rate"] = metrics["error_count"] / metrics["request_count"]
        else:
            metrics["error_rate"] = 0
        
        # Calculate cache hit rate
        cache_requests = metrics["cache_hit_count"] + metrics["cache_miss_count"]
        if cache_requests > 0:
            metrics["cache_hit_rate"] = metrics["cache_hit_count"] / cache_requests
        else:
            metrics["cache_hit_rate"] = 0
        
        # Add average tokens per request
        if metrics["success_count"] > 0:
            metrics["average_tokens_per_request"] = metrics["total_tokens"] / metrics["success_count"]
        else:
            metrics["average_tokens_per_request"] = 0
        
        # Add timestamp
        metrics["timestamp"] = time.time()
        
        return metrics
    
    def health_check(self) -> Dict:
        """
        Performs a health check on the OpenAI API connection.
        
        Returns:
            Health status including availability, latency, and connection details
        """
        start_time = time.time()
        health_status = {
            "status": "unknown",
            "latency_ms": 0,
            "model": self._default_model,
            "api_key_configured": bool(self._api_key),
            "timestamp": time.time()
        }
        
        if not self._api_key:
            health_status["status"] = "failed"
            health_status["message"] = "OpenAI API key not configured"
            return health_status
        
        try:
            # Make a minimal API call to check connectivity
            response = self._openai_client.chat.completions.create(
                model=self._default_model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5,
                temperature=0,
                timeout=5
            )
            
            # Calculate latency
            duration = time.time() - start_time
            health_status["latency_ms"] = int(duration * 1000)
            
            # Check if we got a valid response
            if response and hasattr(response, "choices") and len(response.choices) > 0:
                health_status["status"] = "ok"
                health_status["message"] = "OpenAI API is available"
            else:
                health_status["status"] = "degraded"
                health_status["message"] = "OpenAI API returned an unexpected response"
            
            return health_status
            
        except Exception as e:
            # Calculate latency even for failures
            duration = time.time() - start_time
            health_status["latency_ms"] = int(duration * 1000)
            
            # Update status based on error
            health_status["status"] = "failed"
            health_status["message"] = str(e)
            
            return health_status
    
    def reset_metrics(self) -> None:
        """
        Resets performance metrics tracking.
        """
        self._performance_metrics = {
            "request_count": 0,
            "success_count": 0,
            "error_count": 0,
            "cache_hit_count": 0,
            "cache_miss_count": 0,
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_latency": 0,
            "errors": {},
            "models": {}
        }
        logger.info("OpenAI performance metrics reset")
    
    def handle_token_limit_exceeded(
        self,
        model: str,
        prompt: str,
        parameters: Dict
    ) -> Dict:
        """
        Manages cases where token limits are exceeded.
        
        Args:
            model: The model that exceeded token limits
            prompt: The input prompt
            parameters: Request parameters
            
        Returns:
            Fallback response or error details
        """
        logger.warning(f"Token limit exceeded for model {model}. Attempting fallback strategies.")
        
        # Try fallback model
        if model != self._fallback_model:
            try:
                logger.info(f"Trying fallback model {self._fallback_model}")
                
                # Update parameters with fallback model
                fallback_params = parameters.copy()
                fallback_params["model"] = self._fallback_model
                
                # Use chat completions API
                response = self._openai_client.chat.completions.create(
                    model=self._fallback_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=fallback_params.get("temperature", self._default_temperature),
                    max_tokens=fallback_params.get("max_tokens", self._default_max_tokens),
                    timeout=self._request_timeout
                )
                
                # Convert response object to dict
                return response.model_dump()
                
            except Exception as e:
                logger.error(f"Fallback model also failed: {str(e)}")
        
        # If fallback model failed or we were already using it, try truncating the prompt
        try:
            # Determine how much to truncate
            current_model = self._fallback_model if model != self._fallback_model else model
            token_count = count_tokens(prompt)
            max_tokens = parameters.get("max_tokens", self._default_max_tokens)
            
            # Aim for 75% of the maximum (leaving room for response)
            target_tokens = int(max_tokens * 0.75)
            
            if token_count > target_tokens:
                truncated_prompt = optimize_prompt(prompt, "", target_tokens)
                
                logger.info(f"Truncated prompt from {token_count} to approximately {target_tokens} tokens")
                
                # Use chat completions API with truncated prompt
                response = self._openai_client.chat.completions.create(
                    model=current_model,
                    messages=[{"role": "user", "content": truncated_prompt}],
                    temperature=parameters.get("temperature", self._default_temperature),
                    max_tokens=parameters.get("max_tokens", self._default_max_tokens),
                    timeout=self._request_timeout
                )
                
                # Convert response object to dict
                return response.model_dump()
            
        except Exception as e:
            logger.error(f"Prompt truncation strategy failed: {str(e)}")
        
        # If all strategies fail, return error response
        return {
            "error": True,
            "message": "The input was too large for the AI model and all fallback strategies failed. Please reduce the size of your input."
        }
    
    def update_token_metrics(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int
    ) -> None:
        """
        Records token usage metrics for monitoring and optimization.
        
        Args:
            model: The model used
            prompt_tokens: Number of tokens in the prompt
            completion_tokens: Number of tokens in the completion
            total_tokens: Total tokens used
        """
        # Update global token counts
        self._performance_metrics["prompt_tokens"] += prompt_tokens
        self._performance_metrics["completion_tokens"] += completion_tokens
        self._performance_metrics["total_tokens"] += total_tokens
        
        # Update model-specific token counts
        if model not in self._performance_metrics["models"]:
            self._performance_metrics["models"][model] = {
                "request_count": 0,
                "total_tokens": 0,
                "total_latency": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0
            }
        
        model_metrics = self._performance_metrics["models"][model]
        model_metrics["total_tokens"] = model_metrics.get("total_tokens", 0) + total_tokens
        model_metrics["prompt_tokens"] = model_metrics.get("prompt_tokens", 0) + prompt_tokens
        model_metrics["completion_tokens"] = model_metrics.get("completion_tokens", 0) + completion_tokens
        
        logger.debug(
            f"Token usage for model {model}: {prompt_tokens} prompt, "
            f"{completion_tokens} completion, {total_tokens} total"
        )