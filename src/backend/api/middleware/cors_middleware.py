"""
CORS Middleware for the AI writing enhancement platform.

This module provides middleware for handling Cross-Origin Resource Sharing (CORS)
in the API, enabling secure communication between the frontend and backend services.
It implements security mechanisms and supports both anonymous and authenticated usage
with appropriate CORS configurations for different environments.
"""

import logging
import os
from typing import Dict, List, Any, Optional, Union

from flask import Flask
from flask_cors import CORS, cross_origin  # ~=3.0.10

from ...config import current_config

logger = logging.getLogger(__name__)

DEFAULT_CORS_SETTINGS = {
    "origins": ["*"],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "X-Session-ID"],
    "expose_headers": ["Content-Type", "X-Session-ID"],
    "supports_credentials": True,
    "max_age": 600  # 10 minutes
}


def configure_cors(app: Flask, cors_config: Optional[Dict[str, Any]] = None) -> None:
    """
    Configure CORS for a Flask application with appropriate security settings.
    
    Args:
        app: The Flask application to configure
        cors_config: Optional CORS configuration to override defaults
        
    Returns:
        None: Modifies the Flask app in-place with CORS configuration
    """
    cors_middleware = CORSMiddleware(cors_config)
    cors_middleware.init_app(app)
    logger.info("CORS configured for Flask application")


def get_environment_cors_settings() -> Dict[str, Any]:
    """
    Get environment-specific CORS settings.
    
    Returns:
        Dict[str, Any]: CORS settings appropriate for the current environment
    """
    environment = os.environ.get("FLASK_ENV", "development")
    
    # Get origins from config
    origins = current_config.CORS_ORIGINS
    
    # Default settings
    settings = dict(DEFAULT_CORS_SETTINGS)
    settings["origins"] = origins
    
    # Environment-specific adjustments
    if environment == "development":
        # More permissive in development for easier local testing
        settings["origins"] = origins or ["http://localhost:3000", "http://127.0.0.1:3000"]
        logger.debug("Using development CORS settings with origins: %s", settings["origins"])
    elif environment == "staging":
        # More restrictive in staging, but still allows testing domains
        if not origins:
            settings["origins"] = ["https://staging.example.com"]
        logger.debug("Using staging CORS settings with origins: %s", settings["origins"])
    elif environment == "production":
        # Strict settings for production
        if not origins:
            settings["origins"] = ["https://example.com", "https://www.example.com"]
        # Ensure secure settings in production
        settings["supports_credentials"] = True
        logger.debug("Using production CORS settings with origins: %s", settings["origins"])
    
    return settings


