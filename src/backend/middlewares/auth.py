"""
Flask middleware that handles authentication and authorization for the AI writing enhancement platform,
supporting both JWT-based authentication for registered users and session-based tracking for anonymous users.
Integrates with request processing pipeline to validate auth tokens, manage sessions, and ensure appropriate access controls.
"""

from functools import wraps  # Python Standard Library
from typing import Optional, Tuple  # Python Standard Library

from flask import Flask, request, g, Response, current_app  # Flask ~=2.3.0

from ..core.auth.anonymous_session import AnonymousSessionManager  # Import AnonymousSessionManager class
from ..core.auth.jwt_service import JWTService  # Import JWTService class
from ..core.auth.user_service import UserService  # Import UserService class
from ..core.utils.logger import get_logger  # Import get_logger function from logger module

# Initialize logger
logger = get_logger(__name__)

# Constants
AUTH_HEADER_NAME = "Authorization"
AUTH_TOKEN_COOKIE = "auth_token"
BEARER_PREFIX = "Bearer "


def login_required(f):
    """
    Decorator for routes that require authentication

    Args:
        f: The function to decorate

    Returns:
        Wrapped function that checks authentication
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        """
        Wrapped function that checks authentication
        """
        # Set a flag on the function to indicate it requires authentication
        decorated_function.required_auth = True
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    Decorator for routes that require admin privileges

    Args:
        f: The function to decorate

    Returns:
        Wrapped function that checks admin privileges
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        """
        Wrapped function that checks admin privileges
        """
        # Set flags on the function to indicate it requires authentication and admin role
        decorated_function.required_auth = True
        decorated_function.required_admin = True
        return f(*args, **kwargs)
    return decorated_function


class AuthMiddleware:
    """
    Flask middleware that handles authentication and authorization for API requests
    """

    def __init__(self, jwt_service: JWTService, user_service: UserService, anonymous_session_manager: AnonymousSessionManager):
        """
        Initialize the auth middleware with required services

        Args:
            jwt_service: JWT service for token validation
            user_service: User service for fetching user information
            anonymous_session_manager: Anonymous session manager for handling anonymous sessions
        """
        # Store the JWT service for token validation
        self._jwt_service = jwt_service
        # Store the user service for fetching user information
        self._user_service = user_service
        # Store the anonymous session manager for handling anonymous sessions
        self._session_manager = anonymous_session_manager
        # Initialize empty protected routes dictionary
        self._protected_routes = {}
        # Log middleware initialization
        logger.info("AuthMiddleware initialized")

    def init_app(self, app: Flask):
        """
        Initialize middleware with Flask application

        Args:
            app: Flask application instance
        """
        # Store Flask application reference
        self._app = app
        # Register before_request handler to process authentication
        self._app.before_request(self._before_request)
        # Register after_request handler to apply session cookies
        self._app.after_request(self._after_request)

    def _before_request(self):
        """
        Handler executed before each request to validate authentication

        Returns:
            Response | None: Error response or None to continue
        """
        # Skip authentication check for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return None

        # Extract JWT token from request headers or cookies
        token = self._extract_token()

        # If token exists, validate it using JWT service
        if token:
            validation_result = self._jwt_service.validate_token(token, "access")
            if validation_result["is_valid"]:
                # If token valid, get user from database and store in flask.g
                user_id = validation_result["payload"]["sub"]
                try:
                    user = self._user_service.get_user_by_id(user_id)
                    g.user = user
                    logger.debug(f"Authenticated user {user_id} via JWT")
                except Exception as e:
                    logger.warning(f"Failed to retrieve user {user_id} from database: {e}")
            else:
                logger.debug(f"Invalid JWT token: {validation_result['error']}")

        # If no token or invalid, check for anonymous session
        if not hasattr(g, "user"):
            session_id, session_data, is_new_session = self._session_manager.initialize_session()
            g.session_id = session_id
            g.session = session_data
            g.is_new_session = is_new_session
            logger.debug(f"Using anonymous session {session_id[:8]}...")

        # Check if current route requires authentication or admin role
        requires_auth, requires_admin = self._check_route_requirements()

        # If auth required but not authenticated, return 401 Unauthorized
        if requires_auth and not hasattr(g, "user"):
            logger.warning("Authentication required but no user found")
            return Response("Authentication required", 401)

        # If admin required but user not admin, return 403 Forbidden
        if requires_admin and (not hasattr(g, "user") or g.user.get("role") != "admin"):
            logger.warning("Admin privileges required but user is not admin")
            return Response("Admin privileges required", 403)

        # Allow request to proceed if authentication checks pass
        return None

    def _after_request(self, response: Response) -> Response:
        """
        Handler executed after each request to apply session cookies

        Args:
            response: Flask response object

        Returns:
            Response: Modified response with session cookies if needed
        """
        # Check if anonymous session exists in request context
        if hasattr(g, "session_id") and hasattr(g, "is_new_session") and g.is_new_session:
            # If exists and is new, apply session cookie to response
            response = self._session_manager.apply_session_to_response(response, g.session_id)
            logger.debug(f"Applied session cookie for session {g.session_id[:8]}...")
        # Return the response, possibly modified with cookies
        return response

    def _extract_token(self) -> Optional[str]:
        """
        Extract JWT token from request Authorization header or cookies

        Returns:
            str | None: Extracted token or None if not found
        """
        # Check Authorization header for Bearer token
        auth_header = request.headers.get(AUTH_HEADER_NAME)
        if auth_header and auth_header.startswith(BEARER_PREFIX):
            token = auth_header[len(BEARER_PREFIX):]
            logger.debug("Extracted token from Authorization header")
            return token

        # Check cookies for auth_token
        token = request.cookies.get(AUTH_TOKEN_COOKIE)
        if token:
            logger.debug("Extracted token from auth_token cookie")
            return token

        # Return None if no token found
        return None

    def _check_route_requirements(self) -> Tuple[bool, bool]:
        """
        Check if the current route has authentication requirements

        Returns:
            tuple: (requires_auth: bool, requires_admin: bool)
        """
        # Get current endpoint from request
        endpoint = request.endpoint

        # Check protected routes dictionary for endpoint
        if endpoint in self._protected_routes:
            route_info = self._protected_routes[endpoint]
            requires_auth = route_info.get("auth_required", False)
            requires_admin = route_info.get("admin_required", False)
            logger.debug(f"Route {endpoint} requires auth: {requires_auth}, admin: {requires_admin}")
            return requires_auth, requires_admin

        # Default to not protected if endpoint not configured
        logger.debug(f"Route {endpoint} is not protected")
        return False, False

    def login_required(self, route_function):
        """
        Decorator that marks a route as requiring authentication

        Args:
            route_function: The function to decorate

        Returns:
            function: Original function with auth requirement metadata
        """
        # Register route in protected routes dictionary with auth_required=True
        endpoint = route_function.__name__
        self._protected_routes[endpoint] = {"auth_required": True}
        logger.debug(f"Registered route {endpoint} as requiring authentication")
        # Return the original function unchanged
        return route_function

    def admin_required(self, route_function):
        """
        Decorator that marks a route as requiring admin privileges

        Args:
            route_function: The function to decorate

        Returns:
            function: Original function with admin requirement metadata
        """
        # Register route in protected routes dictionary with auth_required=True and admin_required=True
        endpoint = route_function.__name__
        self._protected_routes[endpoint] = {"auth_required": True, "admin_required": True}
        logger.debug(f"Registered route {endpoint} as requiring admin privileges")
        # Return the original function unchanged
        return route_function

    def get_current_user(self) -> Optional[dict]:
        """
        Get the current authenticated user from the request context

        Returns:
            dict | None: Current user data or None if not authenticated
        """
        # Check if user exists in flask.g context
        if hasattr(g, "user"):
            # Return user data if found, otherwise None
            return g.user
        return None

    def get_current_session(self) -> Optional[dict]:
        """
        Get the current session (anonymous or authenticated) from request context

        Returns:
            dict | None: Current session data or None if no session
        """
        # Check if session exists in flask.g context
        if hasattr(g, "session"):
            # Return session data if found, otherwise None
            return g.session
        return None


class AuthenticationError(Exception):
    """
    Exception raised when authentication fails
    """

    def __init__(self, message: str = None):
        """
        Initialize authentication error with message

        Args:
            message: Error message
        """
        # Set default message if none provided
        if message is None:
            message = "Authentication failed"
        # Call parent Exception constructor with message
        super().__init__(message)