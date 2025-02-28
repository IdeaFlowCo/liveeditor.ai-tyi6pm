#!/usr/bin/env python3
"""
Database migration script for the AI Writing Enhancement platform.

This script manages versioned schema changes and data migrations for the MongoDB database.
It provides utilities for creating, applying, and rolling back migrations with proper
validation and error handling.

The script maintains a migrations collection to track the state of applied migrations,
and supports applying migrations incrementally or rolling back to a previous version.

Usage:
    python db_migration.py status                  # Show migration status
    python db_migration.py migrate                 # Apply all pending migrations
    python db_migration.py migrate --to VERSION    # Migrate to a specific version
    python db_migration.py rollback                # Rollback the last migration
    python db_migration.py rollback --to VERSION   # Rollback to a specific version
    python db_migration.py create DESCRIPTION      # Create a new migration file
"""

import os
import sys
import argparse
import importlib
from datetime import datetime

import pymongo
from bson import ObjectId

from ...core.utils.logger import get_logger
from ...data.mongodb.connection import get_mongodb_client, get_database, get_collection
from ...config import DevelopmentConfig, ProductionConfig, TestingConfig

# Configure logging
logger = get_logger(__name__)

# Constants
MIGRATION_COLLECTION = "migrations"
DEFAULT_MIGRATIONS_PATH = "migrations"


class MigrationError(Exception):
    """Custom exception for migration-related errors"""
    
    def __init__(self, message, original_exception=None):
        """Initialize the migration error
        
        Args:
            message (str): Error message
            original_exception (Exception): The original exception that caused this error
        """
        super().__init__(message)
        self.original_exception = original_exception


class Migration:
    """Class representing a database migration operation"""
    
    def __init__(self, version, description, up_function, down_function, applied_at=None):
        """Initialize a migration instance
        
        Args:
            version (str): Migration version identifier
            description (str): Description of the migration
            up_function (callable): Function to apply the migration
            down_function (callable): Function to roll back the migration
            applied_at (datetime): When the migration was applied (None if not applied)
        """
        self.version = version
        self.description = description
        self.up_function = up_function
        self.down_function = down_function
        self.applied_at = applied_at
    
    def apply(self, db):
        """Apply the migration to the database
        
        Args:
            db (pymongo.database.Database): MongoDB database instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Applying migration {self.version}: {self.description}")
            
            # Call the up function with the database
            self.up_function(db)
            
            # Record the migration in the migrations collection
            migrations_collection = get_collection(MIGRATION_COLLECTION)
            migrations_collection.insert_one({
                "version": self.version,
                "description": self.description,
                "applied_at": datetime.utcnow()
            })
            
            # Update the applied_at timestamp
            self.applied_at = datetime.utcnow()
            
            logger.info(f"Successfully applied migration {self.version}")
            return True
        except Exception as e:
            logger.error(f"Failed to apply migration {self.version}: {str(e)}")
            return False
    
    def rollback(self, db):
        """Rollback the migration from the database
        
        Args:
            db (pymongo.database.Database): MongoDB database instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Rolling back migration {self.version}: {self.description}")
            
            # Call the down function with the database
            self.down_function(db)
            
            # Remove the migration record from the migrations collection
            migrations_collection = get_collection(MIGRATION_COLLECTION)
            migrations_collection.delete_one({"version": self.version})
            
            # Clear the applied_at timestamp
            self.applied_at = None
            
            logger.info(f"Successfully rolled back migration {self.version}")
            return True
        except Exception as e:
            logger.error(f"Failed to rollback migration {self.version}: {str(e)}")
            return False
    
    def is_applied(self):
        """Check if migration has been applied
        
        Returns:
            bool: True if migration has been applied, False otherwise
        """
        return self.applied_at is not None


def init_migration_collection():
    """Initialize the migrations collection if it doesn't exist
    
    Returns:
        pymongo.collection.Collection: The migrations collection
    """
    # Get database instance
    db = get_database()
    
    # Get or create migrations collection
    migrations = get_collection(MIGRATION_COLLECTION)
    
    # Create unique index on version field if it doesn't exist
    if "version_1" not in migrations.index_information():
        migrations.create_index("version", unique=True)
        logger.info(f"Created unique index on 'version' field in {MIGRATION_COLLECTION} collection")
    
    logger.info(f"Initialized migrations collection: {MIGRATION_COLLECTION}")
    return migrations


