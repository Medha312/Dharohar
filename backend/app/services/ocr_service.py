import time
import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.document_page import DocumentPage
from app.models.model_version import ModelVersion
from app.models.ocr_region import OCRRegion
from app.models.ocr_result import OCRResult
from app.services.storage_service import storage_service
from app.utils.enums import ModelType, TextType
from ml.ocr.inference import OCRModel

settings = get_settings()


class OCRService:
    def __init__(self):
        self.model = OCRModel(settings.OCR_MODEL_PATH)

    def _get_or_create_model_version(self, db: Session) -> uuid.UUID:
        mv = db.scalar(
            select(ModelVersion).where(
                ModelVersion.model_type == ModelType.OCR,
                ModelVersion.is_active == True,
            )
        )
        if not mv:
            mv = ModelVersion(
                model_type=ModelType.OCR,
                version="1.0.0",
                file_reference=settings.OCR_MODEL_PATH,
                framework="pytorch",
                is_active=True,
            )
            db.add(mv)
            db.flush()
        return mv.id

    def process_page_ocr(self, db: Session, page: DocumentPage) -> OCRResult:
        """
        Runs OCR on page image (preferring enhanced image if present).
        Records raw OCRResult and individual OCRRegion bounding boxes.
        """
        image_path = page.enhanced_image_path or page.original_image_path
        abs_image_path = storage_service.get_absolute_path(image_path)

        start_time = time.time()
        prediction = self.model.predict(str(abs_image_path))
        elapsed = time.time() - start_time

        model_version_id = self._get_or_create_model_version(db)

        ocr_result = OCRResult(
            document_page_id=page.id,
            language=prediction.get("language", "hi"),
            script=prediction.get("script", "Devanagari"),
            raw_text=prediction.get("raw_text", ""),
            confidence=prediction.get("confidence", 0.0),
            model_version_id=model_version_id,
            processing_time=round(elapsed, 4),
        )
        db.add(ocr_result)
        db.flush()

        # Add regions
        for reg in prediction.get("regions", []):
            ocr_region = OCRRegion(
                ocr_result_id=ocr_result.id,
                text=reg.get("text", ""),
                text_type=TextType(reg.get("text_type", TextType.PRINTED)),
                confidence=reg.get("confidence", 0.0),
                x1=reg.get("x1", 0.0),
                y1=reg.get("y1", 0.0),
                x2=reg.get("x2", 0.0),
                y2=reg.get("y2", 0.0),
            )
            db.add(ocr_region)

        db.flush()
        return ocr_result


ocr_service = OCRService()
