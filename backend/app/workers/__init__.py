from app.workers.celery_app import celery_app
from app.workers.processing_worker import process_document_task

__all__ = ["celery_app", "process_document_task"]