def get_applied_migrations():
    """Retrieve list of already applied migrations from the database
    
    Returns:
        list: List of applied migration versions sorted by version number
    """
    # Get migrations collection
    migrations = init_migration_collection()
    
    # Query for all documents, sorting by version
    applied_migrations = list(migrations.find({}, {"version": 1, "_id": 0}).sort("version", pymongo.ASCENDING))
    
    # Extract version numbers
    versions = [m["version"] for m in applied_migrations]
    
    logger.info(f"Found {len(versions)} applied migrations")
    return versions


def get_available_migrations(migrations_path=None):
    """Discover available migration files in the migrations directory
    
    Args:
        migrations_path (str): Path to migrations directory
        
    Returns:
        dict: Dictionary mapping version numbers to migration module names
    """
    # Use default path if not provided
    if migrations_path is None:
        migrations_path = DEFAULT_MIGRATIONS_PATH
    
    # Ensure the migrations directory exists
    if not os.path.exists(migrations_path):
        logger.warning(f"Migrations directory not found: {migrations_path}")
        return {}
    
    # Get all Python files in the migrations directory
    migrations = {}
    for filename in os.listdir(migrations_path):
        if filename.endswith(".py") and not filename.startswith("__"):
            # Extract version number and name from filename
            # Expected format: V001_description.py
            if not filename.startswith("V"):
                continue
                
            version_part = filename.split("_")[0][1:]  # Remove "V" prefix
            if not version_part.isdigit():
                continue
                
            version = version_part
            module_name = filename[:-3]  # Remove .py extension
            migrations[version] = module_name
    
    # Sort versions numerically
    sorted_migrations = dict(sorted(migrations.items(), key=lambda x: int(x[0])))
    
    logger.info(f"Found {len(sorted_migrations)} available migrations")
    return sorted_migrations


def load_migration_module(version, migrations_path=None):
    """Dynamically load a migration module by version
    
    Args:
        version (str): Migration version to load
        migrations_path (str): Path to migrations directory
        
    Returns:
        module: Loaded Python module containing up/down migration methods
        
    Raises:
        MigrationError: If the migration module is invalid or cannot be loaded
    """
    # Get available migrations
    available_migrations = get_available_migrations(migrations_path)
    
    if version not in available_migrations:
        raise MigrationError(f"Migration version {version} not found")
    
    module_name = available_migrations[version]
    
    try:
        # Use default path if not provided
        if migrations_path is None:
            migrations_path = DEFAULT_MIGRATIONS_PATH
            
        # Get the full file path
        file_path = os.path.join(migrations_path, f"{module_name}.py")
        
        # Import module using importlib.util for better control
        import importlib.util
        
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None:
            raise MigrationError(f"Could not load migration file: {file_path}")
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Validate the module
        if not validate_migration(module):
            raise MigrationError(f"Migration {module_name} is invalid")
        
        logger.info(f"Loaded migration module: {module_name}")
        return module
    except ImportError as e:
        raise MigrationError(f"Failed to import migration {module_name}: {str(e)}", e)
    except Exception as e:
        raise MigrationError(f"Error loading migration {module_name}: {str(e)}", e)


def apply_migration(version, migrations_path=None):
    """Apply a specific migration to the database
    
    Args:
        version (str): Migration version to apply
        migrations_path (str): Path to migrations directory
        
    Returns:
        bool: True if migration was applied successfully, False otherwise
    """
    try:
        # Load the migration module
        module = load_migration_module(version, migrations_path)
        
        # Get database instance
        db = get_database()
        
        # Start a session with transaction if supported
        client = get_mongodb_client()
        session = None
        
        try:
            # Check if transactions are supported (MongoDB 4.0+ with replica set)
            session = client.start_session()
            
            # Try with transaction first
            try:
                with session.start_transaction():
                    logger.info(f"Starting transaction for migration {version}")
                    
                    # Apply the migration
                    logger.info(f"Applying migration {version}: {module.description}")
                    module.up(db)
                    
                    # Record the migration
                    migrations_collection = get_collection(MIGRATION_COLLECTION)
                    migrations_collection.insert_one({
                        "version": version,
                        "description": module.description,
                        "applied_at": datetime.utcnow()
                    }, session=session)
                    
                    logger.info(f"Successfully applied migration {version}")
                    # Transaction will be committed when exiting the with block
                
                # Transaction completed successfully
                logger.info(f"Transaction committed for migration {version}")
                return True
                
            except pymongo.errors.OperationFailure as e:
                # This can happen if transactions are not supported (standalone MongoDB)
                if "transaction" in str(e).lower():
                    logger.warning(f"Transactions not supported, falling back to non-transactional migration: {str(e)}")
                    raise  # Re-raise to be caught by outer exception handler
                else:
                    # Some other operation failure
                    logger.error(f"Failed to apply migration {version}: {str(e)}")
                    if session:
                        session.abort_transaction()
                    return False
                    
        except (pymongo.errors.OperationFailure, AttributeError):
            # AttributeError can happen if start_session is not available
            if session:
                session.end_session()
                session = None
            
            # Apply without transaction
            logger.info(f"Applying migration {version} without transaction: {module.description}")
            
            # Apply the migration
            module.up(db)
            
            # Record the migration
            migrations_collection = get_collection(MIGRATION_COLLECTION)
            migrations_collection.insert_one({
                "version": version,
                "description": module.description,
                "applied_at": datetime.utcnow()
            })
            
            logger.info(f"Successfully applied migration {version} (non-transactional)")
            return True
            
        finally:
            if session:
                session.end_session()
        
    except Exception as e:
        logger.error(f"Failed to apply migration {version}: {str(e)}")
        return False


