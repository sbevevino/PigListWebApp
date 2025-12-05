"""
Pydantic schemas for user-related operations.

These schemas handle request validation, response, serialization, and enforce business rules for user data.
They provide automatic validation and clear API documentation.
"""

from datetime import datetime
from typing import Optional
import re

from pydantic import BaseModel, EmailStr, Field, field_validator

class UserBase(BaseModel):
    """
    Base user schema with common fields.

    This base class is inherited by other schemas to follow DRY principles.
    Contains fields that are common across multiple operations.
    """

    email: EmailStr # Pydantic validates email format automatically
    display_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User's display name"
    )

class UserCreate(UserBase):
    """
    Schema for user registration requests.

    Extends UserBase with password field and validation.
    """

    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password must be 8+ characters and contain an uppercase, lowercase, and number"
    )

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        """
        Validate password meets security requirements

        Requirements:
        - At least 8 characters
        - At least 1 uppercase letter
        - At least 1 lowercase letter
        - At least 1 number

        Args:
            value: Password to validate

        Returns:
            Validated password

        Raises:
            ValueError: If password doesn't meet requirements
        """
        min_length = 8

        if len(value) < min_length:
            raise ValueError(f'Password must be at least {min_length} characters long')

        if not re.search(r'[A-Z]', value):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not re.search(r'[a-z]', value):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not re.search(r'\d', value):
            raise ValueError('Password must contain at least one number')
        
        return value
    
    @field_validator('display_name')
    @classmethod
    def validate_display_name_not_empty(cls, value: str) -> str:
        """
        Ensure display name is not empty after stripping whitespace.

        Args:
            value: Display name to validate

        Returns:
            Stripped display name

        Raises:
            ValueError: If display name is empty after stripping
        """
        value = value.strip()
        if not value:
            raise ValueError('Display name cannot be blank')
        return value

class UserUpdate(BaseModel):
    """
    Schema for updating user profile.

    All fields are optional to allow for partial updates.
    """

    display_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="New display name (optional)"
    )

    @field_validator('display_name')
    @classmethod
    def validate_display_name_if_provided(cls, value: Optional[str]) -> Optional[str]:
        """
        Validate display name if provided in update request.

        Args:
            value: Display name to validate (can be None)

        Returns:
            Validated display name or None
        
        Raises:
            ValueError: If provided display name is empty
        """
        if value is not None:
            value = value.strip()
            if not value:
                raise ValueError('Display name cannot be blank')
        return value

class UserResponse(UserBase):
    """
    Schema for user data in API responses.

    Excludes sensitive data (password_hash) and includes all safe user information.
    Used for profile endpoints.
    """

    id: int # User's unique identifier
    is_active: bool # Account status
    created_at: datetime # Registration timestamp
    last_login: Optional[datetime] = None # Most recent login (can be null)

    class Config:
        """
        Pydantic configuration for ORM compatibility.
        """
        from_attributes = True # Allow creation from SQLAlchemy models

class UserLogin(BaseModel):
    """
    Schema for login requests.

    Simple email/password combination for authentication.
    """

    email: EmailStr
    password: str # No validation here - checked against hash

class Token(BaseModel):
    """
    Schema for authentication token responses.

    Returns both access and refresh tokens following OAuth2 patterns.
    """

    access_token: str # Short-lived token for API requests (4 hours)
    refresh_token: str # Long-lived token for getting new access tokens (30 days)
    token_type: str = "bearer" # OAuth2 token type

class TokenData(BaseModel):
    """
    Schema for decoded token payload data.

    Used internally for token validation and user identification.
    """

    user_id: Optional[int] = None # Extracted from token 'sub' claim
    email: Optional[str] = None # User's email for additional context

class RefreshTokenRequest(BaseModel):
    """
    Schema for token refresh requests.

    Client sends refresh token to get new access token.
    """

    refresh_token: str