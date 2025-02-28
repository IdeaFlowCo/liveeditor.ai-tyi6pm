"""
Schema models for suggestion requests and responses.

This module defines the schemas used for validating and serializing data
involved in the AI suggestion API endpoints. These schemas support the track changes
review system by structuring data for generating, displaying, and reviewing
text improvement suggestions.

The schemas in this module handle:
- Validation of suggestion requests from clients
- Serialization of AI-generated suggestions for client consumption
- Tracking of text change operations (additions, deletions, modifications)
- Handling of suggestion acceptance and rejection
- Collection of user feedback on suggestion quality
- Support for both authenticated and anonymous users
"""

from marshmallow import Schema, fields, validate, validates_schema, ValidationError, INCLUDE  # marshmallow 3.14.0
import uuid  # standard library
from datetime import datetime  # standard library

# Allowed suggestion types
SUGGESTION_TYPES = ['grammar', 'style', 'conciseness', 'clarity', 'professional', 'academic', 'creative', 'custom']

# Allowed operation types for text changes
OPERATION_TYPES = ['addition', 'deletion', 'modification']

# Maximum word count for document processing
MAX_DOCUMENT_SIZE = 25000

# Maximum length for custom prompts
MAX_CUSTOM_PROMPT_LENGTH = 1000


class Meta:
    """Meta class for configuring marshmallow schema behavior."""
    unknown = INCLUDE


class TextSelectionSchema(Schema):
    """
    Schema for validating text selection ranges within a document.
    
    This enables targeted suggestions for specific portions of text. The selection
    is defined by start and end character positions, where start must be less than end.
    Both values must be non-negative integers.
    """
    start = fields.Integer(required=True, validate=validate.Range(min=0),
                          description="Starting character position of text selection (inclusive)")
    end = fields.Integer(required=True, validate=validate.Range(min=0),
                        description="Ending character position of text selection (exclusive)")
    
    class Meta(Meta):
        pass
    
    @validates_schema
    def validate_selection_range(self, data, **kwargs):
        """
        Validates that start position is before end position and both are non-negative.
        
        Args:
            data (dict): The data to validate containing start and end positions
            **kwargs: Additional arguments passed by marshmallow
            
        Returns:
            dict: The validated data if validation passes
            
        Raises:
            ValidationError: If start position is greater than or equal to end position
        """
        if 'start' in data and 'end' in data:
            if data['start'] >= data['end']:
                raise ValidationError('Start position must be less than end position')
        return data


class ChangeSchema(Schema):
    """
    Schema for representing individual text change operations within a suggestion.
    
    Represents additions, deletions, or modifications to the text. Each change has:
    - A unique identifier
    - An operation type (addition, deletion, modification)
    - The original text (for deletions and modifications)
    - The new text (for additions and modifications)
    - Start and end positions in the document
    """
    change_id = fields.String(required=True, 
                             description="Unique identifier for the change")
    operation_type = fields.String(required=True, validate=validate.OneOf(OPERATION_TYPES),
                                  description=f"Type of change: {', '.join(OPERATION_TYPES)}")
    original_text = fields.String(allow_none=True,
                                 description="Original text being changed (for deletions and modifications)")
    new_text = fields.String(allow_none=True,
                            description="New text being proposed (for additions and modifications)")
    start_position = fields.Integer(required=True, validate=validate.Range(min=0),
                                   description="Starting character position of the change")
    end_position = fields.Integer(required=True, validate=validate.Range(min=0),
                                 description="Ending character position of the change")
    
    class Meta(Meta):
        pass
    
    @validates_schema
    def validate_operation_type(self, data, **kwargs):
        """
        Validates that operation_type is one of the allowed types.
        
        Args:
            data (dict): The data to validate containing operation_type
            **kwargs: Additional arguments passed by marshmallow
            
        Returns:
            dict: The validated data if validation passes
            
        Raises:
            ValidationError: If operation_type is not one of the allowed types
        """
        if 'operation_type' in data:
            if data['operation_type'] not in OPERATION_TYPES:
                raise ValidationError(f"Operation type must be one of: {', '.join(OPERATION_TYPES)}")
        return data