def rollback_migration(version, migrations_path=None):
    """Rollback a specific migration from the database
    
    Args:
        version (str): Migration version to roll back
        migrations_path (str): Path to migrations directory
        
    Returns:
        bool: True if migration was rolled back successfully, False otherwise
    """
    try:
        # Load the migration module
        module = load_migration_module(version, migrations_path)
        
        # Get database instance
        db = get_database()
        
        # Start a session with transaction if supported
        client = get_mongodb_client()
        session = None
        
        try:
            # Check if transactions are supported (MongoDB 4.0+ with replica set)
            session = client.start_session()
            
            # Try with transaction first
            try:
                with session.start_transaction():
                    logger.info(f"Starting transaction for rollback of migration {version}")
                    
                    # Rollback the migration
                    logger.info(f"Rolling back migration {version}: {module.description}")
                    module.down(db)
                    
                    # Remove the migration record
                    migrations_collection = get_collection(MIGRATION_COLLECTION)
                    migrations_collection.delete_one({"version": version}, session=session)
                    
                    logger.info(f"Successfully rolled back migration {version}")
                    # Transaction will be committed when exiting the with block
                
                # Transaction completed successfully
                logger.info(f"Transaction committed for rollback of migration {version}")
                return True
                
            except pymongo.errors.OperationFailure as e:
                # This can happen if transactions are not supported (standalone MongoDB)
                if "transaction" in str(e).lower():
                    logger.warning(f"Transactions not supported, falling back to non-transactional rollback: {str(e)}")
                    raise  # Re-raise to be caught by outer exception handler
                else:
                    # Some other operation failure
                    logger.error(f"Failed to roll back migration {version}: {str(e)}")
                    if session:
                        session.abort_transaction()
                    return False
                    
        except (pymongo.errors.OperationFailure, AttributeError):
            # AttributeError can happen if start_session is not available
            if session:
                session.end_session()
                session = None
            
            # Rollback without transaction
            logger.info(f"Rolling back migration {version} without transaction: {module.description}")
            
            # Rollback the migration
            module.down(db)
            
            # Remove the migration record
            migrations_collection = get_collection(MIGRATION_COLLECTION)
            migrations_collection.delete_one({"version": version})
            
            logger.info(f"Successfully rolled back migration {version} (non-transactional)")
            return True
            
        finally:
            if session:
                session.end_session()
        
    except Exception as e:
        logger.error(f"Failed to roll back migration {version}: {str(e)}")
        return False


def migrate_to_version(target_version=None, migrations_path=None):
    """Apply or rollback migrations to reach a specific version
    
    Args:
        target_version (str): Target migration version, or None for latest
        migrations_path (str): Path to migrations directory
        
    Returns:
        bool: True if migration to target version was successful, False otherwise
    """
    # Get applied migrations
    applied_versions = get_applied_migrations()
    
    # Get available migrations
    available_migrations = get_available_migrations(migrations_path)
    available_versions = list(available_migrations.keys())
    
    # Determine current version
    current_version = applied_versions[-1] if applied_versions else "0"
    
    # If no target version specified, use latest available
    if target_version is None:
        if not available_versions:
            logger.info("No migrations available to apply")
            return True
        target_version = available_versions[-1]
    
    # Check if target version exists
    if target_version not in available_versions and target_version != "0":
        logger.error(f"Target version {target_version} does not exist")
        return False
    
    logger.info(f"Current version: {current_version}, Target version: {target_version}")
    
    # If already at target version, nothing to do
    if current_version == target_version:
        logger.info(f"Already at target version {target_version}")
        return True
    
    # Convert versions to integers for comparison
    current_ver_int = int(current_version)
    target_ver_int = int(target_version)
    
    success = True
    
    if target_ver_int > current_ver_int:
        # Need to apply migrations
        logger.info(f"Applying migrations from {current_version} to {target_version}")
        
        # Get versions that need to be applied
        versions_to_apply = [v for v in available_versions if int(v) > current_ver_int and int(v) <= target_ver_int]
        
        # Apply migrations in order
        for version in versions_to_apply:
            if not apply_migration(version, migrations_path):
                logger.error(f"Migration to version {target_version} failed at version {version}")
                success = False
                break
    else:
        # Need to rollback migrations
        logger.info(f"Rolling back migrations from {current_version} to {target_version}")
        
        # Get versions that need to be rolled back, in reverse order
        versions_to_rollback = [v for v in applied_versions if int(v) > target_ver_int]
        versions_to_rollback.sort(key=int, reverse=True)
        
        # Rollback migrations in reverse order
        for version in versions_to_rollback:
            if not rollback_migration(version, migrations_path):
                logger.error(f"Rollback to version {target_version} failed at version {version}")
                success = False
                break
    
    if success:
        new_current = get_applied_migrations()[-1] if get_applied_migrations() else "0"
        logger.info(f"Successfully migrated from version {current_version} to {new_current}")
    
    return success


