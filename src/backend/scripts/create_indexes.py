#!/usr/bin/env python3
"""
A standalone script that creates and ensures all necessary MongoDB indexes for 
the AI writing enhancement platform. This script optimizes database performance 
by setting up appropriate indexes for all collections based on common query patterns.
"""

import argparse
import sys
import pymongo
from typing import List, Dict, Any

from ..data.mongodb.connection import get_mongodb_client, get_database, close_connections
from ..data.mongodb.repositories.document_repository import DocumentRepository
from ..data.mongodb.repositories.user_repository import UserRepository
from ..data.mongodb.repositories.template_repository import TemplateRepository
from ..data.mongodb.repositories.version_repository import VersionRepository
from ..data.mongodb.repositories.ai_interaction_repository import AIInteractionRepository
from ..core.utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

def create_document_indexes(db: pymongo.database.Database) -> List[str]:
    """Creates indexes for the documents collection
    
    Args:
        db: MongoDB database connection
        
    Returns:
        List of created index names
    """
    logger.info("Creating indexes for documents collection")
    collection = db[DocumentRepository.COLLECTION_NAME]
    
    indexes = [
        # Index on userId for user document queries
        collection.create_index('userId'),
        
        # Compound index on (userId, isArchived) for active document queries
        collection.create_index([('userId', pymongo.ASCENDING), ('isArchived', pymongo.ASCENDING)]),
        
        # Index on sessionId for anonymous session documents
        collection.create_index('sessionId'),
        
        # Indexes for time-based queries
        collection.create_index('createdAt'),
        collection.create_index('updatedAt'),
        
        # Text index on title and description for search functionality
        collection.create_index([('title', 'text'), ('description', 'text')]),
        
        # Index on tags for tag-based filtering
        collection.create_index('tags'),
        
        # Index on currentVersionId for efficient version lookup
        collection.create_index('currentVersionId')
    ]
    
    logger.info(f"Created {len(indexes)} indexes for documents collection")
    return indexes

def create_user_indexes(db: pymongo.database.Database) -> List[str]:
    """Creates indexes for the users collection
    
    Args:
        db: MongoDB database connection
        
    Returns:
        List of created index names
    """
    logger.info("Creating indexes for users collection")
    collection = db[UserRepository.COLLECTION_NAME]
    
    indexes = [
        # Unique index on email field to prevent duplicates
        collection.create_index('email', unique=True),
        
        # Index on sessionId for anonymous users
        collection.create_index('sessionId'),
        
        # Indexes for time-based queries
        collection.create_index('createdAt'),
        collection.create_index('lastLogin'),
        
        # Index on accountStatus for filtering active/inactive accounts
        collection.create_index('accountStatus'),
        
        # Index on verificationToken for efficient token verification
        collection.create_index('verificationToken'),
        
        # Index on resetToken for password reset functionality
        collection.create_index('resetToken'),
        
        # Index on expiresAt for anonymous user cleanup
        collection.create_index('expiresAt')
    ]
    
    logger.info(f"Created {len(indexes)} indexes for users collection")
    return indexes

def create_version_indexes(db: pymongo.database.Database) -> List[str]:
    """Creates indexes for the document versions collection
    
    Args:
        db: MongoDB database connection
        
    Returns:
        List of created index names
    """
    logger.info("Creating indexes for document versions collection")
    collection = db[VersionRepository.COLLECTION_NAME]
    
    indexes = [
        # Index on documentId for version history queries
        collection.create_index('documentId'),
        
        # Compound index on (documentId, versionNumber) for specific version retrieval
        collection.create_index([('documentId', pymongo.ASCENDING), ('versionNumber', pymongo.DESCENDING)]),
        
        # Index on createdAt for time-based queries
        collection.create_index('createdAt'),
        
        # Index on createdBy for user-based version queries
        collection.create_index('createdBy'),
        
        # Index on previousVersionId for version chain navigation
        collection.create_index('previousVersionId')
    ]
    
    logger.info(f"Created {len(indexes)} indexes for document versions collection")
    return indexes

