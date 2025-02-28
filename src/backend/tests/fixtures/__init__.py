"""
Initialization file for the test fixtures package that provides easy access to test fixtures
for the AI writing enhancement interface backend.
"""

# Import fixture functions
from .user_fixtures import regular_user_data
from .document_fixtures import get_document_data
from .template_fixtures import get_template_data
from .suggestion_fixtures import create_suggestion_data


def create_test_user(options=None):
    """
    Creates a test user with customizable options.
    
    Args:
        options (dict, optional): Dictionary of user configuration options
            
    Returns:
        dict: User data for testing
    """
    options = options or {}
    user_data = dict(regular_user_data())
    
    # Apply any custom options provided
    for key, value in options.items():
        user_data[key] = value
    
    return user_data


def create_test_document(options=None):
    """
    Creates a test document with customizable options.
    
    Args:
        options (dict, optional): Dictionary of document configuration options
            
    Returns:
        dict: Document data for testing
    """
    options = options or {}
    return get_document_data(**options)


def create_test_template(options=None):
    """
    Creates a test template with customizable options.
    
    Args:
        options (dict, optional): Dictionary of template configuration options
            
    Returns:
        dict: Template data for testing
    """
    options = options or {}
    return get_template_data(**options)


def create_test_suggestion(options=None):
    """
    Creates a test suggestion with customizable options.
    
    Args:
        options (dict, optional): Dictionary of suggestion configuration options
            
    Returns:
        dict: Suggestion data for testing
    """
    options = options or {}
    return create_suggestion_data(**options)


def create_test_fixtures(options=None):
    """
    Creates a complete set of related test fixtures (user, document, template, and suggestion)
    for comprehensive test scenarios.
    
    Args:
        options (dict): Dictionary with configuration options for each fixture type
            
    Returns:
        dict: Dictionary containing all created test fixtures
    """
    options = options or {}
    user_options = options.get('user', {})
    document_options = options.get('document', {})
    template_options = options.get('template', {})
    suggestion_options = options.get('suggestion', {})
    
    # Create a test user using create_test_user
    user = create_test_user(user_options)
    
    # Create a test document owned by the user using create_test_document
    document_options['user_id'] = user.get('_id')
    document = create_test_document(document_options)
    
    # Create a test template using create_test_template
    template_options['created_by'] = user.get('_id')
    template_options['is_system'] = False
    template = create_test_template(template_options)
    
    # Create a test suggestion for the document using create_test_suggestion
    suggestion_options['document_id'] = document.get('_id')
    suggestion = create_test_suggestion(suggestion_options)
    
    # Return dictionary with all created fixtures
    return {
        'user': user,
        'document': document,
        'template': template,
        'suggestion': suggestion
    }


# Export the test fixture functions
__all__ = [
    'create_test_user',
    'create_test_document',
    'create_test_template',
    'create_test_suggestion',
    'create_test_fixtures',
]