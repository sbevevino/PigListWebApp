"""
User profile management endpoints.

This module provides endpoints for viewing and updating user profiles.
All endpoints require authentication and operate on the current user's data.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.schemas.user import UserResponse, UserUpdate
from app.services import user_service
from app.api.dependencies import get_current_user
from app.models.user import User
from app.core.exceptions import NotFoundError
from app.core.logging import logger

# Create router with prefix and tags
router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Retrieve the authenticated user's profile information."
)
async def get_current_user_profile(current_user: User = Depends(get_current_user)) -> UserResponse:
    """
    Get current user's profile.

    Returns the authenticated user's profile information excluding sensitive data like password hash.
    This endpoint is useful for displaying user info in the UI.

    Args:
        current_user: Current authenticated user (injected dependency)

    Returns:
        UserResponse with profile information

    Security:
        - Requires valid access token
        - Only returns current user's data (no access to other users)
        - Password hash excluded from response
    
    Example Request:
        GET /api/users/me
        Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...

    Example Response:
        {
            "id": 1,
            "email": "user@example.com",
            "display_name": "John Doe",
            "is_active": true,
            "created_at": "2024-01-01T00:00:00",
            "last_login": "2024-01-02T12:00:00"
        }
    """
    logger.info(
        "User profile retrieved",
        extra={"user_id": current_user.id}
    )

    return current_user

@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
    description="Update the authenticated user's profile information."
)
async def update_current_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Update current user's profile.

    Allows users to update their profile information. Currently supports updating display_name.

    Args:
        user_data: Update data (only provided fields are updated)
        current_user: Current authenticated user (injected dependency)
        db: Database session (injected dependency)

    Returns:
        Updated user profile

    Raises:
        HTTPException 404: If user not found
        HTTPException 422: If validation fails - FastAPI automatically validates requst data against UserUpdate schema

    Security:
        - Requires valid access token
        - Users can only update their own profile
        - Validation applied via Pydantic schema

    Example Request:
        PUT /api/users/me
        Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
        {
            "display_name": "Jane Doe"
        }
        
    Example Response:
        {
            "id": 1,
            "email": "user@example.com",
            "display_name": "Jane Doe",
            "is_active": true,
            "created_at": "2024-01-01T00:00:00",
            "last_login": "2024-01-02T12:00:00"
        }
    """
    try:
        # Update user profile
        updated_user = await user_service.update_user(
            db,
            current_user.id,
            user_data
        )

        logger.info(
            "User profile updated",
            extra={
                "user_id": current_user.id,
                "updated_fields": [field for field, value in user_data.dict(exclude_unset=True).items()]
            }
        )

        return updated_user
    
    except NotFoundError as e:
        # Shouldn't happen with valid token, included to handle gracefully
        logger.error(
            "Profile update failed - user not found",
            extra={"user_id": current_user.id}
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    except Exception as e:
        # Unexpected error
        logger.error(
            "Profile update failed with unexpected error",
            extra={
                "user_id": current_user.id,
                "error": str(e)
            }
        )
        raise