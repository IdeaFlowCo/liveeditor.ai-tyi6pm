"""
Implements RESTful API endpoints for the AI prompt template management functionality,
allowing retrieval, creation, modification and deletion of templates used for
AI-powered writing improvements. Supports both system-defined and user-created
templates with appropriate authentication controls.
"""

from flask_restful import Resource, reqparse
from flask import request, jsonify, make_response

from ...core.templates.template_service import TemplateService
from ..schemas.template_schema import (
    template_create_schema,
    template_update_schema,
    template_response_schema,
    template_list_query_schema,
    template_list_response_schema,
    template_category_schema,
    template_search_schema,
)
from ..middleware.auth_middleware import auth_required, get_current_user_id, is_authenticated
from ...core.utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)


class TemplateResource(Resource):
    """Resource for managing individual template operations"""
    
    def __init__(self, template_service: TemplateService):
        """Initialize the template resource with required dependencies"""
        self._template_service = template_service
        logger.info("Template resource initialized")
        
    @auth_required(allow_anonymous=True)
    def get(self, template_id):
        """Retrieve a template by ID"""
        logger.info(f"Retrieving template with ID: {template_id}")
        
        try:
            # Get current user ID (may be None for anonymous users)
            user_id = get_current_user_id()
            
            # Get template by ID
            template = self._template_service.get_template_by_id(template_id)
            
            if not template:
                logger.warning(f"Template not found: {template_id}")
                return {"error": "Template not found"}, 404
                
            # Serialize template data
            result = template_response_schema.dump(template)
            return result, 200
            
        except ValueError as e:
            logger.error(f"Error retrieving template {template_id}: {str(e)}")
            return {"error": str(e)}, 400
        except Exception as e:
            logger.error(f"Unexpected error retrieving template {template_id}: {str(e)}")
            return {"error": "Internal server error"}, 500
    
    @auth_required(allow_anonymous=False)
    def put(self, template_id):
        """Update an existing template"""
        logger.info(f"Updating template with ID: {template_id}")
        
        # Get current user ID
        user_id = get_current_user_id()
        
        try:
            # Parse and validate request data
            data = request.get_json()
            errors = template_update_schema.validate(data)
            if errors:
                return {"error": "Validation failed", "details": errors}, 400
            
            # Update the template
            updated_template = self._template_service.update_template(template_id, data, user_id)
            
            # Serialize the updated template
            result = template_response_schema.dump(updated_template)
            return result, 200
            
        except ValueError as e:
            if "Permission denied" in str(e):
                logger.warning(f"Permission denied: User {user_id} attempted to update template {template_id}")
                return {"error": "Permission denied to modify this template"}, 403
            elif "Template not found" in str(e):
                logger.warning(f"Template not found: {template_id}")
                return {"error": "Template not found"}, 404
            else:
                logger.error(f"Validation error updating template {template_id}: {str(e)}")
                return {"error": str(e)}, 400
        except Exception as e:
            logger.error(f"Unexpected error updating template {template_id}: {str(e)}")
            return {"error": "Internal server error"}, 500
    
    @auth_required(allow_anonymous=False)
    def delete(self, template_id):
        """Delete a template"""
        logger.info(f"Deleting template with ID: {template_id}")
        
        # Get current user ID
        user_id = get_current_user_id()
        
        try:
            # Delete the template
            result = self._template_service.delete_template(template_id, user_id)
            
            if result:
                return "", 204
            else:
                logger.warning(f"Template not found: {template_id}")
                return {"error": "Template not found"}, 404
            
        except ValueError as e:
            if "Permission denied" in str(e):
                logger.warning(f"Permission denied: User {user_id} attempted to delete template {template_id}")
                return {"error": "Permission denied to delete this template"}, 403
            elif "Template not found" in str(e):
                logger.warning(f"Template not found: {template_id}")
                return {"error": "Template not found"}, 404
            else:
                logger.error(f"Validation error deleting template {template_id}: {str(e)}")
                return {"error": str(e)}, 400
        except Exception as e:
            logger.error(f"Unexpected error deleting template {template_id}: {str(e)}")
            return {"error": "Internal server error"}, 500


