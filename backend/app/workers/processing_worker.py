import logging
import uuid

from app.db.database import SessionLocal
from app.services.processing_service import processing_service
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="process_document_task")
def process_document_task(job_id_str: str) -> bool:
    """
    Celery task that executes the complete document processing pipeline asynchronously.
    """
    logger.info("Starting processing task for job %s", job_id_str)
    db = SessionLocal()
    try:
        job_uuid = uuid.UUID(job_id_str)
        processing_service.execute_pipeline(db, job_uuid)
        db.commit()
        logger.info("Successfully completed processing task for job %s", job_id_str)
        return True
    except Exception as exc:
        db.rollback()
        logger.error("Error processing document task: %s", exc, exc_info=True)
        return False
    finally:
        db.close()
