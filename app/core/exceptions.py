import logging
from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse

logger = logging.getLogger("app.exceptions")

class AnalyticsException(Exception):
    """Base application exception for custom analytical errors."""
    def __init__(self, status_code: int, detail: str, code: str = "ERROR"):
        self.status_code = status_code
        self.detail = detail
        self.code = code

class ResourceNotFoundException(AnalyticsException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=404, detail=detail, code="RESOURCE_NOT_FOUND")

class TenantAccessDeniedException(AnalyticsException):
    def __init__(self, detail: str = "Access denied to this tenant resource"):
        super().__init__(status_code=403, detail=detail, code="TENANT_ACCESS_DENIED")

class AuthenticationFailedException(AnalyticsException):
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(status_code=401, detail=detail, code="AUTHENTICATION_FAILED")


def register_exception_handlers(app: FastAPI):
    """Register application-wide global error interceptors on FastAPI."""
    @app.exception_handler(AnalyticsException)
    async def analytics_exception_handler(request: Request, exc: AnalyticsException):
        logger.warning(f"Application error intercepted [{exc.code}]: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "code": exc.code,
                "detail": exc.detail
            }
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        # Catch and safely redact unhandled runtime or database syntax exceptions
        logger.error(f"Unhandled server exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "code": "INTERNAL_SERVER_ERROR",
                "detail": "An unexpected server error occurred."
            }
        )