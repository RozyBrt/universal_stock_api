from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.openapi.utils import get_openapi
from datetime import datetime, timezone
from typing import Any, Dict
import logging

from app.config import settings
from app.core.exceptions import AppException, ErrorCode, InternalServerErrorException
from app.api.v1.routes import items, categories, transactions, auth

# ============= LOGGING SETUP =============
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run on app startup and shutdown"""
    logger.info(f"🚀 {settings.API_TITLE} v{settings.API_VERSION} starting up...")
    yield
    logger.info(f"🛑 {settings.API_TITLE} shutting down...")

# ============= APP INITIALIZATION =============
app = FastAPI(
    title=settings.API_TITLE,
    description="Universal Stock API - Production-ready inventory management system",
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# ============= MIDDLEWARE SETUP =============

# 1. Trust proxy headers (untuk deployment di reverse proxy)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Restrict ini di production
)

# 2. CORS configuration (untuk frontend access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # Next.js dev
        "http://localhost:8081",      # Flutter dev
        "http://localhost:5173",      # Vite dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============= REQUEST/RESPONSE LOGGING MIDDLEWARE =============

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log semua HTTP requests dan responses"""
    # Log request
    logger.info(
        f"→ {request.method} {request.url.path} | "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )
    
    try:
        response = await call_next(request)
        
        # Log response
        logger.info(
            f"← {request.method} {request.url.path} | "
            f"Status: {response.status_code}"
        )
        
        return response
    except Exception as e:
        logger.error(
            f"✗ {request.method} {request.url.path} | "
            f"Error: {str(e)}",
            exc_info=True
        )
        raise

# ============= EXCEPTION HANDLERS =============

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handle custom AppException dengan standardized error response.
    
    Response format:
    {
        "error": {
            "code": "ERROR_CODE",
            "message": "Human-readable message",
            "timestamp": "2024-01-21T10:30:00Z",
            "path": "/api/v1/items",
            "details": {...}
        }
    }
    """
    response_body: Dict[str, Any] = {
        "error": {
            "code": exc.code.value,
            "message": exc.message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": str(request.url.path),
        }
    }
    
    # Include details jika ada (untuk debugging)
    if exc.details:
        response_body["error"]["details"] = exc.details
    
    # Log error dengan context
    log_level = "warning" if exc.status_code < 500 else "error"
    getattr(logger, log_level)(
        f"AppException: {exc.code.value} | "
        f"Message: {exc.message} | "
        f"Path: {request.url.path}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_body,
        headers=exc.headers
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions (catch-all).
    
    Why separate handler?
    - Untuk error yang tidak inherit dari AppException
    - Log dengan full traceback untuk debugging
    - Return standardized error response (jangan expose internal details di production)
    """
    # Generate error ID untuk tracking
    error_id = f"ERR-{datetime.now(timezone.utc).timestamp()}"
    
    logger.error(
        f"Unexpected error {error_id} at {request.url.path}: {str(exc)}",
        exc_info=True
    )
    
    # In production, don't expose full exception message
    message = (
        "Internal server error. Error ID: " + error_id
        if settings.DEBUG
        else "Internal server error"
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": ErrorCode.INTERNAL_SERVER_ERROR.value,
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "path": str(request.url.path),
                "error_id": error_id
            }
        }
    )

# ============= ROUTES REGISTRATION =============

# Include routers dari v1 API
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(items.router, prefix="/api/v1/items")
app.include_router(categories.router, prefix="/api/v1/categories")
app.include_router(transactions.router, prefix="/api/v1/transactions")

# ============= HEALTH CHECK ENDPOINT =============

@app.get("/health", tags=["Health"])
async def health_check():
    """Simple health check endpoint untuk monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.API_VERSION
    }

# ============= CUSTOM OPENAPI SCHEMA =============

def custom_openapi():
    """Customize OpenAPI schema untuk better documentation"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        description="Enterprise-grade inventory management API dengan authentication, pagination, dan concurrency safety",
        routes=app.routes,
    )
    
    # Add info tentang error codes
    openapi_schema["info"]["x-error-codes"] = {
        "INSUFFICIENT_STOCK": "Stok tidak cukup untuk operasi",
        "ITEM_NOT_FOUND": "Item tidak ditemukan",
        "UNAUTHORIZED": "Authentication required",
        "PERMISSION_DENIED": "User tidak punya permission",
        "DUPLICATE_SKU": "SKU sudah terdaftar",
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# ============= ROOT ENDPOINT =============

@app.get("/", tags=["Root"])
async def root():
    """API root endpoint dengan info"""
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "api": "/api/v1"
        }
    }

# ============= LIFESPAN EVENTS =============
# Replaced by lifespan context manager

