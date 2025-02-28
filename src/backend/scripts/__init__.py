"""
Initialization file for the scripts package.

This module exposes key script functions and utilities for database setup, migrations,
template generation, and seed data operations, making these utilities available for
import at the package level.
"""

# Import script functions
from .create_indexes import create_all_indexes
from .db_migration import main as run_migrations
from .generate_templates import main as generate_templates
from .seed_data import main as seed_data

def create_default_users():
    """
    Create default admin and user accounts.
    
    This is a convenience function that creates admin and regular user accounts
    with predefined credentials.
    
    Returns:
        list: The created users
    """
    from .seed_data import create_admin_user, create_regular_user
    from ..data.mongodb.repositories.user_repository import UserRepository
    
    user_repo = UserRepository()
    admin = create_admin_user(user_repo)
    
    # Create a default regular user with standard credentials
    from .seed_data import DEFAULT_USER_EMAIL, DEFAULT_USER_PASSWORD
    user = create_regular_user(
        user_repo, 
        DEFAULT_USER_EMAIL, 
        DEFAULT_USER_PASSWORD,
        "Regular",
        "User"
    )
    
    return [admin, user]

def create_default_templates():
    """
    Create default AI prompt templates.
    
    This is a convenience function that initializes the system with
    default AI prompt templates.
    
    Returns:
        bool: True if successful
    """
    from .seed_data import initialize_system_data
    return initialize_system_data()

# Export all required functions
__all__ = [
    'create_all_indexes',
    'run_migrations',
    'generate_templates',
    'seed_data',
    'create_default_users',
    'create_default_templates'
]