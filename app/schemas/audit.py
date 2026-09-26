"""Pydantic schemas for creating and reading audit log entries, used by
AuditService/AuditRepository and any admin-facing audit endpoints.
"""
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from app.models.audit import AuditResultEnum


class AuditLogCreate(BaseModel):
    user_id: Optional[UUID] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    ip_address: str
    result: AuditResultEnum
    metadata: Optional[Dict[str, Any]] = None


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: Optional[UUID] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    ip_address: str
    result: AuditResultEnum
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
