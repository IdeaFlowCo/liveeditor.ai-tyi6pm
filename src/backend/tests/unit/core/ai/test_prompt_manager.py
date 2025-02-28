import pytest
from unittest.mock import Mock, patch
from typing import Dict

from src.backend.core.ai.prompt_manager import (
    PromptManager, 
    PromptTemplateNotFoundError, 
    PromptFormatError,
    DEFAULT_SYSTEM_PROMPT,
    TRACK_CHANGES_FORMAT
)
from src.backend.core.ai.token_optimizer import TokenOptimizer
from src.backend.core.ai.context_manager import ContextManager
from src.backend.core.templates.template_service import TemplateService

from src.backend.tests.fixtures.template_fixtures import (
    basic_system_template,
    professional_system_template,
    grammar_system_template,
    basic_user_template
)

# Constants for testing
MOCK_DOCUMENT = "This is a sample document for testing prompt optimization and suggestions. It contains enough text to test token optimization features."
CUSTOM_PROMPT = "Please improve this text to sound more professional and concise while maintaining the original meaning."
TEMPLATE_WITH_VARIABLES = "Improve this text to be more {style} and {tone} while keeping the original meaning."

def test_create_system_prompt_default():
    """Tests that system prompt is created with default values correctly"""
    # Create mocks for dependencies
    template_service = Mock(spec=TemplateService)
    token_optimizer = Mock(spec=TokenOptimizer)
    context_manager = Mock(spec=ContextManager)
    
    # Initialize PromptManager with mocked dependencies
    prompt_manager = PromptManager(
        template_service=template_service,
        token_optimizer=token_optimizer,
        context_manager=context_manager
    )
    
    # Call create_system_prompt without custom instruction
    result = prompt_manager.create_system_prompt()
    
    # Assert that returned prompt contains DEFAULT_SYSTEM_PROMPT and TRACK_CHANGES_FORMAT
    assert DEFAULT_SYSTEM_PROMPT in result
    assert TRACK_CHANGES_FORMAT in result

def test_create_system_prompt_with_custom_instruction():
    """Tests system prompt creation with custom instruction"""
    # Create mocks for dependencies
    template_service = Mock(spec=TemplateService)
    token_optimizer = Mock(spec=TokenOptimizer)
    context_manager = Mock(spec=ContextManager)
    
    # Initialize PromptManager with mocked dependencies
    prompt_manager = PromptManager(
        template_service=template_service,
        token_optimizer=token_optimizer,
        context_manager=context_manager
    )
    
    # Define a custom instruction string
    custom_instruction = "Respond in a formal and concise manner."
    
    # Call create_system_prompt with custom instruction
    result = prompt_manager.create_system_prompt(custom_instruction)
    
    # Assert that returned prompt contains both DEFAULT_SYSTEM_PROMPT, custom instruction, and TRACK_CHANGES_FORMAT
    assert DEFAULT_SYSTEM_PROMPT in result
    assert custom_instruction in result
    assert TRACK_CHANGES_FORMAT in result

def test_create_template_prompt_success(basic_system_template):
    """Tests successful template prompt creation using system template"""
    # Create mocks for dependencies
    template_service = Mock(spec=TemplateService)
    token_optimizer = Mock(spec=TokenOptimizer)
    context_manager = Mock(spec=ContextManager)
    
    # Configure template_service mock to return basic_system_template fixture
    template_id = str(basic_system_template["_id"])
    template_service.get_template_by_id.return_value = basic_system_template
    
    # Initialize PromptManager with mocked dependencies
    prompt_manager = PromptManager(
        template_service=template_service,
        token_optimizer=token_optimizer,
        context_manager=context_manager
    )
    
    # Call create_template_prompt with template identifier and parameters
    result = prompt_manager.create_template_prompt(template_id, {})
    
    # Assert that returned prompt contains formatted template text
    assert basic_system_template["promptText"] in result
    
    # Verify template_service.get_template_by_id was called with correct ID
    template_service.get_template_by_id.assert_called_once_with(template_id)

