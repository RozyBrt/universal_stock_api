from fastapi import HTTPException, status
from typing import Optional, Dict, Any
from enum import Enum

class ErrorCode(str, Enum):
    """Standardized error codes untuk frontend handling"""
    
    # Authentication errors
    UNAUTHORIZED = "UNAUTHORIZED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INVALID_TOKEN = "INVALID_TOKEN"
    API_KEY_INVALID = "API_KEY_INVALID"
    API_KEY_EXPIRED = "API_KEY_EXPIRED"
    
    # Authorization errors
    PERMISSION_DENIED = "PERMISSION_DENIED"
    FORBIDDEN = "FORBIDDEN"
    
    # Resource errors
    NOT_FOUND = "NOT_FOUND"
    ITEM_NOT_FOUND = "ITEM_NOT_FOUND"
    CATEGORY_NOT_FOUND = "CATEGORY_NOT_FOUND"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    
    # Duplicate errors
    DUPLICATE_SKU = "DUPLICATE_SKU"
    DUPLICATE_EMAIL = "DUPLICATE_EMAIL"
    DUPLICATE_USERNAME = "DUPLICATE_USERNAME"
    
    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    INVALID_EMAIL = "INVALID_EMAIL"
    WEAK_PASSWORD = "WEAK_PASSWORD"
    
    # Stock/Inventory errors
    INSUFFICIENT_STOCK = "INSUFFICIENT_STOCK"
    INVALID_QUANTITY = "INVALID_QUANTITY"
    STOCK_MOVEMENT_FAILED = "STOCK_MOVEMENT_FAILED"
    
    # Business rule errors
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    OPERATION_NOT_ALLOWED = "OPERATION_NOT_ALLOWED"
    
    # System errors
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    DATABASE_ERROR = "DATABASE_ERROR"


class AppException(HTTPException):
    """
    Base exception class untuk semua custom exceptions.
    
    Design principles:
    - Inheritance dari HTTPException buat compatible dengan FastAPI
    - Include error code untuk programmatic handling di frontend
    - Include structured data untuk logging
    - Support localization dengan message templates
    """
    
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.headers = headers or {}
        
        # Initialize parent HTTPException untuk FastAPI compatibility
        super().__init__(
            status_code=status_code,
            detail={
                "error": {
                    "code": code,
                    "message": message,
                    "details": details
                }
            },
            headers=headers
        )


# ============= AUTHENTICATION EXCEPTIONS =============

class UnauthorizedException(AppException):
    """User tidak login atau token invalid"""
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            code=ErrorCode.UNAUTHORIZED,
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class InvalidCredentialsException(AppException):
    """Email atau password salah"""
    def __init__(self):
        super().__init__(
            code=ErrorCode.INVALID_CREDENTIALS,
            message="Email atau password salah",
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class TokenExpiredException(AppException):
    """JWT token sudah expired"""
    def __init__(self):
        super().__init__(
            code=ErrorCode.TOKEN_EXPIRED,
            message="Token sudah expired, silakan login kembali",
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class InvalidTokenException(AppException):
    """JWT token tidak valid"""
    def __init__(self):
        super().__init__(
            code=ErrorCode.INVALID_TOKEN,
            message="Token tidak valid",
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class APIKeyInvalidException(AppException):
    """API Key tidak valid atau tidak ditemukan"""
    def __init__(self):
        super().__init__(
            code=ErrorCode.API_KEY_INVALID,
            message="API Key tidak valid",
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class APIKeyExpiredException(AppException):
    """API Key sudah expired"""
    def __init__(self):
        super().__init__(
            code=ErrorCode.API_KEY_EXPIRED,
            message="API Key sudah expired",
            status_code=status.HTTP_401_UNAUTHORIZED
        )


# ============= AUTHORIZATION EXCEPTIONS =============

class PermissionDeniedException(AppException):
    """User tidak punya permission untuk action ini"""
    def __init__(self, required_role: str = "admin"):
        super().__init__(
            code=ErrorCode.PERMISSION_DENIED,
            message=f"Memerlukan {required_role} role untuk action ini",
            status_code=status.HTTP_403_FORBIDDEN,
            details={"required_role": required_role}
        )


class ForbiddenException(AppException):
    """Access denied (generic)"""
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            code=ErrorCode.FORBIDDEN,
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )


# ============= NOT FOUND EXCEPTIONS =============

class ResourceNotFoundException(AppException):
    """Generic resource not found"""
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            code=ErrorCode.NOT_FOUND,
            message=f"{resource} dengan identifier '{identifier}' tidak ditemukan",
            status_code=status.HTTP_404_NOT_FOUND,
            details={
                "resource": resource,
                "identifier": str(identifier)
            }
        )


class ItemNotFoundException(AppException):
    """Item tidak ditemukan"""
    def __init__(self, item_id: int):
        super().__init__(
            code=ErrorCode.ITEM_NOT_FOUND,
            message=f"Item dengan ID {item_id} tidak ditemukan",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"item_id": item_id}
        )


class CategoryNotFoundException(AppException):
    """Category tidak ditemukan"""
    def __init__(self, category_id: int):
        super().__init__(
            code=ErrorCode.CATEGORY_NOT_FOUND,
            message=f"Category dengan ID {category_id} tidak ditemukan",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"category_id": category_id}
        )


