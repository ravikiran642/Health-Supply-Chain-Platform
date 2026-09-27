"""Pydantic schemas for user create/read/update payloads, decoupling the API shape
of `User` from its ORM model in app/models/user.py.
"""
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.models.user import ScopeLevelEnum
from app.schemas.rbac import RoleResponse
from app.schemas.common import PaginationMeta


def validate_password_complexity(v: str) -> str:
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not any(c.isalpha() for c in v):
        raise ValueError("Password must contain at least one letter")
    if not any(c.isdigit() for c in v):
        raise ValueError("Password must contain at least one number")
    return v


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=150)
    phone: Optional[str] = Field(None, max_length=20)
    is_active: bool = True
    scope_level: ScopeLevelEnum
    scope_id: Optional[UUID] = None


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=150)
    password: str = Field(..., min_length=8)
    phone: Optional[str] = Field(None, max_length=20)
    is_active: bool = True
    scope_level: ScopeLevelEnum
    scope_id: Optional[UUID] = None
    role_names: List[str] = Field(..., min_length=1, max_length=1)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_password_complexity(v)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    phone: Optional[str] = Field(None, max_length=20)
    scope_level: Optional[ScopeLevelEnum] = None
    scope_id: Optional[UUID] = None
    role_names: Optional[List[str]] = Field(None, min_length=1, max_length=1)


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    phone: Optional[str] = Field(None, max_length=20)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_new_pwd(cls, v: str) -> str:
        return validate_password_complexity(v)


class ResetPasswordResponse(BaseModel):
    temporary_password: str
    message: str = "Password reset successfully"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    is_active: bool
    scope_level: ScopeLevelEnum
    scope_id: Optional[UUID] = None
    must_change_password: bool = False
    roles: List[RoleResponse] = []
    permissions: List[str] = []
    created_at: datetime
    updated_at: datetime


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    is_active: bool
    scope_level: ScopeLevelEnum
    scope_id: Optional[UUID] = None
    must_change_password: bool = False
    roles: List[str] = []
    permissions: List[str] = []


class UserListResponse(BaseModel):
    items: List[UserResponse]
    pagination: PaginationMeta
