import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUserDep, SessionDep
from app.models.document_page import DocumentPage
from app.models.extracted_field import ExtractedField
from app.models.land_record import LandRecord
from app.models.ocr_result import OCRResult
from app.schemas.document import DocumentPageRead
from app.schemas.field import DocumentFieldsResponse, ExtractedFieldRead
from app.schemas.land_record import LandRecordRead
from app.schemas.ocr import DocumentOCRResponse, OCRResultRead
from app.services.document_service import document_service
from app.services.land_record_service import land_record_service

router = APIRouter(prefix="/documents")


@router.get("/{document_id}/ocr", response_model=DocumentOCRResponse)
def get_document_ocr(
    document_id: uuid.UUID,
    db: SessionDep,
    current_user: CurrentUserDep,
) -> DocumentOCRResponse:
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

    # Collect OCR across pages
    ocr_list: List[OCRResult] = []
    for page in doc.pages:
        for res in page.ocr_results:
            ocr_list.append(res)

    return DocumentOCRResponse(
        document_id=doc.id,
        pages_ocr=ocr_list,
    )


@router.get("/{document_id}/fields", response_model=DocumentFieldsResponse)
def get_document_fields(
    document_id: uuid.UUID,
    db: SessionDep,
    current_user: CurrentUserDep,
) -> DocumentFieldsResponse:
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

    fields = list(
        db.scalars(
            select(ExtractedField).where(ExtractedField.document_id == document_id)
        ).all()
    )
    return DocumentFieldsResponse(
        document_id=doc.id,
        fields=fields,
    )


@router.get("/{document_id}/land-record", response_model=LandRecordRead)
def get_document_land_record(
    document_id: uuid.UUID,
    db: SessionDep,
    current_user: CurrentUserDep,
) -> LandRecord:
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

    record = land_record_service.get_record_by_document(db=db, document_id=document_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Land record has not yet been generated for this document",
        )
    return record


@router.get("/{document_id}/enhanced-pages", response_model=List[DocumentPageRead])
def get_document_enhanced_pages(
    document_id: uuid.UUID,
    db: SessionDep,
    current_user: CurrentUserDep,
) -> List[DocumentPage]:
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

    enhanced = [p for p in doc.pages if p.enhanced_image_path is not None]
    return enhanced
