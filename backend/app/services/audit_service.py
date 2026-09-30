import json
import uuid
from typing import Any, List, Optional
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditService:
    @staticmethod
    def log(
        db: Session,
        action: str,
        entity_type: str,
        entity_id: str,
        user_id: Optional[uuid.UUID] = None,
        document_id: Optional[uuid.UUID] = None,
        old_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        metadata: Optional[dict] = None,
    ) -> AuditLog:
        old_val_str = (
            json.dumps(old_value, default=str)
            if isinstance(old_value, (dict, list))
            else (str(old_value) if old_value is not None else None)
        )
        new_val_str = (
            json.dumps(new_value, default=str)
            if isinstance(new_value, (dict, list))
            else (str(new_value) if new_value is not None else None)
        )
        meta_str = json.dumps(metadata, default=str) if metadata else None

        audit_entry = AuditLog(
            user_id=user_id,
            document_id=document_id,
            entity_type=entity_type,
            entity_id=str(entity_id),
            action=action,
            old_value=old_val_str,
            new_value=new_val_str,
            metadata_json=meta_str,
        )
        db.add(audit_entry)
        db.flush()
        return audit_entry

    @staticmethod
    def get_logs(
        db: Session,
        document_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        action: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AuditLog]:
        query = select(AuditLog)
        if document_id:
            query = query.where(AuditLog.document_id == document_id)
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        if action:
            query = query.where(AuditLog.action == action)

        query = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit)
        return list(db.scalars(query).all())


audit_service = AuditService()