class TemplatesResource(Resource):
    """Resource for template collection operations"""
    
    def __init__(self, template_service: TemplateService):
        """Initialize the templates resource with required dependencies"""
        self._template_service = template_service
        logger.info("Templates collection resource initialized")
        
    @auth_required(allow_anonymous=True)
    def get(self):
        """List templates with filtering and pagination"""
        logger.info("Retrieving template list")
        
        try:
            # Parse query parameters
            parser = reqparse.RequestParser()
            parser.add_argument('category', type=str, location='args')
            parser.add_argument('systemOnly', type=bool, default=False, location='args')
            parser.add_argument('userOnly', type=bool, default=False, location='args')
            parser.add_argument('page', type=int, default=1, location='args')
            parser.add_argument('perPage', type=int, default=10, location='args')
            args = parser.parse_args()
            
            # Validate using schema
            errors = template_list_query_schema.validate(args)
            if errors:
                return {"error": "Validation failed", "details": errors}, 400
            
            # Get templates with the specified filters
            templates = self._template_service.get_all_templates(
                system_only=args.systemOnly,
                user_only=args.userOnly
            )
            
            # Apply pagination
            total = len(templates)
            page = max(1, args.page)  # Ensure page is at least 1
            per_page = min(max(1, args.perPage), 100)  # Ensure perPage is between 1 and 100
            skip = (page - 1) * per_page
            paginated_templates = templates[skip:skip + per_page]
            
            # Calculate total pages
            total_pages = (total + per_page - 1) // per_page if total > 0 else 0
            
            # Prepare response
            response = {
                "templates": paginated_templates,
                "total": total,
                "page": page,
                "perPage": per_page,
                "pages": total_pages
            }
            
            # Serialize using schema
            result = template_list_response_schema.dump(response)
            return result, 200
            
        except Exception as e:
            logger.error(f"Error retrieving templates: {str(e)}")
            return {"error": "Internal server error"}, 500
    
    @auth_required(allow_anonymous=False)
    def post(self):
        """Create a new template"""
        logger.info("Creating new template")
        
        # Get current user ID
        user_id = get_current_user_id()
        
        try:
            # Parse and validate request data
            data = request.get_json()
            errors = template_create_schema.validate(data)
            if errors:
                return {"error": "Validation failed", "details": errors}, 400
            
            # Create the template
            created_template = self._template_service.create_template(data, user_id)
            
            # Serialize the created template
            result = template_response_schema.dump(created_template)
            
            # Create response with Location header
            response = make_response(jsonify(result), 201)
            response.headers['Location'] = f"/api/templates/{created_template['_id']}"
            return response
            
        except ValueError as e:
            logger.error(f"Validation error creating template: {str(e)}")
            return {"error": str(e)}, 400
        except Exception as e:
            logger.error(f"Unexpected error creating template: {str(e)}")
            return {"error": "Internal server error"}, 500


class TemplateCategoriesResource(Resource):
    """Resource for listing available template categories"""
    
    def __init__(self, template_service: TemplateService):
        """Initialize the template categories resource"""
        self._template_service = template_service
        logger.info("Template categories resource initialized")
        
    @auth_required(allow_anonymous=True)
    def get(self):
        """List all available template categories"""
        logger.info("Retrieving template categories")
        
        try:
            # Get categories from template schema
            from ..schemas.template_schema import TEMPLATE_CATEGORIES
            
            # Prepare response
            response = {
                "categories": TEMPLATE_CATEGORIES
            }
            
            # Serialize using schema
            result = template_category_schema.dump(response)
            return result, 200
            
        except Exception as e:
            logger.error(f"Error retrieving template categories: {str(e)}")
            return {"error": "Internal server error"}, 500


class TemplateByCategoryResource(Resource):
    """Resource for listing templates by category"""
    
    def __init__(self, template_service: TemplateService):
        """Initialize the templates by category resource"""
        self._template_service = template_service
        logger.info("Template by category resource initialized")
        
    @auth_required(allow_anonymous=True)
    def get(self, category):
        """Get templates filtered by category"""
        logger.info(f"Retrieving templates by category: {category}")
        
        try:
            # Parse query parameters for pagination
            parser = reqparse.RequestParser()
            parser.add_argument('page', type=int, default=1, location='args')
            parser.add_argument('perPage', type=int, default=10, location='args')
            args = parser.parse_args()
            
            # Get templates in the specified category
            templates = self._template_service.get_templates_by_category(category)
            
            # Apply pagination
            total = len(templates)
            page = max(1, args.page)  # Ensure page is at least 1
            per_page = min(max(1, args.perPage), 100)  # Ensure perPage is between 1 and 100
            skip = (page - 1) * per_page
            paginated_templates = templates[skip:skip + per_page]
            
            # Calculate total pages
            total_pages = (total + per_page - 1) // per_page if total > 0 else 0
            
            # Prepare response
            response = {
                "templates": paginated_templates,
                "total": total,
                "page": page,
                "perPage": per_page,
                "pages": total_pages,
                "category": category
            }
            
            # Serialize using schema
            result = template_list_response_schema.dump(response)
            return result, 200
            
        except ValueError as e:
            logger.error(f"Invalid category: {category} - {str(e)}")
            return {"error": f"Invalid category: {str(e)}"}, 400
        except Exception as e:
            logger.error(f"Error retrieving templates by category {category}: {str(e)}")
            return {"error": "Internal server error"}, 500


