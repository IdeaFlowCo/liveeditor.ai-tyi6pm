"""
Provides structured logging functionality for the AI writing enhancement application
with support for context tracking, correlation IDs, and PII masking.
Implements JSON-formatted logs with consistent fields across all components.
"""

import logging  # standard library
import json  # standard library
import datetime  # standard library
import uuid  # standard library
import re  # standard library
import copy  # standard library
import typing  # standard library
import traceback  # standard library
import threading  # standard library
import flask  # Flask ~=2.3.0

# Default configuration
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_JSON_FORMAT = True
DEFAULT_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

# PII pattern definitions for masking
PII_PATTERNS = {
    "email": r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+',
    "credit_card": r'[0-9]{13,19}',
    "phone": r'(\+\d{1,3}[- ]?)?\d{10}',
    "ssn": r'\d{3}-\d{2}-\d{4}'
}

# Sensitive field names that should always be masked
SENSITIVE_FIELDS = ["password", "token", "secret", "credential", "key", "api_key", "apikey", "auth", "authorization"]

# Thread-local storage for context data
_context_storage = threading.local()

# Flag to track if logging system has been initialized
_initialized = False


class JsonFormatter(logging.Formatter):
    """
    Custom log formatter that outputs logs in JSON format with support for extra fields.
    """
    
    def __init__(self, date_format: str):
        """
        Initialize the JSON formatter with date format.
        
        Args:
            date_format: The date format to use for timestamps
        """
        super().__init__()
        self.date_format = date_format
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON string with standardized fields.
        
        Args:
            record: The log record to format
            
        Returns:
            JSON formatted log entry
        """
        log_record = {
            "timestamp": datetime.datetime.fromtimestamp(record.created).strftime(self.date_format),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "logger": record.name,
            "thread": record.thread,
            "path": record.pathname,
            "line": record.lineno,
        }
        
        # Add correlation ID if available
        correlation_id = get_current_correlation_id()
        if correlation_id:
            log_record["correlation_id"] = correlation_id
        
        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = self.format_exception(record)
        
        # Add any extra fields
        self.add_fields(log_record, record)
        
        # Convert to JSON
        return json.dumps(log_record)
    
    def add_fields(self, log_record: dict, record: logging.LogRecord) -> None:
        """
        Add additional fields to the log record.
        
        Args:
            log_record: The dictionary to add fields to
            record: The log record containing extra fields
        """
        # Add any extra context
        if hasattr(record, "args") and isinstance(record.args, dict):
            for key, value in record.args.items():
                if key not in log_record:
                    log_record[key] = mask_pii(value, SENSITIVE_FIELDS)
        
        # Add any other attributes that were added programmatically
        for key, value in record.__dict__.items():
            if key not in ["args", "exc_info", "exc_text", "stack_info", "lineno", 
                          "funcName", "created", "msecs", "relativeCreated", 
                          "levelname", "levelno", "pathname", "filename", 
                          "module", "name", "thread", "threadName", 
                          "processName", "process", "msg"]:
                if key not in log_record:
                    log_record[key] = mask_pii(value, SENSITIVE_FIELDS)
    
    def format_exception(self, record: logging.LogRecord) -> dict:
        """
        Format exception information for logging.
        
        Args:
            record: The log record with exception information
            
        Returns:
            Formatted exception information
        """
        if not record.exc_info:
            return {}
        
        exc_type, exc_value, exc_tb = record.exc_info
        
        return {
            "type": exc_type.__name__ if exc_type else None,
            "message": str(exc_value) if exc_value else None,
            "traceback": traceback.format_exception(*record.exc_info) if record.exc_info else None
        }


class ContextLogger:
    """
    Wrapper for standard logger that provides context tracking capabilities.
    """
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize with a standard logger instance.
        
        Args:
            logger: The standard logger instance to wrap
        """
        self.logger = logger
        self.context = {}
    
    def set_correlation_id(self, correlation_id: str) -> None:
        """
        Set correlation ID for this logger context.
        
        Args:
            correlation_id: The correlation ID to set
        """
        self.context["correlation_id"] = correlation_id
        set_correlation_id(correlation_id)
    
    def bind(self, context_data: dict) -> 'ContextLogger':
        """
        Bind additional context data to the logger.
        
        Args:
            context_data: Dictionary of context data to bind
            
        Returns:
            Self for chaining
        """
        self.context.update(context_data)
        return self
    
    def unbind(self, keys: list) -> 'ContextLogger':
        """
        Remove specific keys from the bound context.
        
        Args:
            keys: List of keys to remove
            
        Returns:
            Self for chaining
        """
        for key in keys:
            if key in self.context:
                del self.context[key]
        return self
    
    def new(self, context_data: dict) -> 'ContextLogger':
        """
        Create a new logger with additional context.
        
        Args:
            context_data: Context data for the new logger
            
        Returns:
            New logger instance with combined context
        """
        new_logger = ContextLogger(self.logger)
        new_logger.context = self.context.copy()
        new_logger.context.update(context_data)
        return new_logger
    
    def debug(self, msg: str, **extra) -> None:
        """
        Log a debug message with context.
        
        Args:
            msg: The message to log
            extra: Additional data to log
        """
        combined_extra = self.context.copy()
        combined_extra.update(extra)
        self.logger.debug(msg, extra=combined_extra)
    
    def info(self, msg: str, **extra) -> None:
        """
        Log an info message with context.
        
        Args:
            msg: The message to log
            extra: Additional data to log
        """
        combined_extra = self.context.copy()
        combined_extra.update(extra)
        self.logger.info(msg, extra=combined_extra)
    
    def warning(self, msg: str, **extra) -> None:
        """
        Log a warning message with context.
        
        Args:
            msg: The message to log
            extra: Additional data to log
        """
        combined_extra = self.context.copy()
        combined_extra.update(extra)
        self.logger.warning(msg, extra=combined_extra)
    
    def error(self, msg: str, **extra) -> None:
        """
        Log an error message with context.
        
        Args:
            msg: The message to log
            extra: Additional data to log
        """
        combined_extra = self.context.copy()
        combined_extra.update(extra)
        self.logger.error(msg, extra=combined_extra)
    
    def critical(self, msg: str, **extra) -> None:
        """
        Log a critical message with context.
        
        Args:
            msg: The message to log
            extra: Additional data to log
        """
        combined_extra = self.context.copy()
        combined_extra.update(extra)
        self.logger.critical(msg, extra=combined_extra)
    
    def exception(self, msg: str, **extra) -> None:
        """
        Log an exception message with context.
        
        Args:
            msg: The message to log
            extra: Additional data to log
        """
        combined_extra = self.context.copy()
        combined_extra.update(extra)
        self.logger.exception(msg, extra=combined_extra)


