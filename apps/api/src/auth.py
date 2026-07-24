"""
JWT Authentication Module for RealtyAI API.

Provides token creation, validation, and FastAPI dependency for protected routes.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Optional

from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from .config import settings

_EMAIL_RE = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


# ─── Models ────────────────────────────────────────────────────────────────────

class TokenPayload(BaseModel):
    sub: str  # user_id
    email: str
    name: str = ""
    brokerage_id: str | None = None
    exp: int
    iat: int
    scope: str = "user"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserCreate(BaseModel):
    email: str = Field(pattern=_EMAIL_RE)
    password: str
    name: str


class UserLogin(BaseModel):
    email: str = Field(pattern=_EMAIL_RE)
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    brokerage_id: str | None = None
    created_at: datetime


# ─── Token Functions ──────────────────────────────────────────────────────────

def create_access_token(
    user_id: str,
    email: str,
    name: str = "",
    brokerage_id: str | None = None,
    expires_delta: Optional[timedelta] = None,
) -> tuple[str, int]:
    """Create a JWT access token. Returns (token, expires_in_seconds)."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.auth_token_expire_minutes)
    
    expire = datetime.utcnow() + expires_delta
    iat = int(time.time())
    exp = int(expire.timestamp())
    
    payload = {
        "sub": user_id,
        "email": email,
        "name": name,
        "brokerage_id": brokerage_id,
        "exp": exp,
        "iat": iat,
        "scope": "user",
    }
    
    token = jwt.encode(
        payload,
        settings.auth_secret_key,
        algorithm=settings.auth_algorithm,
    )
    
    return token, int(expires_delta.total_seconds())


def decode_token(token: str) -> TokenPayload:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.auth_secret_key,
            algorithms=[settings.auth_algorithm],
        )
        return TokenPayload(**payload)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


# ─── User Storage (Database-backed) ───────────────────────────────────────────

async def get_user_by_email(email: str) -> Optional[dict]:
    """Fetch user by email from database."""
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import Session
        
        db_url = settings.database_url.replace('+asyncpg', '')
        engine = create_engine(db_url)
        
        with Session(engine) as session:
            result = session.execute(
                text("SELECT id, email, full_name, password_hash, brokerage_id, created_at FROM users WHERE email = :email"),
                {"email": email}
            ).first()
            
            if result:
                return {
                    "id": str(result.id),
                    "email": result.email,
                    "name": result.full_name,
                    "password_hash": result.password_hash,
                    "brokerage_id": str(result.brokerage_id) if result.brokerage_id else None,
                    "created_at": result.created_at,
                }
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Database error getting user: {e}")
    return None


async def create_user(email: str, password: str, name: str) -> Optional[dict]:
    """Create a new user in the database."""
    import uuid
    import bcrypt

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user_id = str(uuid.uuid4())
    brokerage_id = str(uuid.uuid4())
    
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import Session
        
        db_url = settings.database_url.replace('+asyncpg', '')
        engine = create_engine(db_url)
        
        with Session(engine) as session:
            session.execute(
                text("""
                    INSERT INTO users (id, email, full_name, password_hash, role, is_active, brokerage_id, created_at, updated_at)
                    VALUES (:id, :email, :full_name, :password_hash, 'AGENT', true, :brokerage_id, NOW(), NOW())
                """),
                {
                    "id": user_id,
                    "email": email,
                    "full_name": name,
                    "password_hash": password_hash,
                    "brokerage_id": brokerage_id,
                }
            )
            session.commit()
            
        return {
            "id": user_id,
            "email": email,
            "name": name,
            "brokerage_id": brokerage_id,
            "created_at": datetime.utcnow(),
        }
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Database error creating user: {e}")
        return None


async def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plain password against a hash."""
    import bcrypt
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


# ─── FastAPI Security Dependency ──────────────────────────────────────────────

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> TokenPayload:
    """FastAPI dependency to get current authenticated user from JWT."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return decode_token(credentials.credentials)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[TokenPayload]:
    """Optional auth - returns None if no token provided."""
    if not credentials:
        return None
    try:
        return decode_token(credentials.credentials)
    except HTTPException:
        return None