class SuggestionRequestSchema(Schema):
    """
    Schema for validating and deserializing suggestion requests from clients.
    
    Clients must provide either:
    - Document content directly or a document ID for stored documents
    - A template ID for predefined suggestions or a custom prompt
    
    Optional fields include:
    - Text selection to target specific portions of the document
    - Session ID for anonymous users
    - Suggestion type to categorize the request
    """
    document_content = fields.String(description="Raw document content to analyze")
    document_id = fields.String(description="ID of previously stored document to analyze")
    selection = fields.Nested(TextSelectionSchema, required=False,
                             description="Text selection range for targeted suggestions")
    template_id = fields.String(description="ID of predefined suggestion template to use")
    custom_prompt = fields.String(validate=validate.Length(max=MAX_CUSTOM_PROMPT_LENGTH),
                                 description=f"Custom improvement prompt (max {MAX_CUSTOM_PROMPT_LENGTH} chars)")
    suggestion_type = fields.String(validate=validate.OneOf(SUGGESTION_TYPES),
                                   description=f"Type of suggestion: {', '.join(SUGGESTION_TYPES)}")
    session_id = fields.String(required=False, 
                              description="Session identifier for anonymous users")
    
    class Meta(Meta):
        pass
    
    @validates_schema
    def validate_suggestion_input(self, data, **kwargs):
        """
        Validates that either template_id or custom_prompt is provided but not both.
        
        Args:
            data (dict): The data to validate
            **kwargs: Additional arguments passed by marshmallow
            
        Returns:
            dict: The validated data if validation passes
            
        Raises:
            ValidationError: If neither or both of template_id and custom_prompt are provided
        """
        has_template = 'template_id' in data and data['template_id']
        has_custom_prompt = 'custom_prompt' in data and data['custom_prompt']
        
        if has_template and has_custom_prompt:
            raise ValidationError("Cannot provide both template_id and custom_prompt")
        
        if not has_template and not has_custom_prompt:
            raise ValidationError("Either template_id or custom_prompt must be provided")
        
        return data
    
    @validates_schema
    def validate_document_input(self, data, **kwargs):
        """
        Validates that either document_content or document_id is provided but not both.
        
        Args:
            data (dict): The data to validate
            **kwargs: Additional arguments passed by marshmallow
            
        Returns:
            dict: The validated data if validation passes
            
        Raises:
            ValidationError: If neither or both of document_content and document_id are provided
        """
        has_content = 'document_content' in data and data['document_content']
        has_id = 'document_id' in data and data['document_id']
        
        if has_content and has_id:
            raise ValidationError("Cannot provide both document_content and document_id")
        
        if not has_content and not has_id:
            raise ValidationError("Either document_content or document_id must be provided")
        
        return data
    
    @validates_schema
    def validate_document_size(self, data, **kwargs):
        """
        Validates that document content does not exceed maximum size limit.
        
        Args:
            data (dict): The data to validate containing document_content
            **kwargs: Additional arguments passed by marshmallow
            
        Returns:
            dict: The validated data if validation passes
            
        Raises:
            ValidationError: If document size exceeds the maximum allowed
        """
        if 'document_content' in data and data['document_content']:
            # Simple word count estimation
            word_count = len(data['document_content'].split())
            if word_count > MAX_DOCUMENT_SIZE:
                raise ValidationError(f"Document exceeds maximum size of {MAX_DOCUMENT_SIZE} words")
        
        return data


class SuggestionResponseSchema(Schema):
    """
    Schema for serializing suggestion responses to clients.
    
    Each suggestion response includes:
    - A unique suggestion ID
    - The original and suggested text
    - A list of specific changes (additions, deletions, modifications)
    - Start and end positions in the document
    - Suggestion type and creation timestamp
    - Optional explanation of the suggestion
    """
    suggestion_id = fields.String(required=True, 
                                 description="Unique identifier for the suggestion")
    original_text = fields.String(required=True,
                                 description="Original text before suggestion")
    suggested_text = fields.String(required=True,
                                  description="Suggested improved text")
    explanation = fields.String(required=False,
                               description="Explanation of why the change was suggested")
    changes = fields.List(fields.Nested(ChangeSchema), required=True,
                         description="List of specific text changes")
    start_position = fields.Integer(required=True, validate=validate.Range(min=0),
                                   description="Starting character position of suggestion in document")
    end_position = fields.Integer(required=True, validate=validate.Range(min=0),
                                 description="Ending character position of suggestion in document")
    suggestion_type = fields.String(required=True, validate=validate.OneOf(SUGGESTION_TYPES),
                                   description=f"Type of suggestion: {', '.join(SUGGESTION_TYPES)}")
    created_at = fields.DateTime(required=True,
                                description="Timestamp when suggestion was created")
    
    class Meta(Meta):
        pass


class SuggestionWithDiffSchema(Schema):
    """
    Schema for serializing suggestions with detailed diff information for track changes display.
    
    Includes the base suggestion data plus:
    - Detailed diff operations for rendering in the UI
    - HTML representation of the diff for easy display
    - Statistics about the changes
    """
    suggestion = fields.Nested(SuggestionResponseSchema, required=True,
                              description="The base suggestion data")
    diff_operations = fields.List(fields.Dict(), required=False,
                                 description="Detailed diff operations for rendering")
    html_diff = fields.String(required=False,
                             description="HTML representation of the diff for display")
    diff_statistics = fields.Dict(required=False,
                                 description="Statistics about the changes (e.g., words changed)")
    
    class Meta(Meta):
        pass


