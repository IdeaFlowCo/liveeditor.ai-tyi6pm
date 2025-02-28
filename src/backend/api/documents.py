"""
Defines a Flask Blueprint with routes for document-related API endpoints in the AI writing enhancement platform.
This module integrates the document service with RESTful API resources, supporting both anonymous and authenticated usage paths for document creation, editing, storage, and version management.
"""

from flask import Blueprint  # flask==2.3.3
from flask_restful import Api  # flask_restful==0.3.10

from .resources.document_resource import DocumentResource, DocumentsResource, DocumentVersionResource, DocumentVersionsResource, DocumentCompareResource, DocumentExportResource, DocumentImportResource  # src/backend/api/resources/document_resource.py
from ..core.documents.document_service import DocumentService  # src/backend/core/documents/document_service.py
from ..core.utils.logger import get_logger  # src/backend/core/utils/logger.py

# Create a Flask blueprint for document endpoints
documents_bp = Blueprint('documents', __name__, url_prefix='/api/documents')

# Create a Flask-RESTful API instance
documents_api = Api(documents_bp)

# Configure logging for document API endpoints
logger = get_logger(__name__)

# Global variable to hold the DocumentService instance
_document_service = None


def init_document_resources(document_service: DocumentService) -> None:
    """Initialize document API resources with required services

    Args:
        document_service: document_service
    Returns:
        None: Modifies the documents_api in place
    """
    global _document_service
    # Store document_service globally for potential reuse
    _document_service = document_service
    # Instantiate document resources with the service
    register_document_resources(documents_api, document_service)
    # Log successful resource initialization
    logger.info("Document API resources initialized")


def register_document_resources(api: Api, document_service: DocumentService) -> None:
    """Register document API resources with Flask-RESTful

    Args:
        api: api
        document_service: document_service
    Returns:
        None: Modifies the api in place
    """
    # Register DocumentsResource at '/'
    api.add_resource(DocumentsResource, '/', resource_class_kwargs={'document_service': document_service})
    # Register DocumentResource at '/<document_id>'
    api.add_resource(DocumentResource, '/<string:document_id>', resource_class_kwargs={'document_service': document_service})
    # Register DocumentVersionsResource at '/<document_id>/versions'
    api.add_resource(DocumentVersionsResource, '/<string:document_id>/versions', resource_class_kwargs={'document_service': document_service})
    # Register DocumentVersionResource at '/<document_id>/versions/<version_id>'
    api.add_resource(DocumentVersionResource, '/<string:document_id>/versions/<string:version_id>', resource_class_kwargs={'document_service': document_service})
    # Register DocumentCompareResource at '/<document_id>/compare'
    api.add_resource(DocumentCompareResource, '/<string:document_id>/compare', resource_class_kwargs={'document_service': document_service})
    # Register DocumentExportResource at '/<document_id>/export'
    api.add_resource(DocumentExportResource, '/<string:document_id>/export', resource_class_kwargs={'document_service': document_service})
    # Register DocumentImportResource at '/import'
    api.add_resource(DocumentImportResource, '/import', resource_class_kwargs={'document_service': document_service})


# Export the blueprint and initialization function
__all__ = ['documents_bp', 'init_document_resources']