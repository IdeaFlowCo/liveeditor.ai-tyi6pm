"""
Defines Marshmallow schemas for document-related requests and responses in the AI writing enhancement platform.
These schemas handle validation, serialization, and deserialization of document data for API operations
including creation, updating, listing, and versioning support.
"""

from marshmallow import Schema, fields, validate, ValidationError  # marshmallow 3.14.0
from datetime import datetime  # standard library

from src.backend.core.utils.validators import is_valid_title, validate_document_content  # src/backend/core/utils/validators.py
from src.backend.data.mongodb.repositories.version_repository import VersionType  # src/backend/data/mongodb/repositories/version_repository.py


# Global constants for validation
MAX_DOCUMENT_SIZE_WORDS = 25000
MAX_TITLE_LENGTH = 255
MAX_DESCRIPTION_LENGTH = 1000
MAX_TAG_LENGTH = 50
MAX_TAG_COUNT = 20


def validate_document_size(content: str) -> str:
    """Custom validator for document content size

    Args:
        content: The document content to validate

    Returns:
        The validated content if valid

    Raises:
        ValidationError: If the content exceeds the maximum allowed size
    """
    if content is None:
        return content

    valid, error_message = validate_document_content(content)
    if not valid:
        raise ValidationError(error_message)

    return content


def validate_tag_list(tags: list) -> list:
    """Custom validator for document tags

    Args:
        tags: The list of tags to validate

    Returns:
        The validated tags list if valid

    Raises:
        ValidationError: If the number of tags or any tag length exceeds the maximum allowed
    """
    if tags is None:
        return tags

    if len(tags) > MAX_TAG_COUNT:
        raise ValidationError(f"Maximum {MAX_TAG_COUNT} tags allowed")

    for tag in tags:
        if len(tag) > MAX_TAG_LENGTH:
            raise ValidationError(f"Tag length exceeds maximum {MAX_TAG_LENGTH} characters")

    return tags


class DocumentCreateSchema(Schema):
    """Schema for validating document creation requests"""

    def __init__(self, *args, **kwargs):
        """Initialize document creation schema with field definitions"""
        super().__init__(*args, **kwargs)

        self.title = fields.String(required=True, validate=lambda t: is_valid_title(t),
                                   metadata={"description": "Title of the document"})
        self.content = fields.String(required=True, validate=validate_document_size,
                                     metadata={"description": "Content of the document"})
        self.description = fields.String(required=False, validate=validate.Length(max=MAX_DESCRIPTION_LENGTH),
                                          metadata={"description": "Description of the document"})
        self.tags = fields.List(fields.String(), required=False, validate=validate_tag_list,
                                metadata={"description": "List of tags associated with the document"})


class DocumentUpdateSchema(Schema):
    """Schema for validating document update requests"""

    def __init__(self, *args, **kwargs):
        """Initialize document update schema with field definitions"""
        super().__init__(*args, **kwargs)

        self.title = fields.String(required=False, validate=lambda t: is_valid_title(t),
                                   metadata={"description": "Title of the document"})
        self.content = fields.String(required=False, validate=validate_document_size,
                                     metadata={"description": "Content of the document"})
        self.description = fields.String(required=False, validate=validate.Length(max=MAX_DESCRIPTION_LENGTH),
                                          metadata={"description": "Description of the document"})
        self.tags = fields.List(fields.String(), required=False, validate=validate_tag_list,
                                metadata={"description": "List of tags associated with the document"})
        self.create_version = fields.Boolean(required=False, default=False,
                                             metadata={"description": "Flag to create a new version on update"})


class DocumentResponseSchema(Schema):
    """Schema for serializing document responses"""

    def __init__(self, *args, **kwargs):
        """Initialize document response schema with field definitions"""
        super().__init__(*args, **kwargs)

        self.id = fields.String(metadata={"description": "Unique identifier of the document"})
        self.title = fields.String(metadata={"description": "Title of the document"})
        self.content = fields.String(dump_only=True, metadata={"description": "Content of the document"})  # Content is only dumped, not loaded
        self.description = fields.String(dump_only=True, metadata={"description": "Description of the document"})  # Description is only dumped
        self.tags = fields.List(fields.String(), default=[], metadata={"description": "List of tags associated with the document"})
        self.created_at = fields.DateTime(format='iso', metadata={"description": "Creation timestamp of the document"})
        self.updated_at = fields.DateTime(format='iso', metadata={"description": "Last updated timestamp of the document"})
        self.user_id = fields.String(dump_only=True, metadata={"description": "User ID of the document owner"})  # User ID is only dumped
        self.is_archived = fields.Boolean(default=False, metadata={"description": "Archival status of the document"})
        self.current_version_id = fields.String(dump_only=True, metadata={"description": "ID of the current version"})


