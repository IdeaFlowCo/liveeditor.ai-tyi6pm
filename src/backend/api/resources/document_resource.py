# src/backend/api/resources/document_resource.py
"""
Implements RESTful API endpoints for document operations in the AI writing enhancement platform,
supporting both anonymous and authenticated users. Handles document creation, retrieval, updating,
deletion, versioning, and format conversion while integrating with authentication and validation mechanisms.
"""

from flask import request, g, jsonify, make_response  # flask==2.3.0
from flask_restful import Resource, reqparse  # flask_restful==0.3.10

from src.backend.core.documents.document_service import DocumentService, DocumentServiceError, DocumentAccessError, AnonymousRateLimitError  # src/backend/core/documents/document_service.py
from src.backend.api.schemas.document_schema import DocumentCreateSchema, DocumentUpdateSchema, DocumentResponseSchema, DocumentListQuerySchema, DocumentListResponseSchema, DocumentVersionResponseSchema, DocumentVersionListResponseSchema, DocumentExportSchema, DocumentImportSchema, DocumentCompareSchema  # src/backend/api/schemas/document_schema.py
from src.backend.api.middleware.auth_middleware import auth_required, get_current_user_id, is_anonymous_session  # src/backend/api/middleware/auth_middleware.py
from src.backend.core.utils.logger import get_logger  # src/backend/core/utils/logger.py

# Initialize logger
logger = get_logger(__name__)


class DocumentResource(Resource):
    """Resource for managing individual document operations"""

    def __init__(self, document_service: DocumentService):
        """Initialize the document resource with required dependencies"""
        # Store document_service instance
        self.document_service = document_service
        # Initialize document schema instances
        self.document_schema = DocumentResponseSchema()
        self.update_schema = DocumentUpdateSchema()
        # Set up logger for document operations
        self.logger = logger

    @auth_required(allow_anonymous=True)
    def get(self, document_id: str):
        """Retrieve a document by ID"""
        # Log document retrieval request
        logger.info(f"Retrieving document with ID: {document_id}")

        # Get current user ID or anonymous session ID
        user_id = get_current_user_id()
        session_id = None
        if is_anonymous_session():
            session_id = request.cookies.get('anonymous_session')

        try:
            # Call document_service.get_document with authentication context
            document = self.document_service.get_document(document_id, user_id, session_id, include_content=True)
            # Serialize document data using DocumentResponseSchema
            result = self.document_schema.dump(document)
            # Return response with 200 status code
            return jsonify(result), 200
        except DocumentServiceError as e:
            # Handle document access errors (404 if not found, 403 if unauthorized)
            logger.error(f"Error retrieving document {document_id}: {str(e)}")
            return jsonify({"error": "document_not_found", "message": str(e)}), 404
        except DocumentAccessError as e:
            logger.error(f"Access denied to document {document_id}: {str(e)}")
            return jsonify({"error": "access_denied", "message": str(e)}), 403

    @auth_required(allow_anonymous=True)
    def put(self, document_id: str):
        """Update an existing document"""
        # Log document update request
        logger.info(f"Updating document with ID: {document_id}")

        # Parse and validate request data using DocumentUpdateSchema
        try:
            data = self.update_schema.load(request.get_json())
        except Exception as e:
            logger.error(f"Invalid request data: {str(e)}")
            return jsonify({"error": "invalid_request", "message": str(e)}), 400

        # Get current user ID or anonymous session ID
        user_id = get_current_user_id()
        session_id = None
        if is_anonymous_session():
            session_id = request.cookies.get('anonymous_session')

        try:
            # Call document_service.update_document with document data
            document = self.document_service.update_document(document_id, data, user_id, session_id, create_version=data.get('create_version', False))
            # Serialize updated document using DocumentResponseSchema
            result = self.document_schema.dump(document)
            # Return response with 200 status code
            return jsonify(result), 200
        except DocumentServiceError as e:
            # Handle document access and validation errors
            logger.error(f"Error updating document {document_id}: {str(e)}")
            return jsonify({"error": "document_update_failed", "message": str(e)}), 400
        except DocumentAccessError as e:
            logger.error(f"Access denied to document {document_id}: {str(e)}")
            return jsonify({"error": "access_denied", "message": str(e)}), 403

    @auth_required(allow_anonymous=True)
    def delete(self, document_id: str):
        """Delete a document"""
        # Log document deletion request
        logger.info(f"Deleting document with ID: {document_id}")

        # Get current user ID or anonymous session ID
        user_id = get_current_user_id()
        session_id = None
        if is_anonymous_session():
            session_id = request.cookies.get('anonymous_session')

        try:
            # Call document_service.delete_document
            self.document_service.delete_document(document_id, user_id, session_id)
            # Return success response with 204 status code
            return '', 204
        except DocumentServiceError as e:
            # Handle document access and service errors
            logger.error(f"Error deleting document {document_id}: {str(e)}")
            return jsonify({"error": "document_deletion_failed", "message": str(e)}), 400
        except DocumentAccessError as e:
            logger.error(f"Access denied to document {document_id}: {str(e)}")
            return jsonify({"error": "access_denied", "message": str(e)}), 403