def create_migration_file(description, migrations_path=None):
    """Create a new migration file with template for up/down methods
    
    Args:
        description (str): Short description of the migration
        migrations_path (str): Path to migrations directory
        
    Returns:
        str: Path to the newly created migration file
    """
    # Use default path if not provided
    if migrations_path is None:
        migrations_path = DEFAULT_MIGRATIONS_PATH
    
    # Ensure the migrations directory exists
    if not os.path.exists(migrations_path):
        os.makedirs(migrations_path)
        logger.info(f"Created migrations directory: {migrations_path}")
    
    # Get available migrations
    available_migrations = get_available_migrations(migrations_path)
    available_versions = list(available_migrations.keys())
    
    # Determine next version number
    if available_versions:
        next_version = int(available_versions[-1]) + 1
    else:
        next_version = 1
    
    # Format version number with leading zeros
    version = f"{next_version:03d}"
    
    # Format description for filename (lowercase, no spaces)
    filename_description = description.lower().replace(" ", "_")
    filename = f"V{version}_{filename_description}.py"
    
    # Full path to migration file
    file_path = os.path.join(migrations_path, filename)
    
    # Create migration file with template
    with open(file_path, "w") as f:
        f.write(f'''"""
Migration {version}: {description}

This file contains the migration logic to update the database schema or data.
Created at: {datetime.utcnow().isoformat()}
"""

# Description of this migration (used by the migration tool)
description = "{description}"

def up(db):
    """
    Apply the migration.
    
    Args:
        db: MongoDB database instance
    
    Example:
        # Create a new collection with a validator
        db.create_collection("new_collection", validator={{
            "$jsonSchema": {{
                "bsonType": "object",
                "required": ["name", "email"],
                "properties": {{
                    "name": {{
                        "bsonType": "string",
                        "description": "User's name"
                    }},
                    "email": {{
                        "bsonType": "string",
                        "description": "User's email address"
                    }}
                }}
            }}
        }})
        
        # Or add a field to existing documents
        db.existing_collection.update_many(
            {{}},  # match all documents
            {{"$set": {{"new_field": "default_value"}}}}
        )
    """
    # TODO: Implement migration logic
    pass

def down(db):
    """
    Rollback the migration.
    
    Args:
        db: MongoDB database instance
    
    Example:
        # Drop a collection created in the "up" function
        db.drop_collection("new_collection")
        
        # Or remove a field added in the "up" function
        db.existing_collection.update_many(
            {{}},  # match all documents
            {{"$unset": {{"new_field": ""}}}}
        )
    """
    # TODO: Implement rollback logic
    pass
''')
    
    logger.info(f"Created migration file: {file_path}")
    return file_path