class DocumentListQuerySchema(Schema):
    """Schema for validating document list query parameters"""

    def __init__(self, *args, **kwargs):
        """Initialize document list query schema with field definitions"""
        super().__init__(*args, **kwargs)

        self.limit = fields.Integer(required=False, default=10, validate=validate.Range(min=1, max=100),
                                    metadata={"description": "Maximum number of documents to return"})
        self.skip = fields.Integer(required=False, default=0, validate=validate.Range(min=0),
                                   metadata={"description": "Number of documents to skip for pagination"})
        self.is_archived = fields.Boolean(required=False, metadata={"description": "Filter by archival status"})
        self.tags = fields.List(fields.String(), required=False, metadata={"description": "Filter by tags"})
        self.search = fields.String(required=False, metadata={"description": "Search term for document content and title"})
        self.sort_by = fields.String(required=False, default='updated_at',
                                      validate=validate.OneOf(['updated_at', 'created_at', 'title']),
                                      metadata={"description": "Field to sort by"})
        self.sort_direction = fields.String(required=False, default='desc', validate=validate.OneOf(['asc', 'desc']),
                                             metadata={"description": "Sort direction (asc or desc)"})


class DocumentListResponseSchema(Schema):
    """Schema for serializing document list responses"""

    def __init__(self, *args, **kwargs):
        """Initialize document list response schema with field definitions"""
        super().__init__(*args, **kwargs)

        self.items = fields.List(fields.Nested(DocumentResponseSchema), metadata={"description": "List of documents"})
        self.total = fields.Integer(metadata={"description": "Total number of documents"})
        self.limit = fields.Integer(metadata={"description": "Maximum number of documents returned"})
        self.skip = fields.Integer(metadata={"description": "Number of documents skipped"})


class DocumentVersionResponseSchema(Schema):
    """Schema for serializing document version responses"""

    def __init__(self, *args, **kwargs):
        """Initialize document version response schema with field definitions"""
        super().__init__(*args, **kwargs)

        self.id = fields.String(metadata={"description": "Unique identifier of the document version"})
        self.document_id = fields.String(metadata={"description": "ID of the associated document"})
        self.version_number = fields.Integer(metadata={"description": "Version number of the document"})
        self.content = fields.String(metadata={"description": "Content of the document version"})
        self.created_at = fields.DateTime(format='iso', metadata={"description": "Creation timestamp of the version"})
        self.created_by = fields.String(required=False, metadata={"description": "User ID or session ID that created the version"})
        self.version_type = fields.Integer(metadata={"description": "Type of the version (MAJOR, MINOR, AI_SUGGESTION)"})
        self.change_description = fields.String(required=False, metadata={"description": "Description of changes in this version"})
        self.previous_version_id = fields.String(required=False, metadata={"description": "ID of the previous version"})
        self.metadata = fields.Dict(required=False, metadata={"description": "Additional metadata associated with the version"})


class DocumentVersionListResponseSchema(Schema):
    """Schema for serializing document version list responses"""

    def __init__(self, *args, **kwargs):
        """Initialize document version list response schema with field definitions"""
        super().__init__(*args, **kwargs)

        self.items = fields.List(fields.Nested(DocumentVersionResponseSchema), metadata={"description": "List of document versions"})
        self.total = fields.Integer(metadata={"description": "Total number of document versions"})
        self.limit = fields.Integer(metadata={"description": "Maximum number of document versions returned"})
        self.skip = fields.Integer(metadata={"description": "Number of document versions skipped"})


class DocumentExportSchema(Schema):
    """Schema for validating document export requests"""

    def __init__(self, *args, **kwargs):
        """Initialize document export schema with field definitions"""
        super().__init__(*args, **kwargs)

        self.format = fields.String(required=True, validate=validate.OneOf(['txt', 'html', 'docx', 'pdf']),
                                    metadata={"description": "Format to export the document in"})
        self.version_id = fields.String(required=False, metadata={"description": "ID of the version to export"})
        self.options = fields.Dict(required=False, metadata={"description": "Format-specific options for export"})


class DocumentImportSchema(Schema):
    """Schema for validating document import requests"""

    def __init__(self, *args, **kwargs):
        """Initialize document import schema with field definitions"""
        super().__init__(*args, **kwargs)

        self.content = fields.String(required=True, metadata={"description": "Content of the document to import"})
        self.format = fields.String(required=True, validate=validate.OneOf(['txt', 'html', 'docx']),
                                    metadata={"description": "Format of the document to import"})
        self.title = fields.String(required=False, validate=lambda t: is_valid_title(t),
                                   metadata={"description": "Title of the document"})
        self.description = fields.String(required=False, validate=validate.Length(max=MAX_DESCRIPTION_LENGTH),
                                          metadata={"description": "Description of the document"})


class DocumentCompareSchema(Schema):
    """Schema for validating document version comparison requests"""

    def __init__(self, *args, **kwargs):
        """Initialize document comparison schema with field definitions"""
        super().__init__(*args, **kwargs)

        self.base_version_id = fields.String(required=True, metadata={"description": "ID of the base version"})
        self.comparison_version_id = fields.String(required=True, metadata={"description": "ID of the version to compare against the base version"})
        self.format = fields.String(required=False, default='html', validate=validate.OneOf(['html', 'diff']),
                                    metadata={"description": "Format of the comparison output"})