class RequestLogger:
    """
    Specialized logger for HTTP request/response logging with PII protection.
    """
    
    def __init__(self, logger: ContextLogger):
        """
        Initialize with a context logger instance.
        
        Args:
            logger: The context logger to use
        """
        self.logger = logger
    
    def log_request(self, method: str, path: str, headers: dict, 
                   query_params: dict, body: typing.Any, correlation_id: str = None) -> None:
        """
        Log HTTP request details with PII protection.
        
        Args:
            method: HTTP method
            path: Request path
            headers: Request headers
            query_params: Query parameters
            body: Request body
            correlation_id: Correlation ID (generated if not provided)
        """
        if not correlation_id:
            correlation_id = generate_correlation_id()
        
        self.logger.set_correlation_id(correlation_id)
        
        # Mask sensitive information
        masked_headers = self.mask_headers(headers)
        masked_params = mask_pii(query_params, SENSITIVE_FIELDS)
        masked_body = mask_pii(body, SENSITIVE_FIELDS)
        
        request_data = {
            "event": "http_request",
            "method": method,
            "path": path,
            "headers": masked_headers,
            "query_params": masked_params,
            "body": masked_body
        }
        
        self.logger.info(f"HTTP Request: {method} {path}", **request_data)
    
    def log_response(self, status_code: int, headers: dict, body: typing.Any, 
                    duration: float, correlation_id: str = None) -> None:
        """
        Log HTTP response details.
        
        Args:
            status_code: HTTP status code
            headers: Response headers
            body: Response body
            duration: Request duration in seconds
            correlation_id: Correlation ID (uses current if not provided)
        """
        if correlation_id:
            self.logger.set_correlation_id(correlation_id)
        
        # Determine log level based on status code
        level = "info" if status_code < 400 else "error"
        
        # Mask sensitive information
        masked_headers = self.mask_headers(headers)
        masked_body = mask_pii(body, SENSITIVE_FIELDS)
        
        response_data = {
            "event": "http_response",
            "status_code": status_code,
            "headers": masked_headers,
            "body": masked_body,
            "duration_ms": int(duration * 1000)
        }
        
        if level == "info":
            self.logger.info(f"HTTP Response: {status_code}", **response_data)
        else:
            self.logger.error(f"HTTP Error Response: {status_code}", **response_data)
    
    def mask_headers(self, headers: dict) -> dict:
        """
        Mask sensitive information in HTTP headers.
        
        Args:
            headers: Headers dictionary
            
        Returns:
            Headers with sensitive information masked
        """
        if not headers:
            return {}
        
        sensitive_headers = ["authorization", "cookie", "set-cookie", "x-api-key"]
        masked_headers = headers.copy()
        
        for header, value in masked_headers.items():
            header_lower = header.lower()
            if header_lower in sensitive_headers:
                masked_headers[header] = "****"
            elif any(sensitive in header_lower for sensitive in SENSITIVE_FIELDS):
                masked_headers[header] = "****"
        
        return masked_headers


