from datetime import datetime
# marshmallow v3.15.0 - Schema definition and field types for API data validation and serialization
from marshmallow import Schema, fields, validates, ValidationError

class ChatMessageSchema(Schema):
    """Schema for validating and serializing chat messages sent between user and AI"""
    message = fields.String(required=True)
    sender_type = fields.String(required=True)
    timestamp = fields.DateTime(default=datetime.utcnow)
    session_id = fields.String(required=True)
    document_id = fields.String(allow_none=True)
    
    class Meta:
        """Meta class configuration for the schema"""
        unknown = "EXCLUDE"  # Ignore unknown fields
        ordered = True  # Preserve field order in serialized output
    
    @validates("message")
    def validate_message(self, message):
        """
        Validates that the message is not empty and is within allowed length
        
        Args:
            message (str): The chat message to validate
            
        Returns:
            str: Validated message
            
        Raises:
            ValidationError: If message is empty or exceeds maximum length
        """
        if not message or message.isspace():
            raise ValidationError("Message cannot be empty")
        
        if len(message) > 2000:  # Set a reasonable message length limit
            raise ValidationError("Message too long, maximum 2000 characters allowed")
        
        return message
    
    @validates("sender_type")
    def validate_sender_type(self, sender_type):
        """
        Validates that the sender type is either 'user' or 'ai'
        
        Args:
            sender_type (str): The sender type to validate
            
        Returns:
            str: Validated sender_type
            
        Raises:
            ValidationError: If sender_type is not one of the allowed values
        """
        allowed_types = ["user", "ai"]
        if sender_type not in allowed_types:
            raise ValidationError(f"Sender type must be one of: {', '.join(allowed_types)}")
        
        return sender_type


class ChatRequestSchema(Schema):
    """Schema for validating and serializing chat request payload sent from the client"""
    message = fields.String(required=True)
    session_id = fields.String(required=True)
    document_id = fields.String(allow_none=True)
    context = fields.Dict(required=False, default={})
    
    class Meta:
        """Meta class configuration for the schema"""
        unknown = "EXCLUDE"
        ordered = True
    
    @validates("message")
    def validate_message(self, message):
        """
        Validates that the message is not empty and is within allowed length
        
        Args:
            message (str): The chat message to validate
            
        Returns:
            str: Validated message
            
        Raises:
            ValidationError: If message is empty or exceeds maximum length
        """
        if not message or message.isspace():
            raise ValidationError("Message cannot be empty")
        
        if len(message) > 2000:
            raise ValidationError("Message too long, maximum 2000 characters allowed")
        
        return message


class ChatResponseSchema(Schema):
    """Schema for validating and serializing chat response payload sent to the client"""
    message = fields.String(required=True)
    session_id = fields.String(required=True)
    suggestions = fields.List(fields.Nested("ChatSuggestionSchema"), default=[])
    can_apply_to_document = fields.Boolean(default=False)
    timestamp = fields.DateTime(default=datetime.utcnow)
    
    class Meta:
        """Meta class configuration for the schema"""
        unknown = "EXCLUDE"
        ordered = True


class ChatHistorySchema(Schema):
    """Schema for validating and serializing chat history responses"""
    session_id = fields.String(required=True)
    document_id = fields.String(allow_none=True)
    messages = fields.List(fields.Nested(ChatMessageSchema), default=[])
    
    class Meta:
        """Meta class configuration for the schema"""
        unknown = "EXCLUDE"
        ordered = True


class ChatSuggestionSchema(Schema):
    """Schema for validating and serializing chat suggestions that can be applied to the document"""
    original_text = fields.String(required=True)
    suggested_text = fields.String(required=True)
    explanation = fields.String(required=False, allow_none=True)
    # Position should include start and end indices in the document or selection
    position = fields.Dict(required=True)
    
    class Meta:
        """Meta class configuration for the schema"""
        unknown = "EXCLUDE"
        ordered = True