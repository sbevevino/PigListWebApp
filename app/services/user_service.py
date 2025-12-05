"""
User service for business logic and database operations.

This service layer separates business logic from API routes, making code more maintainable and testable.
All user-related database operations go through this service.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from app.core.exceptions import NotFoundError, ConflictError, UnauthorizedError

async def get_user_by_id(
        db: AsyncSession,
        user_id: int
) -> Optional[User]:
    """
    Retrieve user by ID.

    Args:
        db: Database session
        user_id: User's unique identifier

    Returns:
        User object if found, None otherwise
    """
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def get_user_by_email(
        db: AsyncSession,
        email: str
) -> Optional[User]:
    """
    Retrieve user by email address.

    Used during login and registraction to check if email exists.
    Email lookups are fast due to database index.

    Args:
        db: Database session
        email: User's email address

    Returns:
        User object if found, None otherwise
    """
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def create_user(
        db: AsyncSession,
        user_data: UserCreate
) -> User:
    """
    Create a new user account.

    Validates email uniqueness and creates user with hashed password.
    Only place where new users are created.

    Args:
        db: Database session
        user_data: Validated user creation data from Pydantic schema

    Returns:
        Created user object
    
    Raises:
        ConflictError: If email already exists in database

    Security:
        - Password is hashed before storage
        - Email uniqueness enforced at both app and database level
        - Display name is stripped of whitespace

    Note:
        - User is automatically set to active status
        - created_at timestamp is set automatically
        - last_login is null until first login
    """
    # Check if email already exists
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        raise ConflictError(f"User with email {user_data.email} already exists")
    
    # Create new user with hashed password
    db_user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),  # Hash password
        display_name=user_data.display_name.strip(),  # Remove extra whitespace
        is_active=True,
        created_at=datetime.utcnow(),
    )
    
    # Add to database and commit
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user) # Refresh to get generated ID

    return db_user

async def authenticate_user(
        db: AsyncSession,
        email: str,
        password: str
) -> User:
    """
    Authentic user with email and password.

    Verifies credentials and updates last_log timestamp.
    This is the only place where authentication happens.

    Args:
        db: Database session
        email: User's email address
        password: Plain text password from login form

    Returns:
        Authenticated user object

    Raises:
        UnauthorizedError: If credentials are invalid or account is inactive
    
    Security:
        - Uses constant-time password comparison (via bcrypt)
        - Doesn't reveal whether email or password was wrong
        - Checks account active status
        - Updated last_login for audit trail

    Note:
        - Generic error message prevents user enumeration
        - last_login updated on successful authentication
    """
    # Look up user by email
    user = await get_user_by_email(db, email)

    # Check if user exists
    if not user:
        # Generic error message
        raise UnauthorizedError("Invalid email or password")
    
    # Verify password using constant-time comparison
    if not verify_password(password, user.password_hash):
        # Same generic error message
        raise UnauthorizedError("Invalid email or password")
    
    # Check if account is active
    if not user.is_active:
        raise UnauthorizedError("User account is inactive")
    
    # Update last login timestamp for audit trail
    user.last_login = datetime.utcnow()
    await db.commit()

    return user

async def update_user(
        db: AsyncSession,
        user_id: int,
        user_data: UserUpdate
) -> User:
    """
    Update user profile information.

    Currently supports updating display_name. Can be extended to support other profile fields in the future.

    Args:
        db: Database session
        user_id: ID of user to update
        user_data: Validated update data from Pydantic schema

    Returns:
        Updated user object

    Raises:
        NotFoundError: If user with given ID doesn't exist
    """
    # Get user from database
    user = await get_user_by_id(db, user_id)

    if not user:
        raise NotFoundError(f"User with ID {user_id} not found")
    
    # Update fields if provided (partial update support)
    if user_data.display_name is not None:
        user.display_name = user_data.display_name.strip()

    # Commit changes and refresh
    await db.commit()
    await db.refresh(user)

    return user