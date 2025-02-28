"""
Schema definitions for AI prompt templates used in the writing enhancement platform.

This module provides Marshmallow schemas for validating, serializing, and deserializing 
template data used throughout the API. It supports all template-related operations including
creating, updating, listing, and searching templates that power AI-assisted writing improvements.

Templates are used by the AI suggestion engine to provide predefined improvement prompts
such as "Make it shorter" or "More professional tone" in the application sidebar.
"""

from marshmallow import Schema, fields, validate, validates_schema, INCLUDE, ValidationError  # marshmallow 3.14.0
from bson import ObjectId  # bson 4.2.0
from datetime import datetime  # standard library

from ...core.utils.validators import validate_object_id

# Template validation constants
TEMPLATE_NAME_MIN_LENGTH = 3
TEMPLATE_NAME_MAX_LENGTH = 50
TEMPLATE_DESCRIPTION_MAX_LENGTH = 200
TEMPLATE_PROMPT_MAX_LENGTH = 2000
TEMPLATE_CATEGORIES = ['grammar', 'style', 'conciseness', 'clarity', 'professional', 'academic', 'creative', 'custom']


class TemplateSchema(Schema):
    """Base schema for template data serialization and deserialization."""
    
    id = fields.String(dump_only=True)
    name = fields.String(required=True)
    description = fields.String()
    promptText = fields.String(required=True)
    category = fields.String(required=True)
    isSystem = fields.Boolean(default=False)
    createdAt = fields.DateTime(dump_only=True)
    createdBy = fields.String(dump_only=True)
    
    class Meta:
        """Schema configuration."""
        unknown = INCLUDE


class TemplateCreateSchema(Schema):
    """Schema for validating template creation requests."""
    
    name = fields.String(
        required=True,
        validate=validate.Length(
            min=TEMPLATE_NAME_MIN_LENGTH,
            max=TEMPLATE_NAME_MAX_LENGTH,
            error=f"Template name must be between {TEMPLATE_NAME_MIN_LENGTH} and {TEMPLATE_NAME_MAX_LENGTH} characters."
        )
    )
    description = fields.String(
        validate=validate.Length(
            max=TEMPLATE_DESCRIPTION_MAX_LENGTH,
            error=f"Description cannot exceed {TEMPLATE_DESCRIPTION_MAX_LENGTH} characters."
        )
    )
    promptText = fields.String(
        required=True,
        validate=validate.Length(
            max=TEMPLATE_PROMPT_MAX_LENGTH,
            error=f"Prompt text cannot exceed {TEMPLATE_PROMPT_MAX_LENGTH} characters."
        )
    )
    category = fields.String(
        required=True,
        validate=validate.OneOf(
            TEMPLATE_CATEGORIES,
            error=f"Category must be one of: {', '.join(TEMPLATE_CATEGORIES)}."
        )
    )
    isSystem = fields.Boolean(default=False)
    
    class Meta:
        """Schema configuration."""
        unknown = INCLUDE
    
    @validates_schema
    def validate_template_data(self, data, **kwargs):
        """Validates template creation data at schema level."""
        # Check if promptText contains at least some variables or is a valid prompt
        prompt_text = data.get('promptText', '')
        if not prompt_text or prompt_text.isspace():
            raise ValidationError("Prompt text cannot be empty or contain only whitespace.")
        
        # Additional validation for category if needed beyond the field validation
        if 'category' in data and data['category'] not in TEMPLATE_CATEGORIES:
            raise ValidationError(
                f"Invalid category. Must be one of: {', '.join(TEMPLATE_CATEGORIES)}.",
                field_name="category"
            )


