"""
Shared dependencies for v1 API routers.

Provides auth dependencies that inject the current user's identity
into handler functions, replacing hardcoded UUIDs.
"""

from typing import Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Re-export from the app-level auth module
from ...auth import (
    TokenPayload,
    get_current_user as _get_current_user_strict,
    get_current_user_optional as _get_current_user_optional,
    decode_token,
)

# Router-level dependencies for convenience
def require_user() -> TokenPayload:
    """Dependency that requires a valid JWT and returns TokenPayload."""
    return Depends(_get_current_user_strict)


def optional_user() -> Optional[TokenPayload]:
    """Dependency that returns TokenPayload if JWT present, else None."""
    return Depends(_get_current_user_optional)
