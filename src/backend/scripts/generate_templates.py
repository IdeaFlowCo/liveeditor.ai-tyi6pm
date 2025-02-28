#!/usr/bin/env python3
"""
Script to generate and initialize standard AI prompt templates for the writing enhancement platform.

This script can be run as a standalone utility or as part of the application initialization
process to ensure that essential prompt templates are available in the system.
"""

import os
import sys
import argparse
import json
from datetime import datetime

from ..core.utils.logger import get_logger
from ..data.mongodb.connection import init_mongodb, get_collection
from ..data.mongodb.repositories.template_repository import TemplateRepository

# Configure logging
logger = get_logger(__name__)

# Constants
DEFAULT_TEMPLATES_FILE = 'templates.json'
DEFAULT_CATEGORIES = ['Style', 'Length', 'Tone', 'Grammar', 'Structure']

def load_templates_from_file(filename: str) -> list:
    """
    Loads template definitions from a JSON configuration file.
    
    Args:
        filename: Path to the JSON file containing template definitions
        
    Returns:
        List of template definitions
        
    Raises:
        FileNotFoundError: If the specified file does not exist
        json.JSONDecodeError: If the file contains invalid JSON
        ValueError: If the file does not contain a valid list of templates
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Template file not found: {filename}")
    
    try:
        with open(filename, 'r') as file:
            templates = json.load(file)
        
        if not isinstance(templates, list):
            raise ValueError("Template file must contain a list of template objects")
        
        # Validate each template
        valid_templates = []
        for i, template in enumerate(templates):
            if validate_template(template):
                # Mark as system template
                template['isSystem'] = True
                valid_templates.append(template)
            else:
                logger.warning(f"Skipping invalid template at index {i}")
        
        logger.info(f"Loaded {len(valid_templates)} templates from {filename}")
        return valid_templates
    
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in template file: {str(e)}")
        raise

def generate_default_templates() -> list:
    """
    Creates a set of standard templates if no external file is provided.
    
    Returns:
        List of default template definitions
    """
    logger.info("Generating default templates")
    
    templates = []
    
    # Make it shorter template
    templates.append({
        "name": "Make it shorter",
        "description": "Condense the text while preserving the key message",
        "promptText": "Rewrite the following text to be more concise while preserving the key message and maintaining the same tone and style. Remove unnecessary words and phrases without losing important information.",
        "category": "Length",
        "isSystem": True
    })
    
    # More professional tone template
    templates.append({
        "name": "More professional",
        "description": "Elevate the tone to be more formal and professional",
        "promptText": "Rewrite the following text to have a more professional and formal tone. Use appropriate business language and eliminate casual expressions while maintaining the original meaning.",
        "category": "Tone",
        "isSystem": True
    })
    
    # Improve grammar template
    templates.append({
        "name": "Improve grammar",
        "description": "Fix grammatical errors and improve sentence structure",
        "promptText": "Correct any grammatical errors, improve sentence structure, and ensure proper punctuation in the following text while preserving the original meaning and tone.",
        "category": "Grammar",
        "isSystem": True
    })
    
    # Simplify language template
    templates.append({
        "name": "Simplify language",
        "description": "Make the text easier to understand with simpler language",
        "promptText": "Rewrite the following text using simpler language and shorter sentences to make it more accessible. Replace complex terminology with more common words when possible without changing the meaning.",
        "category": "Style",
        "isSystem": True
    })
    
    # Add examples template
    templates.append({
        "name": "Add examples",
        "description": "Enhance the text with relevant examples",
        "promptText": "Enhance the following text by adding relevant examples to illustrate the key points. The examples should be clear, concise, and directly related to the content.",
        "category": "Structure",
        "isSystem": True
    })
    
    # Academic style template
    templates.append({
        "name": "Academic style",
        "description": "Convert to a scholarly, academic writing style",
        "promptText": "Rewrite the following text in an academic style appropriate for scholarly publications. Use formal language, third-person perspective, precise terminology, and a structured approach while maintaining the original content.",
        "category": "Style",
        "isSystem": True
    })
    
    # Creative rewrite template
    templates.append({
        "name": "Creative rewrite",
        "description": "Make the text more engaging and creative",
        "promptText": "Rewrite the following text to be more creative and engaging while preserving the key message. Use vivid language, varied sentence structure, and compelling phrasing to capture the reader's attention.",
        "category": "Style",
        "isSystem": True
    })
    
    # Fix punctuation template
    templates.append({
        "name": "Fix punctuation",
        "description": "Correct punctuation issues in the text",
        "promptText": "Review and correct any punctuation errors in the following text, including commas, periods, semicolons, and apostrophes. Ensure proper use of quotation marks and parentheses while maintaining the original content.",
        "category": "Grammar",
        "isSystem": True
    })
    
    # Eliminate passive voice template
    templates.append({
        "name": "Eliminate passive voice",
        "description": "Convert passive voice to active voice",
        "promptText": "Identify and revise instances of passive voice in the following text, replacing them with active voice constructions. Make sure to maintain the original meaning while making the text more direct and engaging.",
        "category": "Style",
        "isSystem": True
    })
    
    # Make it longer template
    templates.append({
        "name": "Make it longer",
        "description": "Expand the text with additional details and explanation",
        "promptText": "Expand the following text by adding relevant details, elaborating on key points, and providing additional context or explanation. Maintain the original tone and purpose while making the content more comprehensive.",
        "category": "Length",
        "isSystem": True
    })
    
    logger.info(f"Generated {len(templates)} default templates")
    return templates

def validate_template(template: dict) -> bool:
    """
    Validates a template definition has all required fields.
    
    Args:
        template: A template definition object
        
    Returns:
        True if valid, False otherwise
    """
    # Required fields
    required_fields = ['name', 'description', 'promptText', 'category']
    
    # Check all required fields exist
    for field in required_fields:
        if field not in template:
            logger.warning(f"Template missing required field: {field}")
            return False
        if not isinstance(template[field], str):
            logger.warning(f"Template field '{field}' must be a string")
            return False
    
    # Check that category is valid
    if template['category'] not in DEFAULT_CATEGORIES:
        logger.warning(f"Template has invalid category: {template['category']}")
        return False
    
    return True

def initialize_templates(templates: list) -> int:
    """
    Initializes the templates in the database.
    
    Args:
        templates: List of template definitions
        
    Returns:
        Number of templates created
    """
    try:
        # Initialize repository
        template_repository = TemplateRepository()
        
        # Initialize templates
        created_count = template_repository.initialize_system_templates(templates)
        
        logger.info(f"Successfully initialized {created_count} templates")
        return created_count
    
    except Exception as e:
        logger.error(f"Error initializing templates: {str(e)}")
        raise

def parse_args() -> argparse.Namespace:
    """
    Parses command line arguments for script options.
    
    Returns:
        Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description='Generate and initialize AI prompt templates for the writing enhancement platform'
    )
    
    parser.add_argument(
        '--file',
        type=str,
        help=f'Path to a JSON file containing template definitions (default: {DEFAULT_TEMPLATES_FILE})'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite existing templates with same names'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview templates without adding to database'
    )
    
    return parser.parse_args()

def main() -> int:
    """
    Main function to execute the template generation process.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Parse command line arguments
        args = parse_args()
        
        # Initialize MongoDB connection
        init_mongodb()
        
        # Get templates from file or generate defaults
        templates = []
        if args.file:
            try:
                templates = load_templates_from_file(args.file)
            except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
                logger.error(f"Error loading templates from file: {str(e)}")
                logger.info("Falling back to default templates")
                templates = generate_default_templates()
        else:
            templates = generate_default_templates()
        
        # If dry run, just print the templates
        if args.dry_run:
            logger.info("Dry run - templates that would be created:")
            for i, template in enumerate(templates):
                logger.info(f"Template {i+1}: {template['name']} ({template['category']})")
            logger.info(f"Total: {len(templates)} templates")
            return 0
        
        # Initialize the templates in the database
        created_count = initialize_templates(templates)
        
        logger.info(f"Template initialization complete. Created {created_count} new templates.")
        return 0
    
    except Exception as e:
        logger.error(f"Error in template generation: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())