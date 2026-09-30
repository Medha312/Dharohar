import logging
import uuid
from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUserDep, SessionDep
from app.models.document import Document
from app.models.processing_job import ProcessingJob
from app.schemas.processing import ProcessingJobRead, ProcessingStatusResponse
from app.services.document_service import document_service
from app.services.processing_service import processing_service
from app.utils.enums import DocumentStatus, ProcessingStatus
from app.workers.processing_worker import process_document_task

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents")


@router.post("/{document_id}/process", response_model=ProcessingJobRead, status_code=status.HTTP_202_ACCEPTED)
def start_processing(
    document_id: uuid.UUID,
    db: SessionDep,
    current_user: CurrentUserDep,
) -> ProcessingJob:
    doc = document_service.get_document_by_id(
        db=db,
        document_id=document_id,
        current_user=current_user,
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Create job record
    job = processing_service.create_job(db=db, document=doc)
    db.commit()
    db.refresh(job)

    # Dispatch to Celery background worker, with graceful fallback to inline execution if broker is offline
    try:
        process_document_task.delay(str(job.id))
    except Exception as exc:
        logger.warning("Celery dispatch failed (%s), running synchronous pipeline execution", exc)
        processing_service.execute_pipeline(db=db, job_id=job.id)
        db.commit()
        db.refresh(job)

    return job


@router.get("/{document_id}/status", response_model=ProcessingStatusResponse)
def get_processing_status(
    document_id: uuid.UUID,
    db: SessionDep,
    current_user: CurrentUserDep,
) -> ProcessingStatusResponse:
    doc = document_service.get_document_by_id(
        db=db,
        document_id=document_id,
        current_user=current_user,
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    job = processing_service.get_latest_job(db=db, document_id=document_id)
    if not job:
        return ProcessingStatusResponse(
            document_id=doc.id,
            status=ProcessingStatus.QUEUED,
            current_stage=job.current_stage if job else "QUEUED",
            progress=0,
            job_id=None,
        )

    return ProcessingStatusResponse(
        document_id=doc.id,
        status=job.status,
        current_stage=job.current_stage,
        progress=job.progress,
        error_message=job.error_message,
        job_id=job.id,
    )


@router.post("/{document_id}/retry", response_model=ProcessingJobRead)
def retry_processing(
    document_id: uuid.UUID,
    db: SessionDep,
    current_user: CurrentUserDep,
) -> ProcessingJob:
    doc = document_service.get_document_by_id(
        db=db,
        document_id=document_id,
        current_user=current_user,
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    job = processing_service.create_job(db=db, document=doc)
    job.retry_count += 1
    db.commit()
    db.refresh(job)

    try:
        process_document_task.delay(str(job.id))
    except Exception as exc:
        logger.warning("Celery dispatch failed (%s), running synchronous pipeline execution", exc)
        processing_service.execute_pipeline(db=db, job_id=job.id)
        db.commit()
        db.refresh(job)

    return job
