"""
Core security utilities for the AI writing enhancement application.

This module provides functions and classes for handling security-related operations,
including encryption, token handling, security validation, and protection against
common web vulnerabilities.
"""

import secrets
import hashlib
import hmac
import base64
import os
import re
import time
import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

from Cryptodome.Cipher import AES  # pycryptodomex 3.10.1
from Cryptodome.Random import get_random_bytes  # pycryptodomex 3.10.1
import jwt  # PyJWT 2.7.0
import bleach  # bleach 5.0.1
from werkzeug.security import generate_password_hash, check_password_hash  # Werkzeug 2.3.0

# Constants
DEFAULT_ENCRYPTION_KEY_LENGTH = 32  # 256 bits
DEFAULT_TOKEN_LENGTH = 48
DEFAULT_HASH_ALGORITHM = 'sha256'
CSRF_TOKEN_VALIDITY = 3600  # 1 hour in seconds

# Token Generation and Validation

def generate_token(length: int = DEFAULT_TOKEN_LENGTH) -> str:
    """
    Generates a cryptographically secure random token of specified length.
    
    Args:
        length: Length of the token to generate (default: DEFAULT_TOKEN_LENGTH)
        
    Returns:
        A secure random token string
    """
    # Generate a token using secrets module which provides cryptographically strong randomness
    raw_token = secrets.token_urlsafe(length)
    
    # Ensure the token is exactly the requested length
    # token_urlsafe() might generate tokens slightly longer due to base64 encoding
    if len(raw_token) > length:
        return raw_token[:length]
    return raw_token


def generate_csrf_token() -> str:
    """
    Generates a CSRF token for form protection.
    
    Returns:
        A CSRF token that can be included in forms and verified later
    """
    # Generate a secure random token
    token_value = generate_token(32)
    
    # Include a timestamp for expiration checking
    timestamp = str(int(time.time()))
    
    # Combine token and timestamp
    raw_token = f"{token_value}|{timestamp}"
    
    # Sign the token using HMAC
    # In a real application, the secret key would be retrieved from a secure source
    # For this implementation, we'll use a placeholder secret
    secret = "application_secret_key"  # In production, this would be securely stored
    signature = generate_signature(raw_token, secret, DEFAULT_HASH_ALGORITHM)
    
    # Combine token, timestamp, and signature
    combined = f"{raw_token}|{signature}"
    
    # Encode as URL-safe base64
    return base64.urlsafe_b64encode(combined.encode()).decode()


def verify_csrf_token(token: str) -> bool:
    """
    Verifies a CSRF token is valid and not expired.
    
    Args:
        token: The CSRF token to verify
        
    Returns:
        True if token is valid and not expired, False otherwise
    """
    try:
        # Decode the token
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
        
        # Split into parts
        parts = decoded.split('|')
        if len(parts) != 3:
            return False
        
        token_value, timestamp, signature = parts
        
        # Verify the signature
        raw_token = f"{token_value}|{timestamp}"
        secret = "application_secret_key"  # Same secret used for generation
        expected_signature = generate_signature(raw_token, secret, DEFAULT_HASH_ALGORITHM)
        
        if not secure_compare(signature, expected_signature):
            return False
        
        # Check if token has expired
        token_time = int(timestamp)
        current_time = int(time.time())
        if current_time - token_time > CSRF_TOKEN_VALIDITY:
            return False
        
        return True
    except Exception:
        # Any exception during verification means the token is invalid
        return False


# Hashing and Encryption

def hash_string(input_string: str, algorithm: str = DEFAULT_HASH_ALGORITHM) -> str:
    """
    Creates a secure hash of a string using specified algorithm.
    
    Args:
        input_string: The string to hash
        algorithm: Hashing algorithm to use (default: DEFAULT_HASH_ALGORITHM)
        
    Returns:
        Hexadecimal representation of the hash
    """
    if algorithm not in hashlib.algorithms_guaranteed:
        raise ValueError(f"Unsupported hashing algorithm: {algorithm}")
    
    # Create a new hash object with the specified algorithm
    hash_obj = hashlib.new(algorithm)
    
    # Update the hash object with the input string
    hash_obj.update(input_string.encode('utf-8'))
    
    # Return the hexadecimal digest
    return hash_obj.hexdigest()


