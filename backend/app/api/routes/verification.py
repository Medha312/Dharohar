import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import SessionDep, VerifierOrAdminDep
from app.models.extracted_field import ExtractedField
from app.models.verification import VerificationAction, VerificationTask
from app.schemas.common import PaginatedResponse
from app.schemas.verification import (
    VerificationActionRead,
    VerificationFieldActionRequest,
    VerificationTaskDetail,
    VerificationTaskRead,
)
from app.services.verification_service import verification_service
from app.utils.enums import TaskPriority, TaskStatus

router = APIRouter(prefix="/verification")


@router.get("/tasks", response_model=PaginatedResponse[VerificationTaskRead])
def list_verification_tasks(
    db: SessionDep,
    current_user: VerifierOrAdminDep,
    status_filter: Optional[TaskStatus] = Query(None, alias="status"),
    priority_filter: Optional[TaskPriority] = Query(None, alias="priority"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[VerificationTaskRead]:
    offset = (page - 1) * page_size
    tasks, total = verification_service.get_tasks(
        db=db,
        status_filter=status_filter,
        priority_filter=priority_filter,
        limit=page_size,
        offset=offset,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(
        items=tasks,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/tasks/{task_id}", response_model=VerificationTaskDetail)
def get_verification_task(
    task_id: uuid.UUID,
    db: SessionDep,
    current_user: VerifierOrAdminDep,
) -> VerificationTaskDetail:
    task = verification_service.get_task_by_id(db=db, task_id=task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification task not found",
        )

    # Load associated document fields and past actions
    doc = task.document
    return VerificationTaskDetail(
        id=task.id,
        document_id=task.document_id,
        assigned_to=task.assigned_to,
        status=task.status,
        priority=task.priority,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        fields=doc.extracted_fields,
        actions=task.actions,
    )


@router.post("/tasks/{task_id}/start", response_model=VerificationTaskRead)
def start_verification_task(
    task_id: uuid.UUID,
    db: SessionDep,
    current_user: VerifierOrAdminDep,
) -> VerificationTask:
    task = verification_service.get_task_by_id(db=db, task_id=task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification task not found",
        )

    updated_task = verification_service.start_task(
        db=db, task=task, verifier=current_user
    )
    db.commit()
    db.refresh(updated_task)
    return updated_task


@router.patch("/tasks/{task_id}/fields/{field_id}", response_model=VerificationActionRead)
def verify_field_action(
    task_id: uuid.UUID,
    field_id: uuid.UUID,
    action_in: VerificationFieldActionRequest,
    db: SessionDep,
    current_user: VerifierOrAdminDep,
) -> VerificationAction:
    task = verification_service.get_task_by_id(db=db, task_id=task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification task not found",
        )

    field = db.get(ExtractedField, field_id)
    if not field or field.document_id != task.document_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extracted field not found for this document",
        )

    action = verification_service.process_field_action(
        db=db,
        task=task,
        field=field,
        verifier=current_user,
        action_type=action_in.action,
        new_value=action_in.new_value,
        comment=action_in.comment,
    )
    db.commit()
    db.refresh(action)
    return action


@router.post("/tasks/{task_id}/complete", response_model=VerificationTaskRead)
def complete_verification_task(
    task_id: uuid.UUID,
    db: SessionDep,
    current_user: VerifierOrAdminDep,
) -> VerificationTask:
    task = verification_service.get_task_by_id(db=db, task_id=task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification task not found",
        )

    completed_task = verification_service.complete_task(
        db=db,
        task=task,
        verifier=current_user,
    )
    db.commit()
    db.refresh(completed_task)
    return completed_task
