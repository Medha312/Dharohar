import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.utils.enums import ProcessingStage, ProcessingStatus


class ProcessingJobRead(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    status: ProcessingStatus
    current_stage: ProcessingStage
    progress: int
    error_message: Optional[str] = None
    retry_count: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProcessingStatusResponse(BaseModel):
    document_id: uuid.UUID
    status: ProcessingStatus
    current_stage: ProcessingStage
    progress: int
    error_message: Optional[str] = None
    job_id: Optional[uuid.UUID] = None