def test_create_template_prompt_not_found():
    """Tests error handling when template is not found"""
    # Create mocks for dependencies
    template_service = Mock(spec=TemplateService)
    token_optimizer = Mock(spec=TokenOptimizer)
    context_manager = Mock(spec=ContextManager)
    
    # Configure template_service mock to return None (template not found)
    template_service.get_template_by_id.return_value = None
    
    # Initialize PromptManager with mocked dependencies
    prompt_manager = PromptManager(
        template_service=template_service,
        token_optimizer=token_optimizer,
        context_manager=context_manager
    )
    
    # Use pytest.raises to assert PromptTemplateNotFoundError is raised
    with pytest.raises(PromptTemplateNotFoundError):
        # Call create_template_prompt with non-existent template identifier
        prompt_manager.create_template_prompt("non_existent_id", {})

def test_create_template_prompt_with_variables():
    """Tests template prompt creation with variable substitution"""
    # Create mocks for dependencies
    template_service = Mock(spec=TemplateService)
    token_optimizer = Mock(spec=TokenOptimizer)
    context_manager = Mock(spec=ContextManager)
    
    # Configure mock template with variables
    template_with_vars = {
        "_id": "template123",
        "name": "Template with Variables",
        "promptText": TEMPLATE_WITH_VARIABLES,
        "category": "style"
    }
    template_service.get_template_by_id.return_value = template_with_vars
    
    # Initialize PromptManager with mocked dependencies
    prompt_manager = PromptManager(
        template_service=template_service,
        token_optimizer=token_optimizer,
        context_manager=context_manager
    )
    
    # Define parameters for variable substitution
    params = {"style": "professional", "tone": "confident"}
    
    # Call create_template_prompt with template identifier and parameters
    result = prompt_manager.create_template_prompt("template123", params)
    
    # Assert variables are correctly substituted in the result
    expected_text = TEMPLATE_WITH_VARIABLES.format(**params)
    assert result == expected_text

def test_create_template_prompt_missing_variables():
    """Tests error handling when required template variables are missing"""
    # Create mocks for dependencies
    template_service = Mock(spec=TemplateService)
    token_optimizer = Mock(spec=TokenOptimizer)
    context_manager = Mock(spec=ContextManager)
    
    # Configure mock template with variables
    template_with_vars = {
        "_id": "template123",
        "name": "Template with Variables",
        "promptText": TEMPLATE_WITH_VARIABLES,
        "category": "style"
    }
    template_service.get_template_by_id.return_value = template_with_vars
    
    # Initialize PromptManager with mocked dependencies
    prompt_manager = PromptManager(
        template_service=template_service,
        token_optimizer=token_optimizer,
        context_manager=context_manager
    )
    
    # Define incomplete parameters (missing some variables)
    params = {"style": "professional"}  # Missing "tone" variable
    
    # Use pytest.raises to assert PromptFormatError is raised
    with pytest.raises(PromptFormatError):
        # Call create_template_prompt with missing parameters
        prompt_manager.create_template_prompt("template123", params)

def test_create_custom_prompt():
    """Tests custom prompt creation without template"""
    # Create mocks for dependencies
    template_service = Mock(spec=TemplateService)
    token_optimizer = Mock(spec=TokenOptimizer)
    context_manager = Mock(spec=ContextManager)
    
    # Initialize PromptManager with mocked dependencies
    prompt_manager = PromptManager(
        template_service=template_service,
        token_optimizer=token_optimizer,
        context_manager=context_manager
    )
    
    # Define custom prompt text
    prompt_text = CUSTOM_PROMPT
    
    # Call create_custom_prompt with prompt text
    result = prompt_manager.create_custom_prompt(prompt_text)
    
    # Assert that returned prompt contains custom text and TRACK_CHANGES_FORMAT
    assert prompt_text in result
    assert TRACK_CHANGES_FORMAT in result

