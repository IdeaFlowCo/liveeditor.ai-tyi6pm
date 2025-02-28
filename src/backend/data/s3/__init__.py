"""
S3 data access package for the AI writing enhancement platform.

This package provides classes and functions for interacting with AWS S3 storage,
enabling document storage, retrieval, versioning, and management capabilities with
appropriate error handling and security.

Exports:
    S3Connection: Class for establishing and managing connections to AWS S3.
    DocumentStorage: Class for managing document storage and retrieval operations using AWS S3.
"""

from .connection import S3Connection
from .document_storage import DocumentStorage

__all__ = ['S3Connection', 'DocumentStorage']