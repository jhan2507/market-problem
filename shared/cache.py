"""
Redis caching utilities.
"""

import json
import logging
from typing import Any, Optional
from datetime import timedelta
from shared.events import get_redis_client

logger = logging.getLogger(__name__)


class Cache:
    """Redis-based cache."""
    
    def __init__(self, key_prefix: str = "cache"):
        self.redis = get_redis_client()
        self.key_prefix = key_prefix
    
    def _make_key(self, key: str) -> str:
        """Make full cache key."""
        return f"{self.key_prefix}:{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None
        """
        try:
            full_key = self._make_key(key)
            value = self.redis.get(full_key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        try:
            full_key = self._make_key(key)
            self.redis.setex(
                full_key,
                ttl,
                json.dumps(value)
            )
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
    
    def delete(self, key: str):
        """Delete cache key."""
        try:
            full_key = self._make_key(key)
            self.redis.delete(full_key)
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
    
    def clear(self, pattern: str = None):
        """
        Clear cache keys.
        
        Args:
            pattern: Optional pattern to match keys
        """
        try:
            if pattern:
                full_pattern = self._make_key(pattern)
                keys = self.redis.keys(full_pattern)
            else:
                keys = self.redis.keys(f"{self.key_prefix}:*")
            
            if keys:
                self.redis.delete(*keys)
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            full_key = self._make_key(key)
            return self.redis.exists(full_key) > 0
        except Exception as e:
            logger.error(f"Error checking cache key {key}: {e}")
            return False


# Global cache instance
_cache: Optional[Cache] = None


def get_cache(key_prefix: str = "cache") -> Cache:
    """Get global cache instance."""
    global _cache
    if _cache is None:
        _cache = Cache(key_prefix)
    return _cache

