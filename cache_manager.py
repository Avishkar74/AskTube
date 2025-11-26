"""
Simple file-based caching system for transcripts and generated outputs.

Caches are stored as JSON files in a cache directory with TTL (time-to-live).
"""
import json
import hashlib
import time
from pathlib import Path
from typing import Optional, Any, Dict


class CacheManager:
    """File-based cache manager with TTL support."""

    def __init__(self, cache_dir: str = "cache", default_ttl: int = 86400):
        """Initialize cache manager.

        Args:
            cache_dir: Directory to store cache files
            default_ttl: Default time-to-live in seconds (default: 24 hours)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = default_ttl

    def _get_cache_key(self, key: str) -> str:
        """Generate a hash-based cache key from input string."""
        return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]

    def _get_cache_path(self, key: str, namespace: str = "default") -> Path:
        """Get the file path for a cache key."""
        cache_key = self._get_cache_key(key)
        namespace_dir = self.cache_dir / namespace
        namespace_dir.mkdir(parents=True, exist_ok=True)
        return namespace_dir / f"{cache_key}.json"

    def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """Retrieve cached value if it exists and hasn't expired.

        Args:
            key: Cache key (will be hashed)
            namespace: Namespace for organizing caches

        Returns:
            Cached value if found and valid, None otherwise
        """
        cache_path = self._get_cache_path(key, namespace)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            # Check expiration
            if cache_data.get("expires_at", 0) < time.time():
                # Cache expired, delete it
                cache_path.unlink(missing_ok=True)
                return None

            return cache_data.get("value")

        except (json.JSONDecodeError, KeyError, IOError):
            # Corrupted cache, delete it
            cache_path.unlink(missing_ok=True)
            return None

    def set(
        self,
        key: str,
        value: Any,
        namespace: str = "default",
        ttl: Optional[int] = None,
    ) -> None:
        """Store value in cache.

        Args:
            key: Cache key (will be hashed)
            value: Value to cache (must be JSON serializable)
            namespace: Namespace for organizing caches
            ttl: Time-to-live in seconds (None = use default)
        """
        cache_path = self._get_cache_path(key, namespace)
        ttl = ttl if ttl is not None else self.default_ttl

        cache_data = {
            "key": key,
            "value": value,
            "cached_at": time.time(),
            "expires_at": time.time() + ttl,
        }

        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except (IOError, TypeError) as e:
            print(f"Warning: Failed to cache value for key '{key[:30]}...': {e}")

    def delete(self, key: str, namespace: str = "default") -> bool:
        """Delete a cached value.

        Args:
            key: Cache key
            namespace: Namespace

        Returns:
            True if cache was deleted, False if it didn't exist
        """
        cache_path = self._get_cache_path(key, namespace)
        if cache_path.exists():
            cache_path.unlink()
            return True
        return False

    def clear_namespace(self, namespace: str = "default") -> int:
        """Clear all caches in a namespace.

        Args:
            namespace: Namespace to clear

        Returns:
            Number of cache files deleted
        """
        namespace_dir = self.cache_dir / namespace
        if not namespace_dir.exists():
            return 0

        count = 0
        for cache_file in namespace_dir.glob("*.json"):
            cache_file.unlink()
            count += 1

        return count

    def clear_expired(self, namespace: Optional[str] = None) -> int:
        """Remove all expired caches.

        Args:
            namespace: If specified, only clear from this namespace.
                      If None, clear from all namespaces.

        Returns:
            Number of expired cache files deleted
        """
        count = 0
        current_time = time.time()

        if namespace:
            namespaces = [self.cache_dir / namespace]
        else:
            namespaces = [d for d in self.cache_dir.iterdir() if d.is_dir()]

        for ns_dir in namespaces:
            if not ns_dir.exists():
                continue

            for cache_file in ns_dir.glob("*.json"):
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        cache_data = json.load(f)

                    if cache_data.get("expires_at", 0) < current_time:
                        cache_file.unlink()
                        count += 1

                except (json.JSONDecodeError, KeyError, IOError):
                    # Corrupted cache, delete it
                    cache_file.unlink()
                    count += 1

        return count

    def get_stats(self, namespace: str = "default") -> Dict[str, Any]:
        """Get cache statistics for a namespace.

        Args:
            namespace: Namespace to get stats for

        Returns:
            Dictionary with cache statistics
        """
        namespace_dir = self.cache_dir / namespace
        if not namespace_dir.exists():
            return {"total": 0, "valid": 0, "expired": 0, "corrupted": 0}

        total = 0
        valid = 0
        expired = 0
        corrupted = 0
        current_time = time.time()

        for cache_file in namespace_dir.glob("*.json"):
            total += 1
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)

                if cache_data.get("expires_at", 0) < current_time:
                    expired += 1
                else:
                    valid += 1

            except (json.JSONDecodeError, KeyError, IOError):
                corrupted += 1

        return {
            "total": total,
            "valid": valid,
            "expired": expired,
            "corrupted": corrupted,
        }


# Convenience functions for common use cases

def get_transcript_cache() -> CacheManager:
    """Get cache manager for transcripts with 7-day TTL."""
    return CacheManager(cache_dir="cache/transcripts", default_ttl=604800)  # 7 days


def get_output_cache() -> CacheManager:
    """Get cache manager for generated outputs with 24-hour TTL."""
    return CacheManager(cache_dir="cache/outputs", default_ttl=86400)  # 24 hours


if __name__ == "__main__":
    # Simple test/demo
    cache = CacheManager(cache_dir="cache/test")

    # Test set and get
    print("Testing cache...")
    cache.set("test_key", {"data": "Hello World"}, ttl=60)
    result = cache.get("test_key")
    print(f"Cached value: {result}")

    # Test stats
    stats = cache.get_stats()
    print(f"Cache stats: {stats}")

    # Cleanup
    cache.clear_namespace()
    print("Cache cleared")
