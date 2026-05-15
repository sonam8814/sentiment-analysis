"""Disk cache wrapper for LLM responses.

Keys are SHA-256 hashes of (prompt_version + comment) to ensure
cache invalidation on prompt changes.
"""

import hashlib
from typing import Any

import diskcache
from loguru import logger

from src.ai.prompts import PROMPT_VERSION

_cache_instance: diskcache.Cache | None = None


def get_cache(cache_dir: str, expiry_days: int) -> diskcache.Cache:
    """Return a singleton diskcache.Cache instance.

    Args:
        cache_dir: Path to the cache directory.
        expiry_days: TTL for cache entries in days.

    Returns:
        Configured diskcache.Cache instance.
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = diskcache.Cache(cache_dir)
        logger.info(f"Disk cache initialized at {cache_dir}")
    return _cache_instance


def make_cache_key(comment: str) -> str:
    """Generate a deterministic cache key from prompt version and comment.

    Args:
        comment: The PII-redacted comment text.

    Returns:
        SHA-256 hex digest string.
    """
    raw = f"{PROMPT_VERSION}:{comment}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get_cached(cache: diskcache.Cache, comment: str) -> dict[str, Any] | None:
    """Look up a cached ABSA result for a comment.

    Args:
        cache: The diskcache instance.
        comment: The PII-redacted comment text.

    Returns:
        Cached result dict, or None if not found.
    """
    key = make_cache_key(comment)
    result = cache.get(key)
    if result is not None:
        logger.debug(f"Cache HIT for key={key[:12]}...")
    else:
        logger.debug(f"Cache MISS for key={key[:12]}...")
    return result


def set_cached(
    cache: diskcache.Cache,
    comment: str,
    result: dict[str, Any],
    expiry_days: int,
) -> None:
    """Store an ABSA result in the cache.

    Args:
        cache: The diskcache instance.
        comment: The PII-redacted comment text.
        result: Parsed ABSA result dict to cache.
        expiry_days: TTL in days.
    """
    key = make_cache_key(comment)
    ttl_seconds = expiry_days * 86400
    cache.set(key, result, expire=ttl_seconds)
    logger.debug(f"Cache SET for key={key[:12]}... (TTL={expiry_days}d)")


def close_cache() -> None:
    """Close the cache instance and reset the singleton."""
    global _cache_instance
    if _cache_instance is not None:
        _cache_instance.close()
        _cache_instance = None
        logger.info("Disk cache closed")
