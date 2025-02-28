"""
Authentication test package initialization.

This module initializes the authentication unit test package and provides
common imports and constants for authentication test cases.
"""

# External imports
import pytest  # pytest 7.0.0
from freezegun import freeze_time  # freezegun 1.2.0 - For testing time-dependent authentication features

# Global constants for auth testing
AUTH_TEST_MODULE = "backend.core.auth"

# Export pytest for other test modules
__all__ = ["pytest"]