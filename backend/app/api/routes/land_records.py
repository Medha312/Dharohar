import uuid
from datetime import date
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUserDep, SessionDep, VerifierOrAdminDep
from app.models.land_record import LandRecord
from app.schemas.common import PaginatedResponse
from app.schemas.land_record import LandRecordRead, LandRecordUpdate
from app.services.audit_service import audit_service
from app.services.land_record_service import land_record_service
from app.utils.enums import AuditAction

router = APIRouter(prefix="/land-records")


@router.get("", response_model=PaginatedResponse[LandRecordRead])
def list_land_records(
    db: SessionDep,
    current_user: CurrentUserDep,
    owner_name: Optional[str] = Query(None),
    khata_number: Optional[str] = Query(None),
    khasra_number: Optional[str] = Query(None),
    survey_number: Optional[str] = Query(None),
    village: Optional[str] = Query(None),
    tehsil: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    created_after: Optional[date] = Query(None, description="Include records created on or after this date (YYYY-MM-DD)"),
    created_before: Optional[date] = Query(None, description="Include records created on or before this date (YYYY-MM-DD)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[LandRecordRead]:
    offset = (page - 1) * page_size
    records, total = land_record_service.get_records(
        db=db,
        owner_name=owner_name,
        khata_number=khata_number,
        khasra_number=khasra_number,
        survey_number=survey_number,
        village=village,
        tehsil=tehsil,
        district=district,
        status=status,
        created_after=created_after,
        created_before=created_before,
        limit=page_size,
        offset=offset,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(
        items=records,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{record_id}", response_model=LandRecordRead)
def get_land_record(
    record_id: uuid.UUID,
    db: SessionDep,
    current_user: CurrentUserDep,
) -> LandRecord:
    record = land_record_service.get_record_by_id(db=db, record_id=record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Land record not found",
        )
    return record


@router.patch("/{record_id}", response_model=LandRecordRead)
def update_land_record(
    record_id: uuid.UUID,
    record_update: LandRecordUpdate,
    db: SessionDep,
    current_user: VerifierOrAdminDep,
) -> LandRecord:
    record = land_record_service.get_record_by_id(db=db, record_id=record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Land record not found",
        )

    old_vals = {
        "owner_name": record.owner_name,
        "khata_number": record.khata_number,
        "khasra_number": record.khasra_number,
    }

    update_dict = record_update.model_dump(exclude_unset=True)
    for field_name, value in update_dict.items():
        if hasattr(record, field_name) and value is not None:
            setattr(record, field_name, value)

    db.commit()
    db.refresh(record)

    audit_service.log(
        db=db,
        action=AuditAction.RECORD_VERIFIED,
        entity_type="LandRecord",
        entity_id=str(record.id),
        user_id=current_user.id,
        document_id=record.document_id,
        old_value=old_vals,
        new_value=update_dict,
    )

    return record
