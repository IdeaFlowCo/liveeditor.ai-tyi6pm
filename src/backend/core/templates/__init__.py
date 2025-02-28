"""
Templates module for managing AI improvement prompt templates.

This module provides functionality for creating, retrieving, updating, and 
managing both system-defined and user-created templates. These templates are used 
in the AI-powered writing enhancement platform to guide the generation of 
contextual writing improvements.

Exported Components:
    - TemplateManager: Core manager for template operations
    - TemplateService: Business logic service layer for API endpoints
    - validate_template: Utility function to validate template data
    - load_default_templates: Function to load predefined system templates
    - Error classes: TemplateValidationError, TemplateServiceError, 
      TemplateNotFoundError, TemplateAccessError
"""

# Import core components from the template_manager module
from .template_manager import (
    TemplateManager,
    TemplateValidationError,
    get_default_templates
)

# Import service layer and exceptions from the template_service module
from .template_service import (
    TemplateService,
    TemplateServiceError,
    TemplateNotFoundError,
    TemplateAccessError
)

# Create adapter functions to match the expected exports

def load_default_templates():
    """
    Function to load the predefined system improvement templates
    
    Returns:
        List of predefined template dictionaries with standard templates like
        'Make it shorter', 'More professional', etc.
    """
    return get_default_templates()

def validate_template(template_data, is_update=False):
    """
    Utility function to validate template data structure and types
    
    Args:
        template_data: Template data to validate
        is_update: Whether this is an update operation
            
    Returns:
        bool: True if template is valid
            
    Raises:
        TemplateValidationError: If validation fails
    """
    # Implementation copied from TemplateManager.validate_template
    if not isinstance(template_data, dict):
        raise TemplateValidationError("Template data must be a dictionary")
    
    # For create operations, verify required fields
    if not is_update:
        required_fields = ['name', 'description', 'promptText', 'category']
        for field in required_fields:
            if field not in template_data or not template_data[field]:
                raise TemplateValidationError(f"Template '{field}' is required")
                
    # For update operations, verify at least one valid field is provided
    elif is_update and not any(f in template_data for f in ['name', 'description', 'promptText', 'category']):
        raise TemplateValidationError("Update must include at least one of: name, description, promptText, category")
    
    # Validate field types and values
    if 'name' in template_data:
        if not isinstance(template_data['name'], str):
            raise TemplateValidationError("Template name must be a string")
        if len(template_data['name']) > 100:
            raise TemplateValidationError("Template name must be 100 characters or less")
    
    if 'description' in template_data:
        if not isinstance(template_data['description'], str):
            raise TemplateValidationError("Template description must be a string")
        if len(template_data['description']) > 500:
            raise TemplateValidationError("Template description must be 500 characters or less")
    
    if 'promptText' in template_data:
        if not isinstance(template_data['promptText'], str):
            raise TemplateValidationError("Template promptText must be a string")
        if len(template_data['promptText']) > 2000:
            raise TemplateValidationError("Template promptText must be 2000 characters or less")
        if len(template_data['promptText']) < 10:
            raise TemplateValidationError("Template promptText must be at least 10 characters")
    
    if 'category' in template_data:
        if not isinstance(template_data['category'], str):
            raise TemplateValidationError("Template category must be a string")
        if len(template_data['category']) > 50:
            raise TemplateValidationError("Template category must be 50 characters or less")
    
    return True

# Define module exports
__all__ = [
    'TemplateManager',
    'TemplateService',
    'validate_template',
    'load_default_templates',
    'TemplateValidationError',
    'TemplateServiceError',
    'TemplateNotFoundError',
    'TemplateAccessError'
]