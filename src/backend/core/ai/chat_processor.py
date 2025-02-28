"""
Processes chat interactions between users and the AI assistant, managing conversation context,
formatting messages, and generating responses that may include document improvement suggestions.
"""

import re
import json
import time
import asyncio
from typing import Dict, List, Optional, Union, Generator, Any

from .openai_service import OpenAIService
from .context_manager import ContextManager
from .token_optimizer import TokenOptimizer
from .prompt_manager import PromptManager
from ...data.mongodb.repositories.ai_interaction_repository import AIInteractionRepository
from ...core.utils.logger import get_logger
from ...core.utils.validators import validate_prompt

# Constants
DEFAULT_SYSTEM_INSTRUCTION = "You are an AI writing assistant helping to improve documents. Be helpful, concise, and focus on the user's specific questions about their document."
TRACK_CHANGES_PATTERN = "Use track changes format with [-deleted text-]{+added text+} for suggesting document changes."
MAX_CHAT_HISTORY = 10
DEFAULT_AI_MODEL = "gpt-4"
DEFAULT_TEMPERATURE = 0.7
MAX_RESPONSE_TOKENS = 1024
SUGGESTION_PATTERN = r"\[-(.*?)-\]\{\+(.*?)\+\}"

# Initialize logger
logger = get_logger(__name__)


def sanitize_message(message: str) -> str:
    """
    Sanitizes user input to prevent prompt injection and ensure safe processing
    
    Args:
        message: The message to sanitize
        
    Returns:
        Sanitized message content
    """
    if not message:
        return ""
    
    # Remove any potential prompt injection patterns
    message = message.replace("{{", "").replace("}}", "")
    message = message.replace("```system", "").replace("```", "")
    
    # Trim whitespace and normalize text
    message = message.strip()
    
    # Validate message is not empty after sanitization
    if not message:
        raise ValueError("Message content cannot be empty after sanitization")
    
    # Ensure the message doesn't exceed maximum allowed length
    max_length = 5000
    if len(message) > max_length:
        message = message[:max_length]
        logger.warning(f"Message truncated to {max_length} characters")
    
    return message


def extract_suggestions(response_text: str) -> List[Dict]:
    """
    Extracts document improvement suggestions from AI response in track changes format
    
    Args:
        response_text: The response text to extract suggestions from
        
    Returns:
        List of suggestion dictionaries with original and suggested text
    """
    if not response_text:
        return []
    
    suggestions = []
    
    # Use regex to find all track changes patterns
    matches = re.finditer(SUGGESTION_PATTERN, response_text)
    
    for match in matches:
        original_text = match.group(1)
        suggested_text = match.group(2)
        
        suggestion = {
            "original_text": original_text,
            "suggested_text": suggested_text
        }
        
        suggestions.append(suggestion)
    
    return suggestions


def format_chat_history(interactions: List) -> List[Dict]:
    """
    Formats previous chat interactions into a format suitable for AI context
    
    Args:
        interactions: List of interaction records
        
    Returns:
        List of formatted message dictionaries
    """
    if not interactions:
        return []
    
    messages = []
    
    for interaction in interactions:
        # Determine message role based on the interaction
        if interaction.get("metadata", {}).get("is_user_message", False):
            role = "user"
        else:
            role = "assistant"
        
        # Extract content from the interaction
        content = interaction.get("custom_prompt", "")
        
        # Create formatted message
        message = {
            "role": role,
            "content": content
        }
        
        messages.append(message)
    
    # Ensure messages are in chronological order
    messages.sort(key=lambda x: x.get("timestamp", 0))
    
    return messages


