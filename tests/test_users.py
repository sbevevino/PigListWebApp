"""
Tests for user profile endpoints.

This module tests user profile retrieval and updates,
including authentication requirements and validation.
"""

import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
async def test_get_current_user_success(
    client: AsyncClient,
    auth_headers: dict,
    test_user: User
):
    """
    Test getting current user profile.
    
    Verifies that:
    - Authenticated request returns 200
    - Response includes user data
    - Password is not included in response
    """
    response = await client.get("/api/users/me", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify user data
    assert data["email"] == "testuser@example.com"
    assert data["display_name"] == "Test User"
    assert "id" in data
    assert data["is_active"] is True
    assert "created_at" in data
    
    # Verify password is not in response
    assert "password" not in data
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_get_current_user_unauthorized(client: AsyncClient):
    """
    Test getting profile without authentication fails.
    
    Verifies that:
    - Request without token returns 403
    """
    response = await client.get("/api/users/me")
    
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(client: AsyncClient):
    """
    Test getting profile with invalid token fails.
    
    Verifies that:
    - Request with invalid token returns 401
    """
    headers = {"Authorization": "Bearer invalid_token"}
    response = await client.get("/api/users/me", headers=headers)
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_current_user_success(
    client: AsyncClient,
    auth_headers: dict,
    test_user: User
):
    """
    Test updating current user profile.
    
    Verifies that:
    - Update with valid data returns 200
    - Display name is updated
    - Other fields remain unchanged
    """
    response = await client.put(
        "/api/users/me",
        headers=auth_headers,
        json={"display_name": "Updated Name"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify update
    assert data["display_name"] == "Updated Name"
    
    # Verify other fields unchanged
    assert data["email"] == "testuser@example.com"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_update_user_unauthorized(client: AsyncClient):
    """
    Test updating profile without authentication fails.
    
    Verifies that:
    - Update without token returns 403
    """
    response = await client.put(
        "/api/users/me",
        json={"display_name": "Updated Name"}
    )
    
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_user_empty_display_name(
    client: AsyncClient,
    auth_headers: dict
):
    """
    Test updating with empty display name fails.
    
    Verifies that:
    - Empty display name returns 422 validation error
    """
    response = await client.put(
        "/api/users/me",
        headers=auth_headers,
        json={"display_name": "   "}  # Only whitespace
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_user_display_name_too_long(
    client: AsyncClient,
    auth_headers: dict
):
    """
    Test updating with too long display name fails.
    
    Verifies that:
    - Display name > 100 characters returns 422
    """
    response = await client.put(
        "/api/users/me",
        headers=auth_headers,
        json={"display_name": "a" * 101}  # 101 characters
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_user_partial_update(
    client: AsyncClient,
    auth_headers: dict,
    test_user: User
):
    """
    Test partial update (only display_name).
    
    Verifies that:
    - Can update only display_name
    - Other fields remain unchanged
    """
    # Get original data
    original_response = await client.get("/api/users/me", headers=auth_headers)
    original_data = original_response.json()
    
    # Update only display_name
    response = await client.put(
        "/api/users/me",
        headers=auth_headers,
        json={"display_name": "New Name"}
    )
    
    assert response.status_code == 200
    updated_data = response.json()
    
    # Verify only display_name changed
    assert updated_data["display_name"] == "New Name"
    assert updated_data["email"] == original_data["email"]
    assert updated_data["id"] == original_data["id"]