def test_create_custom_prompt_with_parameters():
    """Tests custom prompt creation with parameter substitution"""
    # Create mocks for dependencies
    template_service = Mock(spec=TemplateService)
    token_optimizer = Mock(spec=TokenOptimizer)
    context_manager = Mock(spec=ContextManager)
    
    # Initialize PromptManager with mocked dependencies
    prompt_manager = PromptManager(
        template_service=template_service,
        token_optimizer=token_optimizer,
        context_manager=context_manager
    )
    
    # Define custom prompt text with variables
    prompt_with_vars = "Make this text more {style} while keeping the original meaning."
    
    # Define parameters for variable substitution
    params = {"style": "professional"}
    
    # Call create_custom_prompt with prompt text and parameters
    result = prompt_manager.create_custom_prompt(prompt_with_vars, params)
    
    # Assert variables are correctly substituted in the result
    expected_text = prompt_with_vars.format(**params)
    assert expected_text in result

def test_optimize_prompt_with_content():
    """Tests prompt optimization with document content"""
    # Create mocks for dependencies
    template_service = Mock(spec=TemplateService)
    token_optimizer = Mock(spec=TokenOptimizer)
    context_manager = Mock(spec=ContextManager)
    
    # Configure token_optimizer mock to return optimized content
    prompt = "Improve this text:"
    document = MOCK_DOCUMENT
    optimized_content = f"{prompt}\n\n{document}"
    token_optimizer.optimize_prompt.return_value = optimized_content
    
    # Initialize PromptManager with mocked dependencies
    prompt_manager = PromptManager(
        template_service=template_service,
        token_optimizer=token_optimizer,
        context_manager=context_manager
    )
    
    # Call optimize_prompt_with_content
    result = prompt_manager.optimize_prompt_with_content(prompt, document)
    
    # Assert token_optimizer.optimize_prompt was called with correct parameters
    token_optimizer.optimize_prompt.assert_called_once()
    call_args = token_optimizer.optimize_prompt.call_args[1]
    assert call_args["prompt"] == prompt
    assert call_args["content"] == document
    
    # Verify optimized content is returned correctly
    assert result == optimized_content

def test_create_chat_prompt():
    """Tests chat prompt creation with messages"""
    # Create mocks for dependencies
    template_service = Mock(spec=TemplateService)
    token_optimizer = Mock(spec=TokenOptimizer)
    context_manager = Mock(spec=ContextManager)
    
    # Configure context_manager mock to return optimized document content
    document_content = MOCK_DOCUMENT
    optimized_document = "Optimized document content"
    context_manager.optimize_document_context.return_value = optimized_document
    
    # Initialize PromptManager with mocked dependencies
    prompt_manager = PromptManager(
        template_service=template_service,
        token_optimizer=token_optimizer,
        context_manager=context_manager
    )
    
    # Define chat messages array with user and assistant messages
    messages = [
        {"role": "user", "content": "Can you help me improve this text?"},
        {"role": "assistant", "content": "Sure, I'd be happy to help."}
    ]
    
    # Call create_chat_prompt with messages and document content
    result = prompt_manager.create_chat_prompt(messages, document_content=document_content)
    
    # Assert returned structure contains system message and formatted chat messages
    assert len(result) == 3  # System message + 2 chat messages
    assert result[0]["role"] == "system"
    assert DEFAULT_SYSTEM_PROMPT in result[0]["content"]
    assert optimized_document in result[0]["content"]
    assert result[1] == messages[0]
    assert result[2] == messages[1]
    
    # Verify context_manager.optimize_document_context was called if document provided
    context_manager.optimize_document_context.assert_called_once_with(document_content)

def test_create_suggestion_prompt_with_template(professional_system_template):
    """Tests suggestion prompt creation using template"""
    # Create mocks for dependencies
    template_service = Mock(spec=TemplateService)
    token_optimizer = Mock(spec=TokenOptimizer)
    context_manager = Mock(spec=ContextManager)
    
    # Configure template_service mock to return template fixture
    template_id = str(professional_system_template["_id"])
    template_service.get_template_by_id.return_value = professional_system_template
    
    # Configure token_optimizer mock for optimization
    document = MOCK_DOCUMENT
    template_prompt = professional_system_template["promptText"]
    optimized_prompt = f"{template_prompt}\n\n{document}"
    token_optimizer.optimize_prompt.return_value = optimized_prompt
    
    # Initialize PromptManager with mocked dependencies
    prompt_manager = PromptManager(
        template_service=template_service,
        token_optimizer=token_optimizer,
        context_manager=context_manager
    )
    
    # Call create_suggestion_prompt with document content and template identifier
    result = prompt_manager.create_suggestion_prompt(document, template_id)
    
    # Assert template_service.get_template_by_id was called
    template_service.get_template_by_id.assert_called_once_with(template_id)
    
    # Verify token_optimizer.optimize_prompt was called for document optimization
    token_optimizer.optimize_prompt.assert_called_once()
    
    # Check final prompt contains properly formatted template and improvement instructions
    assert result == optimized_prompt