class CORSMiddleware:
    """
    Middleware class for handling Cross-Origin Resource Sharing (CORS).
    
    This class manages CORS configuration for the application, enabling secure
    cross-origin requests while maintaining appropriate security controls.
    It supports both anonymous and authenticated usage with proper CORS settings.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the CORS middleware with config options.
        
        Args:
            config: Optional configuration dictionary to override defaults
        """
        # Store configuration or use defaults
        self._config = config or {}
        
        # Get environment settings if not explicitly provided
        env_settings = get_environment_cors_settings()
        
        # Apply environment settings for anything not explicitly configured
        for key, value in env_settings.items():
            if key not in self._config:
                self._config[key] = value
        
        # Initialize properties
        self._allowed_origins = self._config.get("origins", env_settings.get("origins", ["*"]))
        self._supports_credentials = self._config.get("supports_credentials", True)
        self._allowed_headers = self._config.get("allow_headers", DEFAULT_CORS_SETTINGS["allow_headers"])
        self._exposed_headers = self._config.get("expose_headers", DEFAULT_CORS_SETTINGS["expose_headers"])
        self._websocket_support = self._config.get("websocket_support", False)
        
        # Ensure X-Session-ID is in headers for anonymous usage
        if "X-Session-ID" not in self._allowed_headers:
            self._allowed_headers.append("X-Session-ID")
        if "X-Session-ID" not in self._exposed_headers:
            self._exposed_headers.append("X-Session-ID")
        
        logger.debug("CORS Middleware initialized with origins: %s", self._allowed_origins)

    def init_app(self, app: Flask) -> None:
        """
        Initialize CORS for the Flask application.
        
        Args:
            app: The Flask application to configure
            
        Returns:
            None: Modifies the Flask app in-place with CORS configuration
        """
        cors_options = self.get_cors_options()
        
        # Create CORS instance
        cors = self.create_cors_instance(app)
        
        # Configure WebSocket support if enabled
        if self._websocket_support:
            self.configure_websocket_support(app)
        
        # Configure route-specific CORS if provided
        route_configs = self._config.get("routes", {})
        if route_configs:
            self.configure_route_specific_cors(app, route_configs)
        
        # Special configuration for anonymous endpoints
        if self._config.get("configure_anonymous", True):
            # Ensure anonymous endpoints can be accessed without authentication
            @app.after_request
            def add_anonymous_cors_headers(response):
                if request.endpoint and request.endpoint.startswith("anonymous_"):
                    response.headers.add("Access-Control-Allow-Credentials", "true")
                    # Allow the session header for anonymous sessions
                    response.headers.add("Access-Control-Allow-Headers", 
                                         "X-Session-ID, Content-Type")
                    response.headers.add("Access-Control-Expose-Headers", 
                                         "X-Session-ID")
                return response
        
        logger.info("CORS initialized for Flask application with origins: %s", cors_options["origins"])

    def get_cors_options(self) -> Dict[str, Any]:
        """
        Get CORS options from config with sensible defaults.
        
        Returns:
            Dict[str, Any]: Dictionary of CORS configuration options
        """
        # Start with default options
        options = {
            "origins": self._allowed_origins,
            "methods": self._config.get("methods", DEFAULT_CORS_SETTINGS["methods"]),
            "allow_headers": self._allowed_headers,
            "expose_headers": self._exposed_headers,
            "supports_credentials": self._supports_credentials,
            "max_age": self._config.get("max_age", DEFAULT_CORS_SETTINGS["max_age"]),
            "send_wildcard": self._config.get("send_wildcard", False),
            "vary_header": self._config.get("vary_header", True),
        }
        
        # In production, ensure secure settings
        environment = os.environ.get("FLASK_ENV", "development")
        if environment == "production":
            # Don't allow wildcard origins in production
            if options["origins"] == ["*"]:
                logger.warning("Wildcard CORS origin (*) detected in production! Using config origins instead.")
                options["origins"] = current_config.CORS_ORIGINS
            
            # Always enable vary header in production
            options["vary_header"] = True
            
            # Ensure credentials are properly supported
            if options["supports_credentials"] and "*" in options["origins"]:
                logger.warning(
                    "Wildcard origin with credentials is not allowed. Disabling credentials support."
                )
                options["supports_credentials"] = False
        
        return options
    
    def create_cors_instance(self, app: Flask) -> CORS:
        """
        Create a configured instance of the CORS extension.
        
        Args:
            app: The Flask application to configure
            
        Returns:
            CORS: Configured CORS extension instance
        """
        options = self.get_cors_options()
        
        # Use resources parameter for specific routes if configured
        resources = self._config.get("resources", {r"/*": options})
        
        return CORS(
            app,
            resources=resources,
            supports_credentials=options["supports_credentials"],
            origins=options["origins"],
            methods=options["methods"],
            allow_headers=options["allow_headers"],
            expose_headers=options["expose_headers"],
            max_age=options["max_age"],
            send_wildcard=options["send_wildcard"],
            vary_header=options["vary_header"],
        )
    
    def configure_websocket_support(self, app: Flask) -> None:
        """
        Configure CORS for WebSocket connections.
        
        Args:
            app: The Flask application to configure
            
        Returns:
            None: Adds WebSocket support to the application
        """
        # Add WebSocket-specific headers to all responses
        @app.after_request
        def add_websocket_cors_headers(response):
            response.headers.add("Access-Control-Allow-Headers", "Upgrade, Connection")
            response.headers.add("Access-Control-Allow-Methods", "GET, OPTIONS")
            return response
        
        logger.info("WebSocket CORS support configured")
    
    def configure_route_specific_cors(self, app: Flask, route_configs: Dict[str, Dict[str, Any]]) -> None:
        """
        Apply route-specific CORS configurations.
        
        Args:
            app: The Flask application to configure
            route_configs: Dictionary mapping route patterns to CORS configurations
            
        Returns:
            None: Applies route-specific CORS settings
        """
        for route, config in route_configs.items():
            cors_options = {**self.get_cors_options(), **config}
            
            # Create resource-specific CORS configuration
            CORS(
                app,
                resources={route: cors_options},
                supports_credentials=cors_options.get("supports_credentials", 
                                                    self._supports_credentials)
            )
            
            logger.debug("Route-specific CORS configured for %s with options: %s", 
                        route, cors_options)