class TemplateSearchResource(Resource):
    """Resource for searching templates"""
    
    def __init__(self, template_service: TemplateService):
        """Initialize the template search resource"""
        self._template_service = template_service
        logger.info("Template search resource initialized")
        
    @auth_required(allow_anonymous=True)
    def post(self):
        """Search for templates matching criteria"""
        logger.info("Searching for templates")
        
        try:
            # Parse and validate request data
            data = request.get_json()
            errors = template_search_schema.validate(data)
            if errors:
                return {"error": "Validation failed", "details": errors}, 400
            
            # Extract search parameters
            query = data.get('query', '')
            category = data.get('category')
            include_system = data.get('includeSystem', True)
            page = data.get('page', 1)
            per_page = data.get('perPage', 10)
            
            # Get templates based on category
            if category:
                templates = self._template_service.get_templates_by_category(category)
            else:
                templates = self._template_service.get_all_templates()
            
            # Filter templates based on query
            filtered_templates = []
            for template in templates:
                # Check if query appears in name, description, or promptText
                if (query.lower() in template.get('name', '').lower() or
                    query.lower() in template.get('description', '').lower() or
                    query.lower() in template.get('promptText', '').lower()):
                    # Check includeSystem filter
                    if not include_system and template.get('isSystem', False):
                        continue
                    filtered_templates.append(template)
            
            # Apply pagination
            total = len(filtered_templates)
            page = max(1, page)  # Ensure page is at least 1
            per_page = min(max(1, per_page), 100)  # Ensure perPage is between 1 and 100
            skip = (page - 1) * per_page
            paginated_templates = filtered_templates[skip:skip + per_page]
            
            # Calculate total pages
            total_pages = (total + per_page - 1) // per_page if total > 0 else 0
            
            # Prepare response
            response = {
                "templates": paginated_templates,
                "total": total,
                "page": page,
                "perPage": per_page,
                "pages": total_pages,
                "query": query
            }
            
            # Serialize using schema
            result = template_list_response_schema.dump(response)
            return result, 200
            
        except Exception as e:
            logger.error(f"Error searching templates: {str(e)}")
            return {"error": "Internal server error"}, 500


class TemplateMetricsResource(Resource):
    """Resource for template usage metrics"""
    
    def __init__(self, template_service: TemplateService):
        """Initialize the template metrics resource"""
        self._template_service = template_service
        logger.info("Template metrics resource initialized")
        
    @auth_required(allow_anonymous=False)
    def get(self, template_id):
        """Get usage metrics for a template"""
        logger.info(f"Retrieving metrics for template: {template_id}")
        
        # Get current user ID
        user_id = get_current_user_id()
        
        try:
            # Get template metrics
            metrics = self._template_service.get_template_usage_metrics(template_id)
            
            if not metrics:
                logger.warning(f"Template not found for metrics: {template_id}")
                return {"error": "Template not found"}, 404
                
            return metrics, 200
            
        except ValueError as e:
            if "Template not found" in str(e):
                logger.warning(f"Template not found for metrics: {template_id}")
                return {"error": "Template not found"}, 404
            elif "Permission denied" in str(e):
                logger.warning(f"Permission denied: User {user_id} attempted to access metrics for template {template_id}")
                return {"error": "Permission denied to access template metrics"}, 403
            else:
                logger.error(f"Validation error retrieving metrics for template {template_id}: {str(e)}")
                return {"error": str(e)}, 400
        except Exception as e:
            logger.error(f"Error retrieving template metrics for {template_id}: {str(e)}")
            return {"error": "Internal server error"}, 500


class PopularTemplatesResource(Resource):
    """Resource for retrieving most used templates"""
    
    def __init__(self, template_service: TemplateService):
        """Initialize the popular templates resource"""
        self._template_service = template_service
        logger.info("Popular templates resource initialized")
        
    @auth_required(allow_anonymous=True)
    def get(self):
        """Get most popular templates by usage"""
        logger.info("Retrieving popular templates")
        
        try:
            # Parse query parameters
            parser = reqparse.RequestParser()
            parser.add_argument('limit', type=int, default=10, location='args')
            args = parser.parse_args()
            
            # Get popular templates
            templates = self._template_service.get_popular_templates(args.limit)
            
            # Prepare response with metrics
            response = {
                "templates": templates,
                "total": len(templates),
                "limit": args.limit
            }
            
            return response, 200
            
        except Exception as e:
            logger.error(f"Error retrieving popular templates: {str(e)}")
            return {"error": "Internal server error"}, 500