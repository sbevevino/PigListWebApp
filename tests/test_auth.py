"""
Tests for authentication endpoints.

This module tests user registration, login, token refresh, and logout functionality.
Tests cover both success and failure cases.
"""

import pytest
from httpx import AsyncClient

from app.models.user import User

@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """
    Test successful user registration.

    Verifies that:
    - Registration returns 201 Created
    - Reponse includes access_token and refresh_token
    - Token type is "bearer"
    """
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "NewPass123",
            "display_name": "New User"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

    # Verify tokens are non-empty strings
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0
    assert isinstance(data["refresh_token"], str)
    assert len(data["refresh_token"]) > 0

@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user: User):
    """
    Test registration with duplicate email fails.

    Verifies that:
    - Attempting to register with existing email returns 400
    - Error message indicates email already exists
    """
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "testuser@example.com", # Already exists from test_user fixture
            "password": "TestPass123",
            "display_name": "Another User"
        }
    )

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_register_weak_password_too_short(client: AsyncClient):
    """
    Test registration with password too short fails.

    Verifies that:
    - Password < 8 chars returns 422 validation error
    """
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "Short1",
            "display_name": "New User"
        }
    )

    assert response.status_code == 422 # Validation error

@pytest.mark.asyncio
async def test_register_weak_password_no_uppercase(client: AsyncClient):
    """
    Test registration without uppercase letter fails.
    
    Verifies that:
    - Password without uppercase returns 422 validation error
    """
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "password123",  # No uppercase
            "display_name": "New User"
        }
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_weak_password_no_lowercase(client: AsyncClient):
    """
    Test registration without lowercase letter fails.
    
    Verifies that:
    - Password without lowercase returns 422 validation error
    """
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "PASSWORD123",  # No lowercase
            "display_name": "New User"
        }
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_weak_password_no_number(client: AsyncClient):
    """
    Test registration without number fails.
    
    Verifies that:
    - Password without number returns 422 validation error
    """
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "PasswordOnly",  # No number
            "display_name": "New User"
        }
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient):
    """
    Test registration with invalid email format fails.
    
    Verifies that:
    - Invalid email format returns 422 validation error
    """
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "not-an-email",  # Invalid format
            "password": "TestPass123",
            "display_name": "New User"
        }
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_empty_display_name(client: AsyncClient):
    """
    Test registration with empty display name fails.
    
    Verifies that:
    - Empty display name returns 422 validation error
    """
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "TestPass123",
            "display_name": "   "  # Only whitespace
        }
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user: User):
    """
    Test successful login.
    
    Verifies that:
    - Login with valid credentials returns 200
    - Response includes access_token and refresh_token
    """
    response = await client.post(
        "/api/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "TestPass123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_email(client: AsyncClient):
    """
    Test login with non-existent email fails.
    
    Verifies that:
    - Login with non-existent email returns 401
    - Error message is generic (doesn't reveal if email exists)
    """
    response = await client.post(
        "/api/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "TestPass123"
        }
    )
    
    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, test_user: User):
    """
    Test login with wrong password fails.
    
    Verifies that:
    - Login with wrong password returns 401
    - Error message is generic (doesn't reveal if email or password was wrong)
    """
    response = await client.post(
        "/api/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "WrongPassword123"
        }
    )
    
    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_refresh_token_success(client: AsyncClient, test_user: User):
    """
    Test successful token refresh.
    
    Verifies that:
    - Refresh token can be used to get new tokens
    - New tokens are different from original tokens
    """
    import asyncio
    
    # Login to get refresh token
    login_response = await client.post(
        "/api/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "TestPass123"
        }
    )
    
    original_tokens = login_response.json()
    refresh_token = original_tokens["refresh_token"]
    
    # Wait 1 second to ensure new tokens have different timestamps
    await asyncio.sleep(1)
    
    # Use refresh token to get new tokens
    response = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    
    assert response.status_code == 200
    new_tokens = response.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
    
    # Verify new tokens are different (token rotation)
    assert new_tokens["access_token"] != original_tokens["access_token"]
    assert new_tokens["refresh_token"] != original_tokens["refresh_token"]


@pytest.mark.asyncio
async def test_refresh_token_invalid(client: AsyncClient):
    """
    Test refresh with invalid token fails.
    
    Verifies that:
    - Invalid refresh token returns 401
    """
    response = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": "invalid_token"}
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_with_access_token_fails(client: AsyncClient, auth_token: str):
    """
    Test refresh with access token instead of refresh token fails.
    
    Verifies that:
    - Using access token for refresh returns 401
    - Error indicates wrong token type
    """
    response = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": auth_token}  # Using access token
    )
    
    assert response.status_code == 401
    assert "token type" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_logout_success(client: AsyncClient, auth_headers: dict):
    """
    Test successful logout.
    
    Verifies that:
    - Logout with valid token returns 204
    """
    response = await client.post(
        "/api/auth/logout",
        headers=auth_headers
    )
    
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_logout_without_token_fails(client: AsyncClient):
    """
    Test logout without authentication fails.
    
    Verifies that:
    - Logout without token returns 403
    """
    response = await client.post("/api/auth/logout")
    
    assert response.status_code == 403