def validate_migration(migration_module):
    """Validate a migration module before execution
    
    Args:
        migration_module: Migration module to validate
        
    Returns:
        bool: True if migration is valid, False otherwise
    """
    # Check for required functions
    if not hasattr(migration_module, "up") or not callable(migration_module.up):
        logger.error("Migration module is missing an 'up' function")
        return False
        
    if not hasattr(migration_module, "down") or not callable(migration_module.down):
        logger.error("Migration module is missing a 'down' function")
        return False
    
    # Check for description
    if not hasattr(migration_module, "description") or not isinstance(migration_module.description, str):
        logger.warning("Migration module is missing a 'description' attribute or it's not a string")
        return False
    
    # Check function signatures
    import inspect
    
    up_sig = inspect.signature(migration_module.up)
    if len(up_sig.parameters) != 1:
        logger.error("'up' function should take exactly one parameter (db)")
        return False
    
    down_sig = inspect.signature(migration_module.down)
    if len(down_sig.parameters) != 1:
        logger.error("'down' function should take exactly one parameter (db)")
        return False
    
    # Additional validation
    try:
        # Check for empty description
        if not migration_module.description.strip():
            logger.warning("Migration description is empty")
            return False
        
        # Check for common issues in up/down functions (optional)
        up_source = inspect.getsource(migration_module.up)
        down_source = inspect.getsource(migration_module.down)
        
        # Check for empty template functions
        if "pass" in up_source and "TODO" in up_source and len(up_source.strip().split("\n")) < 5:
            logger.warning("'up' function appears to be unimplemented (contains 'pass' and 'TODO')")
            # We don't fail validation for this, just warn
            
        if "pass" in down_source and "TODO" in down_source and len(down_source.strip().split("\n")) < 5:
            logger.warning("'down' function appears to be unimplemented (contains 'pass' and 'TODO')")
            # We don't fail validation for this, just warn
            
    except Exception as e:
        logger.warning(f"Error during additional validation: {str(e)}")
        # Continue anyway, as this is just additional validation
    
    return True


def show_migration_status(migrations_path=None):
    """Display the current migration status
    
    Args:
        migrations_path (str): Path to migrations directory
        
    Returns:
        dict: Status information including applied and pending migrations
    """
    # Get applied migrations
    applied_versions = get_applied_migrations()
    
    # Get available migrations
    available_migrations = get_available_migrations(migrations_path)
    available_versions = list(available_migrations.keys())
    
    # Determine current version
    current_version = applied_versions[-1] if applied_versions else "0"
    
    # Determine pending migrations
    pending_versions = [v for v in available_versions if v not in applied_versions]
    
    # Display status
    print(f"\nCurrent database version: {current_version}")
    print(f"Applied migrations: {len(applied_versions)}")
    print(f"Pending migrations: {len(pending_versions)}")
    
    if applied_versions:
        print("\nApplied migrations:")
        for version in applied_versions:
            # Get migration details from database
            migrations_collection = get_collection(MIGRATION_COLLECTION)
            migration = migrations_collection.find_one({"version": version})
            if migration:
                applied_at = migration.get("applied_at", "Unknown")
                description = migration.get("description", "No description")
                print(f"  V{version}: {description} (applied at {applied_at})")
            else:
                print(f"  V{version}: Unknown migration")
    
    if pending_versions:
        print("\nPending migrations:")
        for version in pending_versions:
            # Try to load migration to get description
            try:
                module = load_migration_module(version, migrations_path)
                description = getattr(module, "description", "No description")
                print(f"  V{version}: {description}")
            except Exception:
                print(f"  V{version}: Unknown migration")
    
    # Prepare return data
    status = {
        "current_version": current_version,
        "applied_migrations": applied_versions,
        "pending_migrations": pending_versions
    }
    
    return status


def main():
    """Main entry point for the migration script
    
    Returns:
        int: Exit code (0 for success, non-zero for errors)
    """
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Database migration tool for AI Writing Enhancement platform")
    
    # Add subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show migration status")
    status_parser.add_argument("--path", help="Path to migrations directory")
    
    # Migrate command
    migrate_parser = subparsers.add_parser("migrate", help="Apply migrations")
    migrate_parser.add_argument("--to", help="Target version to migrate to")
    migrate_parser.add_argument("--path", help="Path to migrations directory")
    
    # Rollback command
    rollback_parser = subparsers.add_parser("rollback", help="Rollback migrations")
    rollback_parser.add_argument("--to", help="Target version to rollback to")
    rollback_parser.add_argument("--path", help="Path to migrations directory")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new migration file")
    create_parser.add_argument("description", help="Description of the migration")
    create_parser.add_argument("--path", help="Path to migrations directory")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
    if args.command == "status":
        show_migration_status(args.path)
        return 0
    elif args.command == "migrate":
        success = migrate_to_version(args.to, args.path)
        return 0 if success else 1
    elif args.command == "rollback":
        if not args.to:
            # Get current version
            applied_versions = get_applied_migrations()
            if len(applied_versions) <= 1:
                logger.error("Cannot rollback: no previous version available")
                return 1
                
            current_version = applied_versions[-1]
            previous_version = applied_versions[-2]
            args.to = previous_version
            logger.info(f"Rollback target not specified, using previous version: {previous_version}")
        
        success = migrate_to_version(args.to, args.path)
        return 0 if success else 1
    elif args.command == "create":
        create_migration_file(args.description, args.path)
        return 0
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())