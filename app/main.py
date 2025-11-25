"""
Main FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.middleware import RequestIDMiddleware, error_handler_middleware

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

@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "message": "Welcome to Piglist API",
        "version": "0.1.0",
        "status": "healthy",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    from app.db.base import check_db_connection

    db_healthy = await check_db_connection()

    return JSONResponse(
        status_code=200 if db_healthy else 503,
        content={
            "status": "healthy" if db_healthy else "unhealthy",
            "service": "piglist-api",
            "database": "connected" if db_healthy else "disconnected",
        },
    )

@app.get("/test/error")
async def test_error():
    """Test error handling"""
    from app.core.exceptions import ValidationError
    raise ValidationError("This is a test error")


# Include routers (to be added later)
# from app.api.v1 import api_router
# app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
