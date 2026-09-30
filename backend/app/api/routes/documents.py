import uuid
from typing import List, Optional
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status

from app.api.deps import CurrentUserDep, SessionDep
from app.models.document import Document
from app.models.document_page import DocumentPage
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.document import DocumentDetail, DocumentPageRead, DocumentRead
from app.services.document_service import document_service
from app.utils.enums import DocumentStatus

router = APIRouter(prefix="/documents")


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
def upload_document(
    db: SessionDep,
    current_user: CurrentUserDep,
    file: UploadFile = File(...),
) -> Document:
    doc = document_service.create_document_from_upload(
        db=db,
        file=file,
        current_user=current_user,
    )
    db.commit()
    db.refresh(doc)
    return doc


@router.get("", response_model=PaginatedResponse[DocumentRead])
def list_documents(
    db: SessionDep,
    current_user: CurrentUserDep,
    status_filter: Optional[DocumentStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[DocumentRead]:
    offset = (page - 1) * page_size
    docs, total = document_service.get_documents(
        db=db,
        current_user=current_user,
        status_filter=status_filter,
        limit=page_size,
        offset=offset,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(
        items=docs,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(
    document_id: uuid.UUID,
    db: SessionDep,
    current_user: CurrentUserDep,
) -> Document:
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
    return doc


@router.delete("/{document_id}", response_model=MessageResponse)
def delete_document(
    document_id: uuid.UUID,
    db: SessionDep,
    current_user: CurrentUserDep,
) -> MessageResponse:
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
    document_service.delete_document(db=db, document=doc, current_user=current_user)
    db.commit()
    return MessageResponse(message=f"Document {document_id} deleted successfully")


@router.get("/{document_id}/pages", response_model=List[DocumentPageRead])
def get_document_pages(
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
    return doc.pages
