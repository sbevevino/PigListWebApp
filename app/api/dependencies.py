"""
FastAPI dependencies for authentication and authorization.

Dependencies are reusable components that can be injected into route handlers.
They handle authentication, authorization, and provide the current user to protected endpoints.
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.core.security import decode_token
from app.services import user_service
from app.models.user import User

# HTTP Bearer token scheme for Swagger UI
# Adds "Authorize" button to API documentation
security = HTTPBearer()

async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependence to get current authenticated user from JWT token.

    This dependency:
    1. Extracts Bearer token from Authorization header
    2. Decodes and validates JWT token
    3. Retrieves user from database
    4. Verifies user is active

    Use this dependency on any route that requires authentication.

    Args:
        credentials: HTTP Bearer credentials (auto-extracted from header)
        db: Database session (injected dependency)

    Returns:
        Current authenticated user object

    Raises:
        HTTPException 401: If token is invalid, expired, or user not found
        HTTPException 403: If user account is inactive

    Usage:
        @router.get("/protected")
        async def protected_route(user: User = Depends(get_current_user)):
            return {"user_id": user.id}

    Security:
        - Validates token signature and expiration
        - Checks token type (must be "access" token)
        - Verifies user still exists and is active
        - Generic error messages prevent information leakage
    """
    # Standard credentials exception for invalid tokens
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Extract and decode token
    token = credentials.credentials
    payload = decode_token(token)

    # Check if token is valid
    if payload is None:
        raise credentials_exception
    
    # Verify this is as access token (not refresh token)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user ID from token payload
    user_id: Optional[int] = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # Get user from database
    user = await user_service.get_user_by_id(db, int(user_id))
    if user is None:
        raise credentials_exception
    
    # Verify user account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency for routes that require an active user.

    This is a convenience dependency that adds an extra active status check.
    In practice, get_current_user already checks this, so this is mainly for explicit documentation.

    Args:
        current_user: Current user from get_current_user dependency

    Returns:
        Current active user
    
    Raises:
        HTTPException 403: If user is inactive

    Usage:
        @router.get("/admin")
        async def admin_route(user: User = Depends(get_current_active_user)):
            return {"admin": True}
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    return current_user