class ChatProcessor:
    """
    Processes chat interactions between users and the AI assistant, managing conversation context
    and generating responses
    """
    
    def __init__(
        self,
        openai_service: OpenAIService,
        context_manager: ContextManager,
        token_optimizer: TokenOptimizer,
        prompt_manager: PromptManager,
        repository: AIInteractionRepository,
        max_history: int = MAX_CHAT_HISTORY
    ):
        """
        Initializes the ChatProcessor with required dependencies
        
        Args:
            openai_service: Service for AI response generation
            context_manager: Manager for conversation context
            token_optimizer: Optimizer for token usage
            prompt_manager: Manager for prompt creation
            repository: Repository for storing interactions
            max_history: Maximum number of messages to keep in history
        """
        self._openai_service = openai_service
        self._context_manager = context_manager
        self._token_optimizer = token_optimizer
        self._prompt_manager = prompt_manager
        self._repository = repository
        self._max_history = max_history
    
    def process_message(
        self,
        message: str,
        session_id: str,
        conversation_id: str = None,
        user_id: str = None,
        document_id: str = None,
        document_content: str = None,
        parameters: Dict = {}
    ) -> Dict:
        """
        Processes a user message and generates an AI response
        
        Args:
            message: User's message
            session_id: Session identifier
            conversation_id: Conversation identifier (optional)
            user_id: User identifier (optional)
            document_id: Document identifier (optional)
            document_content: Document content (optional)
            parameters: Additional parameters for AI processing
            
        Returns:
            Dict containing AI response and metadata
        """
        # Start timer for performance monitoring
        start_time = time.time()
        
        try:
            # Sanitize user message
            sanitized_message = sanitize_message(message)
            
            # Generate or retrieve conversation_id
            if not conversation_id:
                conversation_id = str(time.time())
                logger.info(f"Generated new conversation ID: {conversation_id}")
            
            # Get existing conversation context or create new one
            context = self._context_manager.get_context(session_id, conversation_id)
            if not context:
                # Prepare system instruction with or without document context
                system_instruction = self.prepare_system_instruction(document_content)
                # Create new conversation context
                context = self._context_manager.create_context(
                    session_id=session_id,
                    conversation_id=conversation_id,
                    document_content=document_content,
                    system_message=system_instruction,
                    user_id=user_id
                )
                logger.info(f"Created new conversation context for session {session_id}")
            
            # Add user message to context
            self._context_manager.add_message_to_context(
                session_id=session_id,
                conversation_id=conversation_id,
                role="user",
                content=sanitized_message
            )
            
            # Optimize document content if provided
            if document_content:
                document_content = self._context_manager.optimize_document_context(
                    document_content, query=sanitized_message
                )
            
            # Prepare context for AI processing
            ai_messages = self._context_manager.prepare_context_for_ai(context)
            
            # Get AI response
            ai_model = parameters.get("model", DEFAULT_AI_MODEL)
            temperature = parameters.get("temperature", DEFAULT_TEMPERATURE)
            max_tokens = parameters.get("max_tokens", MAX_RESPONSE_TOKENS)
            
            ai_response = self._openai_service.get_chat_response(
                messages=ai_messages,
                parameters={
                    "model": ai_model,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            
            # Extract response text from AI response
            response_text = ai_response["choices"][0]["message"]["content"]
            
            # Extract any suggestions from the response
            suggestions = self.extract_document_suggestions(response_text)
            
            # Add AI response to conversation context
            self._context_manager.add_message_to_context(
                session_id=session_id,
                conversation_id=conversation_id,
                role="assistant",
                content=response_text
            )
            
            # Log the interaction
            self._repository.log_chat_interaction(
                session_id=session_id,
                user_id=user_id,
                conversation_id=conversation_id,
                message=sanitized_message,
                document_id=document_id,
                processing_time=time.time() - start_time,
                metadata={
                    "model": ai_model,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "suggestion_count": len(suggestions)
                }
            )
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Construct response
            response = {
                "content": response_text,
                "conversation_id": conversation_id,
                "suggestions": suggestions,
                "processing_time": processing_time
            }
            
            logger.info(f"Processed message in {processing_time:.2f}s, found {len(suggestions)} suggestions")
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error processing message: {str(e)}")
            raise ChatProcessingError(f"Failed to process message: {str(e)}")
    
    def stream_response(
        self,
        message: str,
        session_id: str,
        conversation_id: str = None,
        user_id: str = None,
        document_id: str = None,
        document_content: str = None,
        parameters: Dict = {}
    ) -> Generator:
        """
        Streams an AI response for real-time display
        
        Args:
            message: User's message
            session_id: Session identifier
            conversation_id: Conversation identifier (optional)
            user_id: User identifier (optional)
            document_id: Document identifier (optional)
            document_content: Document content (optional)
            parameters: Additional parameters for AI processing
            
        Returns:
            Generator yielding response chunks
        """
        # Start timer for performance monitoring
        start_time = time.time()
        
        try:
            # Sanitize user message
            sanitized_message = sanitize_message(message)
            
            # Generate or retrieve conversation_id
            if not conversation_id:
                conversation_id = str(time.time())
                logger.info(f"Generated new conversation ID: {conversation_id}")
            
            # Get existing conversation context or create new one
            context = self._context_manager.get_context(session_id, conversation_id)
            if not context:
                # Prepare system instruction with or without document context
                system_instruction = self.prepare_system_instruction(document_content)
                # Create new conversation context
                context = self._context_manager.create_context(
                    session_id=session_id,
                    conversation_id=conversation_id,
                    document_content=document_content,
                    system_message=system_instruction,
                    user_id=user_id
                )
                logger.info(f"Created new conversation context for session {session_id}")
            
            # Add user message to context
            self._context_manager.add_message_to_context(
                session_id=session_id,
                conversation_id=conversation_id,
                role="user",
                content=sanitized_message
            )
            
            # Optimize document content if provided
            if document_content:
                document_content = self._context_manager.optimize_document_context(
                    document_content, query=sanitized_message
                )
            
            # Prepare context for AI processing
            ai_messages = self._context_manager.prepare_context_for_ai(context)
            
            # Get AI model parameters
            ai_model = parameters.get("model", DEFAULT_AI_MODEL)
            temperature = parameters.get("temperature", DEFAULT_TEMPERATURE)
            max_tokens = parameters.get("max_tokens", MAX_RESPONSE_TOKENS)
            
            # Get streaming response generator
            stream = self._openai_service.stream_response(
                messages=ai_messages,
                parameters={
                    "model": ai_model,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            
            # Initialize full response accumulator
            full_response = ""
            
            # Stream response chunks
            for chunk in stream:
                if "error" in chunk:
                    # If there's an error, yield it and stop
                    yield chunk
                    break
                
                # Extract content from the chunk
                content = chunk.get("content", "")
                
                # Append to full response
                full_response += content
                
                # Yield chunk for real-time display
                yield chunk
            
            # After streaming completes, add the full response to conversation context
            if full_response:
                self._context_manager.add_message_to_context(
                    session_id=session_id,
                    conversation_id=conversation_id,
                    role="assistant",
                    content=full_response
                )
                
                # Extract any suggestions from the response
                suggestions = self.extract_document_suggestions(full_response)
                
                # Log the interaction
                self._repository.log_chat_interaction(
                    session_id=session_id,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    message=sanitized_message,
                    document_id=document_id,
                    processing_time=time.time() - start_time,
                    metadata={
                        "model": ai_model,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "streaming": True,
                        "suggestion_count": len(suggestions)
                    }
                )
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Yield final metadata
            yield {
                "done": True,
                "processing_time": processing_time,
                "conversation_id": conversation_id
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error streaming response: {str(e)}")
            yield {
                "error": str(e),
                "done": True,
                "processing_time": processing_time
            }
    
    def get_conversation_history(self, session_id: str, conversation_id: str) -> List:
        """
        Retrieves the conversation history for a given session and conversation
        
        Args:
            session_id: Session identifier
            conversation_id: Conversation identifier
            
        Returns:
            List of previous messages in the conversation
        """
        try:
            # Try to get conversation context from context manager
            context = self._context_manager.get_context(session_id, conversation_id)
            
            if context and "messages" in context:
                # Return messages from context
                messages = context.get("messages", [])
                
                # Limit to max history if needed
                if len(messages) > self._max_history:
                    messages = messages[-self._max_history:]
                
                return messages
            
            # If no context found, try to get from repository
            interactions = self._repository.get_conversation_interactions(conversation_id)
            
            # Format interactions into messages
            messages = format_chat_history(interactions)
            
            # Limit to max history if needed
            if len(messages) > self._max_history:
                messages = messages[-self._max_history:]
            
            return messages
            
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {str(e)}")
            return []
    
    def create_new_conversation(
        self,
        session_id: str,
        user_id: str = None,
        document_id: str = None,
        document_content: str = None
    ) -> Dict:
        """
        Creates a new conversation with initial context
        
        Args:
            session_id: Session identifier
            user_id: User identifier (optional)
            document_id: Document identifier (optional)
            document_content: Document content (optional)
            
        Returns:
            Newly created conversation context
        """
        try:
            # Generate system instruction
            system_instruction = self.prepare_system_instruction(document_content)
            
            # Optimize document content if provided
            if document_content:
                document_content = self._context_manager.optimize_document_context(document_content)
            
            # Create new conversation context
            context = self._context_manager.create_context(
                session_id=session_id,
                document_content=document_content,
                system_message=system_instruction,
                user_id=user_id
            )
            
            conversation_id = context.get("conversation_id")
            logger.info(f"Created new conversation {conversation_id} for session {session_id}")
            
            return context
            
        except Exception as e:
            logger.error(f"Error creating new conversation: {str(e)}")
            raise ChatProcessingError(f"Failed to create new conversation: {str(e)}")
    
    def extract_document_suggestions(self, response_text: str) -> List[Dict]:
        """
        Extracts document improvement suggestions from AI response
        
        Args:
            response_text: AI response text
            
        Returns:
            List of suggestion objects
        """
        return extract_suggestions(response_text)
    
    def get_conversation_metadata(self, session_id: str, conversation_id: str) -> Dict:
        """
        Retrieves metadata about a conversation
        
        Args:
            session_id: Session identifier
            conversation_id: Conversation identifier
            
        Returns:
            Conversation metadata
        """
        try:
            # Get conversation context
            context = self._context_manager.get_context(session_id, conversation_id)
            
            if not context:
                return {"error": "Conversation not found"}
            
            # Extract metadata
            metadata = context.get("metadata", {}).copy()
            
            # Add basic information
            metadata.update({
                "conversation_id": conversation_id,
                "session_id": session_id,
                "message_count": len(context.get("messages", [])),
                "created_at": context.get("created_at"),
                "updated_at": context.get("updated_at"),
                "has_document": "document_content" in context
            })
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error retrieving conversation metadata: {str(e)}")
            return {"error": str(e)}
    
    def prepare_system_instruction(self, document_content: str = None, is_document_focused: bool = False) -> str:
        """
        Prepares a system instruction with document context
        
        Args:
            document_content: Document content (optional)
            is_document_focused: Whether the focus is on document improvement
            
        Returns:
            Formatted system instruction
        """
        # Start with the default system instruction
        system_instruction = DEFAULT_SYSTEM_INSTRUCTION
        
        # Add document-specific instructions if document_content is provided
        if document_content:
            system_instruction += f" The following document content is provided for context: '{document_content}'"
        
        # Add track changes instructions if focused on document improvement
        if is_document_focused or document_content:
            system_instruction += f" {TRACK_CHANGES_PATTERN}"
        
        return system_instruction
    
    def clear_conversation(self, session_id: str, conversation_id: str) -> bool:
        """
        Clears a conversation's history
        
        Args:
            session_id: Session identifier
            conversation_id: Conversation identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Clear context from context manager
            success = self._context_manager.clear_context(session_id, conversation_id)
            
            if success:
                logger.info(f"Cleared conversation {conversation_id} for session {session_id}")
            else:
                logger.warning(f"Failed to clear conversation {conversation_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error clearing conversation: {str(e)}")
            return False


class ChatProcessingError(Exception):
    """
    Exception raised when there is an error processing a chat message
    """
    
    def __init__(self, message: str, error_type: str = "processing_error"):
        """
        Initialize the exception with error details
        
        Args:
            message: Error message
            error_type: Type of error for categorization
        """
        super().__init__(message)
        self.message = message
        self.error_type = error_type