def create_template_indexes(db: pymongo.database.Database) -> List[str]:
    """Creates indexes for the AI prompt templates collection
    
    Args:
        db: MongoDB database connection
        
    Returns:
        List of created index names
    """
    logger.info("Creating indexes for AI prompt templates collection")
    collection = db[TemplateRepository.COLLECTION_NAME]
    
    indexes = [
        # Index on name for template lookup
        collection.create_index('name'),
        
        # Index on category for template filtering
        collection.create_index('category'),
        
        # Index on isSystem to separate system vs user templates
        collection.create_index('isSystem'),
        
        # Index on createdBy for user-created templates
        collection.create_index('createdBy'),
        
        # Text index on name and description for template search
        collection.create_index([('name', 'text'), ('description', 'text')])
    ]
    
    logger.info(f"Created {len(indexes)} indexes for AI prompt templates collection")
    return indexes

def create_ai_interaction_indexes(db: pymongo.database.Database) -> List[str]:
    """Creates indexes for the AI interactions collection
    
    Args:
        db: MongoDB database connection
        
    Returns:
        List of created index names
    """
    logger.info("Creating indexes for AI interactions collection")
    collection = db[AIInteractionRepository.COLLECTION_NAME]
    
    indexes = [
        # Index on timestamp for chronological queries and data retention
        collection.create_index('timestamp'),
        
        # Index on userId for user-based interaction history
        collection.create_index('userId'),
        
        # Index on sessionId for anonymous session interactions
        collection.create_index('sessionId'),
        
        # Index on documentId for document-specific interactions
        collection.create_index('documentId'),
        
        # Index on interaction_type for filtering by type
        collection.create_index('interaction_type'),
        
        # Index on conversationId for chat thread grouping
        collection.create_index('metadata.conversation_id'),
        
        # Compound index on (userId, interaction_type) for filtered user history
        collection.create_index([('userId', pymongo.ASCENDING), ('interaction_type', pymongo.ASCENDING)]),
        
        # Compound index on (documentId, timestamp) for document interaction history
        collection.create_index([('documentId', pymongo.ASCENDING), ('timestamp', pymongo.DESCENDING)])
    ]
    
    logger.info(f"Created {len(indexes)} indexes for AI interactions collection")
    return indexes

def create_all_indexes() -> Dict[str, List[str]]:
    """Creates all required indexes for all collections
    
    Returns:
        Dictionary mapping collection names to lists of created indexes
    """
    try:
        logger.info("Starting index creation for all collections")
        
        # Get database connection
        db = get_database()
        
        # Initialize results dictionary
        results = {}
        
        # Create indexes for each collection
        results[DocumentRepository.COLLECTION_NAME] = create_document_indexes(db)
        results[UserRepository.COLLECTION_NAME] = create_user_indexes(db)
        results[VersionRepository.COLLECTION_NAME] = create_version_indexes(db)
        results[TemplateRepository.COLLECTION_NAME] = create_template_indexes(db)
        results[AIInteractionRepository.COLLECTION_NAME] = create_ai_interaction_indexes(db)
        
        # Log summary
        total_indexes = sum(len(indexes) for indexes in results.values())
        logger.info(f"Successfully created {total_indexes} indexes across {len(results)} collections")
        
        # Close connections
        close_connections()
        
        return results
    
    except Exception as e:
        logger.error(f"Error creating indexes: {str(e)}")
        raise

def main():
    """Main function that parses arguments and runs the index creation"""
    parser = argparse.ArgumentParser(
        description='Create MongoDB indexes for the AI writing enhancement platform'
    )
    parser.add_argument(
        '-v', '--verbose', 
        action='store_true', 
        help='Enable verbose logging'
    )
    args = parser.parse_args()
    
    # Configure logging based on verbosity level
    if args.verbose:
        logger.info("Verbose logging enabled")
    
    try:
        # Create all indexes
        logger.info("Starting MongoDB index creation script")
        results = create_all_indexes()
        
        # Log successful index creation with summary
        logger.info("MongoDB indexes created successfully")
        return 0
    
    except Exception as e:
        # Log any exceptions during creation
        logger.error(f"Failed to create MongoDB indexes: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())