"""
Unit tests package initialization for the AI writing enhancement platform's backend.

This module defines the package structure for backend unit tests and provides
utilities specific to unit testing.
"""

import os
import pytest  # pytest 7.0.0

from .. import TEST_ROOT, get_test_path

# Define the unit test root directory
UNIT_TEST_ROOT = os.path.dirname(os.path.abspath(__file__))


def get_unit_test_path(relative_path: str) -> str:
    """
    Helper function to build paths relative to the unit test directory.
    
    Args:
        relative_path: Path relative to the unit test directory
        
    Returns:
        Absolute path to the requested unit test resource
    """
    return os.path.join(UNIT_TEST_ROOT, relative_path)