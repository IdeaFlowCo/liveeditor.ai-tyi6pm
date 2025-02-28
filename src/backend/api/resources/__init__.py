"""
Module that imports and exports all API resource classes to allow convenient import from the resources package and provides utility functions for registering resources with the Flask application.
"""

from flask_restful import Api # flask_restful 0.3.10

from .health_resource import HealthResource, DetailedHealthResource, DependencyHealthResource # ./health_resource
from .auth_resource import AuthResource # ./auth_resource
from .user_resource import UserResource, CurrentUserResource, UserPreferencesResource, CurrentUserPreferencesResource, UserPasswordResource, CurrentUserPasswordResource # ./user_resource
from .document_resource import DocumentResource, DocumentsResource, DocumentVersionResource, DocumentVersionsResource, DocumentCompareResource, DocumentExportResource, DocumentImportResource # ./document_resource
from .chat_resource import ChatResource # ./chat_resource
from .suggestion_resource import SuggestionResource, SuggestionBatchResource, SuggestionTypeResource, SuggestionReviewResource, SuggestionFeedbackResource # ./suggestion_resource
from .template_resource import TemplateResource, TemplatesResource, TemplateCategoriesResource, TemplateByCategoryResource, TemplateSearchResource, TemplateMetricsResource, PopularTemplatesResource # ./template_resource


def register_resources(api: Api) -> None:
    """Function to register all API resources with the Flask application

    Args:
        api: Flask-RESTful Api instance
    """
    # Registers HealthResource with '/health' endpoint
    api.add_resource(HealthResource, '/health')
    api.add_resource(DetailedHealthResource, '/health/detailed')
    api.add_resource(DependencyHealthResource, '/health/<string:dependency>')

    # Registers AuthResource with '/auth' endpoints
    api.add_resource(AuthResource, '/auth')

    # Registers UserResource with '/users' endpoints
    api.add_resource(UserResource, '/users/<string:user_id>')
    api.add_resource(CurrentUserResource, '/users/me')
    api.add_resource(UserPreferencesResource, '/users/<string:user_id>/preferences')
    api.add_resource(CurrentUserPreferencesResource, '/users/me/preferences')
    api.add_resource(UserPasswordResource, '/users/<string:user_id>/password')
    api.add_resource(CurrentUserPasswordResource, '/users/me/password')

    # Registers DocumentResource with '/documents' endpoints
    api.add_resource(DocumentResource, '/documents/<string:document_id>')
    api.add_resource(DocumentsResource, '/documents')
    api.add_resource(DocumentVersionResource, '/documents/<string:document_id>/versions/<string:version_id>')
    api.add_resource(DocumentVersionsResource, '/documents/<string:document_id>/versions')
    api.add_resource(DocumentCompareResource, '/documents/<string:document_id>/compare')
    api.add_resource(DocumentExportResource, '/documents/<string:document_id>/export')
    api.add_resource(DocumentImportResource, '/documents/import')

    # Registers ChatResource with '/chat' endpoints
    api.add_resource(ChatResource, '/chat')

    # Registers SuggestionResource with '/suggestions' endpoints
    api.add_resource(SuggestionResource, '/suggestions')
    api.add_resource(SuggestionBatchResource, '/suggestions/batch')
    api.add_resource(SuggestionTypeResource, '/suggestions/types')
    api.add_resource(SuggestionReviewResource, '/suggestions/<string:document_id>/review')
    api.add_resource(SuggestionFeedbackResource, '/suggestions/feedback')

    # Registers TemplateResource with '/templates' endpoints
    api.add_resource(TemplateResource, '/templates/<string:template_id>')
    api.add_resource(TemplatesResource, '/templates')
    api.add_resource(TemplateCategoriesResource, '/templates/categories')
    api.add_resource(TemplateByCategoryResource, '/templates/category/<string:category>')
    api.add_resource(TemplateSearchResource, '/templates/search')
    api.add_resource(TemplateMetricsResource, '/templates/<string:template_id>/metrics')
    api.add_resource(PopularTemplatesResource, '/templates/popular')

# Export all resource classes for use in API registration
__all__ = [
    'HealthResource',
    'DetailedHealthResource',
    'DependencyHealthResource',
    'AuthResource',
    'UserResource',
    'CurrentUserResource',
    'UserPreferencesResource',
    'CurrentUserPreferencesResource',
    'UserPasswordResource',
    'CurrentUserPasswordResource',
    'DocumentResource',
    'DocumentsResource',
    'DocumentVersionResource',
    'DocumentVersionsResource',
    'DocumentCompareResource',
    'DocumentExportResource',
    'DocumentImportResource',
    'ChatResource',
    'SuggestionResource',
    'SuggestionBatchResource',
    'SuggestionTypeResource',
    'SuggestionReviewResource',
    'SuggestionFeedbackResource',
    'TemplateResource',
    'TemplatesResource',
    'TemplateCategoriesResource',
    'TemplateByCategoryResource',
    'TemplateSearchResource',
    'TemplateMetricsResource',
    'PopularTemplatesResource',
    'register_resources'
]