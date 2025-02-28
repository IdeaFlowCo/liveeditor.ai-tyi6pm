"""
Provides common validation utilities for the AI-powered writing enhancement application,
including functions to validate input data, sanitize content, check for malicious patterns,
and verify document content against defined constraints. Used across the application to
ensure data integrity and security.
"""

import re  # standard library
import typing  # standard library
import datetime  # standard library
from email_validator import validate_email, EmailNotValidError  # email_validator 2.0.0
import validators  # validators 0.20.0
from pydantic import ValidationError as PydanticValidationError  # pydantic ^1.10.0

from .logger import get_logger
from .security import sanitize_html, validate_safe_content

# Initialize logger
logger = get_logger('validators')

# Regular expression patterns
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
URL_REGEX = re.compile(r'^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/ \w \.-]*)*\/?$')
PASSWORD_REGEX = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')
USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9_-]{3,16}$')

# Constants
MAX_DOCUMENT_SIZE_WORDS = 25000
MAX_DOCUMENT_SIZE_BYTES = 10485760  # 10 MB
MAX_TITLE_LENGTH = 100
MAX_PROMPT_LENGTH = 1000
ALLOWED_DOCUMENT_FORMATS = ["txt", "html", "md", "docx", "rtf"]
ALLOWED_HTML_TAGS = ["p", "h1", "h2", "h3", "h4", "h5", "h6", "strong", "em", "u", "s", "ul", "ol", "li", "blockquote", "pre", "code", "br"]


def is_valid_email(email: str) -> bool:
    """
    Validates if a string is a properly formatted email address.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email is valid, False otherwise
    """
    if not email:
        return False
        
    try:
        # Validate using email_validator library
        validate_email(email)
        return True
    except EmailNotValidError as e:
        logger.debug(f"Invalid email format: {email} - {str(e)}")
        return False
    except Exception as e:
        logger.warning(f"Error validating email: {str(e)}")
        return False


def is_valid_url(url: str) -> bool:
    """
    Validates if a string is a properly formatted URL.
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL is valid, False otherwise
    """
    if not url:
        return False
        
    return validators.url(url) is True


def is_valid_password(password: str) -> bool:
    """
    Validates if a password meets security requirements.
    
    Args:
        password: Password to validate
        
    Returns:
        True if password meets requirements, False otherwise
    """
    if not password:
        return False
    
    return bool(PASSWORD_REGEX.match(password))


def is_valid_username(username: str) -> bool:
    """
    Validates if a username meets formatting requirements.
    
    Args:
        username: Username to validate
        
    Returns:
        True if username is valid, False otherwise
    """
    if not username:
        return False
    
    return bool(USERNAME_REGEX.match(username))


def is_document_size_valid(content: str) -> bool:
    """
    Checks if document size is within acceptable limits.
    
    Args:
        content: Document content to check
        
    Returns:
        True if document size is valid, False otherwise
    """
    if not content:
        return True
    
    # Check byte size
    if len(content.encode('utf-8')) > MAX_DOCUMENT_SIZE_BYTES:
        logger.info(f"Document exceeds maximum byte size: {len(content.encode('utf-8'))} bytes")
        return False
    
    # Check word count
    word_count = get_word_count(content)
    if word_count > MAX_DOCUMENT_SIZE_WORDS:
        logger.info(f"Document exceeds maximum word count: {word_count} words")
        return False
    
    return True


def validate_document_content(content: str, check_malicious_content: bool = True) -> typing.Tuple[bool, str]:
    """
    Validates document content for size, format, and security issues.
    
    Args:
        content: Document content to validate
        check_malicious_content: Whether to check for malicious content
        
    Returns:
        Tuple of (valid, error_message)
    """
    if not content:
        return False, "Content cannot be empty"
    
    # Check document size
    if not is_document_size_valid(content):
        return False, f"Document exceeds maximum size limit of {MAX_DOCUMENT_SIZE_WORDS} words or {MAX_DOCUMENT_SIZE_BYTES/1024/1024:.1f} MB"
    
    # Check for malicious content if enabled
    if check_malicious_content and not validate_safe_content(content):
        return False, "Document contains potentially unsafe content"
    
    return True, ""