def generate_encryption_key(length: int = DEFAULT_ENCRYPTION_KEY_LENGTH) -> bytes:
    """
    Generates a secure random key for encryption operations.
    
    Args:
        length: Length of the key in bytes (default: DEFAULT_ENCRYPTION_KEY_LENGTH)
        
    Returns:
        Binary key suitable for encryption operations
    """
    return os.urandom(length)


def encrypt_text(plaintext: str, key: bytes) -> str:
    """
    Encrypts text data using AES-256 encryption.
    
    Args:
        plaintext: The text to encrypt
        key: The encryption key (should be 32 bytes for AES-256)
        
    Returns:
        Base64-encoded encrypted data with IV
    """
    # Validate key length for AES-256
    if len(key) != 32:
        raise ValueError("Key must be 32 bytes (256 bits) for AES-256 encryption")
    
    # Generate a random initialization vector (IV)
    iv = get_random_bytes(16)  # AES block size is 16 bytes
    
    # Create a new AES cipher object in CBC mode
    cipher = AES.new(key, AES.MODE_CBC, iv)
    
    # Encode and pad the plaintext
    # PKCS#7 padding: pad with bytes all of the same value as the number of padding bytes
    data = plaintext.encode('utf-8')
    block_size = 16
    padding_length = block_size - (len(data) % block_size)
    padding = bytes([padding_length]) * padding_length
    padded_data = data + padding
    
    # Encrypt the padded data
    ciphertext = cipher.encrypt(padded_data)
    
    # Combine the IV and ciphertext
    encrypted_data = iv + ciphertext
    
    # Encode as Base64 and return as string
    return base64.b64encode(encrypted_data).decode('utf-8')


def decrypt_text(ciphertext: str, key: bytes) -> str:
    """
    Decrypts text data that was encrypted with encrypt_text.
    
    Args:
        ciphertext: Base64-encoded encrypted data with IV
        key: The encryption key (should be 32 bytes for AES-256)
        
    Returns:
        Original plaintext if decryption is successful
    """
    # Validate key length for AES-256
    if len(key) != 32:
        raise ValueError("Key must be 32 bytes (256 bits) for AES-256 decryption")
    
    try:
        # Decode the Base64-encoded ciphertext
        encrypted_data = base64.b64decode(ciphertext.encode('utf-8'))
        
        # Extract the IV (first 16 bytes)
        iv = encrypted_data[:16]
        
        # Extract the actual ciphertext data
        actual_ciphertext = encrypted_data[16:]
        
        # Create a new AES cipher object in CBC mode
        cipher = AES.new(key, AES.MODE_CBC, iv)
        
        # Decrypt the ciphertext
        padded_data = cipher.decrypt(actual_ciphertext)
        
        # Remove the padding
        # PKCS#7 unpadding: last byte indicates the number of padding bytes
        padding_length = padded_data[-1]
        if padding_length > 16:  # Sanity check for valid padding
            raise ValueError("Invalid padding")
        
        data = padded_data[:-padding_length]
        
        # Decode the data to string
        return data.decode('utf-8')
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")


# Content Security

def sanitize_html(html_content: str, 
                 allowed_tags: List[str] = None, 
                 allowed_attributes: Dict[str, List[str]] = None) -> str:
    """
    Sanitizes HTML content to prevent XSS attacks.
    
    Args:
        html_content: The HTML content to sanitize
        allowed_tags: List of allowed HTML tags (default: bleach defaults)
        allowed_attributes: Dictionary of allowed attributes for tags (default: bleach defaults)
        
    Returns:
        Sanitized HTML content with potentially dangerous tags/attributes removed
    """
    if allowed_tags is None:
        allowed_tags = bleach.ALLOWED_TAGS
    
    if allowed_attributes is None:
        allowed_attributes = bleach.ALLOWED_ATTRIBUTES
    
    # Use bleach to clean the HTML
    return bleach.clean(
        html_content,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )


