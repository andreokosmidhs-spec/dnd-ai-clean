"""
JWT auth dependency for FastAPI endpoints.
get_current_user      → raises 401 if no/invalid token
get_current_user_opt  → returns user_id or None (non-blocking)
"""
import os
from typing import Optional
from fastapi import Header, HTTPException
from jose import jwt, JWTError

JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"


def _decode(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


async def get_current_user_opt(authorization: Optional[str] = Header(None)) -> Optional[str]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    return _decode(authorization.split(" ", 1)[1])


async def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = _decode(authorization.split(" ", 1)[1])
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user_id
