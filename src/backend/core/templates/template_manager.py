"""
Provides a robust management layer for AI improvement prompt templates, handling CRUD operations,
caching, and default template initialization. Acts as the core business logic for managing both
system-defined and user-created templates.
"""

import json
import copy
import datetime
from typing import Dict, List, Optional, Tuple, Any, Union

from ...data.mongodb.repositories.template_repository import (
    TemplateRepository, TemplateNotFoundError, TemplateAccessError
)
from ...data.redis.caching_service import (
    cache_template, get_cached_template, is_cache_available, DEFAULT_TEMPLATE_TTL
)
from ..utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Cache key constants
CACHE_KEY_TEMPLATE = "template:{0}"
CACHE_KEY_CATEGORY = "templates:category:{0}"
CACHE_KEY_ALL_TEMPLATES = "templates:all"
CACHE_KEY_SYSTEM_TEMPLATES = "templates:system"
CACHE_KEY_CATEGORIES = "templates:categories"


def get_default_templates() -> List[Dict]:
    """
    Returns a list of predefined system templates for AI writing improvements
    
    Returns:
        List[Dict]: List of template dictionaries with predefined system templates
    """
    templates = [
        {
            "name": "Make it shorter",
            "description": "Condense the text while maintaining key information",
            "promptText": "Rewrite the provided text to be more concise and shorter without losing the key information or meaning. Aim to reduce the length by 30-50% by removing unnecessary words, phrases, and redundant information.",
            "category": "Length",
            "isSystem": True
        },
        {
            "name": "More professional",
            "description": "Improve the formality and professional tone of the text",
            "promptText": "Rewrite the provided text to use a more formal and professional tone. Replace casual language with professional alternatives, improve the structure, and ensure it's appropriate for a business or academic context.",
            "category": "Tone",
            "isSystem": True
        },
        {
            "name": "Improve grammar",
            "description": "Fix grammatical errors and improve sentence structure",
            "promptText": "Review the provided text for grammatical errors, punctuation issues, and sentence structure problems. Correct all errors while maintaining the original meaning. Focus on proper verb tense, subject-verb agreement, punctuation, and overall clarity.",
            "category": "Corrections",
            "isSystem": True
        },
        {
            "name": "Simplify language",
            "description": "Make the text easier to understand with simpler language",
            "promptText": "Rewrite the provided text using simpler language and clearer sentence structures. Aim for a reading level appropriate for a general audience. Replace complex terminology with simpler alternatives when possible, without losing the core meaning.",
            "category": "Clarity",
            "isSystem": True
        },
        {
            "name": "Add examples",
            "description": "Enhance the text with relevant examples",
            "promptText": "Expand the provided text by adding relevant examples to illustrate the main points. The examples should be concrete, clear, and directly related to the concepts being discussed. Maintain the overall tone and style of the original text.",
            "category": "Enhancement",
            "isSystem": True
        },
        {
            "name": "Academic style",
            "description": "Convert text to a formal academic style",
            "promptText": "Rewrite the provided text to follow formal academic writing conventions. Use an objective tone, proper citations (if relevant information is provided), academic terminology, and well-structured arguments. Avoid first-person perspective, contractions, and colloquial language.",
            "category": "Style",
            "isSystem": True
        },
        {
            "name": "Creative rewrite",
            "description": "Make the text more engaging and creative",
            "promptText": "Rewrite the provided text to be more engaging, creative, and interesting to read. Use vivid language, varied sentence structures, and rhetorical techniques to capture the reader's attention while maintaining the original meaning and key information.",
            "category": "Style",
            "isSystem": True
        }
    ]
    
    return templates


class TemplateValidationError(Exception):
    """
    Exception raised when a template fails validation checks
    """
    
    def __init__(self, message: str):
        """
        Initialize the template validation error
        
        Args:
            message: Error message
        """
        super().__init__(message)
        self.message = message