def generate_signature(data: str, key: str, algorithm: str = DEFAULT_HASH_ALGORITHM) -> str:
    """
    Creates an HMAC signature for data using a secret key.
    
    Args:
        data: The data to sign
        key: The secret key for signing
        algorithm: Hashing algorithm to use (default: DEFAULT_HASH_ALGORITHM)
        
    Returns:
        Hexadecimal signature string
    """
    # Encode the data and key
    data_bytes = data.encode('utf-8')
    key_bytes = key.encode('utf-8')
    
    # Create an HMAC object
    hmac_obj = hmac.new(key_bytes, data_bytes, getattr(hashlib, algorithm))
    
    # Return the hexadecimal digest
    return hmac_obj.hexdigest()


def verify_signature(data: str, signature: str, key: str, 
                    algorithm: str = DEFAULT_HASH_ALGORITHM) -> bool:
    """
    Verifies an HMAC signature against data using a secret key.
    
    Args:
        data: The data that was signed
        signature: The signature to verify
        key: The secret key used for signing
        algorithm: Hashing algorithm used (default: DEFAULT_HASH_ALGORITHM)
        
    Returns:
        True if signature is valid, False otherwise
    """
    # Generate a signature for the data using the same key and algorithm
    expected_signature = generate_signature(data, key, algorithm)
    
    # Compare the generated signature with the provided signature using constant-time comparison
    return secure_compare(signature, expected_signature)


def get_secure_headers(with_content_security_policy: bool = True) -> Dict[str, str]:
    """
    Returns a dictionary of recommended security headers for HTTP responses.
    
    Args:
        with_content_security_policy: Whether to include Content-Security-Policy header
        
    Returns:
        Dictionary of security headers and their values
    """
    headers = {
        # Prevent MIME type sniffing
        'X-Content-Type-Options': 'nosniff',
        
        # Control how the browser renders page in frames (clickjacking protection)
        'X-Frame-Options': 'DENY',
        
        # Enable browser's XSS filtering
        'X-XSS-Protection': '1; mode=block',
        
        # HTTP Strict Transport Security (force HTTPS)
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        
        # Restrict where resources can be loaded from
        'Referrer-Policy': 'same-origin'
    }
    
    # Add Content-Security-Policy if requested
    if with_content_security_policy:
        headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "img-src 'self' data:; "
            "style-src 'self'; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )
    
    return headers


def validate_safe_content(content: str) -> bool:
    """
    Validates if content contains potentially malicious patterns.
    
    Args:
        content: The content to validate
        
    Returns:
        True if content appears safe, False if suspicious patterns are detected
    """
    # Check for suspicious patterns that might indicate XSS attempts
    suspicious_patterns = [
        r'<script.*?>',                 # Script tags
        r'javascript:',                 # JavaScript URLs
        r'<iframe.*?>',                 # iframes
        r'<object.*?>',                 # object tags
        r'<embed.*?>',                  # embed tags
        r'on\w+\s*=',                   # Event handlers (onclick, onload, etc.)
        r'document\.cookie',            # Cookie access
        r'document\.location',          # Location manipulation
        r'eval\s*\(',                   # eval function calls
        r'setTimeout\s*\(',             # setTimeout function calls
        r'setInterval\s*\(',            # setInterval function calls
        r'<!ENTITY',                    # XML entity attacks
        r'data:text/html',              # Data URLs for HTML
    ]
    
    # Check each pattern
    for pattern in suspicious_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return False
    
    return True


# JWT Token Handling

