"""
Service layer for managing AI improvement prompt templates in the writing enhancement platform.

This module provides business logic for template operations including CRUD functionality,
usage tracking, template validation, and optimization based on user acceptance rates.
"""

import logging
import re
from datetime import datetime
from typing import Optional, List, Dict

from bson import ObjectId

from ...data.mongodb.repositories.template_repository import TemplateRepository, TemplateNotFoundError, TemplateAccessError
from ...data.mongodb.repositories.ai_interaction_repository import AIInteractionRepository
from ..utils.logger import setup_logger
from ..utils.validators import validate_template

# Set up logger for the module
logger = logging.getLogger(__name__)

# Regex pattern for extracting variables from templates
TEMPLATE_VARIABLE_PATTERN = r'{(.*?)}'

class TemplateService:
    """Service class that provides business logic for managing improvement templates"""
    
    def __init__(self, template_repository: TemplateRepository, ai_interaction_repository: AIInteractionRepository):
        """
        Initializes the template service with required dependencies
        
        Args:
            template_repository: Repository for template storage and retrieval
            ai_interaction_repository: Repository for AI interaction data
        """
        self._template_repository = template_repository
        self._ai_interaction_repository = ai_interaction_repository
        logger.info("Template service initialized successfully")
    
    def get_template_by_id(self, template_id: str) -> Dict:
        """
        Retrieves a single template by its unique identifier
        
        Args:
            template_id: The ID of the template to retrieve
            
        Returns:
            Template object or None if not found
        """
        logger.info(f"Retrieving template with ID: {template_id}")
        try:
            # Retrieve the template using the repository
            template = self._template_repository.get_by_id(template_id)
            return template
        except ValueError as e:
            logger.error(f"Invalid template ID format: {template_id}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving template {template_id}: {str(e)}")
            raise
    
    def get_all_templates(self, system_only: bool = False, user_only: bool = False) -> List[Dict]:
        """
        Retrieves all available templates, optionally filtered by system/user created
        
        Args:
            system_only: If True, return only system templates
            user_only: If True, return only user-created templates
            
        Returns:
            List of template objects
        """
        logger.info(f"Retrieving templates with filters - system_only: {system_only}, user_only: {user_only}")
        try:
            # Apply filtering logic based on parameters
            if system_only and user_only:
                logger.warning("Both system_only and user_only are True, ignoring both filters")
                system_only = user_only = False
            
            if system_only:
                # Get system templates only
                templates, _ = self._template_repository.find_system_templates()
                return templates
            elif user_only:
                # In a real implementation, we would get the current user's ID
                # For now, just return an empty list since we don't have a user_id
                logger.warning("User-only filter requires a user ID, which is not provided")
                return []
            else:
                # Get all templates
                templates, _ = self._template_repository.get_all_templates()
                return templates
        except Exception as e:
            logger.error(f"Error retrieving templates: {str(e)}")
            raise
    
    def get_templates_by_category(self, category: str) -> List[Dict]:
        """
        Retrieves templates filtered by category
        
        Args:
            category: The category to filter by
            
        Returns:
            List of template objects in the specified category
        """
        logger.info(f"Retrieving templates in category: {category}")
        try:
            # Validate the category string
            if not category or not isinstance(category, str):
                logger.error(f"Invalid category: {category}")
                return []
            
            # Use the repository to get templates in the specified category
            templates, _ = self._template_repository.find_by_category(category)
            
            return templates
        except Exception as e:
            logger.error(f"Error retrieving templates by category {category}: {str(e)}")
            raise
    
    def create_template(self, template_data: Dict, user_id: str) -> Dict:
        """
        Creates a new template in the system
        
        Args:
            template_data: Template data including name, description, promptText, and category
            user_id: ID of the user creating the template (None for system templates)
            
        Returns:
            Newly created template object with id
        """
        logger.info(f"Creating new template: {template_data.get('name', 'unnamed')}")
        try:
            # Validate the template data using the imported validator
            if not validate_template(template_data):
                logger.error("Template validation failed")
                raise ValueError("Invalid template data")
            
            # Ensure required fields are present
            required_fields = ['name', 'promptText', 'category']
            for field in required_fields:
                if field not in template_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Extract variables from the template text
            template_text = template_data.get('promptText', '')
            variables = self._extract_variables(template_text)
            
            # Add createdBy if user_id is provided
            if user_id:
                template_data['createdBy'] = user_id
            
            # Create the template using the repository
            created_template = self._template_repository.create(template_data)
            
            logger.info(f"Created template with ID: {created_template.get('_id')}")
            return created_template
        except Exception as e:
            logger.error(f"Error creating template: {str(e)}")
            raise
    
    def update_template(self, template_id: str, template_data: Dict, user_id: str) -> Dict:
        """
        Updates an existing template
        
        Args:
            template_id: ID of the template to update
            template_data: New template data
            user_id: ID of the user performing the update
            
        Returns:
            Updated template object
        """
        logger.info(f"Updating template {template_id}")
        try:
            # Validate the template data if provided
            if template_data and not validate_template(template_data):
                logger.error("Template validation failed")
                raise ValueError("Invalid template data")
            
            # Extract variables if promptText is being updated
            if template_data and 'promptText' in template_data:
                variables = self._extract_variables(template_data['promptText'])
                # Could add variables to template_data if needed
            
            # The repository handles permissions checking
            updated_template = self._template_repository.update(template_id, template_data, user_id)
            
            logger.info(f"Updated template {template_id}")
            return updated_template
        except TemplateNotFoundError:
            logger.error(f"Template not found: {template_id}")
            raise ValueError(f"Template not found: {template_id}")
        except TemplateAccessError:
            logger.error(f"User {user_id} does not have permission to update template {template_id}")
            raise ValueError("Permission denied")
        except ValueError:
            # Re-raise ValueError (like invalid ObjectId)
            raise
        except Exception as e:
            logger.error(f"Error updating template {template_id}: {str(e)}")
            raise
    
    def delete_template(self, template_id: str, user_id: str) -> bool:
        """
        Deletes a template from the system
        
        Args:
            template_id: ID of the template to delete
            user_id: ID of the user performing the deletion
            
        Returns:
            True if deleted successfully, False otherwise
        """
        logger.info(f"Deleting template {template_id}")
        try:
            # Determine if the user is an admin (simplified for now)
            is_admin = False  # In a real system, this would check user roles
            
            # The repository handles permissions checking
            success = self._template_repository.delete(template_id, user_id, is_admin)
            
            if success:
                logger.info(f"Deleted template {template_id}")
            else:
                logger.warning(f"Failed to delete template {template_id}")
            
            return success
        except TemplateNotFoundError:
            logger.error(f"Template not found: {template_id}")
            raise ValueError(f"Template not found: {template_id}")
        except TemplateAccessError:
            logger.error(f"User {user_id} does not have permission to delete template {template_id}")
            raise ValueError("Permission denied")
        except ValueError:
            # Re-raise ValueError (like invalid ObjectId)
            raise
        except Exception as e:
            logger.error(f"Error deleting template {template_id}: {str(e)}")
            raise
    
    def get_template_usage_metrics(self, template_id: str) -> Dict:
        """
        Retrieves usage metrics for a specific template
        
        Args:
            template_id: ID of the template to get metrics for
            
        Returns:
            Metrics including usage count, acceptance rate, etc.
        """
        logger.info(f"Retrieving usage metrics for template {template_id}")
        try:
            # Check if the template exists
            template = self.get_template_by_id(template_id)
            if not template:
                logger.error(f"Template not found with ID: {template_id}")
                raise ValueError(f"Template not found: {template_id}")
            
            # Query for interactions related to this template
            # Note: This is a simplified approach since there's no direct method
            # in AIInteractionRepository to query by template ID
            
            # Get interactions statistics for relevant criteria
            # In a production system, we'd use a more efficient query
            stats = self._ai_interaction_repository.get_interaction_statistics(
                interaction_type='suggestion',
                start_date=(datetime.utcnow().replace(day=1))  # Current month
            )
            
            # Extract metrics relevant to this template
            # This is a simplification; in production we'd have more precise tracking
            usage_count = 0
            accepted_suggestions = 0
            rejected_suggestions = 0
            
            # Default metrics structure
            metrics = {
                'template_id': template_id,
                'template_name': template.get('name', 'unnamed'),
                'usage_count': usage_count,
                'total_suggestions': accepted_suggestions + rejected_suggestions,
                'accepted_suggestions': accepted_suggestions,
                'rejected_suggestions': rejected_suggestions,
                'acceptance_rate': 0 if accepted_suggestions + rejected_suggestions == 0 else
                                 accepted_suggestions / (accepted_suggestions + rejected_suggestions),
                'avg_suggestions_per_use': 0 if usage_count == 0 else
                                          (accepted_suggestions + rejected_suggestions) / usage_count
            }
            
            logger.info(f"Retrieved metrics for template {template_id}")
            return metrics
        except ValueError:
            # Re-raise ValueError (like invalid ObjectId)
            raise
        except Exception as e:
            logger.error(f"Error retrieving metrics for template {template_id}: {str(e)}")
            raise
    
    def get_popular_templates(self, limit: int = 10) -> List[Dict]:
        """
        Retrieves most frequently used templates
        
        Args:
            limit: Maximum number of templates to return
            
        Returns:
            List of popular templates with usage metrics
        """
        logger.info(f"Retrieving {limit} most popular templates")
        try:
            # Since there's no direct way to get template popularity,
            # we'll get all templates and simulate popularity metrics
            
            # Get all templates
            all_templates, _ = self._template_repository.get_all_templates()
            
            # If there are no templates, return an empty list
            if not all_templates:
                return []
            
            # In a production system, we would query the interaction data
            # to determine actual template popularity.
            # For now, we'll prioritize system templates as they're likely
            # to be the most used ones
            
            # Sort templates (system templates first, then by name)
            sorted_templates = sorted(
                all_templates,
                key=lambda t: (not t.get('isSystem', False), t.get('name', ''))
            )
            
            # Limit the number of templates returned
            popular_templates = sorted_templates[:min(limit, len(sorted_templates))]
            
            # Add usage metrics
            for template in popular_templates:
                template['usage_metrics'] = {
                    'usage_count': 0,  # Would be actual counts in production
                    'acceptance_rate': 0.0,  # Would be actual rates in production
                }
            
            logger.info(f"Retrieved {len(popular_templates)} popular templates")
            return popular_templates
        except Exception as e:
            logger.error(f"Error retrieving popular templates: {str(e)}")
            raise
    
    def optimize_template(self, template_id: str) -> Dict:
        """
        Analyzes template performance and suggests improvements
        
        Args:
            template_id: ID of the template to optimize
            
        Returns:
            Optimization suggestions based on usage patterns
        """
        logger.info(f"Optimizing template {template_id}")
        try:
            # Get template usage metrics
            metrics = self.get_template_usage_metrics(template_id)
            
            # Get the template data
            template = self.get_template_by_id(template_id)
            if not template:
                logger.error(f"Template not found with ID: {template_id}")
                raise ValueError(f"Template not found: {template_id}")
            
            # Analyze the metrics
            acceptance_rate = metrics.get('acceptance_rate', 0)
            usage_count = metrics.get('usage_count', 0)
            
            # Prepare analysis results
            analysis = {
                'template_id': template_id,
                'template_name': template.get('name', 'unnamed'),
                'current_metrics': metrics,
                'analysis': {
                    'performance': self._rate_template_performance(acceptance_rate, usage_count),
                    'issues': [],
                    'suggestions': []
                }
            }
            
            # Generate optimization suggestions based on metrics
            if usage_count < 5:
                analysis['analysis']['issues'].append("Insufficient usage data for reliable optimization")
            else:
                # Check acceptance rate
                if acceptance_rate < 0.5:
                    analysis['analysis']['issues'].append("Low acceptance rate")
                    analysis['analysis']['suggestions'].append(
                        "Consider revising the prompt to produce more relevant suggestions"
                    )
                
                # Check for variables
                variables = self._extract_variables(template.get('promptText', ''))
                if variables and acceptance_rate < 0.7:
                    analysis['analysis']['suggestions'].append(
                        "Review variable usage in template to ensure they provide proper context"
                    )
            
            logger.info(f"Completed optimization analysis for template {template_id}")
            return analysis
        except ValueError:
            # Re-raise ValueError (like invalid ObjectId)
            raise
        except Exception as e:
            logger.error(f"Error optimizing template {template_id}: {str(e)}")
            raise
    
    def _validate_user_permission(self, template_id: str, user_id: str) -> bool:
        """
        Private method to check if a user has permission to modify a template
        
        Args:
            template_id: ID of the template
            user_id: ID of the user
            
        Returns:
            True if user has permission, False otherwise
        """
        try:
            # Retrieve the template
            template = self.get_template_by_id(template_id)
            
            # If template doesn't exist, no one has permission
            if not template:
                return False
            
            # System templates can only be modified by admins/system
            # For simplicity, assume user_id=None means system/admin access
            if template.get('isSystem', False) and user_id:
                return False
            
            # User templates can only be modified by their creator
            creator_id = template.get('createdBy')
            if creator_id and creator_id != user_id:
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating user permission: {str(e)}")
            return False
    
    def _format_template(self, template_text: str, parameters: dict) -> str:
        """
        Private method to validate and format template text with variables
        
        Args:
            template_text: The template text with variable placeholders
            parameters: Dictionary of parameter values to insert
            
        Returns:
            Formatted template with variables replaced
        """
        if not template_text:
            return ""
        
        # Extract variables from the template
        variables = self._extract_variables(template_text)
        
        # Check that all required variables are present in parameters
        missing_vars = [var for var in variables if var not in parameters]
        if missing_vars:
            raise ValueError(f"Missing required parameters: {', '.join(missing_vars)}")
        
        # Replace each variable with its value
        formatted_text = template_text
        for var in variables:
            placeholder = f"{{{var}}}"
            value = str(parameters.get(var, ''))
            formatted_text = formatted_text.replace(placeholder, value)
        
        return formatted_text
    
    def _extract_variables(self, template_text: str) -> list:
        """
        Private method to extract variable placeholders from template text
        
        Args:
            template_text: The template text to analyze
            
        Returns:
            List of variable names found in the template
        """
        if not template_text:
            return []
        
        # Find all variable placeholders using regex
        matches = re.findall(TEMPLATE_VARIABLE_PATTERN, template_text)
        
        # Return unique variable names
        return list(set(matches))
    
    def _rate_template_performance(self, acceptance_rate: float, usage_count: int) -> str:
        """
        Private method to rate template performance based on metrics
        
        Args:
            acceptance_rate: The template acceptance rate
            usage_count: Number of times the template has been used
            
        Returns:
            Performance rating (Excellent, Good, Average, Poor, or Insufficient Data)
        """
        if usage_count < 5:
            return "Insufficient Data"
        
        if acceptance_rate >= 0.8:
            return "Excellent"
        elif acceptance_rate >= 0.6:
            return "Good"
        elif acceptance_rate >= 0.4:
            return "Average"
        else:
            return "Poor"