class TemplateManager:
    """
    Core manager for template operations with caching, validation, and CRUD functionality
    """
    
    def __init__(self, repository: TemplateRepository):
        """
        Initialize the template manager with repository and optional caching
        
        Args:
            repository: Repository for template data access
        """
        self._repository = repository
        self._cache_enabled = is_cache_available()
        
        logger.info(f"TemplateManager initialized with caching {'enabled' if self._cache_enabled else 'disabled'}")
    
    def get_template(self, template_identifier: str, by_id: bool = True) -> Optional[Dict]:
        """
        Retrieves a template by ID or name with caching
        
        Args:
            template_identifier: ID or name of the template to retrieve
            by_id: Whether to retrieve by ID (True) or name (False)
            
        Returns:
            Dict: Template object or None if not found
        """
        template = None
        
        # Try to get from cache if enabled and retrieving by ID
        if by_id and self._cache_enabled:
            template = get_cached_template(template_identifier)
            
            if template:
                logger.debug(f"Retrieved template '{template_identifier}' from cache")
                return template
        
        # Retrieve from repository
        try:
            if by_id:
                template = self._repository.get_by_id(template_identifier)
            else:
                template = self._repository.get_by_name(template_identifier)
                
            if template and self._cache_enabled and by_id:
                # Cache the template
                cache_template(template_identifier, template)
                logger.debug(f"Cached template '{template_identifier}'")
                
            if template:
                logger.info(f"Retrieved template '{template_identifier}' from repository")
            else:
                logger.info(f"Template '{template_identifier}' not found")
                
            return template
            
        except Exception as e:
            logger.error(f"Error retrieving template '{template_identifier}': {str(e)}")
            return None
    
    def get_templates_by_category(self, category: str, include_system: bool = True, 
                               user_id: Optional[str] = None, limit: int = 50, 
                               skip: int = 0) -> Tuple[List[Dict], int]:
        """
        Retrieves templates filtered by category
        
        Args:
            category: Category to filter by
            include_system: Whether to include system templates
            user_id: User ID for user-specific templates
            limit: Maximum number of templates to return
            skip: Number of templates to skip (pagination)
            
        Returns:
            Tuple[List[Dict], int]: Tuple of (templates list, total count)
        """
        cache_key = None
        
        # Only cache if no user filtering and include_system is True
        if self._cache_enabled and include_system and not user_id:
            cache_key = CACHE_KEY_CATEGORY.format(category)
            cached_result = get_cached_template(cache_key)
            
            if cached_result:
                templates_list, total_count = cached_result
                logger.debug(f"Retrieved {len(templates_list)} templates for category '{category}' from cache")
                return templates_list, total_count
        
        # Retrieve from repository
        try:
            templates_list, total_count = self._repository.find_by_category(
                category, include_system, user_id, limit, skip
            )
            
            # Cache if appropriate
            if self._cache_enabled and cache_key and templates_list:
                cache_template(cache_key, (templates_list, total_count))
                logger.debug(f"Cached {len(templates_list)} templates for category '{category}'")
            
            logger.info(f"Retrieved {len(templates_list)} templates for category '{category}' from repository")
            return templates_list, total_count
            
        except Exception as e:
            logger.error(f"Error retrieving templates for category '{category}': {str(e)}")
            return [], 0
    
    def get_system_templates(self, category: Optional[str] = None, 
                          limit: int = 50, skip: int = 0) -> Tuple[List[Dict], int]:
        """
        Retrieves system-defined templates
        
        Args:
            category: Optional category filter
            limit: Maximum number of templates to return
            skip: Number of templates to skip (pagination)
            
        Returns:
            Tuple[List[Dict], int]: Tuple of (system templates list, total count)
        """
        cache_key = None
        
        # Generate cache key if caching is enabled
        if self._cache_enabled:
            if category:
                cache_key = f"{CACHE_KEY_SYSTEM_TEMPLATES}:category:{category}"
            else:
                cache_key = CACHE_KEY_SYSTEM_TEMPLATES
                
            cached_result = get_cached_template(cache_key)
            
            if cached_result:
                templates_list, total_count = cached_result
                logger.debug(f"Retrieved {len(templates_list)} system templates from cache")
                return templates_list, total_count
        
        # Retrieve from repository
        try:
            templates_list, total_count = self._repository.find_system_templates(
                category, limit, skip
            )
            
            # Cache if appropriate
            if self._cache_enabled and cache_key and templates_list:
                cache_template(cache_key, (templates_list, total_count))
                logger.debug(f"Cached {len(templates_list)} system templates")
            
            logger.info(f"Retrieved {len(templates_list)} system templates from repository")
            return templates_list, total_count
            
        except Exception as e:
            logger.error(f"Error retrieving system templates: {str(e)}")
            return [], 0
    
    def get_user_templates(self, user_id: str, category: Optional[str] = None,
                        limit: int = 50, skip: int = 0) -> Tuple[List[Dict], int]:
        """
        Retrieves user-created templates
        
        Args:
            user_id: ID of the user
            category: Optional category filter
            limit: Maximum number of templates to return
            skip: Number of templates to skip (pagination)
            
        Returns:
            Tuple[List[Dict], int]: Tuple of (user templates list, total count)
        """
        if not user_id:
            logger.error("User ID is required for retrieving user templates")
            return [], 0
        
        # Retrieve from repository (no caching for user-specific content)
        try:
            templates_list, total_count = self._repository.find_user_templates(
                user_id, category, limit, skip
            )
            
            logger.info(f"Retrieved {len(templates_list)} templates for user '{user_id}' from repository")
            return templates_list, total_count
            
        except Exception as e:
            logger.error(f"Error retrieving templates for user '{user_id}': {str(e)}")
            return [], 0
    
    def get_all_templates(self, include_system: bool = True, user_id: Optional[str] = None,
                       category: Optional[str] = None, limit: int = 50, 
                       skip: int = 0) -> Tuple[List[Dict], int]:
        """
        Retrieves all templates with filtering options
        
        Args:
            include_system: Whether to include system templates
            user_id: User ID for user-specific templates
            category: Optional category filter
            limit: Maximum number of templates to return
            skip: Number of templates to skip (pagination)
            
        Returns:
            Tuple[List[Dict], int]: Tuple of (templates list, total count)
        """
        cache_key = None
        
        # Only cache if no user filtering and include_system is True and no category filter
        if self._cache_enabled and include_system and not user_id and not category:
            cache_key = CACHE_KEY_ALL_TEMPLATES
            cached_result = get_cached_template(cache_key)
            
            if cached_result:
                templates_list, total_count = cached_result
                logger.debug(f"Retrieved {len(templates_list)} templates from cache")
                return templates_list, total_count
        
        # Retrieve from repository
        try:
            templates_list, total_count = self._repository.get_all_templates(
                include_system, user_id, category, limit, skip
            )
            
            # Cache if appropriate
            if self._cache_enabled and cache_key and templates_list:
                cache_template(cache_key, (templates_list, total_count))
                logger.debug(f"Cached {len(templates_list)} templates")
            
            logger.info(f"Retrieved {len(templates_list)} templates from repository")
            return templates_list, total_count
            
        except Exception as e:
            logger.error(f"Error retrieving templates: {str(e)}")
            return [], 0
    
    def create_template(self, template_data: Dict) -> Dict:
        """
        Creates a new template
        
        Args:
            template_data: Template data to create
            
        Returns:
            Dict: Created template with generated ID
            
        Raises:
            TemplateValidationError: If template validation fails
        """
        # Validate template data
        self.validate_template(template_data)
        
        try:
            # Create template in repository
            created_template = self._repository.create(template_data)
            
            # Invalidate relevant cache entries
            self.invalidate_cache_entries(
                template_id=created_template.get('_id'),
                category=created_template.get('category')
            )
            
            logger.info(f"Created template '{created_template.get('name')}' with ID '{created_template.get('_id')}'")
            return created_template
            
        except Exception as e:
            logger.error(f"Error creating template: {str(e)}")
            raise
    
    def update_template(self, template_id: str, update_data: Dict, 
                     user_id: Optional[str] = None) -> Dict:
        """
        Updates an existing template
        
        Args:
            template_id: ID of the template to update
            update_data: Update data for the template
            user_id: ID of user performing the update (for permission checking)
            
        Returns:
            Dict: Updated template data
            
        Raises:
            TemplateValidationError: If update data is invalid
            TemplateNotFoundError: If template doesn't exist
            TemplateAccessError: If user doesn't have permission
        """
        # Validate update data
        self.validate_template(update_data, is_update=True)
        
        try:
            # Update template in repository
            updated_template = self._repository.update(template_id, update_data, user_id)
            
            # Invalidate relevant cache entries
            self.invalidate_cache_entries(
                template_id=template_id,
                category=updated_template.get('category')
            )
            
            user_info = f" by user '{user_id}'" if user_id else ""
            logger.info(f"Updated template '{template_id}'{user_info}")
            return updated_template
            
        except (TemplateNotFoundError, TemplateAccessError):
            # Re-raise these specific exceptions
            raise
        except Exception as e:
            logger.error(f"Error updating template '{template_id}': {str(e)}")
            raise
    
    def delete_template(self, template_id: str, user_id: Optional[str] = None,
                     is_admin: bool = False) -> bool:
        """
        Deletes a template with permission checking
        
        Args:
            template_id: ID of the template to delete
            user_id: ID of user performing the delete (for permission checking)
            is_admin: Whether the user has admin privileges
            
        Returns:
            bool: True if deleted successfully
            
        Raises:
            TemplateNotFoundError: If template doesn't exist
            TemplateAccessError: If user doesn't have permission
        """
        try:
            # Get template to know its category for cache invalidation
            template = self.get_template(template_id)
            category = template.get('category') if template else None
            
            # Delete from repository
            success = self._repository.delete(template_id, user_id, is_admin)
            
            if success:
                # Invalidate cache entries
                self.invalidate_cache_entries(
                    template_id=template_id,
                    category=category
                )
                
                user_info = f" by user '{user_id}'" if user_id else ""
                admin_info = " with admin privileges" if is_admin else ""
                logger.info(f"Deleted template '{template_id}'{user_info}{admin_info}")
            else:
                logger.warning(f"Failed to delete template '{template_id}'")
                
            return success
            
        except (TemplateNotFoundError, TemplateAccessError):
            # Re-raise these specific exceptions
            raise
        except Exception as e:
            logger.error(f"Error deleting template '{template_id}': {str(e)}")
            raise
    
    def search_templates(self, search_text: str, include_system: bool = True,
                      user_id: Optional[str] = None, category: Optional[str] = None,
                      limit: int = 50, skip: int = 0) -> Tuple[List[Dict], int]:
        """
        Searches for templates matching a query string
        
        Args:
            search_text: Text to search for
            include_system: Whether to include system templates
            user_id: User ID for user-specific templates
            category: Optional category filter
            limit: Maximum number of templates to return
            skip: Number of templates to skip (pagination)
            
        Returns:
            Tuple[List[Dict], int]: Tuple of (matching templates list, total count)
        """
        if not search_text or not search_text.strip():
            logger.warning("Empty search text provided")
            return [], 0
        
        # Searches are not cached due to their dynamic nature
        try:
            templates_list, total_count = self._repository.search(
                search_text, include_system, user_id, category, limit, skip
            )
            
            logger.info(f"Search for '{search_text}' returned {len(templates_list)} templates")
            return templates_list, total_count
            
        except Exception as e:
            logger.error(f"Error searching templates for '{search_text}': {str(e)}")
            return [], 0
    
    def get_template_categories(self) -> List[str]:
        """
        Retrieves all unique template categories
        
        Returns:
            List[str]: List of category names
        """
        # Try to get from cache if enabled
        if self._cache_enabled:
            cached_categories = get_cached_template(CACHE_KEY_CATEGORIES)
            
            if cached_categories:
                logger.debug(f"Retrieved {len(cached_categories)} template categories from cache")
                return cached_categories
        
        # Retrieve from repository
        try:
            categories = self._repository.get_categories()
            
            # Cache if enabled
            if self._cache_enabled:
                cache_template(CACHE_KEY_CATEGORIES, categories)
                logger.debug(f"Cached {len(categories)} template categories")
            
            logger.info(f"Retrieved {len(categories)} template categories from repository")
            return categories
            
        except Exception as e:
            logger.error(f"Error retrieving template categories: {str(e)}")
            return []
    
    def initialize_default_templates(self) -> int:
        """
        Creates default system templates if they don't exist
        
        Returns:
            int: Number of templates created
        """
        try:
            # Get default templates
            default_templates = get_default_templates()
            
            # Initialize system templates in repository
            created_count = self._repository.initialize_system_templates(default_templates)
            
            if created_count > 0:
                # Invalidate all template caches if any were created
                self.invalidate_cache_entries()
                logger.info(f"Initialized {created_count} default system templates")
            else:
                logger.info("No new default templates were created (already exist)")
                
            return created_count
            
        except Exception as e:
            logger.error(f"Error initializing default templates: {str(e)}")
            return 0
    
    def validate_template(self, template_data: Dict, is_update: bool = False) -> bool:
        """
        Validates template data structure and content
        
        Args:
            template_data: Template data to validate
            is_update: Whether this is an update operation
            
        Returns:
            bool: True if template is valid
            
        Raises:
            TemplateValidationError: If validation fails
        """
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
    
    def invalidate_cache_entries(self, template_id: Optional[str] = None, 
                              category: Optional[str] = None) -> None:
        """
        Invalidates cache entries related to templates
        
        Args:
            template_id: Optional specific template ID to invalidate
            category: Optional category to invalidate
        """
        if not self._cache_enabled:
            return
        
        try:
            # Invalidate specific template if provided
            if template_id:
                cache_template(template_id, None, ttl=1)  # Short TTL effectively invalidates
                logger.debug(f"Invalidated cache for template '{template_id}'")
            
            # Invalidate category if provided
            if category:
                cache_template(CACHE_KEY_CATEGORY.format(category), None, ttl=1)
                logger.debug(f"Invalidated cache for category '{category}'")
            
            # Always invalidate all templates and system templates caches
            cache_template(CACHE_KEY_ALL_TEMPLATES, None, ttl=1)
            cache_template(CACHE_KEY_SYSTEM_TEMPLATES, None, ttl=1)
            
            # Invalidate categories cache
            cache_template(CACHE_KEY_CATEGORIES, None, ttl=1)
            
            logger.debug("Invalidated template caches")
        
        except Exception as e:
            logger.warning(f"Error invalidating template cache entries: {str(e)}")