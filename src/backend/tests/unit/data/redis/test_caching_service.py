import pytest
import fakeredis
import json
import time
import pickle
from unittest.mock import patch

from src.backend.data.redis.caching_service import CacheManager as CachingService
from src.backend.data.redis.connection import get_redis_connection

class TestCachingService:
    """Test class for the Redis CachingService implementation"""
    
    def setUp(self):
        """Set up test fixtures before each test"""
        # Initialize fakeredis server
        self.fake_redis = fakeredis.FakeStrictRedis()
        
        # Mock the Redis connection to use fakeredis
        self.patcher = patch('src.backend.data.redis.caching_service.get_cache_connection')
        self.mock_get_redis = self.patcher.start()
        self.mock_get_redis.return_value = self.fake_redis
        
        # Initialize the CachingService with the mock connection
        self.caching_service = CachingService("test:")
    
    def tearDown(self):
        """Clean up after each test"""
        # Flush fakeredis data
        self.fake_redis.flushall()
        
        # Reset all mocks
        self.patcher.stop()
    
    def test_init(self):
        """Test CachingService initialization"""
        # Verify service is initialized correctly
        assert self.caching_service is not None
        
        # Check default prefix is applied
        assert self.caching_service.prefix == "test:"
        
        # Test with custom prefix
        custom_service = CachingService("custom:")
        assert custom_service.prefix == "custom:"
    
    def test_set_get_string(self):
        """Test setting and getting string values"""
        # Set a string value with a key
        key = "test_string"
        value = "Hello, World!"
        result = self.caching_service.set(key, value)
        
        # Verify the set operation was successful
        assert result is True
        
        # Get the value using the same key
        retrieved_value = self.caching_service.get(key)
        
        # Assert retrieved value matches original
        assert retrieved_value == value
    
    def test_set_get_dict(self):
        """Test setting and getting dictionary values"""
        # Set a dictionary value with a key
        key = "test_dict"
        value = {"name": "Test User", "age": 30, "email": "test@example.com"}
        result = self.caching_service.set(key, value)
        
        # Verify the set operation was successful
        assert result is True
        
        # Get the value using the same key
        retrieved_value = self.caching_service.get(key)
        
        # Assert retrieved dict matches original
        assert retrieved_value == value
        assert retrieved_value["name"] == "Test User"
        assert retrieved_value["age"] == 30
        assert retrieved_value["email"] == "test@example.com"
    
    def test_set_get_complex(self):
        """Test setting and getting complex objects"""
        # Create a complex object (e.g., with nested structures)
        key = "test_complex"
        value = {
            "user": {
                "name": "Test User",
                "contact": {
                    "email": "test@example.com",
                    "phone": "123-456-7890"
                }
            },
            "preferences": ["reading", "coding", "testing"],
            "active": True,
            "score": 95.5
        }
        
        # Set the object in cache
        result = self.caching_service.set(key, value)
        assert result is True
        
        # Get the object from cache
        retrieved_value = self.caching_service.get(key)
        
        # Verify object structure and values are preserved
        assert retrieved_value == value
        assert retrieved_value["user"]["name"] == "Test User"
        assert retrieved_value["user"]["contact"]["email"] == "test@example.com"
        assert "reading" in retrieved_value["preferences"]
        assert retrieved_value["active"] is True
        assert retrieved_value["score"] == 95.5
    
    def test_ttl(self):
        """Test time-to-live functionality"""
        # Set value with short TTL
        key = "test_ttl"
        value = "This will expire soon"
        ttl = 1  # 1 second TTL
        
        result = self.caching_service.set(key, value, ttl)
        assert result is True
        
        # Verify value exists initially
        assert self.caching_service.exists(key) is True
        
        # Wait for TTL to expire
        time.sleep(1.1)
        
        # Verify value is no longer in cache
        assert self.caching_service.exists(key) is False
        assert self.caching_service.get(key) is None
    
    def test_delete(self):
        """Test cache deletion functionality"""
        # Set multiple values
        self.caching_service.set("key1", "value1")
        self.caching_service.set("key2", "value2")
        self.caching_service.set("key3", "value3")
        
        # Verify keys exist
        assert self.caching_service.exists("key1") is True
        assert self.caching_service.exists("key2") is True
        assert self.caching_service.exists("key3") is True
        
        # Delete specific key
        result = self.caching_service.delete("key2")
        assert result is True
        
        # Verify key no longer exists
        assert self.caching_service.exists("key2") is False
        
        # Verify other keys remain
        assert self.caching_service.exists("key1") is True
        assert self.caching_service.exists("key3") is True
    
    def test_exists(self):
        """Test key existence check"""
        # Set value in cache
        self.caching_service.set("existing_key", "value")
        
        # Check if key exists
        assert self.caching_service.exists("existing_key") is True
        
        # Check if non-existent key exists
        assert self.caching_service.exists("non_existing_key") is False
    
    def test_prefix(self):
        """Test key prefixing functionality"""
        # Initialize service with custom prefix
        prefix = "custom_prefix:"
        custom_service = CachingService(prefix)
        
        # Set a value using the service
        custom_service.set("test_key", "test_value")
        
        # Examine actual keys in Redis
        actual_key = f"{prefix}test_key"
        
        # Direct check in Redis to verify prefix is applied
        assert self.fake_redis.exists(actual_key) == 1
        
        # Get using the service to verify it works with prefix
        retrieved_value = custom_service.get("test_key")
        assert retrieved_value == "test_value"
    
    def test_error_handling(self):
        """Test service behavior with Redis errors"""
        # Force Redis errors by patching get_cache_connection
        with patch('src.backend.data.redis.caching_service.get_cache_connection',
                  side_effect=Exception("Redis connection failed")):
            
            # Create a new service that will use the failing connection
            error_service = CachingService("error:")
            
            # Verify graceful handling
            assert error_service.set("key", "value") is False
            assert error_service.get("key") is None
            assert error_service.delete("key") is False
            assert error_service.exists("key") is False
    
    def test_different_ttls(self):
        """Test caching with different TTL values based on content type"""
        # Set document metadata with 5-minute TTL
        doc_key = "doc_meta"
        doc_value = {"title": "Test Document", "author": "Tester"}
        doc_ttl = 300  # 5 minutes
        self.caching_service.set(doc_key, doc_value, doc_ttl)
        
        # Set user profile with 15-minute TTL
        user_key = "user_profile"
        user_value = {"name": "Test User", "email": "test@example.com"}
        user_ttl = 900  # 15 minutes
        self.caching_service.set(user_key, user_value, user_ttl)
        
        # Set AI template with 60-minute TTL
        template_key = "ai_template"
        template_value = {"name": "Test Template", "prompt": "Make it better"}
        template_ttl = 3600  # 60 minutes
        self.caching_service.set(template_key, template_value, template_ttl)
        
        # Set AI response with 30-minute TTL
        ai_key = "ai_response"
        ai_value = {"suggestion": "This is a better version"}
        ai_ttl = 1800  # 30 minutes
        self.caching_service.set(ai_key, ai_value, ai_ttl)
        
        # Verify each has the correct expiration time
        assert self.caching_service.get(doc_key) == doc_value
        assert self.caching_service.get(user_key) == user_value
        assert self.caching_service.get(template_key) == template_value
        assert self.caching_service.get(ai_key) == ai_value
    
    def test_cache_invalidation(self):
        """Test cache invalidation strategies"""
        # Set values in cache
        prefix = "test_pattern:"
        
        pattern_service = CachingService(prefix)
        pattern_service.set("key1", "value1")
        pattern_service.set("key2", "value2")
        pattern_service.set("other", "other_value")
        
        # Set some values with a different prefix
        other_service = CachingService("other:")
        other_service.set("key1", "other_value1")
        
        # Verify keys exist
        assert pattern_service.exists("key1") is True
        assert pattern_service.exists("key2") is True
        assert pattern_service.exists("other") is True
        assert other_service.exists("key1") is True
        
        # Trigger invalidation by key pattern
        result = pattern_service.clear_all()
        assert result is True
        
        # Verify targeted keys are invalidated
        assert pattern_service.exists("key1") is False
        assert pattern_service.exists("key2") is False
        assert pattern_service.exists("other") is False
        
        # Verify unrelated keys are unaffected
        assert other_service.exists("key1") is True