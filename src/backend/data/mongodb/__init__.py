"""
MongoDB package initialization file that exposes MongoDB connection utilities and repository classes 
for document storage, user data, and AI interactions in the AI writing enhancement platform.
"""

# Import connection utilities
from .connection import (
    init_mongodb, 
    get_database, 
    get_collection, 
    MongoDBConnectionError,
    ConnectionManager,
    close_connection,
    ping_database,
    get_connection_info
)

# Import repository classes
from .repositories.document_repository import DocumentRepository
from .repositories.user_repository import UserRepository
from .repositories.template_repository import TemplateRepository
from .repositories.version_repository import VersionRepository
from .repositories.ai_interaction_repository import AIInteractionRepository

# Import logger
from ...core.utils.logger import get_logger

# External dependency
import pymongo  # pymongo ~=4.3.0

# Setup logger
logger = get_logger(__name__)

# Global variable to cache repository instances
_db_repositories = None

def init_repositories():
    """
    Initialize all MongoDB repositories with database connection
    
    Returns:
        dict: Dictionary of repository instances by type
    """
    logger.info("Initializing MongoDB repositories")
    
    try:
        # Get database connection
        db = get_database()
        
        # Create repository instances
        repositories = {
            'document': DocumentRepository(),
            'user': UserRepository(),
            'template': TemplateRepository(),
            'version': VersionRepository(),
            'ai_interaction': AIInteractionRepository()
        }
        
        # Cache repositories for reuse
        global _db_repositories
        _db_repositories = repositories
        
        logger.info("MongoDB repositories initialized successfully")
        return repositories
    except Exception as e:
        logger.error(f"Error initializing MongoDB repositories: {str(e)}")
        raise

def get_repositories():
    """
    Get all repository instances, initializing them if needed
    
    Returns:
        dict: Dictionary of repository instances
    """
    global _db_repositories
    
    # Initialize repositories if not already done
    if _db_repositories is None:
        return init_repositories()
    
    return _db_repositories