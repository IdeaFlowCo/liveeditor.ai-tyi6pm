"""
Core utility package for the AI writing enhancement platform backend.

This package centralizes access to logging, validation, and security utilities
used throughout the application. It provides structured JSON logging,
input validation, and security mechanisms to protect against common web vulnerabilities.
"""

from typing import *

# Version information
__version__ = '1.0.0'

# Import and re-export logging utilities
from .logger import (
    setup_logging,
    get_logger,
    mask_pii,
    generate_correlation_id,
    JsonFormatter,
    ContextLogger,
    RequestLogger
)

# Import and re-export security utilities
from .security import (
    generate_token,
    generate_csrf_token,
    verify_csrf_token,
    hash_string,
    encrypt_text,
    decrypt_text,
    sanitize_html,
    get_secure_headers,
    encode_jwt,
    decode_jwt,
    secure_compare,
    EncryptionService,
    TokenManager,
    SecurityContext
)

# Import validators utilities (with internal names)
from .validators import (
    is_valid_email,
    is_valid_password,
    is_document_size_valid,
    is_valid_prompt,
    is_valid_username,
    is_valid_url,
    MAX_DOCUMENT_SIZE_WORDS,
    MAX_DOCUMENT_SIZE_BYTES,
    MAX_PROMPT_LENGTH
)

# Constants
PASSWORD_MIN_LENGTH = 10
MAX_DOCUMENT_WORDS = MAX_DOCUMENT_SIZE_WORDS

# Function aliases to match the expected exports
validate_email = is_valid_email
validate_password = is_valid_password
validate_document_size = is_document_size_valid
validate_prompt = is_valid_prompt
validate_username = is_valid_username
validate_url = is_valid_url

# Functions that need to be created to match expected exports
def validate_token(token: str, secret_key: str = None) -> bool:
    """
    Validate JWT token format and expiration.
    
    Args:
        token: Token to validate
        secret_key: Secret key for JWT validation
        
    Returns:
        True if token is valid, False otherwise
    """
    if not token:
        return False
        
    # For JWT tokens
    if token.count('.') == 2 and secret_key:
        try:
            decode_jwt(token, secret_key)
            return True
        except:
            return False
    
    # For simple tokens
    return bool(token) and len(token) >= 8

def validate_object_id(object_id: str) -> bool:
    """
    Validate MongoDB ObjectId format.
    
    Args:
        object_id: String to validate as ObjectId
        
    Returns:
        True if valid ObjectId format, False otherwise
    """
    if not object_id:
        return False
        
    # Simple format validation for MongoDB ObjectId
    # Real implementation would use bson.objectid.ObjectId
    return len(object_id) == 24 and all(c in '0123456789abcdefABCDEF' for c in object_id)