def sanitize_document_content(content: str, is_html: bool = False) -> str:
    """
    Sanitizes document content to remove potentially malicious elements.
    
    Args:
        content: Document content to sanitize
        is_html: Whether the content is HTML
        
    Returns:
        Sanitized content
    """
    if not content:
        return ""
        
    if not is_html:
        return content
    
    return sanitize_html(content, ALLOWED_HTML_TAGS)


def is_valid_document_format(file_extension: str) -> bool:
    """
    Checks if the document format is supported by the system.
    
    Args:
        file_extension: File extension to check
        
    Returns:
        True if format is supported, False otherwise
    """
    if not file_extension:
        return False
        
    # Remove leading dot if present and convert to lowercase
    if file_extension.startswith('.'):
        file_extension = file_extension[1:]
    
    file_extension = file_extension.lower()
    
    return file_extension in ALLOWED_DOCUMENT_FORMATS


def is_valid_prompt(prompt: str) -> bool:
    """
    Validates if an AI prompt meets length and content requirements.
    
    Args:
        prompt: Prompt to validate
        
    Returns:
        True if prompt is valid, False otherwise
    """
    if not prompt:
        return False
    
    # Check length
    if len(prompt) > MAX_PROMPT_LENGTH:
        logger.info(f"Prompt exceeds maximum length: {len(prompt)} characters")
        return False
    
    # Check for malicious content
    if not validate_safe_content(prompt):
        logger.warning(f"Prompt contains potentially unsafe content")
        return False
    
    return True


def is_valid_title(title: str) -> bool:
    """
    Validates if a document title meets length and content requirements.
    
    Args:
        title: Title to validate
        
    Returns:
        True if title is valid, False otherwise
    """
    if not title:
        return False
    
    # Check length
    if len(title) > MAX_TITLE_LENGTH:
        logger.info(f"Title exceeds maximum length: {len(title)} characters")
        return False
    
    # Check for malicious content
    if not validate_safe_content(title):
        logger.warning(f"Title contains potentially unsafe content")
        return False
    
    return True


def is_valid_date_format(date_str: str, format_str: str = "%Y-%m-%d") -> bool:
    """
    Validates if a string is a properly formatted date.
    
    Args:
        date_str: Date string to validate
        format_str: Expected date format
        
    Returns:
        True if date string matches format, False otherwise
    """
    if not date_str:
        return False
        
    try:
        datetime.datetime.strptime(date_str, format_str)
        return True
    except ValueError:
        return False
    except Exception as e:
        logger.warning(f"Error validating date format: {str(e)}")
        return False


def is_valid_uuid(uuid_str: str) -> bool:
    """
    Validates if a string is a properly formatted UUID.
    
    Args:
        uuid_str: UUID string to validate
        
    Returns:
        True if string is a valid UUID, False otherwise
    """
    if not uuid_str:
        return False
        
    return validators.uuid(uuid_str) is True


def get_word_count(content: str) -> int:
    """
    Counts the number of words in a document.
    
    Args:
        content: Document content
        
    Returns:
        Number of words in the content
    """
    if not content:
        return 0
    
    words = [w for w in content.split() if w.strip()]
    return len(words)


