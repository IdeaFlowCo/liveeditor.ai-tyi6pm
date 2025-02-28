import pytest
from datetime import datetime
from bson import ObjectId  # version ^0.5.10

# Template categories available in the system
TEMPLATE_CATEGORIES = ['grammar', 'style', 'conciseness', 'clarity', 'professional', 'academic', 'creative', 'custom']

def get_template_data(name=None, category=None, prompt_text=None, description=None, is_system=True, created_by=None):
    """
    Factory function to generate template test data with customizable fields.
    
    Args:
        name (str, optional): Template name
        category (str, optional): Template category
        prompt_text (str, optional): The actual prompt text for the AI
        description (str, optional): Template description
        is_system (bool, optional): Flag indicating if it's a system template
        created_by (str, optional): ObjectId of creator (for user templates)
    
    Returns:
        dict: Template data object with all required fields
    """
    # Set default values if not provided
    if name is None:
        name = "Test Template"
    if category is None:
        category = "style"
    if prompt_text is None:
        prompt_text = "Improve the following text: {{document}}"
    if description is None:
        description = "A test template for automated testing"
    
    # Create the template data
    template_data = {
        "_id": ObjectId(),
        "name": name,
        "description": description,
        "promptText": prompt_text,
        "category": category,
        "isSystem": is_system,
        "createdAt": datetime.now()
    }
    
    # Add creator ID for user templates
    if not is_system and created_by is not None:
        template_data["createdBy"] = created_by
    
    return template_data

@pytest.fixture
def basic_system_template():
    """
    Fixture providing a standard system template for making text shorter.
    """
    return get_template_data(
        name="Make it Shorter",
        category="conciseness",
        prompt_text="Rewrite the following text to be more concise while preserving the key information: {{document}}",
        description="Makes your text shorter and more concise"
    )

@pytest.fixture
def professional_system_template():
    """
    Fixture providing a system template for professional tone improvements.
    """
    return get_template_data(
        name="More Professional Tone",
        category="professional",
        prompt_text="Rewrite the following text to have a more professional business tone: {{document}}",
        description="Enhances professional language and tone for business communications"
    )

@pytest.fixture
def grammar_system_template():
    """
    Fixture providing a system template for grammar improvements.
    """
    return get_template_data(
        name="Improve Grammar",
        category="grammar",
        prompt_text="Correct any grammatical errors in the following text while preserving the meaning: {{document}}",
        description="Fixes grammatical errors in your text"
    )

@pytest.fixture
def basic_user_template():
    """
    Fixture providing a user-created template example.
    """
    return get_template_data(
        name="My Custom Template",
        category="custom",
        prompt_text="Transform this text to sound like Shakespeare: {{document}}",
        description="Makes text sound like Shakespeare",
        is_system=False,
        created_by=str(ObjectId())
    )

@pytest.fixture
def system_templates():
    """
    Fixture providing a list of all system templates for initialization tests.
    """
    return [
        get_template_data(
            name="Make it Shorter",
            category="conciseness",
            prompt_text="Rewrite the following text to be more concise while preserving the key information: {{document}}",
            description="Makes your text shorter and more concise"
        ),
        get_template_data(
            name="More Professional Tone",
            category="professional",
            prompt_text="Rewrite the following text to have a more professional business tone: {{document}}",
            description="Enhances professional language and tone for business communications"
        ),
        get_template_data(
            name="Improve Grammar",
            category="grammar",
            prompt_text="Correct any grammatical errors in the following text while preserving the meaning: {{document}}",
            description="Fixes grammatical errors in your text"
        ),
        get_template_data(
            name="Academic Style",
            category="academic",
            prompt_text="Rewrite the following text in formal academic style appropriate for scholarly publications: {{document}}",
            description="Transforms text to academic writing style"
        ),
        get_template_data(
            name="Simplify Language",
            category="clarity",
            prompt_text="Rewrite the following text to use simpler language that would be understood by a general audience: {{document}}",
            description="Makes text simpler and easier to understand"
        ),
        get_template_data(
            name="Creative Rewrite",
            category="creative",
            prompt_text="Rewrite the following text in a more engaging and creative style: {{document}}",
            description="Adds creativity and flair to your writing"
        ),
    ]

@pytest.fixture
def create_template():
    """
    Factory fixture to create and optionally save template instances with custom attributes.
    
    Returns a function that can be called to create templates with custom properties.
    
    Example:
        template = create_template(name="Custom Template", save=True)
    """
    def _create_template(name=None, category=None, prompt_text=None, description=None, 
                         is_system=True, created_by=None, save=False):
        """
        Create a template with the given properties.
        
        Args:
            name (str, optional): Template name
            category (str, optional): Template category
            prompt_text (str, optional): The actual prompt text for the AI
            description (str, optional): Template description
            is_system (bool, optional): Flag indicating if it's a system template
            created_by (str, optional): ObjectId of creator (for user templates)
            save (bool, optional): Whether to save the template to the database
        
        Returns:
            dict: The created template data
        """
        template_data = get_template_data(
            name=name,
            category=category,
            prompt_text=prompt_text,
            description=description,
            is_system=is_system,
            created_by=created_by
        )
        
        # Would typically save to DB here if save=True
        # For now, we'll just return the data
        # If this fixture is used in an actual test, we'd need to implement
        # the saving functionality or mock it appropriately
        
        return template_data
    
    return _create_template