class BulkSuggestionResponseSchema(Schema):
    """
    Schema for serializing multiple suggestion responses for a single request.
    
    Used when a single request generates multiple suggestions, such as
    when analyzing an entire document or paragraph.
    """
    suggestions = fields.List(fields.Nested(SuggestionResponseSchema), required=True,
                             description="List of suggestion responses")
    document_id = fields.String(required=False,
                               description="ID of the document if stored")
    request_id = fields.String(required=True,
                              description="Unique identifier for the original request")
    prompt_used = fields.String(required=False,
                               description="The prompt that was used to generate suggestions")
    metadata = fields.Dict(required=False,
                          description="Additional metadata about the bulk suggestions")
    processing_time = fields.Float(required=False,
                                  description="Time taken to process the suggestions in seconds")
    created_at = fields.DateTime(required=True,
                                description="Timestamp when suggestions were created")
    
    class Meta(Meta):
        pass


class SuggestionAcceptRejectSchema(Schema):
    """
    Schema for validating and deserializing suggestion accept/reject requests.
    
    Used when users review suggestions and decide which to accept or reject.
    """
    document_id = fields.String(required=True,
                               description="ID of the document containing suggestions")
    accepted_suggestion_ids = fields.List(fields.String(), required=False,
                                         description="List of suggestion IDs to accept")
    rejected_suggestion_ids = fields.List(fields.String(), required=False,
                                         description="List of suggestion IDs to reject")
    apply_immediately = fields.Boolean(required=False, default=True,
                                      description="Whether to apply changes immediately or stage them")
    
    class Meta(Meta):
        pass


class SuggestionFeedbackSchema(Schema):
    """
    Schema for validating and deserializing user feedback on suggestions.
    
    Collects user feedback on suggestion quality for improving the AI system.
    """
    suggestion_id = fields.String(required=True,
                                 description="ID of the suggestion being rated")
    quality_rating = fields.Integer(required=False,
                                   description="Quality rating from 1-5 (1=poor, 5=excellent)")
    feedback_text = fields.String(required=False,
                                 description="Free-form feedback text about the suggestion")
    improvement_reason = fields.String(required=False,
                                      description="Reason why the suggestion was helpful or unhelpful")
    
    class Meta(Meta):
        pass
    
    @validates_schema
    def validate_rating(self, data, **kwargs):
        """
        Validates quality rating is within valid range.
        
        Args:
            data (dict): The data to validate containing quality_rating
            **kwargs: Additional arguments passed by marshmallow
            
        Returns:
            dict: The validated data if validation passes
            
        Raises:
            ValidationError: If quality_rating is not between 1 and 5
        """
        if 'quality_rating' in data:
            if not 1 <= data['quality_rating'] <= 5:
                raise ValidationError("Quality rating must be between 1 and 5")
        
        return data


class SuggestionBatchRequestSchema(Schema):
    """
    Schema for validating batch processing of multiple suggestion requests.
    
    Allows clients to submit multiple suggestion requests in a single API call,
    improving efficiency for bulk operations.
    """
    requests = fields.List(fields.Nested(SuggestionRequestSchema), required=True,
                          description="List of suggestion requests to process")
    process_in_parallel = fields.Boolean(required=False, default=False,
                                        description="Whether to process requests in parallel")
    batch_options = fields.Dict(required=False,
                               description="Additional options for batch processing")
    
    class Meta(Meta):
        pass
    
    @validates_schema
    def validate_batch_size(self, data, **kwargs):
        """
        Validates batch size is within allowed limits.
        
        Args:
            data (dict): The data to validate containing requests
            **kwargs: Additional arguments passed by marshmallow
            
        Returns:
            dict: The validated data if validation passes
            
        Raises:
            ValidationError: If batch is empty or exceeds maximum size
        """
        if 'requests' in data:
            if not data['requests']:
                raise ValidationError("Batch requests cannot be empty")
            
            if len(data['requests']) > 10:  # Arbitrary limit, adjust as needed
                raise ValidationError("Batch size exceeds maximum allowed (10)")
        
        return data


# Create schema instances for use in API endpoints
text_selection_schema = TextSelectionSchema()
change_schema = ChangeSchema()
suggestion_request_schema = SuggestionRequestSchema()
suggestion_response_schema = SuggestionResponseSchema()
suggestion_with_diff_schema = SuggestionWithDiffSchema()
bulk_suggestion_response_schema = BulkSuggestionResponseSchema()
suggestion_accept_reject_schema = SuggestionAcceptRejectSchema()
suggestion_feedback_schema = SuggestionFeedbackSchema()
suggestion_batch_request_schema = SuggestionBatchRequestSchema()