def truncate_string(text: str, max_length: int) -> str:
    """
    Truncates a string to a specified length with ellipsis.
    
    Args:
        text: String to truncate
        max_length: Maximum length
        
    Returns:
        Truncated string with ellipsis if needed
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."


class ValidationError(Exception):
    """
    Custom exception class for validation errors.
    """
    
    def __init__(self, message: str, errors: typing.Dict[str, typing.List[str]] = None):
        """
        Initialize ValidationError with message and optional errors dict.
        
        Args:
            message: Error message
            errors: Dictionary of field errors
        """
        super().__init__(message)
        self.message = message
        self.errors = errors or {}
    
    def add_error(self, field: str, error: str) -> None:
        """
        Add an error for a specific field.
        
        Args:
            field: Field name
            error: Error message
        """
        if field in self.errors:
            self.errors[field].append(error)
        else:
            self.errors[field] = [error]
    
    def get_errors(self) -> typing.Dict[str, typing.List[str]]:
        """
        Get all validation errors.
        
        Returns:
            Dictionary of field errors
        """
        return self.errors
    
    def has_errors(self) -> bool:
        """
        Check if there are any validation errors.
        
        Returns:
            True if errors dictionary is not empty
        """
        return bool(self.errors)


class DocumentValidator:
    """
    Class for comprehensive document validation.
    """
    
    def __init__(self):
        """
        Initialize document validator.
        """
        self.errors = {}
    
    def validate_document(self, document_data: typing.Dict[str, typing.Any]) -> bool:
        """
        Perform complete validation of document data.
        
        Args:
            document_data: Document data to validate
            
        Returns:
            True if validation passes, False otherwise
        """
        # Clear previous errors
        self.errors = {}
        
        # Validate title
        title = document_data.get('title')
        if not title:
            self._add_error('title', 'Document title is required')
        elif not is_valid_title(title):
            self._add_error('title', f'Document title is invalid or too long (max {MAX_TITLE_LENGTH} characters)')
        
        # Validate content
        content = document_data.get('content')
        valid, error_message = validate_document_content(content)
        if not valid:
            self._add_error('content', error_message)
        
        # Validate tags if present
        tags = document_data.get('tags')
        if tags and not isinstance(tags, list):
            self._add_error('tags', 'Tags must be a list')
        
        # Return whether validation passed
        return not bool(self.errors)
    
    def get_errors(self) -> typing.Dict[str, typing.List[str]]:
        """
        Get all validation errors.
        
        Returns:
            Dictionary of field errors
        """
        return self.errors
    
    def _add_error(self, field: str, message: str) -> None:
        """
        Internal method to add validation error.
        
        Args:
            field: Field name
            message: Error message
        """
        if field in self.errors:
            self.errors[field].append(message)
        else:
            self.errors[field] = [message]


class InputValidator:
    """
    Class for generic input validation with customizable rules.
    """
    
    def __init__(self, validation_rules: typing.Dict[str, typing.Dict[str, typing.Any]] = None):
        """
        Initialize input validator with optional validation rules.
        
        Args:
            validation_rules: Dictionary of field validation rules
        """
        self.validation_rules = validation_rules or {}
        self.errors = {}
    
    def add_rule(self, field: str, validation_func: callable, error_message: str) -> None:
        """
        Add a validation rule for a field.
        
        Args:
            field: Field name
            validation_func: Validation function that returns bool
            error_message: Error message if validation fails
        """
        self.validation_rules[field] = {
            'func': validation_func,
            'error': error_message
        }
    
    def validate(self, data: typing.Dict[str, typing.Any]) -> bool:
        """
        Validate input data against all rules.
        
        Args:
            data: Data to validate
            
        Returns:
            True if all validations pass, False otherwise
        """
        # Clear previous errors
        self.errors = {}
        
        # Check each field against its validation rules
        for field, rule in self.validation_rules.items():
            if field in data:
                value = data[field]
                validation_func = rule['func']
                error_message = rule['error']
                
                if not validation_func(value):
                    if field in self.errors:
                        self.errors[field].append(error_message)
                    else:
                        self.errors[field] = [error_message]
        
        # Return whether validation passed
        return not bool(self.errors)
    
    def get_errors(self) -> typing.Dict[str, typing.List[str]]:
        """
        Get all validation errors.
        
        Returns:
            Dictionary of field errors
        """
        return self.errors
    
    def has_errors(self) -> bool:
        """
        Check if there are any validation errors.
        
        Returns:
            True if errors dictionary is not empty
        """
        return bool(self.errors)