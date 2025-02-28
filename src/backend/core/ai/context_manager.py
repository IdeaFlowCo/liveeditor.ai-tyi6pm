"""
Manages context for AI operations by handling document context, conversation history, and context window optimization.
Provides efficient token usage while maintaining sufficient context for high-quality AI responses in both
document improvement and chat scenarios.

This module is responsible for:
- Managing conversation contexts between the user and AI
- Optimizing document content to fit within token limits
- Balancing context preservation with token efficiency
- Providing relevant context extraction for targeted queries
"""

import json
import uuid
import datetime
from typing import Dict, List, Optional, Any, Union
import time

from .token_optimizer import TokenOptimizer, count_tokens as optimizer_count_tokens, apply_context_window
from ...core.utils.logger import get_logger
from ...data.redis.caching_service import cache_set, cache_get, cache_delete

# Constants for context management
DEFAULT_CONTEXT_LIMIT = 4000
CONVERSATION_CACHE_PREFIX = 'conversation:'
CONVERSATION_TTL = 3600  # 1 hour
SYSTEM_MESSAGE_WEIGHT = 1.5  # System messages are weighted higher for token counting
USER_MESSAGE_WEIGHT = 1.0
ASSISTANT_MESSAGE_WEIGHT = 1.2
MAX_CONVERSATION_MESSAGES = 20  # Maximum messages to retain in conversation history
CONTEXT_CACHE_TTL = 1800  # 30 minutes

# Initialize logger
logger = get_logger(__name__)


def generate_conversation_id() -> str:
    """
    Generates a unique identifier for a new conversation.
    
    Returns:
        A unique conversation ID
    """
    return str(uuid.uuid4())


def format_context_key(session_id: str, conversation_id: str) -> str:
    """
    Creates a cache key for storing conversation context.
    
    Args:
        session_id: Session identifier
        conversation_id: Conversation identifier
        
    Returns:
        Formatted cache key
    """
    return f"{CONVERSATION_CACHE_PREFIX}{session_id}:{conversation_id}"


def count_context_tokens(messages: List) -> int:
    """
    Counts the total tokens in a conversation context.
    
    Args:
        messages: List of message objects with 'role' and 'content' fields
        
    Returns:
        Total token count
    """
    token_count = 0
    token_optimizer = TokenOptimizer()
    
    # Define role weights for token counting
    role_weights = {
        'system': SYSTEM_MESSAGE_WEIGHT,
        'user': USER_MESSAGE_WEIGHT,
        'assistant': ASSISTANT_MESSAGE_WEIGHT
    }
    
    for message in messages:
        content = message.get('content', '')
        role = message.get('role', 'user')
        
        # Apply role-specific weight
        weight = role_weights.get(role, 1.0)
        
        # Count tokens and apply weight
        message_tokens = token_optimizer.count_tokens(content)
        token_count += int(message_tokens * weight)
        
    return token_count


def serialize_context(context: Dict) -> str:
    """
    Serializes conversation context for caching.
    
    Args:
        context: Context dictionary to serialize
        
    Returns:
        JSON serialized context
    """
    # Create a copy to avoid modifying the original
    serializable_context = context.copy()
    
    # Convert datetime objects to ISO format strings
    for key, value in serializable_context.items():
        if isinstance(value, datetime.datetime):
            serializable_context[key] = value.isoformat()
    
    # Handle messages array
    if 'messages' in serializable_context:
        for message in serializable_context['messages']:
            if 'timestamp' in message and isinstance(message['timestamp'], datetime.datetime):
                message['timestamp'] = message['timestamp'].isoformat()
    
    # Serialize to JSON
    return json.dumps(serializable_context)


def deserialize_context(serialized_context: str) -> Dict:
    """
    Deserializes conversation context from cache.
    
    Args:
        serialized_context: JSON serialized context
        
    Returns:
        Deserialized context object
    """
    context = json.loads(serialized_context)
    
    # Convert ISO format strings back to datetime objects
    for key, value in context.items():
        if key in ['created_at', 'updated_at'] and isinstance(value, str):
            try:
                context[key] = datetime.datetime.fromisoformat(value)
            except ValueError:
                # If conversion fails, keep as string
                pass
    
    # Handle messages array
    if 'messages' in context:
        for message in context['messages']:
            if 'timestamp' in message and isinstance(message['timestamp'], str):
                try:
                    message['timestamp'] = datetime.datetime.fromisoformat(message['timestamp'])
                except ValueError:
                    # If conversion fails, keep as string
                    pass
    
    return context