def test_create_suggestion_prompt_with_custom_prompt():
    """Tests suggestion prompt creation using custom prompt"""
    # Create mocks for dependencies
    template_service = Mock(spec=TemplateService)
    token_optimizer = Mock(spec=TokenOptimizer)
    context_manager = Mock(spec=ContextManager)
    
    # Configure token_optimizer mock for optimization
    document = MOCK_DOCUMENT
    custom_prompt = CUSTOM_PROMPT
    optimized_prompt = f"{custom_prompt}\n\n{document}"
    token_optimizer.optimize_prompt.return_value = optimized_prompt
    
    # Initialize PromptManager with mocked dependencies
    prompt_manager = PromptManager(
        template_service=template_service,
        token_optimizer=token_optimizer,
        context_manager=context_manager
    )
    
    # Define parameters with custom_prompt key
    params = {"custom_prompt": custom_prompt}
    
    # Call create_suggestion_prompt with document content and parameters
    result = prompt_manager.create_suggestion_prompt(document, parameters=params)
    
    # Assert token_optimizer.optimize_prompt was called for document optimization
    token_optimizer.optimize_prompt.assert_called_once()
    
    # Check final prompt contains custom prompt and improvement instructions
    assert result == optimized_prompt

def test_estimate_tokens():
    """Tests token estimation for prompt and document"""
    # Create mocks for dependencies
    template_service = Mock(spec=TemplateService)
    token_optimizer = Mock(spec=TokenOptimizer)
    context_manager = Mock(spec=ContextManager)
    
    # Configure token_optimizer.count_tokens to return different values for prompt and document
    token_optimizer.count_tokens.side_effect = [50, 150]  # 50 for prompt, 150 for document
    
    # Initialize PromptManager with mocked dependencies
    prompt_manager = PromptManager(
        template_service=template_service,
        token_optimizer=token_optimizer,
        context_manager=context_manager
    )
    
    # Call estimate_tokens with prompt and document content
    result = prompt_manager.estimate_tokens("Test prompt", MOCK_DOCUMENT)
    
    # Assert returned dictionary contains correct token counts
    assert result["prompt_tokens"] == 50
    assert result["document_tokens"] == 150
    assert result["total_tokens"] == 200
    
    # Verify it includes prompt_tokens, document_tokens, and total_tokens fields
    assert "prompt_tokens" in result
    assert "document_tokens" in result
    assert "total_tokens" in result

def test_caching_disabled():
    """Tests that prompt manager works correctly with caching disabled"""
    # Create mocks for dependencies
    template_service = Mock(spec=TemplateService)
    token_optimizer = Mock(spec=TokenOptimizer)
    context_manager = Mock(spec=ContextManager)
    
    # Initialize PromptManager with use_cache=False
    prompt_manager = PromptManager(
        template_service=template_service,
        token_optimizer=token_optimizer,
        context_manager=context_manager,
        use_cache=False
    )
    
    # Configure template_service mock to return template fixture
    template_id = "template123"
    template = {
        "_id": template_id,
        "name": "Test Template",
        "promptText": "Test prompt text",
        "category": "test"
    }
    template_service.get_template_by_id.return_value = template
    
    # Call create_template_prompt multiple times with same parameters
    prompt_manager.create_template_prompt(template_id, {})
    prompt_manager.create_template_prompt(template_id, {})
    
    # Assert template service is called on each invocation
    assert template_service.get_template_by_id.call_count == 2

