"""
Repository class for logging and retrieving AI interaction data in MongoDB.
Stores information about user interactions with the AI system including suggestion requests,
chat conversations, and the outcomes of these interactions for analytics and improvement purposes.
"""

import pymongo  # pymongo ^4.3.0
from bson import ObjectId  # pymongo ^4.3.0
from datetime import datetime, timedelta  # standard library
from typing import Optional, Dict, List, Any, Union  # standard library
import uuid  # standard library
import re  # standard library

from .connection import get_collection, str_to_object_id, object_id_to_str
from ...core.utils.logger import get_logger
from ...core.utils.validators import validate_object_id

# Constants
COLLECTION_NAME = 'ai_interactions'
MAX_CONTENT_LENGTH = 1000
DEFAULT_RETENTION_DAYS = 90
INTERACTION_TYPES = {
    'suggestion': 'Suggestion generation',
    'chat': 'Free-form chat',
    'template': 'Predefined template',
    'feedback': 'User feedback'
}

# Set up logger
logger = get_logger(__name__)


class AIInteractionRepository:
    """Repository for storing and retrieving AI interaction data in MongoDB"""

    def __init__(self):
        """Initialize the AI interaction repository with MongoDB collection"""
        self._collection = get_collection(COLLECTION_NAME)
        logger.info(f"AIInteractionRepository initialized with collection {COLLECTION_NAME}")

    def log_interaction(self, interaction_type: str, session_id: str,
                      user_id: Optional[str] = None, document_id: Optional[str] = None,
                      prompt_type: Optional[str] = None, custom_prompt: Optional[str] = None,
                      metadata: Optional[dict] = None) -> str:
        """
        Logs an AI interaction event to the MongoDB collection

        Args:
            interaction_type: Type of interaction (suggestion, chat, template, feedback)
            session_id: Unique identifier for the user session
            user_id: Unique identifier for the user (None for anonymous users)
            document_id: Identifier of the document being processed
            prompt_type: Type of prompt template used
            custom_prompt: Text of custom prompt if provided
            metadata: Additional data about the interaction

        Returns:
            ID of the created interaction record
        """
        # Validate interaction_type
        if interaction_type not in INTERACTION_TYPES:
            raise ValueError(f"Invalid interaction_type: {interaction_type}. "
                             f"Must be one of {list(INTERACTION_TYPES.keys())}")

        # Prepare metadata
        if metadata is None:
            metadata = {}

        # Create interaction document
        interaction = {
            'interaction_type': interaction_type,
            'session_id': session_id,
            'timestamp': datetime.utcnow(),
        }

        # Add optional fields if provided
        if user_id:
            interaction['user_id'] = user_id
        if document_id:
            interaction['document_id'] = document_id
        if prompt_type:
            interaction['prompt_type'] = prompt_type
        if custom_prompt:
            # Truncate custom prompt if it exceeds max length
            interaction['custom_prompt'] = custom_prompt[:MAX_CONTENT_LENGTH]
        
        # Add metadata
        interaction['metadata'] = self.sanitize_input(metadata)

        # Insert into MongoDB
        try:
            result = self._collection.insert_one(interaction)
            interaction_id = str(result.inserted_id)
            logger.info(f"Logged {interaction_type} interaction: {interaction_id}")
            return interaction_id
        except Exception as e:
            logger.error(f"Error logging interaction: {str(e)}")
            raise

    def log_suggestion_interaction(self, session_id: str, user_id: Optional[str] = None,
                                 document_id: Optional[str] = None, prompt_type: str = '',
                                 custom_prompt: Optional[str] = None, suggestion_count: int = 0,
                                 processing_time: Optional[float] = None,
                                 metadata: Optional[dict] = None) -> str:
        """
        Logs a suggestion-specific AI interaction with additional fields

        Args:
            session_id: Unique identifier for the user session
            user_id: Unique identifier for the user (None for anonymous users)
            document_id: Identifier of the document being processed
            prompt_type: Type of prompt template used
            custom_prompt: Text of custom prompt if provided
            suggestion_count: Number of suggestions generated
            processing_time: Time taken to process the request in seconds
            metadata: Additional data about the interaction

        Returns:
            ID of the created interaction record
        """
        # Prepare metadata
        if metadata is None:
            metadata = {}
        
        # Add suggestion-specific metadata
        metadata['suggestion_count'] = suggestion_count
        
        if processing_time is not None:
            metadata['processing_time'] = processing_time

        # Log the interaction
        return self.log_interaction(
            interaction_type='suggestion',
            session_id=session_id,
            user_id=user_id,
            document_id=document_id,
            prompt_type=prompt_type,
            custom_prompt=custom_prompt,
            metadata=metadata
        )

    def log_chat_interaction(self, session_id: str, user_id: Optional[str] = None,
                           conversation_id: str = '', message: str = '',
                           document_id: Optional[str] = None,
                           processing_time: Optional[float] = None,
                           metadata: Optional[dict] = None) -> str:
        """
        Logs a chat-specific AI interaction with conversation context

        Args:
            session_id: Unique identifier for the user session
            user_id: Unique identifier for the user (None for anonymous users)
            conversation_id: Unique identifier for the conversation
            message: The chat message content
            document_id: Identifier of the related document (if any)
            processing_time: Time taken to process the message in seconds
            metadata: Additional data about the interaction

        Returns:
            ID of the created interaction record
        """
        # Prepare metadata
        if metadata is None:
            metadata = {}
        
        # Add chat-specific metadata
        metadata['conversation_id'] = conversation_id

        if processing_time is not None:
            metadata['processing_time'] = processing_time

        # Truncate message if it exceeds max length
        truncated_message = message[:MAX_CONTENT_LENGTH]

        # Log the interaction
        return self.log_interaction(
            interaction_type='chat',
            session_id=session_id,
            user_id=user_id,
            document_id=document_id,
            prompt_type=None,
            custom_prompt=truncated_message,
            metadata=metadata
        )

    def log_feedback(self, interaction_id: str, rating: int,
                   feedback_text: Optional[str] = None,
                   user_id: Optional[str] = None) -> bool:
        """
        Logs user feedback on AI suggestions or chat responses

        Args:
            interaction_id: ID of the interaction receiving feedback
            rating: Numeric rating (typically 1-5)
            feedback_text: Optional text feedback
            user_id: User providing the feedback

        Returns:
            True if feedback was successfully logged, False otherwise
        """
        # Validate interaction_id format
        try:
            validate_object_id(interaction_id)
        except ValueError:
            logger.error(f"Invalid interaction_id format: {interaction_id}")
            return False

        # Validate rating
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            logger.error(f"Invalid rating: {rating}. Must be integer between 1-5")
            return False

        # Convert interaction_id to ObjectId
        obj_id = str_to_object_id(interaction_id)

        # Create feedback document
        feedback = {
            'rating': rating,
            'timestamp': datetime.utcnow()
        }

        # Add optional fields
        if feedback_text:
            feedback['feedback_text'] = feedback_text[:MAX_CONTENT_LENGTH]
        if user_id:
            feedback['user_id'] = user_id

        # Update the interaction document
        try:
            result = self._collection.update_one(
                {'_id': obj_id},
                {'$set': {'feedback': feedback}}
            )

            if result.matched_count == 0:
                logger.warning(f"No interaction found with ID: {interaction_id}")
                return False

            logger.info(f"Feedback logged for interaction: {interaction_id}")
            return True
        except Exception as e:
            logger.error(f"Error logging feedback: {str(e)}")
            return False

    def get_interaction(self, interaction_id: str) -> Optional[dict]:
        """
        Retrieves a specific AI interaction by ID

        Args:
            interaction_id: ID of the interaction to retrieve

        Returns:
            Interaction document or None if not found
        """
        try:
            # Validate interaction_id format
            validate_object_id(interaction_id)
            
            # Convert to ObjectId
            obj_id = str_to_object_id(interaction_id)
            
            # Query the database
            interaction = self._collection.find_one({'_id': obj_id})
            
            if interaction:
                # Convert ObjectId to string
                interaction['_id'] = object_id_to_str(interaction['_id'])
                logger.debug(f"Retrieved interaction: {interaction_id}")
                return interaction
            
            logger.warning(f"Interaction not found: {interaction_id}")
            return None
        except ValueError as e:
            logger.error(f"Invalid interaction_id format: {interaction_id}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving interaction {interaction_id}: {str(e)}")
            return None

    def get_user_interactions(self, user_id: str, limit: Optional[int] = None,
                            skip: Optional[int] = None,
                            interaction_type: Optional[str] = None) -> list:
        """
        Retrieves all AI interactions for a specific user

        Args:
            user_id: ID of the user
            limit: Maximum number of results to return
            skip: Number of results to skip (for pagination)
            interaction_type: Filter by interaction type

        Returns:
            List of interaction documents
        """
        # Prepare query filter
        query_filter = {'user_id': user_id}
        
        # Add interaction_type filter if provided
        if interaction_type and interaction_type in INTERACTION_TYPES:
            query_filter['interaction_type'] = interaction_type
            
        # Execute query with optional pagination
        try:
            cursor = self._collection.find(query_filter)
            
            # Sort by timestamp (newest first)
            cursor = cursor.sort('timestamp', pymongo.DESCENDING)
            
            # Apply pagination if specified
            if skip is not None:
                cursor = cursor.skip(skip)
            if limit is not None:
                cursor = cursor.limit(limit)
                
            # Convert to list and format ObjectIds
            interactions = list(cursor)
            for interaction in interactions:
                interaction['_id'] = object_id_to_str(interaction['_id'])
                
            logger.info(f"Retrieved {len(interactions)} interactions for user: {user_id}")
            return interactions
        except Exception as e:
            logger.error(f"Error retrieving user interactions: {str(e)}")
            return []

    def get_session_interactions(self, session_id: str, limit: Optional[int] = None,
                               skip: Optional[int] = None,
                               interaction_type: Optional[str] = None) -> list:
        """
        Retrieves all AI interactions for a specific session

        Args:
            session_id: ID of the session
            limit: Maximum number of results to return
            skip: Number of results to skip (for pagination)
            interaction_type: Filter by interaction type

        Returns:
            List of interaction documents
        """
        # Prepare query filter
        query_filter = {'session_id': session_id}
        
        # Add interaction_type filter if provided
        if interaction_type and interaction_type in INTERACTION_TYPES:
            query_filter['interaction_type'] = interaction_type
            
        # Execute query with optional pagination
        try:
            cursor = self._collection.find(query_filter)
            
            # Sort by timestamp (newest first)
            cursor = cursor.sort('timestamp', pymongo.DESCENDING)
            
            # Apply pagination if specified
            if skip is not None:
                cursor = cursor.skip(skip)
            if limit is not None:
                cursor = cursor.limit(limit)
                
            # Convert to list and format ObjectIds
            interactions = list(cursor)
            for interaction in interactions:
                interaction['_id'] = object_id_to_str(interaction['_id'])
                
            logger.info(f"Retrieved {len(interactions)} interactions for session: {session_id}")
            return interactions
        except Exception as e:
            logger.error(f"Error retrieving session interactions: {str(e)}")
            return []

    def get_document_interactions(self, document_id: str, limit: Optional[int] = None,
                                skip: Optional[int] = None,
                                interaction_type: Optional[str] = None) -> list:
        """
        Retrieves all AI interactions for a specific document

        Args:
            document_id: ID of the document
            limit: Maximum number of results to return
            skip: Number of results to skip (for pagination)
            interaction_type: Filter by interaction type

        Returns:
            List of interaction documents
        """
        # Prepare query filter
        query_filter = {'document_id': document_id}
        
        # Add interaction_type filter if provided
        if interaction_type and interaction_type in INTERACTION_TYPES:
            query_filter['interaction_type'] = interaction_type
            
        # Execute query with optional pagination
        try:
            cursor = self._collection.find(query_filter)
            
            # Sort by timestamp (newest first)
            cursor = cursor.sort('timestamp', pymongo.DESCENDING)
            
            # Apply pagination if specified
            if skip is not None:
                cursor = cursor.skip(skip)
            if limit is not None:
                cursor = cursor.limit(limit)
                
            # Convert to list and format ObjectIds
            interactions = list(cursor)
            for interaction in interactions:
                interaction['_id'] = object_id_to_str(interaction['_id'])
                
            logger.info(f"Retrieved {len(interactions)} interactions for document: {document_id}")
            return interactions
        except Exception as e:
            logger.error(f"Error retrieving document interactions: {str(e)}")
            return []

    def get_conversation_interactions(self, conversation_id: str, 
                                    limit: Optional[int] = None,
                                    skip: Optional[int] = None) -> list:
        """
        Retrieves all chat interactions for a specific conversation

        Args:
            conversation_id: ID of the conversation
            limit: Maximum number of results to return
            skip: Number of results to skip (for pagination)

        Returns:
            List of chat interaction documents
        """
        # Prepare query filter for chat interactions with the given conversation_id
        query_filter = {
            'interaction_type': 'chat',
            'metadata.conversation_id': conversation_id
        }
            
        # Execute query with optional pagination
        try:
            cursor = self._collection.find(query_filter)
            
            # Sort by timestamp (oldest first for conversation flow)
            cursor = cursor.sort('timestamp', pymongo.ASCENDING)
            
            # Apply pagination if specified
            if skip is not None:
                cursor = cursor.skip(skip)
            if limit is not None:
                cursor = cursor.limit(limit)
                
            # Convert to list and format ObjectIds
            interactions = list(cursor)
            for interaction in interactions:
                interaction['_id'] = object_id_to_str(interaction['_id'])
                
            logger.info(f"Retrieved {len(interactions)} interactions for conversation: {conversation_id}")
            return interactions
        except Exception as e:
            logger.error(f"Error retrieving conversation interactions: {str(e)}")
            return []

    def get_interaction_statistics(self, user_id: Optional[str] = None,
                                 interaction_type: Optional[str] = None,
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None) -> dict:
        """
        Retrieves statistics about AI interactions for analytics

        Args:
            user_id: Filter by user ID
            interaction_type: Filter by interaction type
            start_date: Start date for time-based filtering
            end_date: End date for time-based filtering

        Returns:
            Dictionary of interaction statistics
        """
        # Build match stage for aggregation pipeline
        match_stage = {}
        
        if user_id:
            match_stage['user_id'] = user_id
            
        if interaction_type and interaction_type in INTERACTION_TYPES:
            match_stage['interaction_type'] = interaction_type
            
        if start_date or end_date:
            match_stage['timestamp'] = {}
            if start_date:
                match_stage['timestamp']['$gte'] = start_date
            if end_date:
                match_stage['timestamp']['$lte'] = end_date
                
        # Build the aggregation pipeline
        pipeline = []
        
        # Add match stage if filters are applied
        if match_stage:
            pipeline.append({'$match': match_stage})
            
        # Group by interaction_type to get counts
        pipeline.append({
            '$group': {
                '_id': '$interaction_type',
                'count': {'$sum': 1},
                'avg_processing_time': {
                    '$avg': {
                        '$cond': [
                            {'$ifNull': ['$metadata.processing_time', False]},
                            '$metadata.processing_time',
                            None
                        ]
                    }
                },
                'avg_rating': {
                    '$avg': {
                        '$cond': [
                            {'$ifNull': ['$feedback.rating', False]},
                            '$feedback.rating',
                            None
                        ]
                    }
                },
                'suggestion_count_sum': {
                    '$sum': {
                        '$cond': [
                            {'$and': [
                                {'$eq': ['$interaction_type', 'suggestion']},
                                {'$ifNull': ['$metadata.suggestion_count', False]}
                            ]},
                            '$metadata.suggestion_count',
                            0
                        ]
                    }
                }
            }
        })
        
        try:
            # Execute the aggregation pipeline
            result = list(self._collection.aggregate(pipeline))
            
            # Format the results
            statistics = {
                'total_interactions': 0,
                'interaction_types': {},
                'time_period': {
                    'start': start_date.isoformat() if start_date else None,
                    'end': end_date.isoformat() if end_date else None
                }
            }
            
            for item in result:
                interaction_type = item['_id']
                count = item['count']
                statistics['total_interactions'] += count
                
                statistics['interaction_types'][interaction_type] = {
                    'count': count,
                    'avg_processing_time': item['avg_processing_time'],
                    'avg_rating': item['avg_rating']
                }
                
                # Add suggestion-specific metrics
                if interaction_type == 'suggestion':
                    statistics['interaction_types'][interaction_type]['total_suggestions'] = item['suggestion_count_sum']
                    if count > 0:
                        statistics['interaction_types'][interaction_type]['avg_suggestions_per_interaction'] = \
                            item['suggestion_count_sum'] / count
            
            logger.info(f"Generated interaction statistics: {statistics['total_interactions']} total interactions")
            return statistics
        except Exception as e:
            logger.error(f"Error generating interaction statistics: {str(e)}")
            return {'error': str(e), 'total_interactions': 0, 'interaction_types': {}}

    def delete_old_interactions(self, days: Optional[int] = None) -> int:
        """
        Removes interactions older than the retention period

        Args:
            days: Number of days to retain data (uses DEFAULT_RETENTION_DAYS if not specified)

        Returns:
            Number of interactions deleted
        """
        # Use default retention period if not specified
        if days is None:
            days = DEFAULT_RETENTION_DAYS
            
        # Calculate the cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        try:
            # Delete interactions older than the cutoff date
            result = self._collection.delete_many({'timestamp': {'$lt': cutoff_date}})
            deleted_count = result.deleted_count
            
            logger.info(f"Deleted {deleted_count} interactions older than {days} days")
            return deleted_count
        except Exception as e:
            logger.error(f"Error deleting old interactions: {str(e)}")
            return 0

    def anonymize_user_data(self, user_id: str) -> int:
        """
        Anonymizes user data in interactions for privacy compliance

        Args:
            user_id: ID of the user to anonymize

        Returns:
            Number of interactions anonymized
        """
        try:
            # Generate an anonymized identifier
            anonymized_id = f"anonymized_{str(uuid.uuid4())}"
            
            # Update all interactions for this user
            result = self._collection.update_many(
                {'user_id': user_id},
                {'$set': {
                    'user_id': anonymized_id,
                    'anonymized_at': datetime.utcnow(),
                    'custom_prompt': '[REDACTED]'  # Mask any custom prompts
                }}
            )
            
            anonymized_count = result.modified_count
            logger.info(f"Anonymized {anonymized_count} interactions for user: {user_id}")
            return anonymized_count
        except Exception as e:
            logger.error(f"Error anonymizing user data: {str(e)}")
            return 0

    def create_indexes(self) -> list:
        """
        Creates necessary indexes for the ai_interactions collection

        Returns:
            List of created index names
        """
        try:
            indexes = [
                # Index on timestamp for retention/expiry queries
                pymongo.IndexModel([('timestamp', pymongo.DESCENDING)],
                                 name='timestamp_index'),
                
                # Index on user_id for user-based queries
                pymongo.IndexModel([('user_id', pymongo.ASCENDING)],
                                 name='user_id_index'),
                
                # Index on session_id for session-based queries
                pymongo.IndexModel([('session_id', pymongo.ASCENDING)],
                                 name='session_id_index'),
                
                # Index on document_id for document-based queries
                pymongo.IndexModel([('document_id', pymongo.ASCENDING)],
                                 name='document_id_index'),
                
                # Compound index for document interactions over time
                pymongo.IndexModel([
                    ('document_id', pymongo.ASCENDING),
                    ('timestamp', pymongo.DESCENDING)
                ], name='document_time_index'),
                
                # Index for conversation history
                pymongo.IndexModel([
                    ('metadata.conversation_id', pymongo.ASCENDING),
                    ('timestamp', pymongo.ASCENDING)
                ], name='conversation_index'),
                
                # Index for interaction type filtering
                pymongo.IndexModel([('interaction_type', pymongo.ASCENDING)],
                                 name='interaction_type_index'),
                
                # Compound index for user interactions of specific type
                pymongo.IndexModel([
                    ('user_id', pymongo.ASCENDING),
                    ('interaction_type', pymongo.ASCENDING),
                    ('timestamp', pymongo.DESCENDING)
                ], name='user_type_time_index')
            ]
            
            # Create the indexes
            result = self._collection.create_indexes(indexes)
            logger.info(f"Created indexes: {result}")
            return result
        except Exception as e:
            logger.error(f"Error creating indexes: {str(e)}")
            return []

    def sanitize_input(self, data: dict) -> dict:
        """
        Sanitizes input data to remove any sensitive information

        Args:
            data: Data dictionary to sanitize

        Returns:
            Sanitized data dictionary
        """
        if not data or not isinstance(data, dict):
            return {}
            
        # Create a copy to avoid modifying the original
        sanitized = data.copy()
        
        # Sensitive fields that should be redacted
        sensitive_fields = ['password', 'token', 'email', 'api_key', 'secret', 'credit_card',
                           'phone', 'address', 'social_security', 'ssn']
        
        # Basic email pattern for detection
        email_pattern = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
        
        # Process each key-value pair
        for key, value in list(sanitized.items()):
            # Check if key is sensitive
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                sanitized[key] = '[REDACTED]'
                continue
                
            # Check value type
            if isinstance(value, str):
                # Truncate long strings
                if len(value) > MAX_CONTENT_LENGTH:
                    sanitized[key] = value[:MAX_CONTENT_LENGTH]
                
                # Redact emails in string values
                if email_pattern.search(value):
                    sanitized[key] = email_pattern.sub('[REDACTED_EMAIL]', value)
            elif isinstance(value, dict):
                # Recursively sanitize nested dictionaries
                sanitized[key] = self.sanitize_input(value)
            elif isinstance(value, list) and all(isinstance(item, dict) for item in value):
                # Sanitize list of dictionaries
                sanitized[key] = [self.sanitize_input(item) for item in value]
                
        return sanitized