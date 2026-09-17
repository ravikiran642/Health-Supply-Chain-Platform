from typing import Optional, Sequence
from uuid import UUID
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogCreate


class AuditRepository:
    @staticmethod
    def create(db: Session, audit_in: AuditLogCreate) -> AuditLog:
        """Create and write an audit log entry."""
        log = AuditLog(
            user_id=audit_in.user_id,
            action=audit_in.action,
            resource_type=audit_in.resource_type,
            resource_id=audit_in.resource_id,
            ip_address=audit_in.ip_address,
            result=audit_in.result,
            metadata_=audit_in.metadata
        )
        db.add(log)
        db.flush()
        return log

    @staticmethod
    def get_logs(
        db: Session,
        limit: int = 100,
        action: Optional[str] = None
    ) -> Sequence[AuditLog]:
        """Fetch latest audit logs for admin inspection."""
        stmt = select(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        return db.scalars(stmt).all()
