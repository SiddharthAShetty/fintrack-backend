"""
Pydantic v2 schemas for User and Auth flows.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.config import Role


# ── Registration ───────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=64, examples=["alice"])
    email: EmailStr
    password: str = Field(..., min_length=8, examples=["Str0ngP@ss"])
    role: Role = Role.VIEWER  # admins can override this


# ── Response (never expose hashed_password) ───────────────────────────────────

class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: Role
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Admin: update a user's role or status ─────────────────────────────────────

class UserUpdate(BaseModel):
    role: Optional[Role] = None
    is_active: Optional[bool] = None


# ── Auth tokens ───────────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class TokenData(BaseModel):
    user_id: Optional[int] = None
