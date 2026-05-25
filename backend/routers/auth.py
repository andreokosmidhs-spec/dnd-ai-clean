"""
Auth endpoints: register, login, me.
Uses bcrypt for passwords, HS256 JWT for sessions.
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt
from bson import ObjectId

from middleware.auth_middleware import get_current_user, JWT_SECRET, JWT_ALGORITHM

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_EXPIRE_DAYS = 30

_db = None


def set_database(database):
    global _db
    _db = database


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


def _make_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(days=JWT_EXPIRE_DAYS)
    return jwt.encode({"sub": user_id, "exp": expire}, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _safe_user(user: dict) -> dict:
    return {"id": str(user["_id"]), "email": user["email"], "plan": user.get("plan", "free")}


@router.post("/register")
async def register(req: RegisterRequest):
    if not req.email or "@" not in req.email or len(req.password) < 6:
        raise HTTPException(400, "Valid email and password (6+ chars) required")

    existing = await _db.users.find_one({"email": req.email.lower()})
    if existing:
        raise HTTPException(400, "Email already registered")

    user_doc = {
        "email": req.email.lower(),
        "hashed_password": pwd_context.hash(req.password),
        "plan": "free",
        "created_at": datetime.utcnow(),
    }
    result = await _db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id

    logger.info(f"New user registered: {req.email.lower()}")
    return {"token": _make_token(str(result.inserted_id)), "user": _safe_user(user_doc)}


@router.post("/login")
async def login(req: LoginRequest):
    user = await _db.users.find_one({"email": req.email.lower()})
    if not user or not pwd_context.verify(req.password, user["hashed_password"]):
        raise HTTPException(401, "Invalid email or password")

    return {"token": _make_token(str(user["_id"])), "user": _safe_user(user)}


@router.get("/me")
async def me(user_id: str = Depends(get_current_user)):
    user = await _db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(404, "User not found")
    return {"user": _safe_user(user)}
