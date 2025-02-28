#!/usr/bin/env python3
"""
Script that populates the MongoDB database with initial data for development and testing
of the AI writing enhancement platform. Creates sample users, documents, templates, and other
necessary records to enable a fully functional development environment.
"""

import os
import sys
import argparse
import datetime
import uuid
import random
import bcrypt

from ..core.utils.logger import get_logger
from ..data.mongodb.connection import get_mongodb_client, get_collection
from ..data.mongodb.repositories.user_repository import UserRepository
from ..data.mongodb.repositories.document_repository import DocumentRepository
from ..data.mongodb.repositories.template_repository import TemplateRepository
from .generate_templates import generate_default_templates
from ..tests.fixtures.template_fixtures import SAMPLE_SYSTEM_TEMPLATES

# Configure logger
logger = get_logger(__name__)

# Default user credentials
DEFAULT_ADMIN_EMAIL = "admin@example.com"
DEFAULT_ADMIN_PASSWORD = "Admin@123"
DEFAULT_USER_EMAIL = "user@example.com"
DEFAULT_USER_PASSWORD = "User@123"

# Sample data quantities
NUM_SAMPLE_USERS = 5
NUM_SAMPLE_DOCUMENTS = 10
NUM_ANONYMOUS_USERS = 2

# Sample content
SAMPLE_DOCUMENT_TITLES = [
    'Project Proposal', 'Marketing Strategy', 'Customer Email', 'Meeting Notes',
    'Product Review', 'Technical Documentation', 'Blog Post', 'Academic Paper',
    'Cover Letter', 'Business Plan'
]
SAMPLE_DOCUMENT_CONTENT = (
    "The quick brown fox jumps over the lazy dog. This is a sample document that "
    "demonstrates how the text editor looks with content. When AI suggests changes, "
    "they will appear inline with track changes formatting."
)


def hash_password(password):
    """
    Generates a bcrypt hash for a plaintext password
    
    Args:
        password: Plaintext password to hash
        
    Returns:
        Hashed password suitable for storage
    """
    # Convert password to bytes if it's a string
    if isinstance(password, str):
        password = password.encode('utf-8')
    
    # Generate salt and hash the password
    salt = bcrypt.gensalt(12)  # Work factor of 12
    password_hash = bcrypt.hashpw(password, salt)
    
    # Convert hash to string for storage
    return password_hash.decode('utf-8')


def create_admin_user(user_repo):
    """
    Creates an administrator user account
    
    Args:
        user_repo: UserRepository instance
        
    Returns:
        Created admin user data
    """
    # Check if admin already exists
    existing_admin = user_repo.get_by_email(DEFAULT_ADMIN_EMAIL)
    if existing_admin:
        logger.info(f"Admin user already exists: {DEFAULT_ADMIN_EMAIL}")
        return existing_admin
    
    # Create admin user
    admin_data = {
        'email': DEFAULT_ADMIN_EMAIL,
        'password_hash': hash_password(DEFAULT_ADMIN_PASSWORD),
        'first_name': 'Admin',
        'last_name': 'User',
        'account_status': 'active',
        'preferences': {
            'role': 'admin'
        }
    }
    
    admin_user = user_repo.create_user(admin_data)
    logger.info(f"Created admin user: {DEFAULT_ADMIN_EMAIL}")
    return admin_user


def create_regular_user(user_repo, email, password, first_name, last_name):
    """
    Creates a standard user account
    
    Args:
        user_repo: UserRepository instance
        email: Email address for the user
        password: Password for the user
        first_name: User's first name
        last_name: User's last name
        
    Returns:
        Created user data
    """
    # Create user data
    user_data = {
        'email': email,
        'password_hash': hash_password(password),
        'first_name': first_name,
        'last_name': last_name,
        'account_status': 'active',
        'preferences': {
            'role': 'user'
        }
    }
    
    # Create user
    user = user_repo.create_user(user_data)
    logger.info(f"Created regular user: {email}")
    return user


def create_anonymous_users(user_repo, count):
    """
    Creates sample anonymous user accounts
    
    Args:
        user_repo: UserRepository instance
        count: Number of anonymous users to create
        
    Returns:
        List of created anonymous users
    """
    anonymous_users = []
    
    for i in range(count):
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Create anonymous user
        anon_user = user_repo.create_anonymous_user(session_id)
        anonymous_users.append(anon_user)
        
        logger.info(f"Created anonymous user with session ID: {session_id}")
    
    logger.info(f"Created {len(anonymous_users)} anonymous users")
    return anonymous_users


def create_sample_documents(doc_repo, users, anonymous_users, count_per_user):
    """
    Creates sample documents for users
    
    Args:
        doc_repo: DocumentRepository instance
        users: List of regular users
        anonymous_users: List of anonymous users
        count_per_user: Number of documents to create per user
        
    Returns:
        List of created documents
    """
    documents = []
    
    # Create documents for regular users
    for user in users:
        user_id = user['_id']
        
        for i in range(count_per_user):
            # Randomize title and content
            title = random.choice(SAMPLE_DOCUMENT_TITLES)
            if i > 0:
                title = f"{title} {i+1}"
            
            content = SAMPLE_DOCUMENT_CONTENT
            if i > 0:
                content = f"{content}\n\nThis is document number {i+1} for testing purposes."
            
            # Add some random tags to some documents
            tags = []
            if random.random() > 0.3:  # 70% chance to have tags
                num_tags = random.randint(1, 3)
                tag_options = ['important', 'draft', 'work', 'personal', 'business', 'review']
                tags = random.sample(tag_options, min(num_tags, len(tag_options)))
            
            # Create document
            doc_data = {
                'title': title,
                'content': content,
                'description': f"Sample document {i+1} for testing purposes",
                'tags': tags
            }
            
            document = doc_repo.create(doc_data, user_id=user_id)
            documents.append(document)
            
            logger.info(f"Created document '{title}' for user {user_id}")
    
    # Create a few documents for anonymous users
    for anon_user in anonymous_users:
        session_id = anon_user.get('sessionId')
        if not session_id:
            continue
        
        # Create 1-2 documents per anonymous user
        for i in range(random.randint(1, 2)):
            title = f"Anonymous {random.choice(SAMPLE_DOCUMENT_TITLES)}"
            
            # Create document
            doc_data = {
                'title': title,
                'content': f"{SAMPLE_DOCUMENT_CONTENT}\n\nThis is an anonymous document.",
                'description': "Sample anonymous document for testing",
                'tags': ['anonymous', 'draft']
            }
            
            document = doc_repo.create(doc_data, session_id=session_id)
            documents.append(document)
            
            logger.info(f"Created document '{title}' for anonymous session {session_id}")
    
    logger.info(f"Created {len(documents)} sample documents")
    return documents


