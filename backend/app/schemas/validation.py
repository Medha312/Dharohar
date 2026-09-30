import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.utils.enums import Severity, ValidationIssueType


class ValidationIssueRead(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    field_id: Optional[uuid.UUID] = None
    issue_type: ValidationIssueType
    severity: Severity
    message: str
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
