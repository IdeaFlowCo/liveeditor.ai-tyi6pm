"""
Initializes the MongoDB repositories package, exposing repository classes and related exceptions
for documents, users, templates, versions, and AI interactions. This file consolidates imports
to provide a clean interface for accessing data layer functionality throughout the application.
"""

# Import document repository
from .document_repository import (
    DocumentRepository,
    DocumentNotFoundError,
    DocumentAccessError
)

# Import user repository
from .user_repository import (
    UserRepository,
    UserNotFoundError,
    DuplicateEmailError
)

# Import template repository
from .template_repository import (
    TemplateRepository,
    TemplateNotFoundError,
    TemplateAccessError
)

# Import version repository
from .version_repository import (
    VersionRepository,
    VersionType,
    VersionNotFoundError,
    VersionAccessError
)

# Import AI interaction repository
from .ai_interaction_repository import (
    AIInteractionRepository,
    InteractionNotFoundError
)

# Note: These classes are re-exported to provide a clean interface for the data layer