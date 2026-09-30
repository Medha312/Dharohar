import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.extracted_field import ExtractedField
from app.models.user import User
from app.models.verification import VerificationAction, VerificationTask
from app.services.audit_service import audit_service
from app.services.land_record_service import land_record_service
from app.utils.enums import (
    AuditAction,
    DocumentStatus,
    TaskPriority,
    TaskStatus,
    VerificationActionType,
    VerificationStatus,
)


class VerificationService:
    def create_task_for_document(
        self,
        db: Session,
        document: Document,
        priority: TaskPriority = TaskPriority.MEDIUM,
    ) -> VerificationTask:
        """Creates a verification task for a document that requires human review."""
        task = VerificationTask(
            document_id=document.id,
            status=TaskStatus.PENDING,
            priority=priority,
        )
        db.add(task)
        db.flush()
        return task

    def get_tasks(
        self,
        db: Session,
        status_filter: Optional[TaskStatus] = None,
        priority_filter: Optional[TaskPriority] = None,
        assigned_to: Optional[uuid.UUID] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[VerificationTask], int]:
        query = select(VerificationTask)
        if status_filter:
            query = query.where(VerificationTask.status == status_filter)
        if priority_filter:
            query = query.where(VerificationTask.priority == priority_filter)
        if assigned_to:
            query = query.where(VerificationTask.assigned_to == assigned_to)

        from sqlalchemy import func
        count_query = select(func.count()).select_from(query.subquery())
        total = db.scalar(count_query) or 0

        query = query.order_by(desc(VerificationTask.created_at)).offset(offset).limit(limit)
        return list(db.scalars(query).all()), total

    def get_task_by_id(
        self,
        db: Session,
        task_id: uuid.UUID,
    ) -> Optional[VerificationTask]:
        return db.get(VerificationTask, task_id)

    def start_task(
        self,
        db: Session,
        task: VerificationTask,
        verifier: User,
    ) -> VerificationTask:
        task.assigned_to = verifier.id
        task.status = TaskStatus.IN_REVIEW
        task.started_at = datetime.now(timezone.utc)
        db.flush()
        return task

    def process_field_action(
        self,
        db: Session,
        task: VerificationTask,
        field: ExtractedField,
        verifier: User,
        action_type: VerificationActionType,
        new_value: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> VerificationAction:
        old_val = field.verified_value or field.extracted_value or field.raw_value

        if action_type == VerificationActionType.APPROVED:
            field.verification_status = VerificationStatus.APPROVED
            field.verified_value = old_val
        elif action_type == VerificationActionType.CORRECTED:
            if not new_value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="new_value is required when correcting a field",
                )
            field.verification_status = VerificationStatus.CORRECTED
            field.verified_value = new_value
        elif action_type == VerificationActionType.REJECTED:
            field.verification_status = VerificationStatus.REJECTED
            field.verified_value = None

        db.flush()

        action = VerificationAction(
            verification_task_id=task.id,
            field_id=field.id,
            verifier_id=verifier.id,
            old_value=old_val,
            new_value=field.verified_value,
            action=action_type,
            comment=comment,
        )
        db.add(action)
        db.flush()

        audit_action_name = (
            AuditAction.FIELD_APPROVED
            if action_type == VerificationActionType.APPROVED
            else (
                AuditAction.FIELD_CORRECTED
                if action_type == VerificationActionType.CORRECTED
                else AuditAction.FIELD_REJECTED
            )
        )
        audit_service.log(
            db=db,
            action=audit_action_name,
            entity_type="ExtractedField",
            entity_id=str(field.id),
            user_id=verifier.id,
            document_id=task.document_id,
            old_value=old_val,
            new_value=field.verified_value,
            metadata={"comment": comment, "field_name": field.field_name},
        )

        return action

    def complete_task(
        self,
        db: Session,
        task: VerificationTask,
        verifier: User,
    ) -> VerificationTask:
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now(timezone.utc)

        # Update document status to VERIFIED
        doc = db.get(Document, task.document_id)
        if doc:
            doc.status = DocumentStatus.VERIFIED
            # Finalize Land Record
            land_record_service.create_or_update_from_fields(
                db=db,
                document=doc,
                verified_by=verifier.id,
            )
            audit_service.log(
                db=db,
                action=AuditAction.RECORD_VERIFIED,
                entity_type="Document",
                entity_id=str(doc.id),
                user_id=verifier.id,
                document_id=doc.id,
            )

        db.flush()
        return task


verification_service = VerificationService()