def test_caching_enabled():
    """Tests that caching works correctly when enabled"""
    # Create mocks for dependencies including cache_get and cache_set
    template_service = Mock(spec=TemplateService)
    token_optimizer = Mock(spec=TokenOptimizer)
    context_manager = Mock(spec=ContextManager)
    
    # Mock cache functions
    with patch('src.backend.core.ai.prompt_manager.cache_get') as mock_cache_get, \
         patch('src.backend.core.ai.prompt_manager.cache_set') as mock_cache_set:
            
        # Configure cache_get to return None on first call (cache miss) and a value on second call (cache hit)
        mock_cache_get.side_effect = [None, "Cached prompt"]
        
        # Initialize PromptManager with use_cache=True
        prompt_manager = PromptManager(
            template_service=template_service,
            token_optimizer=token_optimizer,
            context_manager=context_manager,
            use_cache=True
        )
        
        # Configure template_service mock to return template fixture
        template_id = "template123"
        template = {
            "_id": template_id,
            "name": "Test Template",
            "promptText": "Test prompt text",
            "category": "test"
        }
        template_service.get_template_by_id.return_value = template
        
        # Call create_template_prompt twice with same parameters
        prompt_manager.create_template_prompt(template_id, {})
        result = prompt_manager.create_template_prompt(template_id, {})
        
        # Verify cache_get and cache_set are called with correct parameters
        assert mock_cache_get.call_count == 2
        mock_cache_set.assert_called_once()
        
        # Assert template service is called only on first invocation (cache miss)
        template_service.get_template_by_id.assert_called_once_with(template_id)
        
        # Verify cached result is returned on second call
        assert result == "Cached prompt"

