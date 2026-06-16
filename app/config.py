import os
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional

app_env = os.getenv("APP_ENV", "development")

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/universal_stock"
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v:
            return v
        
        # Replace postgres:// or postgresql:// with postgresql+asyncpg://
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
            
        # Replace sslmode=require with ssl=require for asyncpg compatibility
        if "sslmode=require" in v:
            v = v.replace("sslmode=require", "ssl=require")
            
        return v
    
    # Security
    SECRET_KEY: str = "your-secret-key-very-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # API
    API_TITLE: str = "Universal Stock API"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # ============= RATE LIMITING CONFIGURATION =============
    # Format: "requests/period" (period = "second", "minute", "hour")
    
    RATE_LIMIT_AUTH_LOGIN: str = "5/minute"         # 5 login attempts per minute
    RATE_LIMIT_AUTH_REGISTER: str = "3/minute"      # 3 register attempts per minute
    RATE_LIMIT_AUTH_REFRESH: str = "10/minute"      # 10 refresh attempts per minute
    RATE_LIMIT_API_KEYS: str = "30/minute"
    
    RATE_LIMIT_ITEMS_GET: str = "100/minute"        # 100 reads per minute
    RATE_LIMIT_ITEMS_CREATE: str = "20/minute"      # 20 creates per minute
    RATE_LIMIT_ITEMS_UPDATE: str = "30/minute"      # 30 updates per minute
    RATE_LIMIT_ITEMS_DELETE: str = "10/minute"      # 10 deletes per minute
    RATE_LIMIT_ITEMS_STOCK: str = "50/minute"       # 50 stock operations per minute
    
    RATE_LIMIT_SEARCH: str = "60/minute"            # 60 searches per minute
    
    RATE_LIMIT_CATEGORIES_GET: str = "100/minute"
    RATE_LIMIT_CATEGORIES_MODIFY: str = "20/minute"
    RATE_LIMIT_TRANSACTIONS_GET: str = "100/minute"
    
    # ============= LOGGING =============
    LOG_LEVEL: str = "INFO" if not DEBUG else "DEBUG"
    
    model_config = {
        "env_file": (".env", f".env.{app_env}"),
        "case_sensitive": True,
        "extra": "ignore"
    }

settings = Settings()
