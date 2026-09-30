from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.document_page import DocumentPage
from app.services.storage_service import storage_service
from ml.enhancement.inference import EnhancementModel

settings = get_settings()


class EnhancementService:
    def __init__(self):
        self.model = EnhancementModel(settings.ENHANCEMENT_MODEL_PATH)

    def enhance_page(self, db: Session, page: DocumentPage) -> str:
        """
        Enhances document page image using ML model or image processing pipeline.
        Saves enhanced image via storage service and updates DocumentPage record.
        """
        abs_original_path = storage_service.get_absolute_path(page.original_image_path)
        
        # Prepare output path
        enhanced_subfolder = "enhanced"
        dest_filename = f"enhanced_page_{page.page_number}_{Path(abs_original_path).name}"
        abs_output_folder = storage_service.get_absolute_path(enhanced_subfolder)
        abs_output_folder.mkdir(parents=True, exist_ok=True)
        abs_output_path = abs_output_folder / dest_filename

        # Run inference
        self.model.predict(str(abs_original_path), str(abs_output_path))

        relative_path = f"{enhanced_subfolder}/{dest_filename}"
        page.enhanced_image_path = relative_path
        page.status = "ENHANCED"
        db.flush()

        return relative_path


enhancement_service = EnhancementService()
