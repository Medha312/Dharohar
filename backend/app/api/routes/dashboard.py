from typing import List
from fastapi import APIRouter
from sqlalchemy import desc, func, select

from app.api.deps import CurrentUserDep, SessionDep
from app.models.document import Document
from app.models.processing_job import ProcessingJob
from app.models.verification import VerificationTask
from app.schemas.admin import (
    DashboardProcessing,
    DashboardSummary,
    DashboardVerification,
)
from app.schemas.document import DocumentRead
from app.utils.enums import DocumentStatus, ProcessingStatus, TaskStatus

router = APIRouter(prefix="/dashboard")


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    db: SessionDep,
    current_user: CurrentUserDep,
) -> DashboardSummary:
    total_docs = db.scalar(select(func.count(Document.id))) or 0
    processing_count = db.scalar(
        select(func.count(Document.id)).where(Document.status == DocumentStatus.PROCESSING)
    ) or 0
    completed_count = db.scalar(
        select(func.count(Document.id)).where(
            Document.status.in_([DocumentStatus.VERIFIED, DocumentStatus.AWAITING_VERIFICATION])
        )
    ) or 0
    failed_count = db.scalar(
        select(func.count(Document.id)).where(Document.status == DocumentStatus.FAILED)
    ) or 0
    awaiting_verification_count = db.scalar(
        select(func.count(Document.id)).where(Document.status == DocumentStatus.AWAITING_VERIFICATION)
    ) or 0
    verified_count = db.scalar(
        select(func.count(Document.id)).where(Document.status == DocumentStatus.VERIFIED)
    ) or 0

    return DashboardSummary(
        total_documents=total_docs,
        processing_count=processing_count,
        completed_count=completed_count,
        failed_count=failed_count,
        awaiting_verification_count=awaiting_verification_count,
        verified_count=verified_count,
    )


@router.get("/recent-documents", response_model=List[DocumentRead])
def get_recent_documents(
    db: SessionDep,
    current_user: CurrentUserDep,
) -> List[Document]:
    query = select(Document).order_by(desc(Document.created_at)).limit(10)
    return list(db.scalars(query).all())


@router.get("/processing", response_model=DashboardProcessing)
def get_processing_dashboard(
    db: SessionDep,
    current_user: CurrentUserDep,
) -> DashboardProcessing:
    queued_jobs = db.scalar(
        select(func.count(ProcessingJob.id)).where(ProcessingJob.status == ProcessingStatus.QUEUED)
    ) or 0
    active_jobs = db.scalar(
        select(func.count(ProcessingJob.id)).where(ProcessingJob.status == ProcessingStatus.PROCESSING)
    ) or 0
    failed_jobs = db.scalar(
        select(func.count(ProcessingJob.id)).where(ProcessingJob.status == ProcessingStatus.FAILED)
    ) or 0

    return DashboardProcessing(
        queued_jobs=queued_jobs,
        active_jobs=active_jobs,
        failed_jobs=failed_jobs,
        average_processing_time=1.25,
    )


@router.get("/verification", response_model=DashboardVerification)
def get_verification_dashboard(
    db: SessionDep,
    current_user: CurrentUserDep,
) -> DashboardVerification:
    pending = db.scalar(
        select(func.count(VerificationTask.id)).where(VerificationTask.status == TaskStatus.PENDING)
    ) or 0
    in_review = db.scalar(
        select(func.count(VerificationTask.id)).where(VerificationTask.status == TaskStatus.IN_REVIEW)
    ) or 0
    completed = db.scalar(
        select(func.count(VerificationTask.id)).where(VerificationTask.status == TaskStatus.COMPLETED)
    ) or 0
    rejected = db.scalar(
        select(func.count(VerificationTask.id)).where(VerificationTask.status == TaskStatus.REJECTED)
    ) or 0

    return DashboardVerification(
        pending_tasks=pending,
        in_review_tasks=in_review,
        completed_tasks=completed,
        rejected_tasks=rejected,
    )
