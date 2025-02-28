"""
Core module unit tests package initialization for the AI writing enhancement platform's backend.

This module defines the package structure for testing the core business logic components
including AI services, authentication, and document processing.
"""

import os  # built-in
from .. import UNIT_TEST_ROOT

# Define the core test root directory
CORE_TEST_ROOT = os.path.dirname(os.path.abspath(__file__))


def get_core_test_path(relative_path: str) -> str:
    """
    Helper function to build paths relative to the core test directory.
    
    Args:
        relative_path: Path relative to the core test directory
        
    Returns:
        Absolute path to the requested core test resource
    """
    return os.path.join(CORE_TEST_ROOT, relative_path)