class DocumentsResource(Resource):
    """Resource for document collection operations"""

    def __init__(self, document_service: DocumentService):
        """Initialize the documents resource with required dependencies"""
        # Store document_service instance
        self.document_service = document_service
        # Initialize document schema instances
        self.create_schema = DocumentCreateSchema()
        self.list_query_schema = DocumentListQuerySchema()
        self.list_response_schema = DocumentListResponseSchema()
        # Set up logger for document collection operations
        self.logger = logger

    @auth_required(allow_anonymous=True)
    def get(self):
        """List documents with filtering and pagination"""
        # Log document list request
        logger.info("Listing documents")

        # Parse and validate query parameters using DocumentListQuerySchema
        try:
            query_params = self.list_query_schema.load(request.args)
        except Exception as e:
            logger.error(f"Invalid query parameters: {str(e)}")
            return jsonify({"error": "invalid_query_parameters", "message": str(e)}), 400

        # Get current user ID or anonymous session ID
        user_id = get_current_user_id()
        session_id = None
        if is_anonymous_session():
            session_id = request.cookies.get('anonymous_session')

        try:
            # Call document_service.list_documents with filters and pagination
            documents, total = self.document_service.list_documents(
                user_id, session_id,
                filters=query_params,
                skip=query_params.get('skip', 0),
                limit=query_params.get('limit', 10)
            )
            # Serialize document list using DocumentListResponseSchema
            result = self.list_response_schema.dump({
                "items": documents,
                "total": total,
                "limit": query_params.get('limit', 10),
                "skip": query_params.get('skip', 0)
            })
            # Return response with 200 status code
            return jsonify(result), 200
        except DocumentServiceError as e:
            # Handle service errors
            logger.error(f"Error listing documents: {str(e)}")
            return jsonify({"error": "document_listing_failed", "message": str(e)}), 500

    @auth_required(allow_anonymous=True)
    def post(self):
        """Create a new document"""
        # Log document creation request
        logger.info("Creating a new document")

        # Parse and validate request data using DocumentCreateSchema
        try:
            data = self.create_schema.load(request.get_json())
        except Exception as e:
            logger.error(f"Invalid request data: {str(e)}")
            return jsonify({"error": "invalid_request", "message": str(e)}), 400

        # Get current user ID or anonymous session ID
        user_id = get_current_user_id()
        session_id = None
        if is_anonymous_session():
            session_id = request.cookies.get('anonymous_session')

        try:
            # Call document_service.create_document with document data
            document = self.document_service.create_document(data, user_id, session_id)
            # Serialize created document using DocumentResponseSchema
            result = self.document_schema.dump(document)
            # Return response with 201 status code and Location header
            response = make_response(jsonify(result), 201)
            response.headers['Location'] = f'/documents/{document["id"]}'
            return response
        except DocumentServiceError as e:
            # Handle validation and rate limit errors
            logger.error(f"Error creating document: {str(e)}")
            return jsonify({"error": "document_creation_failed", "message": str(e)}), 400
        except AnonymousRateLimitError as e:
            logger.error(f"Anonymous rate limit exceeded: {str(e)}")
            return jsonify({"error": "rate_limit_exceeded", "message": str(e)}), 429