def create_user_templates(template_repo, users):
    """
    Creates custom templates for some users
    
    Args:
        template_repo: TemplateRepository instance
        users: List of user data
        
    Returns:
        List of created user templates
    """
    templates = []
    
    # Pick a subset of users to have custom templates
    template_users = random.sample(users, min(len(users), 3))
    
    for user in template_users:
        user_id = user['_id']
        
        # Create 1-3 custom templates for each selected user
        for i in range(random.randint(1, 3)):
            # Generate template data
            template_data = {
                'name': f"Custom Template {i+1}",
                'description': f"User-created template for testing purposes",
                'promptText': f"Please improve the following text in a custom way {i+1}: {{{{document}}}}",
                'category': random.choice(['Style', 'Tone', 'Grammar', 'Custom']),
                'isSystem': False,
                'createdBy': user_id
            }
            
            # Create template
            template = template_repo.create(template_data)
            templates.append(template)
            
            logger.info(f"Created custom template '{template_data['name']}' for user {user_id}")
    
    logger.info(f"Created {len(templates)} user-specific templates")
    return templates


def initialize_system_data():
    """
    Initializes system-level data including templates
    
    Returns:
        True if successful
    """
    # Initialize template repository
    template_repo = TemplateRepository()
    
    # Get default templates
    templates = generate_default_templates()
    
    # Initialize system templates
    template_repo.initialize_system_templates(templates)
    
    logger.info("Initialized system templates")
    return True


def clear_existing_data(force=False):
    """
    Clears all existing data from the database (with confirmation)
    
    Args:
        force: If True, skip confirmation prompt
    """
    if not force:
        confirm = input("This will delete ALL existing data. Are you sure? (y/N): ")
        if confirm.lower() != 'y':
            logger.info("Aborted database clearing")
            return
    
    client = get_mongodb_client()
    db = client.get_default_database()
    
    # Get all collection names
    collections = db.list_collection_names()
    
    for collection in collections:
        db.drop_collection(collection)
        logger.info(f"Dropped collection: {collection}")
    
    logger.info("Cleared all existing data from the database")


def parse_args():
    """
    Parses command line arguments for script options
    
    Returns:
        Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description='Populate the database with sample data for development and testing'
    )
    
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear existing data before seeding'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Skip confirmation prompts'
    )
    
    parser.add_argument(
        '--no-admin',
        action='store_true',
        help='Skip admin user creation'
    )
    
    parser.add_argument(
        '--no-users',
        action='store_true',
        help='Skip regular user creation'
    )
    
    parser.add_argument(
        '--no-templates',
        action='store_true',
        help='Skip template creation'
    )
    
    return parser.parse_args()


def main():
    """
    Main function to execute the database seeding process
    
    Returns:
        0 on success, non-zero on failure
    """
    try:
        # Parse command line arguments
        args = parse_args()
        
        # Clear existing data if requested
        if args.clear:
            clear_existing_data(args.force)
        
        # Initialize repositories
        user_repo = UserRepository()
        doc_repo = DocumentRepository()
        template_repo = TemplateRepository()
        
        # Create admin user if not skipped
        admin_user = None
        if not args.no_admin:
            admin_user = create_admin_user(user_repo)
        
        # Create regular users if not skipped
        users = []
        if not args.no_users:
            # Create one standard user with fixed credentials
            standard_user = create_regular_user(
                user_repo, 
                DEFAULT_USER_EMAIL, 
                DEFAULT_USER_PASSWORD,
                "Regular",
                "User"
            )
            users.append(standard_user)
            
            # Create additional random users
            first_names = ["Alice", "Bob", "Charlie", "David", "Emma", "Frank", "Grace", "Henry"]
            last_names = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson"]
            
            for i in range(NUM_SAMPLE_USERS - 1):
                fname = random.choice(first_names)
                lname = random.choice(last_names)
                email = f"{fname.lower()}.{lname.lower()}@example.com"
                password = f"Password123!"
                
                user = create_regular_user(user_repo, email, password, fname, lname)
                users.append(user)
        
        # Create anonymous users
        anonymous_users = create_anonymous_users(user_repo, NUM_ANONYMOUS_USERS)
        
        # Create sample documents
        documents = create_sample_documents(
            doc_repo, 
            users, 
            anonymous_users, 
            NUM_SAMPLE_DOCUMENTS // len(users) if users else 0
        )
        
        # Initialize system templates if not skipped
        if not args.no_templates:
            initialize_system_data()
            
            # Create user-specific templates
            if users:
                user_templates = create_user_templates(template_repo, users)
        
        logger.info("Database seeding completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Error seeding database: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())