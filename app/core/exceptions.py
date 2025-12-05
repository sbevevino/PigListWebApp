"""
Custom exception classes for the Piglist application.

This module defines all custom exceptions used throughout the application,
providing consistent error handling and HTTP status codes.
"""


class PiglistException(Exception):
    """
    Base exception for all Piglist errors.
    
    All custom exceptions inherit from this base class for consistent
    error handling and status code management.
    """
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(PiglistException):
    """
    Raised when authentication fails.
    
    Used for invalid credentials, expired tokens, etc.
    HTTP Status: 401 Unauthorized
    """
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class UnauthorizedError(PiglistException):
    """
    Raised when authentication fails (alias for AuthenticationError).
    
    Used for invalid credentials, inactive accounts, etc.
    HTTP Status: 401 Unauthorized
    """
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)


class AuthorizationError(PiglistException):
    """
    Raised when user lacks permissions.
    
    Used when authenticated user doesn't have required permissions.
    HTTP Status: 403 Forbidden
    """
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status_code=403)


class NotFoundError(PiglistException):
    """
    Raised when resource is not found.
    
    Used when requested resource doesn't exist in database.
    HTTP Status: 404 Not Found
    """
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ConflictError(PiglistException):
    """
    Raised when resource conflict occurs.
    
    Used for duplicate emails, unique constraint violations, etc.
    HTTP Status: 409 Conflict
    """
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, status_code=409)


class ValidationError(PiglistException):
    """
    Raised when validation fails.
    
    Used for business logic validation errors.
    HTTP Status: 422 Unprocessable Entity
    """
    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status_code=422)


class RateLimitError(PiglistException):
    """
    Raised when rate limit is exceeded.
    
    Used to prevent abuse and protect resources.
    HTTP Status: 429 Too Many Requests
    """
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)