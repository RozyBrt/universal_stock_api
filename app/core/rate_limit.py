import os
from slowapi import Limiter
from slowapi.util import get_remote_address

# Disable rate limiting entirely in test environment to prevent 429 errors in E2E tests
_is_test_env = os.getenv("APP_ENV", "development") == "test"

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[] if _is_test_env else ["100/minute"],
    enabled=not _is_test_env,
    storage_uri=None
)
