"""
Middleware that provides centralized error handling for the AI writing enhancement platform,
handling exceptions from all application layers with standardized responses, consistent logging,
and custom error classes for specific scenarios. Implements user-friendly error messages with
appropriate HTTP status codes.
"""

import traceback  # standard library
import typing  # standard library
import json  # standard library

from flask import Flask, request, jsonify, g, current_app  # Flask ~=2.3.0
from werkzeug.exceptions import HTTPException  # werkzeug.exceptions ~=2.3.0
from openai import OpenAIError # openai ^1.0.0

from ..core.utils.logger import get_logger, generate_correlation_id  # Internal import
from ..core.utils.validators import ValidationError  # Internal import
from ..core.auth.jwt_service import AuthenticationError  # Internal import
from ..core.documents.document_service import DocumentAccessError, AnonymousRateLimitError  # Internal import

# Initialize logger
logger = get_logger(__name__)

# Define standardized error messages
ERROR_MESSAGES = {
    "400": "Bad Request: The server could not process your request due to invalid input.",
    "401": "Unauthorized: Authentication required to access this resource.",
    "403": "Forbidden: You don't have permission to access this resource.",
    "404": "Not Found: The requested resource does not exist.",
    "429": "Too Many Requests: You have exceeded the allowed request rate.",
    "500": "Internal Server Error: An unexpected error occurred on the server.",
    "502": "Bad Gateway: The server received an invalid response from an upstream service.",
    "503": "Service Unavailable: The service is temporarily unavailable. Please try again later.",
    "504": "Gateway Timeout: The server timed out waiting for a response from an upstream service."
}

# Define AI service specific error messages
AI_SERVICE_ERROR_MESSAGES = {
    "token_limit": "The AI service could not process your document due to size constraints. Please try with a shorter selection or document.",
    "rate_limit": "AI service request limit reached. Please try again in a few minutes.",
    "service_unavailable": "AI service is temporarily unavailable. Your document has been saved, and you can try again later."
}


class ErrorResponse:
    """
    Standardized error response structure for API errors
    """

    def __init__(self, status_code: int, message: str, details: dict = None, correlation_id: str = None):
        """
        Initialize error response with standardized structure

        Args:
            status_code: HTTP status code
            message: Error message
            details: Additional error details if provided
            correlation_id: Correlation ID for error tracking
        """
        self.error_code = status_code
        self.message = message
        self.details = details
        self.correlation_id = correlation_id

    def to_dict(self) -> dict:
        """
        Convert error response to dictionary for serialization

        Returns:
            Serializable error response dictionary
        """
        error_dict = {
            "error_code": self.error_code,
            "message": self.message,
            "correlation_id": self.correlation_id
        }
        if self.details:
            error_dict["details"] = self.details
        return error_dict

    def to_response(self) -> tuple:
        """
        Convert to Flask response with appropriate status and headers

        Returns:
            JSON response and HTTP status code
        """
        response_dict = self.to_dict()
        response = jsonify(response_dict)
        response.status_code = self.error_code
        return response, self.error_code