class ContextNotFoundError(Exception):
    """Exception raised when conversation context cannot be found."""
    
    def __init__(self, session_id: str, conversation_id: str, message: str = None):
        """
        Initialize the exception with context identifiers.
        
        Args:
            session_id: Session identifier
            conversation_id: Conversation identifier
            message: Custom error message
        """
        if message is None:
            message = f"Context not found for session {session_id}, conversation {conversation_id}"
        
        super().__init__(message)
        self.session_id = session_id
        self.conversation_id = conversation_id


class ContextManager:
    """
    Manages conversation and document context for AI interactions.
    
    Handles the creation, retrieval, and optimization of context for both
    document improvements and conversational interactions with the AI.
    """
    
    def __init__(self, token_optimizer: TokenOptimizer = None, 
                 context_limit: int = DEFAULT_CONTEXT_LIMIT,
                 use_cache: bool = True,
                 cache_ttl: int = CONTEXT_CACHE_TTL):
        """
        Initializes the context manager with specified parameters.
        
        Args:
            token_optimizer: TokenOptimizer instance for token management
            context_limit: Maximum token limit for contexts
            use_cache: Whether to use Redis caching
            cache_ttl: Time-to-live for cached contexts
        """
        self._token_optimizer = token_optimizer if token_optimizer else TokenOptimizer()
        self._context_limit = context_limit
        self._use_cache = use_cache
        self._cache_ttl = cache_ttl
        self.logger = logger
    
    def create_context(self, session_id: str, conversation_id: str = None, 
                       document_content: str = None, system_message: str = None,
                       user_id: str = None) -> Dict:
        """
        Creates a new conversation context.
        
        Args:
            session_id: Session identifier
            conversation_id: Conversation identifier (generated if None)
            document_content: Optional document content to associate with context
            system_message: Optional system message to initialize conversation
            user_id: Optional user identifier for authenticated sessions
            
        Returns:
            New conversation context dictionary
        """
        # Generate conversation ID if not provided
        if conversation_id is None:
            conversation_id = generate_conversation_id()
            
        # Create timestamp
        current_time = datetime.datetime.utcnow()
        
        # Initialize context structure
        context = {
            'session_id': session_id,
            'conversation_id': conversation_id,
            'user_id': user_id,
            'created_at': current_time,
            'updated_at': current_time,
            'messages': [],
            'metadata': {
                'token_usage': 0,
                'message_count': 0
            }
        }
        
        # Add system message if provided
        if system_message:
            context['messages'].append({
                'role': 'system',
                'content': system_message,
                'timestamp': current_time
            })
            
            # Update message count
            context['metadata']['message_count'] = 1
            
            # Calculate token usage
            context['metadata']['token_usage'] = self._token_optimizer.count_tokens(system_message)
        
        # Store document content if provided
        if document_content:
            context['document_content'] = document_content
            context['metadata']['document_tokens'] = self._token_optimizer.count_tokens(document_content)
        
        # Cache the context if caching is enabled
        if self._use_cache:
            cache_key = format_context_key(session_id, conversation_id)
            try:
                serialized_context = serialize_context(context)
                cache_set(cache_key, serialized_context, self._cache_ttl)
                self.logger.debug(f"Created and cached context for session {session_id}, conversation {conversation_id}")
            except Exception as e:
                self.logger.error(f"Error caching context: {str(e)}")
        
        return context
    
    def get_context(self, session_id: str, conversation_id: str) -> Optional[Dict]:
        """
        Retrieves conversation context from memory or cache.
        
        Args:
            session_id: Session identifier
            conversation_id: Conversation identifier
            
        Returns:
            Conversation context or None if not found
        """
        # Create cache key
        cache_key = format_context_key(session_id, conversation_id)
        
        # Try to retrieve from cache if enabled
        if self._use_cache:
            try:
                serialized_context = cache_get(cache_key)
                if serialized_context:
                    context = deserialize_context(serialized_context)
                    self.logger.debug(f"Retrieved context from cache for session {session_id}, conversation {conversation_id}")
                    return context
            except Exception as e:
                self.logger.error(f"Error retrieving context from cache: {str(e)}")
        
        # Context not found
        self.logger.warning(f"Context not found for session {session_id}, conversation {conversation_id}")
        return None
    
    def add_message_to_context(self, session_id: str, conversation_id: str, 
                               role: str, content: str) -> Optional[Dict]:
        """
        Adds a message to conversation context.
        
        Args:
            session_id: Session identifier
            conversation_id: Conversation identifier
            role: Message role ('user', 'assistant', or 'system')
            content: Message content
            
        Returns:
            Updated conversation context or None if context not found
        """
        # Get existing context
        context = self.get_context(session_id, conversation_id)
        if not context:
            self.logger.warning(f"Cannot add message to non-existent context: {session_id}, {conversation_id}")
            return None
        
        # Create message with current timestamp
        current_time = datetime.datetime.utcnow()
        message = {
            'role': role,
            'content': content,
            'timestamp': current_time
        }
        
        # Add message to context
        context['messages'].append(message)
        
        # Update context metadata
        context['updated_at'] = current_time
        context['metadata']['message_count'] = len(context['messages'])
        
        # Update token usage
        message_tokens = self._token_optimizer.count_tokens(content)
        # Apply role weight
        if role == 'system':
            message_tokens *= SYSTEM_MESSAGE_WEIGHT
        elif role == 'assistant':
            message_tokens *= ASSISTANT_MESSAGE_WEIGHT
        
        context['metadata']['token_usage'] = context['metadata'].get('token_usage', 0) + message_tokens
        
        # Trim context if it exceeds MAX_CONVERSATION_MESSAGES
        if len(context['messages']) > MAX_CONVERSATION_MESSAGES:
            # Keep system messages and most recent messages
            system_messages = [m for m in context['messages'] if m['role'] == 'system']
            recent_messages = context['messages'][-(MAX_CONVERSATION_MESSAGES - len(system_messages)):]
            context['messages'] = system_messages + recent_messages
            
            # Recalculate token usage
            context['metadata']['token_usage'] = count_context_tokens(context['messages'])
            context['metadata']['message_count'] = len(context['messages'])
            
            self.logger.info(f"Trimmed context to {MAX_CONVERSATION_MESSAGES} messages")
        
        # Cache updated context
        if self._use_cache:
            cache_key = format_context_key(session_id, conversation_id)
            try:
                serialized_context = serialize_context(context)
                cache_set(cache_key, serialized_context, self._cache_ttl)
                self.logger.debug(f"Updated context in cache for session {session_id}, conversation {conversation_id}")
            except Exception as e:
                self.logger.error(f"Error updating context in cache: {str(e)}")
        
        return context
    
    def optimize_document_context(self, document_content: str, max_tokens: int = None, 
                                 query: str = None) -> str:
        """
        Optimizes document content to fit within token limits.
        
        Args:
            document_content: Document content to optimize
            max_tokens: Maximum tokens allowed (defaults to context_limit)
            query: Optional query for relevance-based optimization
            
        Returns:
            Optimized document content
        """
        if not document_content:
            return ""
        
        # Set default max_tokens if not provided
        if max_tokens is None:
            max_tokens = self._context_limit
        
        # Count tokens in current document
        current_tokens = self._token_optimizer.count_tokens(document_content)
        
        # If already within limits, return unchanged
        if current_tokens <= max_tokens:
            return document_content
        
        start_time = time.time()
        
        # Apply context windowing to optimize document
        if query:
            # Query-based optimization with context window
            optimized_content = self._token_optimizer.apply_context_window(
                document_content, max_tokens, query=query)
        else:
            # Position-based importance (beginning, end, key sections)
            optimized_content = self._token_optimizer.apply_context_window(
                document_content, max_tokens)
        
        # Calculate optimization stats
        optimized_tokens = self._token_optimizer.count_tokens(optimized_content)
        tokens_saved = current_tokens - optimized_tokens
        percent_reduction = (tokens_saved / current_tokens) * 100 if current_tokens > 0 else 0
        
        self.logger.info(
            f"Optimized document from {current_tokens} to {optimized_tokens} tokens "
            f"({percent_reduction:.1f}% reduction) in {time.time() - start_time:.2f}s"
        )
        
        return optimized_content
    
    def trim_context_to_token_limit(self, context: Dict, max_tokens: int = None) -> Dict:
        """
        Trims conversation context to fit within token limits.
        
        Args:
            context: Conversation context to trim
            max_tokens: Maximum tokens allowed (defaults to context_limit)
            
        Returns:
            Trimmed conversation context
        """
        if not context:
            return {}
        
        # Set default max_tokens if not provided
        if max_tokens is None:
            max_tokens = self._context_limit
        
        # Extract messages
        messages = context.get('messages', [])
        if not messages:
            return context
        
        # Count tokens in entire conversation
        total_tokens = count_context_tokens(messages)
        
        # If already within limits, return unchanged
        if total_tokens <= max_tokens:
            return context
        
        # Create a copy to avoid modifying the original
        trimmed_context = context.copy()
        trimmed_messages = messages.copy()
        
        # Separate system messages and other messages
        system_messages = [m for m in trimmed_messages if m.get('role') == 'system']
        non_system_messages = [m for m in trimmed_messages if m.get('role') != 'system']
        
        # Always keep system messages
        result_messages = system_messages.copy()
        system_tokens = count_context_tokens(system_messages)
        available_tokens = max_tokens - system_tokens
        
        # If we only have system messages and they're already over limit, truncate them
        if not non_system_messages and system_tokens > max_tokens:
            self.logger.warning("System messages alone exceed token limit, truncating them")
            # Sort by timestamp if available
            system_messages.sort(key=lambda m: m.get('timestamp', datetime.datetime.min), reverse=True)
            result_messages = []
            current_tokens = 0
            
            for message in system_messages:
                message_tokens = self._token_optimizer.count_tokens(message.get('content', ''))
                if current_tokens + message_tokens <= max_tokens:
                    result_messages.append(message)
                    current_tokens += message_tokens
                else:
                    break
            
            # Update trimmed context
            trimmed_context['messages'] = result_messages
            trimmed_context['metadata'] = trimmed_context.get('metadata', {}).copy()
            trimmed_context['metadata']['token_usage'] = current_tokens
            trimmed_context['metadata']['message_count'] = len(result_messages)
            
            self.logger.info(f"Trimmed context to {len(result_messages)} messages ({current_tokens} tokens)")
            return trimmed_context
        
        # For normal messages, start from most recent and work backward
        non_system_messages.reverse()  # Most recent first
        current_tokens = 0
        
        for message in non_system_messages:
            # Count message tokens
            message_tokens = self._token_optimizer.count_tokens(message.get('content', ''))
            
            # Add message weight based on role
            role = message.get('role', 'user')
            if role == 'assistant':
                message_tokens *= ASSISTANT_MESSAGE_WEIGHT
            
            # Check if adding this message would exceed limit
            if current_tokens + message_tokens <= available_tokens:
                result_messages.append(message)
                current_tokens += message_tokens
            else:
                break
        
        # Restore original order (system messages first, then chronological)
        non_system_result = [m for m in result_messages if m.get('role') != 'system']
        non_system_result.reverse()  # Restore chronological order
        
        trimmed_context['messages'] = system_messages + non_system_result
        
        # Update metadata
        trimmed_context['metadata'] = trimmed_context.get('metadata', {}).copy()
        trimmed_context['metadata']['token_usage'] = system_tokens + current_tokens
        trimmed_context['metadata']['message_count'] = len(trimmed_context['messages'])
        
        messages_removed = len(messages) - len(trimmed_context['messages'])
        self.logger.info(
            f"Trimmed context from {len(messages)} to {len(trimmed_context['messages'])} messages "
            f"({messages_removed} messages removed)"
        )
        
        return trimmed_context
    
    def prepare_context_for_ai(self, context: Dict, max_tokens: int = None) -> List:
        """
        Prepares conversation context for AI service consumption.
        
        Args:
            context: Conversation context
            max_tokens: Maximum tokens to allow (defaults to context_limit)
            
        Returns:
            List of messages formatted for AI service
        """
        if not context:
            return []
        
        # Set default max_tokens if not provided
        if max_tokens is None:
            max_tokens = self._context_limit
        
        # Trim context if needed
        trimmed_context = self.trim_context_to_token_limit(context, max_tokens)
        
        # Extract messages
        messages = trimmed_context.get('messages', [])
        
        # Format for AI service (content and role only)
        ai_messages = []
        for message in messages:
            ai_message = {
                'role': message.get('role', 'user'),
                'content': message.get('content', '')
            }
            ai_messages.append(ai_message)
        
        # Ensure system message is at the beginning
        has_system = any(m.get('role') == 'system' for m in ai_messages)
        
        if not has_system:
            # Add a default system message if none exists
            default_system = {
                'role': 'system',
                'content': 'You are a helpful AI writing assistant.'
            }
            ai_messages.insert(0, default_system)
        
        return ai_messages
    
    def clear_context(self, session_id: str, conversation_id: str) -> bool:
        """
        Removes conversation context from cache.
        
        Args:
            session_id: Session identifier
            conversation_id: Conversation identifier
            
        Returns:
            True if successful, False otherwise
        """
        if not self._use_cache:
            return True
        
        cache_key = format_context_key(session_id, conversation_id)
        try:
            cache_delete(cache_key)
            self.logger.info(f"Cleared context for session {session_id}, conversation {conversation_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error clearing context: {str(e)}")
            return False
    
    def find_relevant_context(self, document_content: str, query: str, max_tokens: int = None) -> str:
        """
        Finds the most relevant context for a specific query.
        
        Args:
            document_content: Document content to search
            query: Query to find relevant content for
            max_tokens: Maximum tokens to return
            
        Returns:
            Most relevant document context for the query
        """
        if not document_content:
            return ""
            
        if not query:
            # Without a query, fall back to general optimization
            return self.optimize_document_context(document_content, max_tokens)
        
        # Set default max_tokens if not provided
        if max_tokens is None:
            max_tokens = self._context_limit
        
        # Extract relevant sentences using token optimizer
        start_time = time.time()
        relevant_content = self._token_optimizer.extract_key_sentences(
            document_content, 
            max_sentences=20,  # Start with more sentences than we need
            query=query
        )
        
        # Optimize to fit within token limit
        optimized_content = self.optimize_document_context(relevant_content, max_tokens)
        
        self.logger.info(
            f"Found relevant context for query in {time.time() - start_time:.2f}s "
            f"({self._token_optimizer.count_tokens(optimized_content)} tokens)"
        )
        
        return optimized_content
    
    def get_conversation_summary(self, context: Dict, max_tokens: int = None) -> str:
        """
        Creates a summary of the conversation for context preparation.
        
        Args:
            context: Conversation context
            max_tokens: Maximum tokens for the summary
            
        Returns:
            Condensed summary of the conversation
        """
        if not context or not context.get('messages', []):
            return ""
        
        # Set default max_tokens if not provided
        if max_tokens is None:
            max_tokens = min(500, self._context_limit // 4)  # Use at most 1/4 of context limit
        
        messages = context.get('messages', [])
        
        # Extract key messages (system messages and recent exchanges)
        system_messages = [m for m in messages if m.get('role') == 'system']
        # Get last few non-system messages, but no more than would fit in token limit
        recent_messages = [m for m in messages if m.get('role') != 'system'][-10:]
        
        # Prepare a summary message
        summary_parts = []
        
        # Include system instruction
        if system_messages:
            system_content = system_messages[0].get('content', '')
            if len(system_content) > 100:
                # Truncate long system messages for the summary
                system_content = system_content[:100] + "..."
            summary_parts.append(f"System instructions: {system_content}")
        
        # Include key exchanges
        summary_parts.append(f"Conversation summary ({len(messages)} total messages):")
        
        for msg in recent_messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            # Truncate long messages
            if len(content) > 100:
                content = content[:100] + "..."
                
            summary_parts.append(f"- {role.capitalize()}: {content}")
        
        # Join all parts
        summary = "\n".join(summary_parts)
        
        # Ensure summary fits within token limit
        if self._token_optimizer.count_tokens(summary) > max_tokens:
            summary = self._token_optimizer.apply_context_window(summary, max_tokens)
        
        return summary
    
    def merge_document_and_conversation(self, document_content: str, 
                                       conversation_context: Dict,
                                       max_tokens: int = None) -> Dict:
        """
        Combines document content and conversation context efficiently.
        
        Args:
            document_content: Document content
            conversation_context: Conversation context
            max_tokens: Maximum tokens for the combined context
            
        Returns:
            Combined context with balanced token allocation
        """
        if not document_content and not conversation_context:
            return {}
        
        # Set default max_tokens if not provided
        if max_tokens is None:
            max_tokens = self._context_limit
        
        # Create a copy of the conversation context
        merged_context = conversation_context.copy() if conversation_context else {}
        
        # If no document content, just return the conversation context
        if not document_content:
            return self.trim_context_to_token_limit(merged_context, max_tokens)
        
        # If no conversation context, create a context with just the document
        if not conversation_context:
            # Create a basic context structure
            current_time = datetime.datetime.utcnow()
            merged_context = {
                'created_at': current_time,
                'updated_at': current_time,
                'messages': [],
                'metadata': {
                    'token_usage': 0,
                    'message_count': 0
                }
            }
        
        # Calculate token counts
        doc_tokens = self._token_optimizer.count_tokens(document_content)
        conv_tokens = count_context_tokens(merged_context.get('messages', []))
        total_tokens = doc_tokens + conv_tokens
        
        # If total is within limit, no optimization needed
        if total_tokens <= max_tokens:
            # Store the full document content
            merged_context['document_content'] = document_content
            merged_context['metadata'] = merged_context.get('metadata', {}).copy()
            merged_context['metadata']['document_tokens'] = doc_tokens
            return merged_context
        
        # Need to allocate tokens between document and conversation
        # Allocate proportionally, but ensure conversation gets at least 1/3
        conversation_allocation = max(
            max_tokens // 3,  # At least 1/3 of tokens
            int(max_tokens * (conv_tokens / total_tokens))  # Proportional allocation
        )
        document_allocation = max_tokens - conversation_allocation
        
        # Optimize document to fit allocation
        optimized_document = self.optimize_document_context(
            document_content, document_allocation)
        
        # Trim conversation context to fit allocation
        trimmed_context = self.trim_context_to_token_limit(
            merged_context, conversation_allocation)
        
        # Store optimized document in the trimmed context
        trimmed_context['document_content'] = optimized_document
        trimmed_context['metadata'] = trimmed_context.get('metadata', {}).copy()
        trimmed_context['metadata']['document_tokens'] = self._token_optimizer.count_tokens(optimized_document)
        
        # Log the allocation
        self.logger.info(
            f"Merged context: {self._token_optimizer.count_tokens(optimized_document)} document tokens, "
            f"{trimmed_context['metadata'].get('token_usage', 0)} conversation tokens"
        )
        
        return trimmed_context
    
    def update_context_metadata(self, context: Dict, metadata: Dict) -> Dict:
        """
        Updates metadata fields in the conversation context.
        
        Args:
            context: Conversation context
            metadata: Dictionary of metadata fields to update
            
        Returns:
            Updated context with new metadata
        """
        if not context:
            return {}
        
        # Create a copy to avoid modifying the original
        updated_context = context.copy()
        
        # Update metadata
        updated_context['metadata'] = updated_context.get('metadata', {}).copy()
        updated_context['metadata'].update(metadata)
        
        # Update timestamp
        updated_context['updated_at'] = datetime.datetime.utcnow()
        
        # Cache updated context if caching is enabled
        if self._use_cache and 'session_id' in updated_context and 'conversation_id' in updated_context:
            cache_key = format_context_key(
                updated_context['session_id'], 
                updated_context['conversation_id']
            )
            try:
                serialized_context = serialize_context(updated_context)
                cache_set(cache_key, serialized_context, self._cache_ttl)
            except Exception as e:
                self.logger.error(f"Error caching updated context: {str(e)}")
        
        return updated_context
    
    def estimate_token_usage(self, document_content: str, conversation_context: Dict) -> Dict:
        """
        Estimates token usage for a document and conversation.
        
        Args:
            document_content: Document content
            conversation_context: Conversation context
            
        Returns:
            Token usage statistics
        """
        # Count tokens in document
        doc_tokens = 0
        if document_content:
            doc_tokens = self._token_optimizer.count_tokens(document_content)
        
        # Count tokens in conversation
        conv_tokens = 0
        if conversation_context and 'messages' in conversation_context:
            conv_tokens = count_context_tokens(conversation_context['messages'])
        
        # Calculate total and percentage of limit
        total_tokens = doc_tokens + conv_tokens
        percent_of_limit = (total_tokens / self._context_limit) * 100
        
        return {
            'document_tokens': doc_tokens,
            'conversation_tokens': conv_tokens,
            'total_tokens': total_tokens,
            'context_limit': self._context_limit,
            'percent_of_limit': percent_of_limit,
            'is_over_limit': total_tokens > self._context_limit
        }