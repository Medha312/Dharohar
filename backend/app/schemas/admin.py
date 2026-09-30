import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.document import DocumentRead
from app.utils.enums import ModelType


class ModelVersionCreate(BaseModel):
    model_type: ModelType
    version: str
    file_reference: str
    framework: str = "pytorch"
    is_active: bool = True


class ModelVersionRead(ModelVersionCreate):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogRead(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    document_id: Optional[uuid.UUID] = None
    entity_type: str
    entity_id: str
    action: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    metadata_json: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardSummary(BaseModel):
    total_documents: int
    processing_count: int
    completed_count: int
    failed_count: int
    awaiting_verification_count: int
    verified_count: int


class DashboardProcessing(BaseModel):
    queued_jobs: int
    active_jobs: int
    failed_jobs: int
    average_processing_time: float


class DashboardVerification(BaseModel):
    pending_tasks: int
    in_review_tasks: int
    completed_tasks: int
    rejected_tasks: int
