"""Business logic for audit logging: sanitizes event metadata to strip PII
before delegating persistence to AuditRepository. Called from services and
api/deps whenever a security-relevant event occurs.
"""
from uuid import UUID
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.audit import AuditActionEnum, AuditResultEnum, AuditLog
from app.schemas.audit import AuditLogCreate
from app.repositories.audit_repo import AuditRepository


class AuditService:
    @staticmethod
    def log_event(
        db: Session,
        action: AuditActionEnum | str,
        ip_address: str,
        result: AuditResultEnum,
        user_id: Optional[UUID] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """
        Record security and operational events to audit_logs.
        Strictly sanitizes metadata to avoid PII (emails, names, phone numbers).
        """
        sanitized_meta = None
        if metadata:
            # Strip any accidental PII keys
            pii_keys = {"email", "password", "name", "full_name", "phone", "mobile"}
            sanitized_meta = {k: v for k, v in metadata.items() if k.lower() not in pii_keys}

        log_data = AuditLogCreate(
            user_id=user_id,
            action=action.value if isinstance(action, AuditActionEnum) else str(action),
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            result=result,
            metadata=sanitized_meta
        )

        audit_entry = AuditRepository.create(db, log_data)
        return audit_entry