def setup_logging(level: str = "INFO", log_format: str = DEFAULT_LOG_FORMAT, 
                 json_format: bool = DEFAULT_JSON_FORMAT, 
                 date_format: str = DEFAULT_DATE_FORMAT) -> None:
    """
    Initializes the logging system with specified configuration.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format string for non-JSON logs
        json_format: Whether to use JSON formatting
        date_format: Timestamp format
    """
    global _initialized
    
    # Convert string level to logging level constant
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers to prevent duplication
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    
    # Create formatter based on configuration
    if json_format:
        formatter = JsonFormatter(date_format)
    else:
        formatter = logging.Formatter(log_format, date_format)
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    _initialized = True
    
    # Log a startup message
    logger = get_logger("system")
    logger.info("Logging system initialized", 
                log_level=level, 
                json_format=json_format, 
                date_format=date_format)


def get_logger(name: str) -> ContextLogger:
    """
    Returns a configured logger instance for the specified module.
    
    Args:
        name: Logger name, typically __name__ for module loggers
        
    Returns:
        A configured logger instance with context tracking capabilities
    """
    global _initialized
    
    if not _initialized:
        setup_logging()
    
    logger = logging.getLogger(name)
    return ContextLogger(logger)


def generate_correlation_id() -> str:
    """
    Generates a unique correlation ID for request tracing.
    
    Returns:
        A unique correlation ID in UUID format
    """
    return str(uuid.uuid4())


def mask_pii(data: typing.Any, sensitive_fields: list = None) -> typing.Any:
    """
    Masks personally identifiable information in log messages and data.
    
    Args:
        data: Data to mask
        sensitive_fields: List of field names to mask, defaults to SENSITIVE_FIELDS
        
    Returns:
        Data with PII information masked
    """
    if sensitive_fields is None:
        sensitive_fields = SENSITIVE_FIELDS
    
    # Create a deep copy to avoid modifying the original
    data_copy = copy.deepcopy(data)
    
    # Handle different data types
    if isinstance(data_copy, str):
        # Apply pattern-based masking for strings
        for pattern_type, pattern in PII_PATTERNS.items():
            data_copy = re.sub(pattern, f"[REDACTED {pattern_type}]", data_copy)
        
    elif isinstance(data_copy, dict):
        # Process dictionary values recursively
        for key, value in data_copy.items():
            if key.lower() in [f.lower() for f in sensitive_fields]:
                if isinstance(value, str):
                    data_copy[key] = "****"
                else:
                    data_copy[key] = "[REDACTED]"
            else:
                data_copy[key] = mask_pii(value, sensitive_fields)
                
    elif isinstance(data_copy, list):
        # Process list elements recursively
        data_copy = [mask_pii(item, sensitive_fields) for item in data_copy]
        
    return data_copy


def get_current_correlation_id() -> typing.Optional[str]:
    """
    Retrieves the current correlation ID from thread-local storage or global context.
    
    Returns:
        Current correlation ID or None if not set
    """
    # Try to get correlation ID from thread-local storage
    if hasattr(_context_storage, 'correlation_id'):
        return _context_storage.correlation_id
    
    # Try to get from Flask request context if available
    try:
        if flask.has_request_context():
            return flask.request.headers.get('X-Correlation-ID')
    except (ImportError, AttributeError):
        pass
    
    return None


def set_correlation_id(correlation_id: str) -> None:
    """
    Sets a correlation ID in thread-local storage for current context.
    
    Args:
        correlation_id: Correlation ID to set
    """
    _context_storage.correlation_id = correlation_id


def clear_correlation_id() -> None:
    """
    Clears the correlation ID from thread-local storage.
    """
    if hasattr(_context_storage, 'correlation_id'):
        del _context_storage.correlation_id