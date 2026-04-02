"""
Caching service for reducing external API calls.
Implements in-memory caching with TTL support.
"""
import asyncio
from typing import Any, Callable, Dict, Optional
from datetime import datetime, timedelta
import hashlib
import json


class CacheService:
    """
    In-memory cache with TTL support.
    Can be extended to use Redis for distributed caching.
    """
    
    def __init__(self, default_ttl: int = 3600):
        """
        Initialize cache service.
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 1 hour)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self._lock = asyncio.Lock()
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate cache key from arguments.
        
        Args:
            prefix: Key prefix (e.g., 'github:repo')
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Cache key string
        """
        # Create deterministic key from arguments
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        async with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            
            # Check if expired
            if datetime.utcnow() > entry['expires_at']:
                del self._cache[key]
                return None
            
            return entry['value']
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        async with self._lock:
            expires_at = datetime.utcnow() + timedelta(
                seconds=ttl if ttl is not None else self.default_ttl
            )
            
            self._cache[key] = {
                'value': value,
                'expires_at': expires_at,
                'created_at': datetime.utcnow()
            }
    
    async def delete(self, key: str):
        """Delete value from cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    async def clear(self):
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
    
    async def get_or_fetch(
        self,
        key: str,
        fetch_func: Callable,
        ttl: Optional[int] = None
    ) -> Any:
        """
        Get value from cache or fetch if not present.
        
        Args:
            key: Cache key
            fetch_func: Async function to call if cache miss
            ttl: Time-to-live in seconds
            
        Returns:
            Cached or fetched value
        """
        # Try cache first
        cached_value = await self.get(key)
        if cached_value is not None:
            return cached_value
        
        # Cache miss - fetch and store
        value = await fetch_func()
        await self.set(key, value, ttl)
        return value
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        return {
            'total_entries': len(self._cache),
            'size_bytes': sum(
                len(json.dumps(entry['value'])) 
                for entry in self._cache.values()
            )
        }


# Global cache instance
_cache_instance: Optional[CacheService] = None


def get_cache() -> CacheService:
    """
    Get global cache instance.
    
    Returns:
        CacheService instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheService()
    return _cache_instance
