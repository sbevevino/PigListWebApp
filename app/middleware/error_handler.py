"""Middleware for handling errors and exceptions"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.core.exceptions import PiglistException
from app.core.logging import logger

async def error_handler_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except PiglistException as exc:
        logger.error(
            f"Application error: {exc.message}",
            extra={
                "request_id": getattr(request.state, "request_id", None),
                "path": request.url.path,
                "method": request.method,
            }
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.message,
                "request_id": getattr(request.state, "request_id", None),
            }
        )
    except Exception as exc:
        logger.exception(
            "Unhandled exception",
            extra={
                "request_id": getattr(request.state, "request_id", None),
                "path": request.url.path,
                "method": request.method,
            }
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "request_id": getattr(request.state, "request_id", None),
            }
        )