class TestPromptManager:
    def setup_method(self, method):
        """Setup method that runs before each test"""
        # Create mock objects for all dependencies
        self.template_service = Mock(spec=TemplateService)
        self.token_optimizer = Mock(spec=TokenOptimizer)
        self.context_manager = Mock(spec=ContextManager)
        
        # Configure basic mock behaviors
        self.token_optimizer.count_tokens.return_value = 100  # Default token count
        
        # Initialize instance of PromptManager with mocked dependencies
        self.prompt_manager = PromptManager(
            template_service=self.template_service,
            token_optimizer=self.token_optimizer,
            context_manager=self.context_manager
        )
        
        # Set up common test data
        self.test_document = MOCK_DOCUMENT
        self.test_custom_prompt = CUSTOM_PROMPT

    def test_init(self):
        """Tests that PromptManager initializes correctly"""
        # Assert instance attributes are set correctly
        assert self.prompt_manager._template_service == self.template_service
        assert self.prompt_manager._token_optimizer == self.token_optimizer
        assert self.prompt_manager._context_manager == self.context_manager
        assert self.prompt_manager._use_cache is True  # Default value
    
    def test_create_system_prompt_default(self):
        """Tests default system prompt creation"""
        # Call create_system_prompt on prompt manager instance
        result = self.prompt_manager.create_system_prompt()
        
        # Assert result contains DEFAULT_SYSTEM_PROMPT
        assert DEFAULT_SYSTEM_PROMPT in result
        # Verify it also includes TRACK_CHANGES_FORMAT
        assert TRACK_CHANGES_FORMAT in result
        
    def test_create_system_prompt_custom(self):
        """Tests system prompt with custom instruction"""
        # Define custom instruction
        custom_instruction = "Respond in a formal tone."
        
        # Call create_system_prompt with custom instruction
        result = self.prompt_manager.create_system_prompt(custom_instruction)
        
        # Assert result contains both DEFAULT_SYSTEM_PROMPT and custom instruction
        assert DEFAULT_SYSTEM_PROMPT in result
        assert custom_instruction in result
        # Verify TRACK_CHANGES_FORMAT is still included
        assert TRACK_CHANGES_FORMAT in result
        
    def test_create_template_prompt(self, basic_system_template):
        """Tests template prompt creation"""
        # Configure mock template_service to return a specific template
        template_id = str(basic_system_template["_id"])
        self.template_service.get_template_by_id.return_value = basic_system_template
        
        # Call create_template_prompt with template ID
        result = self.prompt_manager.create_template_prompt(template_id, {})
        
        # Assert template_service.get_template_by_id was called
        self.template_service.get_template_by_id.assert_called_once_with(template_id)
        # Verify result contains expected template content
        assert basic_system_template["promptText"] in result
        
    def test_create_template_prompt_not_found(self):
        """Tests error handling for missing template"""
        # Configure mock template_service to return None
        self.template_service.get_template_by_id.return_value = None
        
        # Use pytest.raises to check for PromptTemplateNotFoundError
        with pytest.raises(PromptTemplateNotFoundError):
            self.prompt_manager.create_template_prompt("non_existent_id", {})
            
    def test_create_custom_prompt(self):
        """Tests custom prompt creation"""
        # Define custom prompt text
        prompt_text = self.test_custom_prompt
        
        # Call create_custom_prompt with this text
        result = self.prompt_manager.create_custom_prompt(prompt_text)
        
        # Assert result contains the custom text
        assert prompt_text in result
        # Verify TRACK_CHANGES_FORMAT is also included
        assert TRACK_CHANGES_FORMAT in result
        
    def test_optimize_prompt_with_content(self):
        """Tests prompt optimization with document content"""
        # Define sample prompt and document content
        prompt = "Improve this text:"
        document = self.test_document
        
        # Configure mock token_optimizer.optimize_prompt to return expected result
        optimized_content = f"{prompt}\n\n{document}"
        self.token_optimizer.optimize_prompt.return_value = optimized_content
        
        # Call optimize_prompt_with_content
        result = self.prompt_manager.optimize_prompt_with_content(prompt, document)
        
        # Assert token_optimizer.optimize_prompt was called with correct arguments
        self.token_optimizer.optimize_prompt.assert_called_once()
        call_args = self.token_optimizer.optimize_prompt.call_args[1]
        assert call_args["prompt"] == prompt
        assert call_args["content"] == document
        
        # Verify result matches expected optimized output
        assert result == optimized_content
        
    def test_create_chat_prompt(self):
        """Tests chat prompt creation"""
        # Define sample messages array
        messages = [
            {"role": "user", "content": "Can you help me improve this text?"},
            {"role": "assistant", "content": "Sure, I'd be happy to help."}
        ]
        
        # Call create_chat_prompt with messages
        result = self.prompt_manager.create_chat_prompt(messages)
        
        # Assert result has expected structure with system message
        assert len(result) == 3  # System message + 2 chat messages
        assert result[0]["role"] == "system"
        assert DEFAULT_SYSTEM_PROMPT in result[0]["content"]
        assert result[1] == messages[0]
        assert result[2] == messages[1]
        
    def test_create_suggestion_prompt(self):
        """Tests suggestion prompt creation"""
        # Configure mock dependencies
        template_id = "template123"
        template = {
            "_id": template_id,
            "name": "Test Template",
            "promptText": "Improve this text: {document}",
            "category": "test"
        }
        self.template_service.get_template_by_id.return_value = template
        
        document = self.test_document
        optimized_prompt = f"Improve this text: {document}"
        self.token_optimizer.optimize_prompt.return_value = optimized_prompt
        
        # Call create_suggestion_prompt with document and template ID
        result = self.prompt_manager.create_suggestion_prompt(document, template_id)
        
        # Assert appropriate template methods were called
        self.template_service.get_template_by_id.assert_called_once_with(template_id)
        
        # Verify optimization was applied
        self.token_optimizer.optimize_prompt.assert_called_once()
        
        # Check final prompt contains required instruction elements
        assert result == optimized_prompt
        
    def test_estimate_tokens(self):
        """Tests token estimation"""
        # Configure mock token_optimizer.count_tokens to return known values
        self.token_optimizer.count_tokens.side_effect = [50, 150]  # prompt, document
        
        # Call estimate_tokens with sample text
        result = self.prompt_manager.estimate_tokens("Test prompt", self.test_document)
        
        # Assert returned dictionary has expected structure
        assert "prompt_tokens" in result
        assert "document_tokens" in result
        assert "total_tokens" in result
        
        # Verify counts match expected values
        assert result["prompt_tokens"] == 50
        assert result["document_tokens"] == 150
        assert result["total_tokens"] == 200