class TemplateUpdateSchema(Schema):
    """Schema for validating template update requests."""
    
    name = fields.String(
        validate=validate.Length(
            min=TEMPLATE_NAME_MIN_LENGTH,
            max=TEMPLATE_NAME_MAX_LENGTH,
            error=f"Template name must be between {TEMPLATE_NAME_MIN_LENGTH} and {TEMPLATE_NAME_MAX_LENGTH} characters."
        )
    )
    description = fields.String(
        validate=validate.Length(
            max=TEMPLATE_DESCRIPTION_MAX_LENGTH,
            error=f"Description cannot exceed {TEMPLATE_DESCRIPTION_MAX_LENGTH} characters."
        )
    )
    promptText = fields.String(
        validate=validate.Length(
            max=TEMPLATE_PROMPT_MAX_LENGTH,
            error=f"Prompt text cannot exceed {TEMPLATE_PROMPT_MAX_LENGTH} characters."
        )
    )
    category = fields.String(
        validate=validate.OneOf(
            TEMPLATE_CATEGORIES,
            error=f"Category must be one of: {', '.join(TEMPLATE_CATEGORIES)}."
        )
    )
    
    class Meta:
        """Schema configuration."""
        unknown = INCLUDE
    
    @validates_schema
    def validate_template_data(self, data, **kwargs):
        """Validates template update data at schema level."""
        # Ensure at least one field is provided for update
        if not data:
            raise ValidationError("At least one field must be provided for update.")
        
        # If promptText is provided, apply additional validation
        if 'promptText' in data:
            prompt_text = data['promptText']
            if not prompt_text or prompt_text.isspace():
                raise ValidationError("Prompt text cannot be empty or contain only whitespace.")
        
        # Additional validation for category if needed beyond the field validation
        if 'category' in data and data['category'] not in TEMPLATE_CATEGORIES:
            raise ValidationError(
                f"Invalid category. Must be one of: {', '.join(TEMPLATE_CATEGORIES)}.",
                field_name="category"
            )


class TemplateResponseSchema(Schema):
    """Schema for serializing template response data."""
    
    id = fields.String(dump_only=True)
    name = fields.String()
    description = fields.String()
    promptText = fields.String()
    category = fields.String()
    isSystem = fields.Boolean()
    createdAt = fields.DateTime()
    createdBy = fields.String()
    
    class Meta:
        """Schema configuration."""
        ordered = True  # Keep fields in the defined order


class TemplateListQuerySchema(Schema):
    """Schema for validating template listing query parameters."""
    
    category = fields.String(
        validate=validate.OneOf(
            TEMPLATE_CATEGORIES,
            error=f"Category must be one of: {', '.join(TEMPLATE_CATEGORIES)}."
        )
    )
    systemOnly = fields.Boolean(default=False)
    userOnly = fields.Boolean(default=False)
    page = fields.Integer(default=1, validate=validate.Range(min=1))
    perPage = fields.Integer(default=10, validate=validate.Range(min=1, max=100))
    
    class Meta:
        """Schema configuration."""
        unknown = INCLUDE
    
    @validates_schema
    def validate_filters(self, data, **kwargs):
        """Validates that filter parameters are not conflicting."""
        if data.get('systemOnly') and data.get('userOnly'):
            raise ValidationError(
                "systemOnly and userOnly cannot both be True.",
                field_name="filters"
            )


class TemplateListResponseSchema(Schema):
    """Schema for serializing paginated template listing responses."""
    
    templates = fields.List(fields.Nested(TemplateResponseSchema))
    total = fields.Integer()
    page = fields.Integer()
    perPage = fields.Integer()
    pages = fields.Integer()
    
    class Meta:
        """Schema configuration."""
        ordered = True


class TemplateCategorySchema(Schema):
    """Schema for serializing template category listing."""
    
    categories = fields.List(fields.String())
    
    class Meta:
        """Schema configuration."""
        ordered = True


class TemplateSearchSchema(Schema):
    """Schema for validating template search requests."""
    
    query = fields.String(
        required=True,
        validate=validate.Length(
            min=1,
            max=100,
            error="Search query must be between 1 and 100 characters."
        )
    )
    category = fields.String(
        validate=validate.OneOf(
            TEMPLATE_CATEGORIES,
            error=f"Category must be one of: {', '.join(TEMPLATE_CATEGORIES)}."
        )
    )
    includeSystem = fields.Boolean(default=True)
    page = fields.Integer(default=1, validate=validate.Range(min=1))
    perPage = fields.Integer(default=10, validate=validate.Range(min=1, max=100))
    
    class Meta:
        """Schema configuration."""
        unknown = INCLUDE
    
    @validates_schema
    def validate_search_query(self, data, **kwargs):
        """Validates search query parameter."""
        query = data.get('query', '')
        if not query or query.isspace():
            raise ValidationError("Search query cannot be empty or contain only whitespace.")
        
        if len(query) > 100:
            raise ValidationError("Search query cannot exceed 100 characters.")


# Create schema instances for export
template_schema = TemplateSchema()
template_create_schema = TemplateCreateSchema()
template_update_schema = TemplateUpdateSchema()
template_response_schema = TemplateResponseSchema()
template_list_query_schema = TemplateListQuerySchema()
template_list_response_schema = TemplateListResponseSchema()
template_category_schema = TemplateCategorySchema()
template_search_schema = TemplateSearchSchema()