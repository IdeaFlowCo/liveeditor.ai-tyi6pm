"""
Provides pytest fixtures for generating standardized user data to be used in tests 
for the AI writing enhancement platform.

This module contains fixtures for different user types including regular users, 
verified users, unverified users, and anonymous users with appropriate attributes 
for each type. These fixtures can be used across the test suite to ensure consistent
test data for user-related functionality.

Available fixtures:
- regular_user_data: Standard user with typical fields
- verified_user_data: User with verified email
- unverified_user_data: User with unverified email and verification token
- admin_user_data: User with admin role
- anonymous_user_data: Anonymous user with session ID
- user_with_reset_token: User with password reset token
- user_with_preferences: User with custom preferences settings
- user_list: List of multiple users for pagination testing
"""

import pytest
from datetime import datetime, timedelta
import uuid
from bson import ObjectId  # pymongo ~=4.3.0

# Default values for user data
DEFAULT_PASSWORD = "SecureP@ssw0rd123"
DEFAULT_PASSWORD_HASH = "$2b$12$1234567890123456789012etUvVgBIlJMSrk5QRY5fS8Jb/Ivj.6i"
VERIFIED_EMAIL = "verified@example.com"
UNVERIFIED_EMAIL = "unverified@example.com"
ADMIN_EMAIL = "admin@example.com"


def generate_user_id():
    """Generate a unique user ID in the format of MongoDB ObjectID."""
    return str(ObjectId())


def generate_session_id():
    """Generate a unique session ID for anonymous users."""
    return str(uuid.uuid4())


@pytest.fixture
def regular_user_data():
    """Fixture providing standard user data for tests."""
    return {
        "_id": generate_user_id(),
        "email": "user@example.com",
        "firstName": "Test",
        "lastName": "User",
        "passwordHash": DEFAULT_PASSWORD_HASH,
        "emailVerified": True,
        "accountStatus": "active",
        "createdAt": datetime.utcnow(),
        "lastLogin": datetime.utcnow(),
        "profile": {
            "bio": "Test user for unit testing",
            "avatarUrl": None
        }
    }


@pytest.fixture
def verified_user_data():
    """Fixture providing verified user data for tests."""
    return {
        "_id": generate_user_id(),
        "email": VERIFIED_EMAIL,
        "firstName": "Verified",
        "lastName": "User",
        "passwordHash": DEFAULT_PASSWORD_HASH,
        "emailVerified": True,
        "accountStatus": "active",
        "createdAt": datetime.utcnow(),
        "lastLogin": datetime.utcnow(),
        "profile": {
            "bio": "Verified user for testing",
            "avatarUrl": None
        }
    }


@pytest.fixture
def unverified_user_data():
    """Fixture providing unverified user data for tests."""
    return {
        "_id": generate_user_id(),
        "email": UNVERIFIED_EMAIL,
        "firstName": "Unverified",
        "lastName": "User",
        "passwordHash": DEFAULT_PASSWORD_HASH,
        "emailVerified": False,
        "accountStatus": "pending",
        "createdAt": datetime.utcnow(),
        "lastLogin": None,
        "verificationToken": str(uuid.uuid4()),
        "verificationTokenExpiry": datetime.utcnow() + timedelta(days=1),
        "profile": {
            "bio": "Unverified user for testing",
            "avatarUrl": None
        }
    }


@pytest.fixture
def admin_user_data():
    """Fixture providing admin user data for tests."""
    return {
        "_id": generate_user_id(),
        "email": ADMIN_EMAIL,
        "firstName": "Admin",
        "lastName": "User",
        "passwordHash": DEFAULT_PASSWORD_HASH,
        "emailVerified": True,
        "accountStatus": "active",
        "role": "admin",
        "createdAt": datetime.utcnow(),
        "lastLogin": datetime.utcnow(),
        "profile": {
            "bio": "Admin user for testing",
            "avatarUrl": None
        }
    }


@pytest.fixture
def anonymous_user_data():
    """Fixture providing anonymous user data for tests."""
    created_at = datetime.utcnow()
    return {
        "_id": generate_user_id(),
        "isAnonymous": True,
        "sessionId": generate_session_id(),
        "createdAt": created_at,
        "expiresAt": created_at + timedelta(hours=24)
    }


@pytest.fixture
def user_with_reset_token(regular_user_data):
    """Fixture providing user data with password reset token."""
    user = dict(regular_user_data)  # Create a copy to avoid modifying the original
    user.update({
        "resetToken": str(uuid.uuid4()),
        "resetTokenExpiry": datetime.utcnow() + timedelta(hours=1)
    })
    return user


@pytest.fixture
def user_with_preferences(regular_user_data):
    """Fixture providing user data with custom preferences."""
    user = dict(regular_user_data)  # Create a copy to avoid modifying the original
    user.update({
        "preferences": {
            "theme": "dark",
            "fontSize": 14,
            "defaultPromptCategories": ["professional", "grammar", "concise"],
            "notificationSettings": {
                "emailNotifications": True,
                "documentUpdates": True,
                "marketingEmails": False
            },
            "privacySettings": {
                "shareUsageData": True,
                "storeHistory": True
            }
        }
    })
    return user


@pytest.fixture
def user_list():
    """Fixture providing a list of multiple users for pagination tests."""
    users = []
    for i in range(10):
        user = {
            "_id": generate_user_id(),
            "email": f"user{i}@example.com",
            "firstName": f"Test{i}",
            "lastName": "User",
            "passwordHash": DEFAULT_PASSWORD_HASH,
            "emailVerified": i % 2 == 0,  # alternate between verified and unverified
            "accountStatus": "active" if i % 2 == 0 else "pending",
            "createdAt": datetime.utcnow() - timedelta(days=i),
            "lastLogin": datetime.utcnow() - timedelta(days=i) if i % 2 == 0 else None
        }
        users.append(user)
    return users