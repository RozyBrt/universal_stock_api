from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.openapi.utils import get_openapi
from datetime import datetime, timezone
from typing import Any, Dict
import time
import uuid
import logging

from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.core.rate_limit import limiter
from app.core.logging import StructuredLogger, setup_app_logging
from app.core.exceptions import AppException, ErrorCode, InternalServerErrorException
from app.api.v1.routes import items, categories, transactions, auth

# ============= LOGGING SETUP =============

# Setup application logging
setup_app_logging()
logger = StructuredLogger(__name__)

# ============= APP INITIALIZATION =============

app = FastAPI(
    title=settings.API_TITLE,
    description="Universal Stock API - Production-ready inventory management system dengan structured logging dan rate limiting",
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Attach limiter ke app state
app.state.limiter = limiter

# ============= MIDDLEWARE SETUP =============

# 1. Trust proxy headers
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Restrict ini di production
)

# 2. CORS configuration
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

# ============= REQUEST LOGGING MIDDLEWARE =============

@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """
    Middleware untuk structured logging semua requests.
    
    Responsibilities:
    - Generate request ID untuk tracing
    - Log request start
    - Measure execution time
    - Log response status dan duration
    - Handle errors dengan logging
    """
    # Generate unique request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    request.state.start_time = time.time()
    
    # Log request start
    logger.log_request_start(request, request_id)
    
    try:
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - request.state.start_time) * 1000
        
        # Log request end
        logger.log_request_end(request, request_id, response.status_code, duration_ms)
        
        # Add request ID ke response header (untuk tracing)
        response.headers["X-Request-ID"] = request_id
        
        return response
        
    except Exception as exc:
        # Log error dengan full context
        duration_ms = (time.time() - request.state.start_time) * 1000
        logger.log_error(exc, request=request, request_id=request_id)
        
        raise

# ============= EXCEPTION HANDLERS =============

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom AppException dengan standardized response"""
    request_id = getattr(request.state, "request_id", None)
    
    response_body: Dict[str, Any] = {
        "error": {
            "code": exc.code.value,
            "message": exc.message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": str(request.url.path),
        }
    }
    
    if exc.details:
        response_body["error"]["details"] = exc.details
    
    if request_id:
        response_body["error"]["request_id"] = request_id
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_body,
        headers=exc.headers
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Handle rate limit exceeded error.
    
    When: Client exceeds rate limit
    Response: 429 Too Many Requests dengan retry-after header
    """
    request_id = getattr(request.state, "request_id", None)
    
    logger.log_warning(
        f"Rate limit exceeded",
        request_id=request_id,
        path=request.url.path,
        client_ip=request.client.host if request.client else None
    )
    
    response_body: Dict[str, Any] = {
        "error": {
            "code": "RATE_LIMIT_EXCEEDED",
            "message": "Terlalu banyak request. Silakan coba lagi dalam beberapa saat.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": str(request.url.path),
            "retry_after_seconds": 60
        }
    }
    
    if request_id:
        response_body["error"]["request_id"] = request_id
    
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=response_body,
        headers={"Retry-After": "60"}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    request_id = getattr(request.state, "request_id", None)
    error_id = f"ERR-{datetime.now(timezone.utc).timestamp()}"
    
    logger.log_error(exc, request=request, request_id=request_id)
    
    message = (
        f"Internal server error. Error ID: {error_id}"
        if settings.DEBUG
        else "Internal server error"
    )
    
    response_body: Dict[str, Any] = {
        "error": {
            "code": ErrorCode.INTERNAL_SERVER_ERROR.value,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": str(request.url.path),
            "error_id": error_id
        }
    }
    
    if request_id:
        response_body["error"]["request_id"] = request_id
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_body
    )

# ============= ROUTES REGISTRATION =============

app.include_router(auth.router, prefix="/api/v1")
app.include_router(items.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(transactions.router, prefix="/api/v1")

# ============= HEALTH CHECK ENDPOINT =============

@app.get("/health", tags=["Health"])
async def health_check():
    """Simple health check untuk monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.API_VERSION
    }

# ============= ROOT ENDPOINT =============

@app.get("/", tags=["Root"])
async def root():
    """API root endpoint"""
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

# ============= OPENAPI SCHEMA =============

def custom_openapi():
    """Customize OpenAPI schema"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        description="Enterprise-grade inventory management API",
        routes=app.routes,
    )
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# ============= LIFESPAN EVENTS =============

@app.on_event("startup")
async def startup_event():
    """Run on app startup"""
    logger.log_info(
        f"🚀 {settings.API_TITLE} v{settings.API_VERSION} starting up...",
        debug_mode=settings.DEBUG
    )

@app.on_event("shutdown")
async def shutdown_event():
    """Run on app shutdown"""
    logger.log_info(f"🛑 {settings.API_TITLE} shutting down...")
