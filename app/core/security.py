"""
Security utilities for authentication and authorization

This module provides cryptographic functions for password hashing.
JWT token generation/validation, and session management.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets

from jose import JWTError, jwt
import bcrypt

from app.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    Uses constant-time comparison to prevent timing attacks.

    Args:
        plain_password: The plain text password from user input
        hashed_password: The bcrypt hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Bcrypt automatically generates a unique salt for each password, and includes it in the hash output.
    The default cost factor (12 rounds) provides good security while maintaining reasonable performance.

    Args:
        password: Plain text password to hash

    Returns:
        Bcrypt hashed password string (includes salt)
    """
    # Generate salt and hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token for API authentication.
    Access tokens are short-lived (4 hours by default) to limit exposure if compromised.
    They contain user identification and expiration time.

    Args:
        data: Dictionary of claims to encode in token (typically user_id, email)
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string

    Token Structure:
        - sub: User ID (subject)
        - email: User email
        - exp: Expiration timestamp
        - type: "access" (distinguishes from refresh token)
    """
    to_encode = data.copy()

    # Set expiration time (4 hours default)
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # Add standard JWT claims
    to_encode.update({
        "exp": expire, # Expiration time
        "type": "access" # Token type for validation
        })
    
    # Encode and sign token
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt

def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT refresh token for obtaining new access tokens.

    Refresh tokens are long-lived (30 days) and used to obtain new access tokens without re-authorization.
    They should be stored securely by the client.

    Args:
        data: Dictionary of claims to encode (typically just user_id)

    Returns:
        Encoded JWT refresh token string

    Token Structure:
        - sub: User ID
        - exp: Expiration timestamp (30 days)
        - type: "refresh" (distinguishes from access tokens)
    """
    to_encode = data.copy()

    # Set long expiration (30 days)
    expire = datetime.utcnow() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "type": "refresh" # Distinguish from access tokens
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify JWT access token.

    Validates token signature, expiration, and structure.
    Returns None if token is invalid rather than raising exception for easier error handling.

    Args:
        token: JWT token string to decode

    Returns:
        Decoded token payload dictionary or None if invalid
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        # Token is invalid, expired, or malformed
        # Return None rather than raising for cleaner error handling
        return None

def generate_session_id() -> str:
    """
    Generate a cryptographically secure random session ID.

    Used for Redis session keys to track active user sessions.
    Session ID is URL-safe and sufficiently random to prevent guessing attacks.

    Returns:
        Random session ID string (32 bytes = 43 characters base64)
    """
    return secrets.token_urlsafe(32)
