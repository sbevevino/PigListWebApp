"""
API package - exports main API router with all sub-routers.

This package organizes all API endpoints into a single router that can be included in the main FastAPI application.
Sub-routers are organized by resource (auth, users, groups, etc.).
"""

from fastapi import APIRouter

from app.api import auth, users

# Create main API router with version prefix
api_router = APIRouter(prefix="/api")

# Include sub-routers
# Each router handles a specific resource or functionality
api_router.include_router(
    auth.router,
    # auth.router already has /auth prefix
    # Results in /api/auth/* endpoints
)

api_router.include_router(
    users.router,
    # users.router already has /users prefix
    # Results in /api/users/* endpoints
)

# TODO: Future routers will be added here
# api_router.include_router(groups.router)
# api_router.include_router(gifts.router)
# api_router.include_router(categories.router)

# Export for use in main application
__all__ = ["api_router"]