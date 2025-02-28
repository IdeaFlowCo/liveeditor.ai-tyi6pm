"""
MongoDB repository implementation for AI prompt templates used in the writing enhancement platform.
Handles CRUD operations for both system-defined and user-created improvement templates,
with support for categorization, searching, and access control.
"""

import datetime
from typing import Dict, List, Optional, Tuple, Any, Union
import pymongo
from pymongo.errors import PyMongoError
from bson import ObjectId

from ..connection import get_collection, str_to_object_id, object_id_to_str
from ...core.utils.logger import get_logger
from ...core.utils.validators import validate_object_id

# Initialize logger
logger = get_logger(__name__)


class TemplateRepository:
    """MongoDB repository for AI prompt template operations with support for system and user-created templates"""
    
    COLLECTION_NAME = 'templates'
    
    def __init__(self):
        """Initializes the template repository with MongoDB collection"""
        self._collection = get_collection(self.COLLECTION_NAME)
        
        # Create necessary indexes
        self._collection.create_index("createdBy")
        self._collection.create_index("category")
        self._collection.create_index("isSystem")
        
        # Text index for search functionality
        self._collection.create_index([
            ("name", pymongo.TEXT),
            ("description", pymongo.TEXT),
            ("promptText", pymongo.TEXT)
        ])
        
        logger.info(f"TemplateRepository initialized with collection: {self.COLLECTION_NAME}")

    def create(self, template_data: Dict) -> Dict:
        """Creates a new template in the database
        
        Args:
            template_data: Template data to be created
            
        Returns:
            The created template with ID
        """
        # Validate required fields
        if not template_data.get('name'):
            raise ValueError("Template name is required")
        if not template_data.get('promptText'):
            raise ValueError("Template promptText is required")
        if not template_data.get('category'):
            raise ValueError("Template category is required")
        
        # Set creation time
        template_data['createdAt'] = datetime.datetime.utcnow()
        
        # Set system flag (default to False if not provided)
        template_data['isSystem'] = template_data.get('isSystem', False)
        
        # If it's a system template, createdBy can be null
        if 'createdBy' not in template_data and not template_data['isSystem']:
            raise ValueError("createdBy is required for non-system templates")
        
        try:
            # Insert the document
            result = self._collection.insert_one(template_data)
            
            # Get the inserted document
            created_template = self._collection.find_one({"_id": result.inserted_id})
            
            # Format the template for response
            formatted_template = self._format_template(created_template)
            
            logger.info(f"Created template: {formatted_template['_id']}")
            return formatted_template
            
        except PyMongoError as e:
            logger.error(f"Error creating template: {str(e)}")
            raise

    def get_by_id(self, template_id: str) -> Optional[Dict]:
        """Retrieves a template by its ID
        
        Args:
            template_id: The ID of the template to retrieve
            
        Returns:
            The template document or None if not found
        """
        try:
            # Validate ID format
            validate_object_id(template_id)
            
            # Convert to ObjectId
            obj_id = str_to_object_id(template_id)
            
            # Query the database
            template = self._collection.find_one({"_id": obj_id})
            
            if not template:
                logger.info(f"Template not found with ID: {template_id}")
                return None
            
            # Format the template for response
            formatted_template = self._format_template(template)
            
            logger.info(f"Retrieved template by ID: {template_id}")
            return formatted_template
            
        except ValueError as e:
            logger.error(f"Invalid template ID format: {template_id}")
            return None
        except PyMongoError as e:
            logger.error(f"Error retrieving template: {str(e)}")
            raise

    def get_by_name(self, template_name: str) -> Optional[Dict]:
        """Retrieves a template by its name
        
        Args:
            template_name: The name of the template to retrieve
            
        Returns:
            The template document or None if not found
        """
        try:
            # Query the database - case-insensitive exact match
            template = self._collection.find_one({
                "name": {"$regex": f"^{template_name}$", "$options": "i"}
            })
            
            if not template:
                logger.info(f"Template not found with name: {template_name}")
                return None
            
            # Format the template for response
            formatted_template = self._format_template(template)
            
            logger.info(f"Retrieved template by name: {template_name}")
            return formatted_template
            
        except PyMongoError as e:
            logger.error(f"Error retrieving template by name: {str(e)}")
            raise

    def find_by_category(self, category: str, include_system: bool = True, 
                        user_id: Optional[str] = None, limit: int = 20, 
                        skip: int = 0) -> Tuple[List[Dict], int]:
        """Finds templates in a specific category
        
        Args:
            category: The category to filter by
            include_system: Whether to include system templates
            user_id: If provided, include only this user's templates
            limit: Maximum number of templates to return
            skip: Number of templates to skip (for pagination)
            
        Returns:
            Tuple of (list of templates, total count)
        """
        try:
            # Build query
            query = {"category": category}
            
            # Handle access control
            if not include_system and not user_id:
                # If not including system templates and no user_id, return empty
                return [], 0
            elif not include_system:
                # Only user's templates
                query["createdBy"] = user_id
            elif user_id:
                # Both system and user's templates
                query["$or"] = [{"isSystem": True}, {"createdBy": user_id}]
            
            # Get total count
            total_count = self._collection.count_documents(query)
            
            # Get paginated results
            cursor = self._collection.find(query).sort("name", 1).skip(skip).limit(limit)
            
            # Format templates
            templates = [self._format_template(template) for template in cursor]
            
            logger.info(f"Found {len(templates)} templates in category '{category}' (total: {total_count})")
            return templates, total_count
            
        except PyMongoError as e:
            logger.error(f"Error finding templates by category: {str(e)}")
            raise

    def find_system_templates(self, category: Optional[str] = None, 
                             limit: int = 20, skip: int = 0) -> Tuple[List[Dict], int]:
        """Retrieves all system-defined templates
        
        Args:
            category: Optional category filter
            limit: Maximum number of templates to return
            skip: Number of templates to skip (for pagination)
            
        Returns:
            Tuple of (list of system templates, total count)
        """
        try:
            # Build query
            query = {"isSystem": True}
            
            # Add category filter if provided
            if category:
                query["category"] = category
            
            # Get total count
            total_count = self._collection.count_documents(query)
            
            # Get paginated results
            cursor = self._collection.find(query).sort("name", 1).skip(skip).limit(limit)
            
            # Format templates
            templates = [self._format_template(template) for template in cursor]
            
            logger.info(f"Found {len(templates)} system templates (total: {total_count})")
            return templates, total_count
            
        except PyMongoError as e:
            logger.error(f"Error finding system templates: {str(e)}")
            raise

    def find_user_templates(self, user_id: str, category: Optional[str] = None,
                           limit: int = 20, skip: int = 0) -> Tuple[List[Dict], int]:
        """Retrieves templates created by a specific user
        
        Args:
            user_id: The user ID to filter by
            category: Optional category filter
            limit: Maximum number of templates to return
            skip: Number of templates to skip (for pagination)
            
        Returns:
            Tuple of (list of user templates, total count)
        """
        try:
            if not user_id:
                raise ValueError("user_id is required")
                
            # Build query
            query = {"createdBy": user_id}
            
            # Add category filter if provided
            if category:
                query["category"] = category
            
            # Get total count
            total_count = self._collection.count_documents(query)
            
            # Get paginated results - newest first
            cursor = self._collection.find(query).sort("createdAt", -1).skip(skip).limit(limit)
            
            # Format templates
            templates = [self._format_template(template) for template in cursor]
            
            logger.info(f"Found {len(templates)} templates for user {user_id} (total: {total_count})")
            return templates, total_count
            
        except PyMongoError as e:
            logger.error(f"Error finding user templates: {str(e)}")
            raise

    def get_all_templates(self, include_system: bool = True, user_id: Optional[str] = None,
                         category: Optional[str] = None, limit: int = 20, 
                         skip: int = 0) -> Tuple[List[Dict], int]:
        """Retrieves all templates with filtering options
        
        Args:
            include_system: Whether to include system templates
            user_id: If provided, include only this user's templates
            category: Optional category filter
            limit: Maximum number of templates to return
            skip: Number of templates to skip (for pagination)
            
        Returns:
            Tuple of (list of templates, total count)
        """
        try:
            # Build query
            query = {}
            
            # Handle access control
            if not include_system and not user_id:
                # If not including system templates and no user_id, return empty
                return [], 0
            elif not include_system:
                # Only user's templates
                query["createdBy"] = user_id
            elif user_id:
                # Both system and user's templates
                query["$or"] = [{"isSystem": True}, {"createdBy": user_id}]
            
            # Add category filter if provided
            if category:
                query["category"] = category
            
            # Get total count
            total_count = self._collection.count_documents(query)
            
            # Define sort order: system templates first, then by creation date
            sort_params = [("isSystem", -1), ("createdAt", -1)]
            
            # Get paginated results
            cursor = self._collection.find(query).sort(sort_params).skip(skip).limit(limit)
            
            # Format templates
            templates = [self._format_template(template) for template in cursor]
            
            logger.info(f"Found {len(templates)} templates (total: {total_count})")
            return templates, total_count
            
        except PyMongoError as e:
            logger.error(f"Error retrieving all templates: {str(e)}")
            raise

    def update(self, template_id: str, update_data: Dict, user_id: Optional[str] = None) -> Dict:
        """Updates an existing template with access control
        
        Args:
            template_id: ID of the template to update
            update_data: New template data
            user_id: ID of the user performing the update (for access control)
            
        Returns:
            The updated template
            
        Raises:
            TemplateNotFoundError: If template does not exist
            TemplateAccessError: If user does not have permission to update
        """
        try:
            # Validate ID format
            validate_object_id(template_id)
            
            # Convert to ObjectId
            obj_id = str_to_object_id(template_id)
            
            # Get the existing template to check ownership
            existing_template = self._collection.find_one({"_id": obj_id})
            
            if not existing_template:
                raise TemplateNotFoundError(template_id)
            
            # Check authorization
            is_system_template = existing_template.get('isSystem', False)
            template_owner = existing_template.get('createdBy')
            
            if is_system_template and user_id:
                # System templates can only be updated by admins
                # For simplicity, we'll assume user_id=None means admin access
                raise TemplateAccessError(template_id, user_id)
            elif template_owner and user_id and template_owner != user_id:
                # User templates can only be updated by owner
                raise TemplateAccessError(template_id, user_id)
            
            # Prepare update
            update_fields = {}
            
            # Only allow updating specific fields
            for field in ['name', 'description', 'promptText', 'category']:
                if field in update_data:
                    update_fields[field] = update_data[field]
            
            # Don't allow changing system status
            if 'isSystem' in update_data:
                logger.warning(f"Attempt to change isSystem status for template {template_id} was ignored")
            
            # Update the document
            result = self._collection.update_one(
                {"_id": obj_id},
                {"$set": update_fields}
            )
            
            if result.modified_count == 0:
                logger.warning(f"Template {template_id} was not modified")
            
            # Get the updated document
            updated_template = self._collection.find_one({"_id": obj_id})
            
            # Format the template for response
            formatted_template = self._format_template(updated_template)
            
            logger.info(f"Updated template: {template_id}")
            return formatted_template
            
        except (TemplateNotFoundError, TemplateAccessError):
            # Re-raise these specific exceptions
            raise
        except ValueError as e:
            logger.error(f"Invalid template ID format: {template_id}")
            raise
        except PyMongoError as e:
            logger.error(f"Error updating template: {str(e)}")
            raise

    def delete(self, template_id: str, user_id: Optional[str] = None, is_admin: bool = False) -> bool:
        """Deletes a template with ownership validation
        
        Args:
            template_id: ID of the template to delete
            user_id: ID of the user performing the delete (for access control)
            is_admin: Whether the user has admin privileges
            
        Returns:
            True if deleted successfully, False otherwise
            
        Raises:
            TemplateNotFoundError: If template does not exist
            TemplateAccessError: If user does not have permission to delete
        """
        try:
            # Validate ID format
            validate_object_id(template_id)
            
            # Convert to ObjectId
            obj_id = str_to_object_id(template_id)
            
            # Get the existing template to check ownership
            existing_template = self._collection.find_one({"_id": obj_id})
            
            if not existing_template:
                raise TemplateNotFoundError(template_id)
            
            # Check authorization
            is_system_template = existing_template.get('isSystem', False)
            template_owner = existing_template.get('createdBy')
            
            if is_system_template and not is_admin:
                # System templates can only be deleted by admins
                raise TemplateAccessError(template_id, user_id)
            elif template_owner and user_id and template_owner != user_id and not is_admin:
                # User templates can only be deleted by owner or admin
                raise TemplateAccessError(template_id, user_id)
            
            # Delete the document
            result = self._collection.delete_one({"_id": obj_id})
            
            success = result.deleted_count > 0
            
            if success:
                logger.info(f"Deleted template: {template_id}")
            else:
                logger.warning(f"Failed to delete template: {template_id}")
            
            return success
            
        except (TemplateNotFoundError, TemplateAccessError):
            # Re-raise these specific exceptions
            raise
        except ValueError as e:
            logger.error(f"Invalid template ID format: {template_id}")
            raise
        except PyMongoError as e:
            logger.error(f"Error deleting template: {str(e)}")
            raise

    def search(self, search_text: str, include_system: bool = True, 
              user_id: Optional[str] = None, category: Optional[str] = None,
              limit: int = 20, skip: int = 0) -> Tuple[List[Dict], int]:
        """Searches for templates by text content with access control
        
        Args:
            search_text: Text to search for in templates
            include_system: Whether to include system templates
            user_id: If provided, include only this user's templates
            category: Optional category filter
            limit: Maximum number of templates to return
            skip: Number of templates to skip (for pagination)
            
        Returns:
            Tuple of (list of matching templates, total count)
        """
        try:
            # Build access control part of query
            access_query = {}
            if not include_system and not user_id:
                # If not including system templates and no user_id, return empty
                return [], 0
            elif not include_system:
                # Only user's templates
                access_query["createdBy"] = user_id
            elif user_id:
                # Both system and user's templates
                access_query["$or"] = [{"isSystem": True}, {"createdBy": user_id}]
            
            # Build the search query
            query = {
                "$text": {"$search": search_text},
                **access_query
            }
            
            # Add category filter if provided
            if category:
                query["category"] = category
            
            # Get total count
            total_count = self._collection.count_documents(query)
            
            # Get paginated results with text search scoring
            cursor = self._collection.find(
                query,
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).skip(skip).limit(limit)
            
            # Format templates
            templates = [self._format_template(template) for template in cursor]
            
            logger.info(f"Found {len(templates)} templates matching '{search_text}' (total: {total_count})")
            return templates, total_count
            
        except PyMongoError as e:
            logger.error(f"Error searching templates: {str(e)}")
            raise

    def get_categories(self) -> List[str]:
        """Retrieves all unique template categories
        
        Returns:
            List of category names
        """
        try:
            # Get distinct categories
            categories = self._collection.distinct("category")
            
            # Sort alphabetically
            categories.sort()
            
            logger.info(f"Retrieved {len(categories)} template categories")
            return categories
            
        except PyMongoError as e:
            logger.error(f"Error retrieving template categories: {str(e)}")
            raise

    def initialize_system_templates(self, templates: List[Dict]) -> int:
        """Creates default system templates if they don't exist
        
        Args:
            templates: List of template data to initialize
            
        Returns:
            Number of templates created
        """
        try:
            created_count = 0
            
            for template_data in templates:
                # Check if template already exists
                existing = self._collection.find_one({
                    "name": template_data["name"],
                    "isSystem": True
                })
                
                if not existing:
                    # Add creation time
                    template_data["createdAt"] = datetime.datetime.utcnow()
                    
                    # Ensure it's marked as a system template
                    template_data["isSystem"] = True
                    
                    # Insert the template
                    self._collection.insert_one(template_data)
                    created_count += 1
            
            logger.info(f"Initialized {created_count} system templates")
            return created_count
            
        except PyMongoError as e:
            logger.error(f"Error initializing system templates: {str(e)}")
            raise

    def _format_template(self, template: Dict) -> Dict:
        """Formats a template document for API response
        
        Args:
            template: Template document from MongoDB
            
        Returns:
            Formatted template with string IDs and ISO dates
        """
        if not template:
            return None
            
        # Create a copy to avoid modifying the original
        formatted = dict(template)
        
        # Convert ObjectId to string
        if '_id' in formatted:
            formatted['_id'] = object_id_to_str(formatted['_id'])
        
        # Format dates
        if 'createdAt' in formatted and isinstance(formatted['createdAt'], datetime.datetime):
            formatted['createdAt'] = formatted['createdAt'].isoformat()
        
        return formatted


class TemplateNotFoundError(Exception):
    """Exception raised when a template cannot be found"""
    
    def __init__(self, template_id: str, message: str = None):
        """Initialize the template not found error
        
        Args:
            template_id: ID of the template that was not found
            message: Optional custom error message
        """
        self.template_id = template_id
        if not message:
            message = f"Template with ID '{template_id}' not found"
        super().__init__(message)


class TemplateAccessError(Exception):
    """Exception raised when a user doesn't have access to modify a template"""
    
    def __init__(self, template_id: str, user_id: str, message: str = None):
        """Initialize the template access error
        
        Args:
            template_id: ID of the template that was not accessible
            user_id: ID of the user who tried to access the template
            message: Optional custom error message
        """
        self.template_id = template_id
        self.user_id = user_id
        if not message:
            message = f"User '{user_id}' does not have permission to modify template '{template_id}'"
        super().__init__(message)