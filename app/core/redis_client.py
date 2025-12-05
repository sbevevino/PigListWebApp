"""
Redis client for session management and caching.

This module provides async Redis operations for storing user sessions, enabling token revocation and session tracking.
Redis is used for its speed and built-in TTL (time-to-live) functionality.
"""

from typing import Optional
import redis.asyncio as redis

from app.core.config import settings

# Global Redis client instance (singleton pattern)
# Reusing connections improves performance
_redis_client: Optional[redis.Redis] = None

async def get_redis_client() -> redis.Redis:
    """
    Get or create Redis client instance (singleton pattern).

    Creates a single Redis connection that's reused across requests for better performance.
    Connection is created lazily on first use.

    Returns:
        Redis client instance

    Connection Settings:
        - encoding: UTF-8 for string operations
        - decode_responses: Automatically decode bytes to strings
        - Connection pooling handled automatically by redis-py
    """
    global _redis_client

    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True # Auto-decode bytes to strings
        )
    
    return _redis_client

async def close_redis_client() -> None:
    """
    Close Redis client connection.

    Should be called during application shutdown to cleanly close connections and release resources.
    """
    global _redis_client

    if _redis_client:
        await _redis_client.close()
        _redis_client = None

async def set_session(
        session_id: str,
        user_id: int,
        expire_seconds: int = 2592000 # 30 days default
) -> bool:
    """
    Store user session in Redis with automatic expiration.

    Sessions are stored with TTL (time-to-live) for automatic cleanup.
    This enables token revocation and session tracking without manual cleanup jobs.

    Args:
        session_id: Unique session identifier (from generate_session_id)
        user_id: User ID to associate with this session
        expire_seconds: Session expiration time (default 30 days)

    Returns:
        True if session was stored successfully
    
    Redis Key Format:
        session:{session_id} -> user_id
    """
    client = await get_redis_client()
    key = f"session:{session_id}"

    # Store user_id with automatic expiration
    await client.setex(
        key,
        expire_seconds,
        str(user_id) # Store as string for consistency
    )

    return True

async def get_session(session_id: str) -> Optional[int]:
    """
    Retrieve user ID from session.

    Checks if session exists and is not expired.
    Returns None if session doesn't exist or has expired (Redis auto-deletes).

    Args:
        session_id: Session identifier to look up

    Returns:
        User ID if session exists and is valid, None otherwise
    
    Note:
        - Returns None if session expired (Redis auto-deleted it)
        - Returns None if session never existed
        - No way to distinguish between expired and non-existent
    """
    client = await get_redis_client()
    key = f"session:{session_id}"

    user_id = await client.get(key)

    # Convert string back to int, or return None if not found
    return int(user_id) if user_id else None

async def delete_session(session_id: str) -> bool:
    """
    Delete a session from Redis (logout).

    Removes session immediately, effectively revoking the associated tokens.
    Client should also discard tokens on logout.

    Args:
        session_id: Session identifier to delete

    Returns:
        True if session was deleted, False if it didn't exist
    """
    client = await get_redis_client()
    key = f"session:{session_id}"

    # Delete returns number of keys deleted (0 or 1)
    result = await client.delete(key)

    return result > 0

async def refresh_session(
        session_id: str,
        expire_seconds: int = 2592000 # 30 days default
) -> bool:
    """
    Refresh session expiration time (extend session).

    Updates the TTL on an existing session without changing the stored data.
    Useful for "remember me" functionality

    Args:
        session_id: Session identifier to refresh
        expire_seconds: New expiration time (default 30 days)

    Returns:
        True if session was refreshed, False if session doesn't exist
    """
    client = await get_redis_client()
    key = f"session:{session_id}"

    # Update expiration time
    result = await client.expire(key, expire_seconds)

    return bool(result)