def encode_jwt(payload: Dict[str, Any], secret_key: str, 
               algorithm: str = 'HS256', expiration_seconds: int = 3600) -> str:
    """
    Encodes data into a JSON Web Token (JWT).
    
    Args:
        payload: Dictionary of data to encode in the token
        secret_key: Secret key for signing the token
        algorithm: Algorithm to use for signing (default: 'HS256')
        expiration_seconds: Token expiration time in seconds (default: 1 hour)
        
    Returns:
        Encoded JWT string
    """
    # Create a copy of the payload to avoid modifying the original
    payload_copy = payload.copy()
    
    # Add standard claims: issued at and expiration time
    now = datetime.datetime.utcnow()
    
    # Add issued at claim (iat)
    payload_copy['iat'] = now
    
    # Add expiration claim (exp)
    payload_copy['exp'] = now + datetime.timedelta(seconds=expiration_seconds)
    
    # Encode the token
    return jwt.encode(payload_copy, secret_key, algorithm=algorithm)


def decode_jwt(token: str, secret_key: str, algorithm: str = 'HS256') -> Dict[str, Any]:
    """
    Decodes and validates a JSON Web Token (JWT).
    
    Args:
        token: The JWT to decode and validate
        secret_key: Secret key used to sign the token
        algorithm: Algorithm used for signing (default: 'HS256')
        
    Returns:
        Decoded payload from the JWT if valid
        
    Raises:
        jwt.InvalidTokenError: If token is invalid
        jwt.ExpiredSignatureError: If token has expired
        jwt.DecodeError: If token cannot be decoded
    """
    try:
        # Decode the token and verify signature, expiration, etc.
        return jwt.decode(token, secret_key, algorithms=[algorithm])
    except jwt.ExpiredSignatureError:
        raise jwt.ExpiredSignatureError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise jwt.InvalidTokenError(f"Invalid token: {str(e)}")


# Rate Limiting

def is_rate_limited(key: str, limit: int, period_seconds: int) -> bool:
    """
    Checks if an operation should be rate limited based on key and limit.
    
    Note: This is a simplified implementation. In a real application, this would
    typically use Redis or a similar system to track request counts.
    
    Args:
        key: Identifier for the rate limit (e.g., user ID, IP address)
        limit: Maximum number of operations allowed in the period
        period_seconds: Time period in seconds
        
    Returns:
        True if rate limit is exceeded, False otherwise
    """
    # NOTE: This is a simplified implementation that would be replaced with
    # a real rate limiting implementation using Redis or similar in production
    
    # In a real implementation, you would:
    # 1. Get the current count for the key from Redis
    # 2. Check if the count exceeds the limit
    # 3. If not, increment the count and set expiration if needed
    # 4. Return True if limit exceeded, False otherwise
    
    # For this implementation, we'll just return False (no rate limiting)
    # as this is just a placeholder for the actual implementation
    return False


# Secure Comparison

def secure_compare(a: str, b: str) -> bool:
    """
    Performs a constant-time comparison of two strings to prevent timing attacks.
    
    Args:
        a: First string to compare
        b: Second string to compare
        
    Returns:
        True if strings are equal, False otherwise
    """
    return hmac.compare_digest(a, b)


# Classes

