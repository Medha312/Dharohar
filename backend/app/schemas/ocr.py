import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from app.utils.enums import TextType


class OCRRegionRead(BaseModel):
    id: uuid.UUID
    ocr_result_id: uuid.UUID
    text: str
    text_type: TextType
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float

    model_config = ConfigDict(from_attributes=True)


class OCRResultRead(BaseModel):
    id: uuid.UUID
    document_page_id: uuid.UUID
    language: str
    script: str
    raw_text: str
    confidence: float
    processing_time: Optional[float] = None
    created_at: datetime
    regions: List[OCRRegionRead] = []

    model_config = ConfigDict(from_attributes=True)


class DocumentOCRResponse(BaseModel):
    document_id: uuid.UUID
    pages_ocr: List[OCRResultRead] = []
