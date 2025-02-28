"""
RESTful API resource for handling chat interactions with the AI assistant, providing endpoints for sending messages and retrieving conversation history. Supports both authenticated and anonymous users with appropriate rate limiting.
"""
import uuid  # standard library
import time  # standard library

from flask import request, g, current_app  # Flask ~=2.3.0
from flask_restful import Resource, abort  # flask_restful 0.3.9
from marshmallow import ValidationError  # marshmallow 3.15.0

from ...core.ai.chat_processor import ChatProcessor, sanitize_message  # src/backend/core/ai/chat_processor.py
from ...core.ai.chat_processor import ChatProcessingError
from ..schemas.chat_schema import ChatRequestSchema, ChatResponseSchema, ChatHistorySchema  # src/backend/api/schemas/chat_schema.py
from ...core.utils.logger import get_logger  # src/backend/core/utils/logger.py
from ...core.auth.anonymous_session import get_anonymous_session, get_current_session_id  # src/backend/core/auth/anonymous_session.py
from ..middleware.auth_middleware import get_current_user  # src/backend/api/middleware/auth_middleware.py
from ...data.redis.rate_limiter import RateLimiter, USER_TYPE_ANONYMOUS, USER_TYPE_AUTHENTICATED  # src/backend/data/redis/rate_limiter.py
from ...data.mongodb.repositories.ai_interaction_repository import AIInteractionRepository  # src/backend/data/mongodb/repositories/ai_interaction_repository.py


# Initialize logger
logger = get_logger(__name__)

# Define constants for rate limiting and resource names
CHAT_RESOURCE = "ai_chat"
ANONYMOUS_CHAT_LIMIT = 10
AUTHENTICATED_CHAT_LIMIT = 50
RATE_LIMIT_WINDOW = 60


def get_user_and_session():
    """Extracts user_id and session_id from request context

    Returns:
        Tuple containing (user_id, session_id, user_type)
    """
    user_id = None
    session_id = None
    user_type = USER_TYPE_ANONYMOUS  # Default to anonymous

    # Check if user is authenticated via g.user
    if hasattr(g, 'user') and g.user:
        user_id = str(g.user["_id"])
        user_type = USER_TYPE_AUTHENTICATED
        logger.debug(f"Authenticated user ID: {user_id}")
    else:
        # If not authenticated, get anonymous session_id from cookie or headers
        session_id = get_current_session_id()
        if session_id:
            logger.debug(f"Anonymous session ID: {session_id}")
        else:
            logger.warning("No session ID found for anonymous user")

    return user_id, session_id, user_type


