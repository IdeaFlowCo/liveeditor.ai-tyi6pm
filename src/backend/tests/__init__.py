"""
Test package initialization for the AI writing enhancement platform's backend.

This module provides common testing utilities, package-level imports, and
configuration used throughout the test suite.
"""

import os
import pytest  # pytest 7.0.0

# Define constants for common paths
TEST_ROOT = os.path.dirname(os.path.abspath(__file__))
# PROJECT_ROOT is the 'src' directory (parent of 'backend')
PROJECT_ROOT = os.path.dirname(os.path.dirname(TEST_ROOT))


def get_test_path(relative_path: str) -> str:
    """
    Get the absolute path to a test resource.
    
    Args:
        relative_path: Path relative to the test directory
        
    Returns:
        Absolute path to the requested test resource
    """
    return os.path.join(TEST_ROOT, relative_path)


def get_fixture_path(fixture_name: str) -> str:
    """
    Get the absolute path to a test fixture file.
    
    Args:
        fixture_name: Name of the fixture file
        
    Returns:
        Absolute path to the requested fixture file
    """
    return os.path.join(TEST_ROOT, 'fixtures', fixture_name)