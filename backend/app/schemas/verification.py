import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.field import ExtractedFieldRead
from app.utils.enums import TaskPriority, TaskStatus, VerificationActionType


class VerificationActionRead(BaseModel):
    id: uuid.UUID
    verification_task_id: uuid.UUID
    field_id: uuid.UUID
    verifier_id: uuid.UUID
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    action: VerificationActionType
    comment: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VerificationFieldActionRequest(BaseModel):
    action: VerificationActionType  # APPROVED, CORRECTED, REJECTED
    new_value: Optional[str] = None
    comment: Optional[str] = None


class VerificationTaskRead(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    assigned_to: Optional[uuid.UUID] = None
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class VerificationTaskDetail(VerificationTaskRead):
    fields: List[ExtractedFieldRead] = []
    actions: List[VerificationActionRead] = []

    model_config = ConfigDict(from_attributes=True)