def handle_service_errors(func):
    """Decorator to handle common service layer exceptions"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Validation error: {str(e)}")
            abort(400, error="invalid_request", message=str(e))
        except ChatProcessingError as e:
            logger.error(f"Chat processing error: {str(e)}")
            abort(500, error=e.error_type, message=e.message)
        except Exception as e:
            logger.exception("Unexpected error")
            abort(500, error="internal_server_error", message="An unexpected error occurred")
    return wrapper


class ChatResource(Resource):
    """RESTful resource for handling chat interactions with the AI assistant"""

    def __init__(self, chat_processor: ChatProcessor, ai_interaction_repository: AIInteractionRepository, rate_limiter: RateLimiter):
        """Initialize with required services"""
        self._chat_processor = chat_processor
        self._interaction_repository = ai_interaction_repository
        self._rate_limiter = rate_limiter
        self._request_schema = ChatRequestSchema()
        self._response_schema = ChatResponseSchema()
        self._history_schema = ChatHistorySchema()
        self.logger = get_logger(__name__)

    @handle_service_errors
    def post(self):
        """Process a new chat message and return the AI response"""
        start_time = time.time()

        # Parse and validate request data using ChatRequestSchema
        try:
            request_data = self._request_schema.load(request.get_json())
        except ValidationError as e:
            logger.warning(f"Validation error: {str(e)}")
            abort(400, error="invalid_request", message=str(e))

        # Get user_id, session_id, and user_type from request context
        user_id, session_id, user_type = get_user_and_session()

        # Check rate limits based on user type
        if user_type == USER_TYPE_ANONYMOUS:
            rate_limit = f"{ANONYMOUS_CHAT_LIMIT}/{RATE_LIMIT_WINDOW}"
        else:
            rate_limit = f"{AUTHENTICATED_CHAT_LIMIT}/{RATE_LIMIT_WINDOW}"

        # Generate unique identifier for rate limiting
        rate_limit_identifier = f"{user_type}:{user_id or session_id}:{CHAT_RESOURCE}"

        # Check rate limit
        is_rate_limited, remaining, reset_time = self._rate_limiter.update_rate_limit(
            rate_limit_identifier,
            bucket_size=int(rate_limit.split('/')[0]),
            window_size=int(rate_limit.split('/')[1])
        )

        if is_rate_limited:
            logger.warning(f"Rate limit exceeded for {rate_limit_identifier}")
            abort(429, error="rate_limit_exceeded", message="Rate limit exceeded. Please try again later.",
                  remaining=remaining, reset_time=reset_time)

        # Extract data from validated request
        message = request_data["message"]
        document_id = request_data.get("document_id")
        document_content = request_data.get("document_content")

        # Generate unique conversation_id if not provided in request
        conversation_id = request_data.get("conversation_id")

        # Sanitize user message content
        sanitized_message = sanitize_message(message)

        # Process message with chat processor
        try:
            ai_response = self._chat_processor.process_message(
                message=sanitized_message,
                session_id=session_id,
                conversation_id=conversation_id,
                user_id=user_id,
                document_id=document_id,
                document_content=document_content
            )
        except ChatProcessingError as e:
            logger.error(f"Chat processing error: {str(e)}")
            abort(500, error=e.error_type, message=e.message)
        except Exception as e:
            logger.exception("Unexpected error during chat processing")
            abort(500, error="internal_server_error", message="An unexpected error occurred")

        # Calculate processing time
        processing_time = time.time() - start_time

        # Construct response
        response_data = {
            "message": ai_response["content"],
            "session_id": session_id,
            "suggestions": ai_response.get("suggestions", []),
            "processing_time": processing_time
        }

        # Validate response data
        try:
            response = self._response_schema.dump(response_data)
        except ValidationError as e:
            logger.warning(f"Response validation error: {str(e)}")
            abort(500, error="internal_server_error", message="Failed to format response")

        # Log the interaction for analytics
        self._interaction_repository.log_chat_interaction(
            session_id=session_id,
            user_id=user_id,
            conversation_id=ai_response["conversation_id"],
            message=sanitized_message,
            document_id=document_id,
            processing_time=processing_time,
            metadata={"model": "GPT-4"}
        )

        # Include rate limit information in headers
        headers = {
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time)
        }

        logger.info(f"Chat processed in {processing_time:.2f}s, conversation_id: {ai_response['conversation_id']}")
        return response, 200, headers

    @handle_service_errors
    def get(self):
        """Retrieve chat history for a conversation"""
        # Get user_id, session_id, and user_type from request context
        user_id, session_id, user_type = get_user_and_session()

        # Extract conversation_id from query parameters
        conversation_id = request.args.get("conversation_id")
        if not conversation_id:
            logger.warning("Missing conversation_id parameter")
            abort(400, error="invalid_request", message="conversation_id is required")

        # Verify rate limits (lower priority than posting messages)
        if user_type == USER_TYPE_ANONYMOUS:
            rate_limit = f"{ANONYMOUS_CHAT_LIMIT * 2}/{RATE_LIMIT_WINDOW}"  # Allow twice as many GET requests
        else:
            rate_limit = f"{AUTHENTICATED_CHAT_LIMIT * 2}/{RATE_LIMIT_WINDOW}"

        # Generate unique identifier for rate limiting
        rate_limit_identifier = f"{user_type}:{user_id or session_id}:{CHAT_RESOURCE}:history"

        # Check rate limit
        is_rate_limited, remaining, reset_time = self._rate_limiter.check_rate_limit(
            rate_limit_identifier,
            bucket_size=int(rate_limit.split('/')[0]),
            window_size=int(rate_limit.split('/')[1])
        )

        if is_rate_limited:
            logger.warning(f"Rate limit exceeded for {rate_limit_identifier}")
            abort(429, error="rate_limit_exceeded", message="Rate limit exceeded. Please try again later.",
                  remaining=remaining, reset_time=reset_time)

        # Retrieve conversation history from chat processor
        history = self._chat_processor.get_conversation_history(session_id, conversation_id)

        # Format history using ChatHistorySchema
        response_data = {
            "session_id": session_id,
            "messages": history
        }

        try:
            response = self._history_schema.dump(response_data)
        except ValidationError as e:
            logger.warning(f"History validation error: {str(e)}")
            abort(500, error="internal_server_error", message="Failed to format history")

        # Include rate limit information in headers
        headers = {
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time)
        }

        logger.info(f"Retrieved chat history for conversation_id: {conversation_id}")
        return response, 200, headers

    @handle_service_errors
    def stream(self):
        """Stream an AI response for real-time display"""
        # Parse and validate request data using ChatRequestSchema
        try:
            request_data = self._request_schema.load(request.get_json())
        except ValidationError as e:
            logger.warning(f"Validation error: {str(e)}")
            abort(400, error="invalid_request", message=str(e))

        # Get user_id, session_id, and user_type from request context
        user_id, session_id, user_type = get_user_and_session()

        # Check rate limits based on user type
        if user_type == USER_TYPE_ANONYMOUS:
            rate_limit = f"{ANONYMOUS_CHAT_LIMIT}/{RATE_LIMIT_WINDOW}"
        else:
            rate_limit = f"{AUTHENTICATED_CHAT_LIMIT}/{RATE_LIMIT_WINDOW}"

        # Generate unique identifier for rate limiting
        rate_limit_identifier = f"{user_type}:{user_id or session_id}:{CHAT_RESOURCE}:stream"

        # Check rate limit
        is_rate_limited, remaining, reset_time = self._rate_limiter.update_rate_limit(
            rate_limit_identifier,
            bucket_size=int(rate_limit.split('/')[0]),
            window_size=int(rate_limit.split('/')[1])
        )

        if is_rate_limited:
            logger.warning(f"Rate limit exceeded for {rate_limit_identifier}")
            abort(429, error="rate_limit_exceeded", message="Rate limit exceeded. Please try again later.",
                  remaining=remaining, reset_time=reset_time)

        # Extract data from validated request
        message = request_data["message"]
        document_id = request_data.get("document_id")
        document_content = request_data.get("document_content")

        # Generate unique conversation_id if not provided in request
        conversation_id = request_data.get("conversation_id")

        # Sanitize user message content
        sanitized_message = sanitize_message(message)

        # Set up streaming response with appropriate headers
        def generate():
            try:
                # Stream response using chat processor's stream_response method
                stream = self._chat_processor.stream_response(
                    message=sanitized_message,
                    session_id=session_id,
                    conversation_id=conversation_id,
                    user_id=user_id,
                    document_id=document_id,
                    document_content=document_content
                )

                # Yield each chunk from the stream
                for chunk in stream:
                    yield json.dumps(chunk) + "\n"  # SSE format

                # Log the interaction after streaming completes
                logger.info(f"Streaming completed for conversation_id: {conversation_id}")

            except Exception as e:
                logger.exception("Error during streaming")
                yield json.dumps({"error": str(e), "done": True}) + "\n"

        # Include rate limit information in headers
        headers = {
            "Content-Type": "text/event-stream",  # SSE content type
            "Cache-Control": "no-cache",  # Disable caching
            "Connection": "keep-alive",  # Keep connection alive
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time)
        }

        # Return streaming response
        return current_app.response_class(generate(), mimetype="text/event-stream", headers=headers)