class ErrorHandlerMiddleware:
    """
    Flask middleware that installs global error handlers
    """

    def __init__(self):
        """
        Initialize error handler middleware
        """
        self._app = None

    def init_app(self, app: Flask):
        """
        Register error handlers with Flask application

        Args:
            app: Flask application instance
        """
        self._app = app
        app.errorhandler(Exception)(self.handle_exception)
        app.errorhandler(HTTPException)(self.handle_http_exception)
        app.errorhandler(ValidationError)(self.handle_validation_error)
        app.errorhandler(AuthenticationError)(self.handle_authentication_error)
        app.errorhandler(DocumentAccessError)(self.handle_document_access_error)
        app.errorhandler(OpenAIError)(self.handle_openai_error)
        app.errorhandler(AnonymousRateLimitError)(self.handle_anonymous_rate_limit_error)
        logger.info("Registered error handlers with Flask application")

    def handle_exception(self, exception: Exception) -> tuple:
        """
        Global exception handler for all unhandled exceptions

        Args:
            exception: The exception instance

        Returns:
            Error response tuple
        """
        return handle_error(exception)

    def handle_http_exception(self, exception: HTTPException) -> tuple:
        """
        Handler specifically for HTTP exceptions

        Args:
            exception: The HTTPException instance

        Returns:
            Error response tuple
        """
        status_code = exception.code
        message = ERROR_MESSAGES.get(str(status_code), "An unexpected error occurred.")
        correlation_id = g.get("correlation_id") or generate_correlation_id()
        error_response = ErrorResponse(status_code, message, correlation_id=correlation_id)
        return error_response.to_response()

    def handle_validation_error(self, error: ValidationError) -> tuple:
        """
        Handler specifically for validation errors

        Args:
            error: The ValidationError instance

        Returns:
            Error response tuple
        """
        formatted_errors = format_validation_errors(error)
        correlation_id = g.get("correlation_id") or generate_correlation_id()
        error_response = ErrorResponse(400, "Validation Error", details=formatted_errors, correlation_id=correlation_id)
        return error_response.to_response()

    def handle_authentication_error(self, exception: AuthenticationError) -> tuple:
        """
        Handler specifically for authentication errors

        Args:
            exception: The AuthenticationError instance

        Returns:
            Error response tuple
        """
        correlation_id = g.get("correlation_id") or generate_correlation_id()
        error_response = ErrorResponse(401, "Authentication failed", correlation_id=correlation_id)
        return error_response.to_response()

    def handle_document_access_error(self, exception: DocumentAccessError) -> tuple:
        """
        Handler specifically for document permission errors

        Args:
            exception: The DocumentAccessError instance

        Returns:
            Error response tuple
        """
        correlation_id = g.get("correlation_id") or generate_correlation_id()
        error_response = ErrorResponse(403, "Permission denied", correlation_id=correlation_id)
        return error_response.to_response()

    def handle_openai_error(self, exception: OpenAIError) -> tuple:
        """
        Handler specifically for OpenAI API errors

        Args:
            exception: The OpenAIError instance

        Returns:
            Error response tuple
        """
        status_code = get_error_code(exception)
        message = AI_SERVICE_ERROR_MESSAGES.get(exception.type, "AI service is temporarily unavailable.")
        correlation_id = g.get("correlation_id") or generate_correlation_id()
        error_response = ErrorResponse(status_code, message, correlation_id=correlation_id)
        return error_response.to_response()

    def handle_anonymous_rate_limit_error(self, exception: AnonymousRateLimitError) -> tuple:
        """
        Handler specifically for anonymous rate limit errors

        Args:
            exception: The AnonymousRateLimitError instance

        Returns:
            Error response tuple
        """
        correlation_id = g.get("correlation_id") or generate_correlation_id()
        error_response = ErrorResponse(429, "Too Many Requests: Anonymous usage limit exceeded.", correlation_id=correlation_id)
        return error_response.to_response()


def handle_error(exception: Exception) -> tuple:
    """
    Processes exceptions and generates standardized error responses

    Args:
        exception: The exception instance

    Returns:
        JSON error response and HTTP status code
    """
    correlation_id = g.get("correlation_id") or generate_correlation_id()
    status_code = get_error_code(exception)
    message = ERROR_MESSAGES.get(str(status_code), "An unexpected error occurred.")

    log_exception(exception, status_code, correlation_id)

    error_response = ErrorResponse(status_code, message, correlation_id=correlation_id)
    return error_response.to_response()


def get_error_code(exception: Exception) -> int:
    """
    Determines the appropriate HTTP status code for an exception

    Args:
        exception: The exception instance

    Returns:
        HTTP status code
    """
    if isinstance(exception, ValidationError):
        return 400
    elif isinstance(exception, AuthenticationError):
        return 401
    elif isinstance(exception, DocumentAccessError):
        return 403
    elif isinstance(exception, AnonymousRateLimitError):
        return 429
    elif isinstance(exception, OpenAIError):
        if exception.type == "insufficient_quota":
            return 429
        return 503
    elif isinstance(exception, HTTPException):
        return exception.code
    else:
        return 500


def format_validation_errors(error: ValidationError) -> dict:
    """
    Formats validation errors for client response

    Args:
        error: The ValidationError instance

    Returns:
        Formatted validation errors by field
    """
    errors = error.get_errors()
    formatted_errors = {}
    for field, error_list in errors.items():
        formatted_errors[field] = error_list
    return formatted_errors


def get_request_details() -> dict:
    """
    Extracts relevant request information for error logging

    Returns:
        Request context information for logs
    """
    request_details = {
        "method": request.method,
        "path": request.path,
        "query_params": request.args.to_dict(),
        "api_endpoint": request.endpoint
    }
    if "user_id" in g:
        request_details["user_id"] = g.user_id
    if "correlation_id" in g:
        request_details["correlation_id"] = g.correlation_id
    return request_details


def log_exception(exception: Exception, status_code: int, correlation_id: str):
    """
    Logs exception details with structured context

    Args:
        exception: The exception instance
        status_code: HTTP status code
        correlation_id: Correlation ID
    """
    exception_details = {
        "exception_class": exception.__class__.__name__,
        "exception_message": str(exception)
    }

    if not isinstance(exception, HTTPException):
        exception_details["traceback"] = traceback.format_exc()

    request_context = get_request_details()
    log_data = {
        "status_code": status_code,
        "correlation_id": correlation_id,
        **exception_details,
        **request_context
    }

    if status_code >= 500:
        logger.error("Exception occurred", **log_data)
    else:
        logger.warning("Exception occurred", **log_data)