import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import desc, func, select

from app.api.deps import AdminUserDep, SessionDep
from app.models.audit_log import AuditLog
from app.models.model_version import ModelVersion
from app.models.processing_job import ProcessingJob
from app.models.user import User
from app.schemas.admin import (
    AuditLogRead,
    ModelVersionCreate,
    ModelVersionRead,
)
from app.schemas.common import PaginatedResponse
from app.schemas.processing import ProcessingJobRead
from app.schemas.user import UserAdminUpdate, UserRead
from app.services.audit_service import audit_service
from app.utils.enums import AuditAction

router = APIRouter(prefix="/admin")


@router.get("/users", response_model=PaginatedResponse[UserRead])
def list_admin_users(
    db: SessionDep,
    admin: AdminUserDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[UserRead]:
    offset = (page - 1) * page_size
    query = select(User).order_by(desc(User.created_at))
    total = db.scalar(select(func.count(User.id))) or 0
    users = list(db.scalars(query.offset(offset).limit(page_size)).all())

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(
        items=users,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.patch("/users/{user_id}", response_model=UserRead)
def update_admin_user(
    user_id: uuid.UUID,
    user_in: UserAdminUpdate,
    db: SessionDep,
    admin: AdminUserDep,
) -> User:
    target_user = db.get(User, user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    old_data = {
        "name": target_user.name,
        "email": target_user.email,
        "role": target_user.role.value,
        "is_active": target_user.is_active,
        "is_verified": target_user.is_verified,
    }

    update_dict = user_in.model_dump(exclude_unset=True)
    for field_name, value in update_dict.items():
        if value is not None:
            setattr(target_user, field_name, value)

    db.commit()
    db.refresh(target_user)

    audit_service.log(
        db=db,
        action=AuditAction.USER_UPDATED,
        entity_type="User",
        entity_id=str(target_user.id),
        user_id=admin.id,
        old_value=old_data,
        new_value=update_dict,
    )

    return target_user


@router.get("/processing", response_model=List[ProcessingJobRead])
def list_admin_processing_jobs(
    db: SessionDep,
    admin: AdminUserDep,
    limit: int = Query(50, ge=1, le=200),
) -> List[ProcessingJob]:
    query = select(ProcessingJob).order_by(desc(ProcessingJob.created_at)).limit(limit)
    return list(db.scalars(query).all())


@router.get("/model-versions", response_model=List[ModelVersionRead])
def list_model_versions(
    db: SessionDep,
    admin: AdminUserDep,
) -> List[ModelVersion]:
    query = select(ModelVersion).order_by(desc(ModelVersion.created_at))
    return list(db.scalars(query).all())


@router.post("/model-versions", response_model=ModelVersionRead, status_code=status.HTTP_201_CREATED)
def create_model_version(
    mv_in: ModelVersionCreate,
    db: SessionDep,
    admin: AdminUserDep,
) -> ModelVersion:
    mv = ModelVersion(
        model_type=mv_in.model_type,
        version=mv_in.version,
        file_reference=mv_in.file_reference,
        framework=mv_in.framework,
        is_active=mv_in.is_active,
    )
    db.add(mv)
    db.commit()
    db.refresh(mv)
    return mv


@router.get("/audit-logs", response_model=PaginatedResponse[AuditLogRead])
def list_audit_logs(
    db: SessionDep,
    admin: AdminUserDep,
    document_id: Optional[uuid.UUID] = Query(None),
    user_id: Optional[uuid.UUID] = Query(None),
    action: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> PaginatedResponse[AuditLogRead]:
    offset = (page - 1) * page_size
    logs = audit_service.get_logs(
        db=db,
        document_id=document_id,
        user_id=user_id,
        action=action,
        limit=page_size,
        offset=offset,
    )
    # Simple count query
    count_q = select(func.count(AuditLog.id))
    if document_id:
        count_q = count_q.where(AuditLog.document_id == document_id)
    if user_id:
        count_q = count_q.where(AuditLog.user_id == user_id)
    if action:
        count_q = count_q.where(AuditLog.action == action)
    total = db.scalar(count_q) or 0

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(
        items=logs,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
