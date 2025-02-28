"""
Integration test package initialization for the AI writing enhancement platform's backend.

This module establishes the package structure for backend integration tests,
enabling test discovery and providing common utilities specific to integration testing.
"""

import os
import pytest  # pytest 7.0.0

from .. import TEST_ROOT, get_test_path

# Define constants for integration test paths
INTEGRATION_TEST_ROOT = os.path.dirname(os.path.abspath(__file__))

# Base API URL for integration tests
BASE_API_URL = '/api/v1'


def get_integration_test_path(relative_path: str) -> str:
    """
    Get the absolute path to an integration test resource.
    
    Args:
        relative_path: Path relative to the integration test directory
        
    Returns:
        Absolute path to the requested integration test resource
    """
    return os.path.join(INTEGRATION_TEST_ROOT, relative_path)