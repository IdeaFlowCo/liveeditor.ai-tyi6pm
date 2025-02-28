from flask import Blueprint, request, jsonify
from http import HTTPStatus
from jsonschema import validate
import logging

# Initialize Blueprint
templates_bp = Blueprint('templates', __name__)

# Template schema for validation
template_schema = {
    "type": "object",
    "required": ["name", "promptText", "category"],
    "properties": {
        "name": {"type": "string", "minLength": 1, "maxLength": 100},
        "description": {"type": "string", "maxLength": 500},
        "promptText": {"type": "string", "minLength": 1, "maxLength": 2000},
        "category": {"type": "string", "enum": ["general", "tone", "length", "style", "grammar", "clarity"]},
        "isSystem": {"type": "boolean", "default": False}
    },
    "additionalProperties": False
}

@templates_bp.route('/', methods=['GET'])
def get_templates():
    """
    Get a list of AI improvement prompt templates.
    
    Optional query parameters:
    - category: Filter templates by category
    
    Returns:
        A JSON response with a list of templates
    """
    try:
        logging.info("Received request for templates")
        
        # Extract query parameters
        category = request.args.get('category')
        
        # Here we would query the database for templates, filtered by category if provided
        # For this stub, we're returning an empty array
        
        # In a real implementation, this would return template objects from the database
        return jsonify([]), HTTPStatus.OK
    except Exception as e:
        logging.error(f"Error retrieving templates: {str(e)}")
        return jsonify({"error": "Failed to retrieve templates"}), HTTPStatus.INTERNAL_SERVER_ERROR

@templates_bp.route('/<template_id>', methods=['GET'])
def get_template(template_id):
    """
    Get a specific template by ID.
    
    Args:
        template_id (str): The unique identifier of the template
        
    Returns:
        A JSON response with the template data or error
    """
    try:
        logging.info(f"Received request for template {template_id}")
        
        # In a real implementation, we would query the database for the specific template
        # For this stub, we're returning not found
        
        return jsonify({"error": "Template not found"}), HTTPStatus.NOT_FOUND
    except Exception as e:
        logging.error(f"Error retrieving template {template_id}: {str(e)}")
        return jsonify({"error": "Failed to retrieve template"}), HTTPStatus.INTERNAL_SERVER_ERROR

@templates_bp.route('/', methods=['POST'])
def create_template():
    """
    Create a new template.
    
    Request body should contain template data conforming to the schema.
    
    Returns:
        A JSON response with the created template ID
    """
    try:
        logging.info("Received request to create a template")
        
        # Validate request data against schema
        try:
            validate(instance=request.json, schema=template_schema)
        except Exception as validation_error:
            logging.error(f"Template validation failed: {str(validation_error)}")
            return jsonify({"error": f"Invalid template data: {str(validation_error)}"}), HTTPStatus.BAD_REQUEST
        
        # Extract template data
        template_data = request.json
        
        # Here we would save the template to the database and get an ID
        # For this stub, we're returning a placeholder ID
        
        return jsonify({"id": "new-template-id"}), HTTPStatus.CREATED
    except Exception as e:
        logging.error(f"Error creating template: {str(e)}")
        return jsonify({"error": "Failed to create template"}), HTTPStatus.INTERNAL_SERVER_ERROR

@templates_bp.route('/<template_id>', methods=['PUT'])
def update_template(template_id):
    """
    Update an existing template.
    
    Args:
        template_id (str): The unique identifier of the template to update
        
    Returns:
        A JSON response with the updated template or error
    """
    try:
        logging.info(f"Received request to update template {template_id}")
        
        # Validate request data against schema
        try:
            validate(instance=request.json, schema=template_schema)
        except Exception as validation_error:
            logging.error(f"Template validation failed: {str(validation_error)}")
            return jsonify({"error": f"Invalid template data: {str(validation_error)}"}), HTTPStatus.BAD_REQUEST
        
        # Extract template data
        template_data = request.json
        
        # Here we would update the template in the database
        # For this stub, we're returning not found
        
        return jsonify({"error": "Template not found"}), HTTPStatus.NOT_FOUND
    except Exception as e:
        logging.error(f"Error updating template {template_id}: {str(e)}")
        return jsonify({"error": "Failed to update template"}), HTTPStatus.INTERNAL_SERVER_ERROR

@templates_bp.route('/<template_id>', methods=['DELETE'])
def delete_template(template_id):
    """
    Delete a template.
    
    Args:
        template_id (str): The unique identifier of the template to delete
        
    Returns:
        A JSON response with success or error
    """
    try:
        logging.info(f"Received request to delete template {template_id}")
        
        # Here we would delete the template from the database
        # For this stub, we're returning not found
        
        return jsonify({"error": "Template not found"}), HTTPStatus.NOT_FOUND
    except Exception as e:
        logging.error(f"Error deleting template {template_id}: {str(e)}")
        return jsonify({"error": "Failed to delete template"}), HTTPStatus.INTERNAL_SERVER_ERROR