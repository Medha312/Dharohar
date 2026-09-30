import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from app.utils.enums import DocumentStatus


class DocumentPageRead(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    page_number: int
    original_image_path: str
    enhanced_image_path: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    status: str
    document_section: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    original_filename: str
    storage_path: str
    file_type: str
    file_size: int
    page_count: int
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentDetail(DocumentRead):
    pages: List[DocumentPageRead] = []

    model_config = ConfigDict(from_attributes=True)