class UserNotFoundException(AppException):
    """User tidak ditemukan"""
    def __init__(self, user_id: int):
        super().__init__(
            code=ErrorCode.USER_NOT_FOUND,
            message=f"User dengan ID {user_id} tidak ditemukan",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"user_id": user_id}
        )


# ============= DUPLICATE/CONFLICT EXCEPTIONS =============

class DuplicateSKUException(AppException):
    """SKU sudah terdaftar"""
    def __init__(self, sku: str):
        super().__init__(
            code=ErrorCode.DUPLICATE_SKU,
            message=f"SKU '{sku}' sudah terdaftar. Gunakan PATCH untuk update item yang ada.",
            status_code=status.HTTP_409_CONFLICT,
            details={"sku": sku}
        )


class DuplicateEmailException(AppException):
    """Email sudah terdaftar"""
    def __init__(self, email: str):
        super().__init__(
            code=ErrorCode.DUPLICATE_EMAIL,
            message=f"Email '{email}' sudah terdaftar. Gunakan login untuk akses akun yang ada.",
            status_code=status.HTTP_409_CONFLICT,
            details={"email": email}
        )


class DuplicateUsernameException(AppException):
    """Username sudah terdaftar"""
    def __init__(self, username: str):
        super().__init__(
            code=ErrorCode.DUPLICATE_USERNAME,
            message=f"Username '{username}' sudah digunakan. Pilih username yang berbeda.",
            status_code=status.HTTP_409_CONFLICT,
            details={"username": username}
        )


# ============= VALIDATION EXCEPTIONS =============

class ValidationException(AppException):
    """Generic validation error"""
    def __init__(self, field: str, message: str):
        super().__init__(
            code=ErrorCode.VALIDATION_ERROR,
            message=f"Validasi gagal di field '{field}': {message}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"field": field}
        )


class InvalidInputException(AppException):
    """Input tidak valid"""
    def __init__(self, message: str, details: Optional[Dict] = None, field: Optional[str] = None):
        if field:
            details = details or {}
            details["field"] = field
        super().__init__(
            code=ErrorCode.INVALID_INPUT,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class InvalidEmailException(AppException):
    """Email format tidak valid"""
    def __init__(self, email: str):
        super().__init__(
            code=ErrorCode.INVALID_EMAIL,
            message=f"Email '{email}' tidak valid",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"email": email}
        )


class WeakPasswordException(AppException):
    """Password tidak memenuhi requirements"""
    def __init__(self, requirements: list = None):
        requirements = requirements or [
            "Minimal 8 karakter",
            "Minimal 1 uppercase letter",
            "Minimal 1 digit"
        ]
        message = "Password tidak kuat. Requirements: " + ", ".join(requirements)
        super().__init__(
            code=ErrorCode.WEAK_PASSWORD,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"requirements": requirements}
        )


# ============= STOCK/INVENTORY EXCEPTIONS =============

class InsufficientStockException(AppException):
    """Stok tidak cukup untuk operasi"""
    def __init__(self, required: int, available: int, item_id: int = None):
        details = {
            "required": required,
            "available": available
        }
        if item_id:
            details["item_id"] = item_id
        
        super().__init__(
            code=ErrorCode.INSUFFICIENT_STOCK,
            message=f"Stok tidak cukup. Diperlukan: {required}, Tersedia: {available}",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class InvalidQuantityException(AppException):
    """Quantity tidak valid (harus > 0, integer, etc)"""
    def __init__(self, quantity: Any, reason: str = None):
        message = f"Quantity '{quantity}' tidak valid"
        if reason:
            message += f". {reason}"
        
        super().__init__(
            code=ErrorCode.INVALID_QUANTITY,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"quantity": quantity, "reason": reason}
        )


class StockMovementFailedException(AppException):
    """Stock movement operation gagal"""
    def __init__(self, operation: str, reason: str):
        super().__init__(
            code=ErrorCode.STOCK_MOVEMENT_FAILED,
            message=f"Stock movement '{operation}' gagal: {reason}",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"operation": operation, "reason": reason}
        )


# ============= BUSINESS RULE EXCEPTIONS =============

class BusinessRuleViolationException(AppException):
    """Violasi business rule"""
    def __init__(self, rule: str, message: str):
        super().__init__(
            code=ErrorCode.BUSINESS_RULE_VIOLATION,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"rule": rule}
        )


class OperationNotAllowedException(AppException):
    """Operasi tidak diizinkan dalam kondisi saat ini"""
    def __init__(self, operation: str, reason: str):
        super().__init__(
            code=ErrorCode.OPERATION_NOT_ALLOWED,
            message=f"Operasi '{operation}' tidak diizinkan: {reason}",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"operation": operation, "reason": reason}
        )


# ============= SYSTEM EXCEPTIONS =============

class InternalServerErrorException(AppException):
    """Server error (unexpected)"""
    def __init__(self, message: str = "Internal server error", error_id: str = None):
        details = {}
        if error_id:
            details["error_id"] = error_id
        
        super().__init__(
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class ServiceUnavailableException(AppException):
    """Service tidak tersedia (database down, etc)"""
    def __init__(self, service: str):
        super().__init__(
            code=ErrorCode.SERVICE_UNAVAILABLE,
            message=f"Service '{service}' tidak tersedia. Coba lagi nanti.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"service": service}
        )


class DatabaseException(AppException):
    """Database error"""
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(
            code=ErrorCode.DATABASE_ERROR,
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
