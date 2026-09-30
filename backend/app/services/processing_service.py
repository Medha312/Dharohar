import logging
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.processing_job import ProcessingJob
from app.services.audit_service import audit_service
from app.services.enhancement_service import enhancement_service
from app.services.extraction_service import extraction_service
from app.services.land_record_service import land_record_service
from app.services.ocr_service import ocr_service
from app.services.validation_service import validation_service
from app.services.verification_service import verification_service
from app.utils.enums import (
    AuditAction,
    DocumentStatus,
    ProcessingStage,
    ProcessingStatus,
    TaskPriority,
)

logger = logging.getLogger(__name__)


class ProcessingService:
    def create_job(self, db: Session, document: Document) -> ProcessingJob:
        """Creates a new queued processing job for the document."""
        job = ProcessingJob(
            document_id=document.id,
            status=ProcessingStatus.QUEUED,
            current_stage=ProcessingStage.QUEUED,
            progress=0,
        )
        db.add(job)
        document.status = DocumentStatus.QUEUED
        db.flush()

        audit_service.log(
            db=db,
            action=AuditAction.PROCESSING_STARTED,
            entity_type="ProcessingJob",
            entity_id=str(job.id),
            document_id=document.id,
        )
        return job

    def execute_pipeline(self, db: Session, job_id: uuid.UUID) -> ProcessingJob:
        """
        Executes the entire end-to-end document processing pipeline.
        Tracks stages and progress percentage.
        """
        job = db.get(ProcessingJob, job_id)
        if not job:
            raise ValueError(f"ProcessingJob {job_id} not found")

        doc = db.get(Document, job.document_id)
        if not doc:
            raise ValueError(f"Document {job.document_id} not found")

        try:
            job.status = ProcessingStatus.PROCESSING
            job.started_at = datetime.now(timezone.utc)
            doc.status = DocumentStatus.PROCESSING
            db.flush()

            # Stage 1: PAGE_PROCESSING
            job.current_stage = ProcessingStage.PAGE_PROCESSING
            job.progress = 15
            db.flush()
            logger.info("Stage 1/9: Page processing for doc %s", doc.id)

            # Stage 2: STRUCTURE_DETECTION
            job.current_stage = ProcessingStage.STRUCTURE_DETECTION
            job.progress = 25
            db.flush()
            logger.info("Stage 2/9: Structure detection for doc %s", doc.id)

            # Stage 3: IMAGE_ENHANCEMENT
            job.current_stage = ProcessingStage.IMAGE_ENHANCEMENT
            job.progress = 40
            db.flush()
            logger.info("Stage 3/9: Image enhancement for doc %s", doc.id)
            for page in doc.pages:
                enhancement_service.enhance_page(db, page)

            # Stage 4: LANGUAGE_DETECTION
            job.current_stage = ProcessingStage.LANGUAGE_DETECTION
            job.progress = 50
            db.flush()
            logger.info("Stage 4/9: Language detection for doc %s", doc.id)

            # Stage 5: DOCUMENT_TYPE_DETECTION
            job.current_stage = ProcessingStage.DOCUMENT_TYPE_DETECTION
            job.progress = 60
            db.flush()
            logger.info("Stage 5/9: Document type detection for doc %s", doc.id)

            # Stage 6: OCR
            job.current_stage = ProcessingStage.OCR
            job.progress = 70
            db.flush()
            logger.info("Stage 6/9: OCR extraction for doc %s", doc.id)
            for page in doc.pages:
                ocr_service.process_page_ocr(db, page)

            # Stage 7: FIELD_EXTRACTION
            job.current_stage = ProcessingStage.FIELD_EXTRACTION
            job.progress = 80
            db.flush()
            logger.info("Stage 7/9: Canonical field extraction for doc %s", doc.id)
            extracted_fields = extraction_service.extract_fields_for_document(db, doc)

            # Stage 8: VALIDATION
            job.current_stage = ProcessingStage.VALIDATION
            job.progress = 90
            db.flush()
            logger.info("Stage 8/9: Field validation for doc %s", doc.id)
            issues = validation_service.validate_document_fields(db, doc)

            # Stage 9: VERIFICATION ROUTING & FINALIZATION
            if issues:
                # If there are any validation issues or low confidence fields, route to human verification
                doc.status = DocumentStatus.AWAITING_VERIFICATION
                verification_service.create_task_for_document(
                    db=db,
                    document=doc,
                    priority=TaskPriority.HIGH if any(i.severity == "CRITICAL" for i in issues) else TaskPriority.MEDIUM,
                )
                logger.info("Doc %s has %d issues; routed to human verification", doc.id, len(issues))
            else:
                # No issues: automatically create LandRecord
                doc.status = DocumentStatus.VERIFIED
                land_record_service.create_or_update_from_fields(db, doc)
                logger.info("Doc %s passed validation; LandRecord created", doc.id)

            job.current_stage = ProcessingStage.COMPLETED
            job.status = ProcessingStatus.COMPLETED
            job.progress = 100
            job.completed_at = datetime.now(timezone.utc)
            db.flush()

            audit_service.log(
                db=db,
                action=AuditAction.PROCESSING_COMPLETED,
                entity_type="ProcessingJob",
                entity_id=str(job.id),
                document_id=doc.id,
                new_value={"issues_count": len(issues)},
            )

        except Exception as exc:
            db.rollback()
            # Re-fetch objects after rollback
            job = db.get(ProcessingJob, job_id)
            doc = db.get(Document, job.document_id) if job else None

            if job:
                job.status = ProcessingStatus.FAILED
                job.current_stage = ProcessingStage.FAILED
                job.error_message = str(exc)
                job.completed_at = datetime.now(timezone.utc)
            if doc:
                doc.status = DocumentStatus.FAILED

            db.flush()
            logger.error("Processing pipeline failed for doc: %s", exc, exc_info=True)

            if job and doc:
                audit_service.log(
                    db=db,
                    action=AuditAction.PROCESSING_FAILED,
                    entity_type="ProcessingJob",
                    entity_id=str(job.id),
                    document_id=doc.id,
                    new_value={"error": str(exc)},
                )
            raise

        return job

    def get_latest_job(
        self, db: Session, document_id: uuid.UUID
    ) -> Optional[ProcessingJob]:
        return db.scalar(
            select(ProcessingJob)
            .where(ProcessingJob.document_id == document_id)
            .order_by(desc(ProcessingJob.created_at))
        )


processing_service = ProcessingService()
