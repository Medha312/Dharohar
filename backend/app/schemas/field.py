import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from app.utils.enums import ValidationStatus, VerificationStatus


class ExtractedFieldRead(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    field_name: str
    raw_value: Optional[str] = None
    extracted_value: Optional[str] = None
    confidence: Optional[float] = None
    source_page_id: Optional[uuid.UUID] = None
    source_ocr_region_id: Optional[uuid.UUID] = None
    validation_status: ValidationStatus
    verification_status: VerificationStatus
    verified_value: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FieldCorrectionRequest(BaseModel):
    verified_value: str
    comment: Optional[str] = None


class DocumentFieldsResponse(BaseModel):
    document_id: uuid.UUID
    fields: List[ExtractedFieldRead]