class DocumentVersionResource(Resource):
    """Resource for retrieving a specific document version"""

    def __init__(self, document_service: DocumentService):
        """Initialize the document version resource"""
        # Store document_service instance
        self.document_service = document_service
        # Initialize version response schema
        self.version_schema = DocumentVersionResponseSchema()
        # Set up logger for version operations
        self.logger = logger

    @auth_required(allow_anonymous=True)
    def get(self, document_id: str, version_id: str):
        """Retrieve a specific document version"""
        # Log version retrieval request
        logger.info(f"Retrieving version {version_id} of document {document_id}")

        # Get current user ID or anonymous session ID
        user_id = get_current_user_id()
        session_id = None
        if is_anonymous_session():
            session_id = request.cookies.get('anonymous_session')

        try:
            # Call document_service.get_document_version
            version = self.document_service.get_document_version(document_id, version_id, user_id, session_id)
            # Serialize version data using DocumentVersionResponseSchema
            result = self.version_schema.dump(version)
            # Return response with 200 status code
            return jsonify(result), 200
        except DocumentServiceError as e:
            # Handle document access and not found errors
            logger.error(f"Error retrieving version {version_id} of document {document_id}: {str(e)}")
            return jsonify({"error": "version_retrieval_failed", "message": str(e)}), 404
        except DocumentAccessError as e:
            logger.error(f"Access denied to version {version_id} of document {document_id}: {str(e)}")
            return jsonify({"error": "access_denied", "message": str(e)}), 403


class DocumentVersionsResource(Resource):
    """Resource for listing document versions"""

    def __init__(self, document_service: DocumentService):
        """Initialize the document versions resource"""
        # Store document_service instance
        self.document_service = document_service
        # Initialize version list schema
        self.version_list_schema = DocumentVersionListResponseSchema()
        # Set up logger for version listing operations
        self.logger = logger

    @auth_required(allow_anonymous=True)
    def get(self, document_id: str):
        """List versions of a document with pagination"""
        # Log version list request
        logger.info(f"Listing versions for document {document_id}")

        # Parse pagination parameters from query string
        try:
            limit = int(request.args.get('limit', 10))
            skip = int(request.args.get('skip', 0))
        except ValueError:
            logger.error("Invalid pagination parameters")
            return jsonify({"error": "invalid_query_parameters", "message": "Invalid pagination parameters"}), 400

        # Get current user ID or anonymous session ID
        user_id = get_current_user_id()
        session_id = None
        if is_anonymous_session():
            session_id = request.cookies.get('anonymous_session')

        try:
            # Call document_service.get_document_versions
            versions, total = self.document_service.get_document_versions(document_id, user_id, session_id, limit, skip)
            # Serialize version list using DocumentVersionListResponseSchema
            result = self.version_list_schema.dump({
                "items": versions,
                "total": total,
                "limit": limit,
                "skip": skip
            })
            # Return response with 200 status code
            return jsonify(result), 200
        except DocumentServiceError as e:
            # Handle document access and service errors
            logger.error(f"Error listing versions for document {document_id}: {str(e)}")
            return jsonify({"error": "version_listing_failed", "message": str(e)}), 500
        except DocumentAccessError as e:
            logger.error(f"Access denied to document {document_id}: {str(e)}")
            return jsonify({"error": "access_denied", "message": str(e)}), 403


class DocumentCompareResource(Resource):
    """Resource for comparing document versions"""

    def __init__(self, document_service: DocumentService):
        """Initialize the document comparison resource"""
        # Store document_service instance
        self.document_service = document_service
        # Initialize comparison schema
        self.compare_schema = DocumentCompareSchema()
        # Set up logger for comparison operations
        self.logger = logger

    @auth_required(allow_anonymous=True)
    def post(self, document_id: str):
        """Compare two versions of a document"""
        # Log comparison request
        logger.info(f"Comparing versions of document {document_id}")

        # Parse and validate request data using DocumentCompareSchema
        try:
            data = self.compare_schema.load(request.get_json())
        except Exception as e:
            logger.error(f"Invalid request data: {str(e)}")
            return jsonify({"error": "invalid_request", "message": str(e)}), 400

        # Get current user ID or anonymous session ID
        user_id = get_current_user_id()
        session_id = None
        if is_anonymous_session():
            session_id = request.cookies.get('anonymous_session')

        try:
            # Call document_service.compare_document_versions
            comparison_result = self.document_service.compare_document_versions(
                document_id,
                data['base_version_id'],
                data['comparison_version_id'],
                user_id,
                session_id,
                data.get('format', 'html')
            )
            # Return comparison result with 200 status code
            return jsonify(comparison_result), 200
        except DocumentServiceError as e:
            # Handle document access, not found, and service errors
            logger.error(f"Error comparing versions of document {document_id}: {str(e)}")
            return jsonify({"error": "version_comparison_failed", "message": str(e)}), 500
        except DocumentAccessError as e:
            logger.error(f"Access denied to document {document_id}: {str(e)}")
            return jsonify({"error": "access_denied", "message": str(e)}), 403


