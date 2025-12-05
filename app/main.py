"""
Main FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.middleware import RequestIDMiddleware, error_handler_middleware

from contextlib import asynccontextmanager
from app.core.redis_client import close_redis_client

from app.api import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for proper resource management.
    This ensures Redis connections and other resources are properly
    closed on application shutdown.
    
    Yields:
        Control to the application during its lifetime
    """
    # Startup
    logger.info(
        "Application starting up",
        extra={"version": "0.1.0", "environment": settings.ENVIRONMENT}
    )
    
    yield
    
    # Shutdown
    logger.info("Application shutting down")
    await close_redis_client()
    logger.info("Redis client closed successfully")

# Initalize logging
setup_logging()
logger.info("Starting Piglist API", extra={"version": "0.1.0"})

# Create FastAPI app instance
app = FastAPI(
    title="Piglist API",
    description="Family gift-sharing web application API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request ID and error handler Middleware
app.add_middleware(RequestIDMiddleware)
app.middleware("http")(error_handler_middleware)

# Include API routers
app.include_router(api_router)

@app.get("/")
async def root():
    """
    Root endpoint - API health check and information.
    
    Returns basic API information and links to documentation.
    """
    return {
        "message": "Welcome to Piglist API",
        "version": "0.1.0",
        "status": "healthy",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    
    Checks database connectivity and returns service status.
    Returns 200 if healthy, 503 if unhealthy.
    """
    from app.db.base import check_db_connection

    db_healthy = await check_db_connection()

    return JSONResponse(
        status_code=200 if db_healthy else 503,
        content={
            "status": "healthy" if db_healthy else "unhealthy",
            "service": "piglist-api",
            "version": "0.1.0",
            "database": "connected" if db_healthy else "disconnected",
        },
    )


@app.get("/test/error")
async def test_error():
    """
    Test endpoint for error handling middleware.
    
    Deliberately raises an error to test error handling.
    Should only be available in development.
    """
    from app.core.exceptions import ValidationError
    
    if settings.ENVIRONMENT != "development":
        return {"message": "This endpoint is only available in development"}
    
    raise ValidationError("This is a test error")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
