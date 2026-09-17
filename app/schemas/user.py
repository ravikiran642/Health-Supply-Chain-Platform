from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, EmailStr
from app.models.user import ScopeLevelEnum
from app.schemas.rbac import RoleResponse


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    is_active: bool = True
    scope_level: ScopeLevelEnum
    scope_id: Optional[UUID] = None


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    roles: List[RoleResponse] = []
    permissions: List[str] = []
    created_at: datetime
    updated_at: datetime


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str
    is_active: bool
    scope_level: ScopeLevelEnum
    scope_id: Optional[UUID] = None
    roles: List[str] = []
    permissions: List[str] = []
