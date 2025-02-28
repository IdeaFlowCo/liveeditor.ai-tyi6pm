"""
Module initialization file that exposes the core document-related services and classes from the documents package.
Provides a clean interface for other modules to access document management, versioning, differencing, and format conversion functionality.
"""

from .document_service import (
    DocumentService,
    DocumentServiceError,
    DocumentAccessError,
    AnonymousRateLimitError,
)
from .document_manager import (
    DocumentManager,
    DocumentOperationError,
    DocumentImportError,
    DocumentExportError,
)
from .version_manager import (
    VersionManager,
    VersionNotFoundError,
    VersionAccessError,
)
from .diff_service import (
    DiffService,
    generate_diff,
    calculate_diff_statistics,
)
from .format_converter import (
    FormatConverter,
    FormatConversionError,
    UnsupportedFormatError,
)

__version__ = "0.1.0"

__all__ = [
    "DocumentService",
    "DocumentServiceError",
    "DocumentAccessError",
    "AnonymousRateLimitError",
    "DocumentManager",
    "DocumentOperationError",
    "DocumentImportError",
    "DocumentExportError",
    "VersionManager",
    "VersionNotFoundError",
    "VersionAccessError",
    "DiffService",
    "generate_diff",
    "calculate_diff_statistics",
    "FormatConverter",
    "FormatConversionError",
    "UnsupportedFormatError",
]