class DocumentExportResource(Resource):
    """Resource for exporting documents to different formats"""

    def __init__(self, document_service: DocumentService):
        """Initialize the document export resource"""
        # Store document_service instance
        self.document_service = document_service
        # Initialize export schema
        self.export_schema = DocumentExportSchema()
        # Set up logger for export operations
        self.logger = logger

    @auth_required(allow_anonymous=True)
    def post(self, document_id: str):
        """Export a document to a specified format"""
        # Log export request
        logger.info(f"Exporting document {document_id}")

        # Parse and validate request data using DocumentExportSchema
        try:
            data = self.export_schema.load(request.get_json())
        except Exception as e:
            logger.error(f"Invalid request data: {str(e)}")
            return jsonify({"error": "invalid_request", "message": str(e)}), 400

        # Get current user ID or anonymous session ID
        user_id = get_current_user_id()
        session_id = None
        if is_anonymous_session():
            session_id = request.cookies.get('anonymous_session')

        try:
            # Call document_service.export_document
            exported_document = self.document_service.export_document(
                document_id,
                data['format'],
                user_id,
                session_id,
                data.get('options', {})
            )
            # Return exported document with appropriate content-type header
            response = make_response(exported_document['content'])
            response.headers['Content-Type'] = exported_document['format']
            # Return response with 200 status code
            return response, 200
        except DocumentServiceError as e:
            # Handle document access, format errors, and service errors
            logger.error(f"Error exporting document {document_id}: {str(e)}")
            return jsonify({"error": "document_export_failed", "message": str(e)}), 500
        except DocumentAccessError as e:
            logger.error(f"Access denied to document {document_id}: {str(e)}")
            return jsonify({"error": "access_denied", "message": str(e)}), 403


class DocumentImportResource(Resource):
    """Resource for importing documents from different formats"""

    def __init__(self, document_service: DocumentService):
        """Initialize the document import resource"""
        # Store document_service instance
        self.document_service = document_service
        # Initialize import and response schemas
        self.import_schema = DocumentImportSchema()
        self.document_schema = DocumentResponseSchema()
        # Set up logger for import operations
        self.logger = logger

    @auth_required(allow_anonymous=True)
    def post(self):
        """Import a document from external content"""
        # Log import request
        logger.info("Importing a document")

        # Parse and validate request data using DocumentImportSchema
        try:
            data = self.import_schema.load(request.get_json())
        except Exception as e:
            logger.error(f"Invalid request data: {str(e)}")
            return jsonify({"error": "invalid_request", "message": str(e)}), 400

        # Get current user ID or anonymous session ID
        user_id = get_current_user_id()
        session_id = None
        if is_anonymous_session():
            session_id = request.cookies.get('anonymous_session')

        try:
            # Call document_service.import_document
            document = self.document_service.import_document(
                data['content'],
                data['format'],
                data.get('title', 'Imported Document'),
                user_id,
                session_id
            )
            # Serialize created document using DocumentResponseSchema
            result = self.document_schema.dump(document)
            # Return response with 201 status code and Location header
            response = make_response(jsonify(result), 201)
            response.headers['Location'] = f'/documents/{document["id"]}'
            return response
        except DocumentServiceError as e:
            # Handle format errors, rate limit errors, and service errors
            logger.error(f"Error importing document: {str(e)}")
            return jsonify({"error": "document_import_failed", "message": str(e)}), 500