class EncryptionService:
    """
    Class for handling encryption and decryption operations with key management.
    """
    
    def __init__(self, key: bytes = None):
        """
        Initializes the EncryptionService with an encryption key.
        
        Args:
            key: Encryption key to use (if None, a new key will be generated)
        """
        if key is None:
            # Generate a new key if none is provided
            self._key = generate_encryption_key()
        else:
            # Ensure the provided key is the correct length
            if len(key) != DEFAULT_ENCRYPTION_KEY_LENGTH:
                raise ValueError(
                    f"Encryption key must be {DEFAULT_ENCRYPTION_KEY_LENGTH} bytes for AES-256"
                )
            self._key = key
    
    def encrypt(self, data: str) -> str:
        """
        Encrypts data using the service's encryption key.
        
        Args:
            data: The string data to encrypt
            
        Returns:
            Encrypted data as a Base64 string
        """
        return encrypt_text(data, self._key)
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypts data using the service's encryption key.
        
        Args:
            encrypted_data: The encrypted data to decrypt
            
        Returns:
            Decrypted original data
        """
        return decrypt_text(encrypted_data, self._key)
    
    def rotate_key(self) -> bytes:
        """
        Generates a new encryption key and returns it.
        
        Returns:
            Newly generated encryption key
        """
        # Generate a new key
        new_key = generate_encryption_key()
        
        # Update the service's key
        self._key = new_key
        
        # Return the new key so it can be stored/backed up
        return new_key


class TokenManager:
    """
    Manages creation, validation, and rotation of security tokens.
    """
    
    def __init__(self, secret_key: str):
        """
        Initializes the TokenManager with a secret key.
        
        Args:
            secret_key: Secret key for token signing
        """
        self._secret_key = secret_key
        self._token_blacklist = {}  # token -> expiration_time
    
    def create_token(self, payload: Dict[str, Any], expiration_seconds: int = 3600) -> str:
        """
        Creates a JWT with the specified payload and duration.
        
        Args:
            payload: Data to include in the token
            expiration_seconds: Token lifetime in seconds
            
        Returns:
            JWT token string
        """
        return encode_jwt(payload, self._secret_key, expiration_seconds=expiration_seconds)
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validates a JWT and returns its payload if valid.
        
        Args:
            token: JWT token to validate
            
        Returns:
            Token payload if valid, None otherwise
        """
        # Check if token is blacklisted
        if token in self._token_blacklist:
            return None
        
        try:
            # Decode and validate the token
            payload = decode_jwt(token, self._secret_key)
            return payload
        except Exception:
            # Any exception means the token is invalid
            return None
    
    def blacklist_token(self, token: str) -> bool:
        """
        Adds a token to the blacklist.
        
        Args:
            token: JWT token to blacklist
            
        Returns:
            True if blacklisted successfully, False otherwise
        """
        try:
            # Decode the token to get its expiration time
            payload = decode_jwt(token, self._secret_key)
            exp_time = payload.get('exp')
            
            if exp_time:
                # Add to blacklist with expiration time
                self._token_blacklist[token] = exp_time
                return True
            return False
        except Exception:
            # If token can't be decoded, it's already invalid so no need to blacklist
            return False
    
    def clean_blacklist(self) -> int:
        """
        Removes expired tokens from the blacklist.
        
        Returns:
            Number of tokens removed from blacklist
        """
        current_time = datetime.datetime.utcnow().timestamp()
        expired_tokens = [
            token for token, exp_time in self._token_blacklist.items()
            if exp_time < current_time
        ]
        
        # Remove expired tokens from blacklist
        for token in expired_tokens:
            del self._token_blacklist[token]
        
        return len(expired_tokens)
    
    def refresh_token(self, token: str, expiration_seconds: int = 3600) -> Optional[str]:
        """
        Blacklists the current token and creates a new one with the same payload.
        
        Args:
            token: Current JWT token
            expiration_seconds: New token lifetime in seconds
            
        Returns:
            New JWT token string or None if current token is invalid
        """
        # Validate current token
        payload = self.validate_token(token)
        if not payload:
            return None
        
        # Blacklist current token
        self.blacklist_token(token)
        
        # Create new token with same payload (but new exp)
        # Remove standard JWT claims that will be re-added
        for claim in ['exp', 'iat']:
            if claim in payload:
                del payload[claim]
        
        return self.create_token(payload, expiration_seconds)


class SecurityContext:
    """
    Maintains security-related context for requests and operations.
    """
    
    def __init__(self, initial_context: Dict[str, Any] = None):
        """
        Initializes a new security context with optional initial values.
        
        Args:
            initial_context: Initial context values
        """
        self._context = {}
        
        # Update with initial context if provided
        if initial_context:
            self._context.update(initial_context)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieves a value from the security context.
        
        Args:
            key: Context key to retrieve
            default: Default value if key not found
            
        Returns:
            Value from context or default if not found
        """
        return self._context.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Sets a value in the security context.
        
        Args:
            key: Context key to set
            value: Value to set
        """
        self._context[key] = value
    
    def clear(self) -> None:
        """
        Clears the entire security context.
        """
        self._context = {}
    
    def as_dict(self) -> Dict[str, Any]:
        """
        Returns a copy of the entire security context as a dictionary.
        
        Returns:
            Copy of the security context
        """
        return self._context.copy()