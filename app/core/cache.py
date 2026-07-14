"""Thread-safe, asynchronous LRU cache with Cryptographic Jitter.

This module provides a caching mechanism for storing tenant policies and
API keys. It uses an OrderedDict for O(1) eviction of oldest entries
and implements a jittered TTL to prevent thundering herd scenarios.
"""

import asyncio
import secrets
import time
from collections import OrderedDict
from typing import Any, Generic, TypeVar

T = TypeVar("T")

class TenantCache(Generic[T]):
    """Asynchronous, thread-safe LRU cache with jittered TTL."""

    def __init__(self, maxsize: int = 1000):
        self.maxsize = maxsize
        self._cache: OrderedDict[str, tuple[T, float]] = OrderedDict()
        self._lock = asyncio.Lock()

    def _generate_jittered_ttl(self) -> float:
        """Generate a random TTL between 3600 and 5400 seconds."""
        # 3600 seconds = 1 hour, 5400 seconds = 1.5 hours
        jitter = secrets.randbelow(1801)  # 0 to 1800
        return float(3600 + jitter)

    async def get(self, key: str) -> T | None:
        """Retrieve an item from the cache, respecting its TTL."""
        async with self._lock:
            if key not in self._cache:
                return None
            
            value, expiry = self._cache[key]
            
            if time.time() > expiry:
                # Expired
                del self._cache[key]
                return None
            
            # Move to end to mark as most recently used
            self._cache.move_to_end(key)
            return value

    async def set(self, key: str, value: T) -> None:
        """Insert or update an item in the cache with a new jittered TTL."""
        async with self._lock:
            ttl = self._generate_jittered_ttl()
            expiry = time.time() + ttl
            
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = (value, expiry)
            
            # Enforce maxsize (evict least recently used, which is at the beginning)
            if len(self._cache) > self.maxsize:
                self._cache.popitem(last=False)
