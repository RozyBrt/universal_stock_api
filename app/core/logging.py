import logging
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import Request
import traceback

# ============= STRUCTURED LOGGER CLASS =============

class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter untuk structured logging.
    
    Why JSON?
    - Easy to parse di log aggregation systems (ELK, DataDog, etc)
    - Queryable structured data
    - Machine-readable, not just human-readable
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Include exception info jika ada
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exc()
            }
        
        # Include custom fields jika ada (di logging.info(..., extra={...}))
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "path"):
            log_data["path"] = record.path
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        
        return json.dumps(log_data, ensure_ascii=False)


class StructuredLogger:
    """
    Structured logging wrapper untuk consistent logging across app.
    
    Handles:
    - Request lifecycle logging
    - Error logging dengan context
    - Performance metrics (response time)
    - Request ID tracking untuk tracing
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        
        # Setup JSON formatter
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(JSONFormatter())
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def log_request_start(self, request: Request, request_id: str):
        """Log request start dengan context"""
        extra = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
        }
        
        # Include query params jika ada
        if request.query_params:
            extra["query_params"] = dict(request.query_params)
        
        # Include client IP
        if request.client:
            extra["client_ip"] = request.client.host
        
        self.logger.info(
            f"→ {request.method} {request.url.path}",
            extra=extra
        )
    
    def log_request_end(self, request: Request, request_id: str, status_code: int, duration_ms: float):
        """Log request end dengan status dan performance"""
        extra = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
        }
        
        # Determine log level berdasarkan status code
        if status_code >= 500:
            log_func = self.logger.error
        elif status_code >= 400:
            log_func = self.logger.warning
        else:
            log_func = self.logger.info
        
        log_func(
            f"← {request.method} {request.url.path} [{status_code}] ({round(duration_ms, 2)}ms)",
            extra=extra
        )
    
    def log_error(self, error: Exception, request: Request = None, request_id: str = None):
        """Log error dengan full context"""
        extra = {
            "error_type": type(error).__name__,
            "error_message": str(error),
        }
        
        if request_id:
            extra["request_id"] = request_id
        if request:
            extra["method"] = request.method
            extra["path"] = request.url.path
        
        self.logger.error(
            f"✗ Error: {str(error)}",
            extra=extra,
            exc_info=True
        )
    
    def log_info(self, message: str, **kwargs):
        """Log info dengan optional context"""
        self.logger.info(message, extra=kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """Log warning dengan optional context"""
        self.logger.warning(message, extra=kwargs)
    
    def log_debug(self, message: str, **kwargs):
        """Log debug dengan optional context"""
        self.logger.debug(message, extra=kwargs)


# ============= UTILITY FUNCTIONS =============

def setup_app_logging():
    """
    Setup application-wide logging configuration.
    
    Call ini di app startup untuk configure semua loggers.
    """
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Handler untuk console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(console_handler)


# ============= GLOBAL LOGGER INSTANCE =============

app_logger = StructuredLogger(__name__)
