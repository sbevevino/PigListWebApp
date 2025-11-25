class PiglistException(Exception):
    """Base exception for all Piglist errors"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class AuthenticationError(PiglistException):
    """Raised when authentication fails"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)

class AuthorizationError(PiglistException):
    """Raised when user lacks permissions"""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status_code=403)

class NotFoundError(PiglistException):
    """Raised when resource is not found"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)

class ValidationError(PiglistException):
    """Raised when validation fails"""
    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status_code=422)

class RateLimitError(PiglistException):
    """Raised when the rate limit is exceeded"""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)