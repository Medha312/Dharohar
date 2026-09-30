import io
import os
import uuid
from pathlib import Path
from typing import List, Optional, Tuple
from fastapi import HTTPException, UploadFile, status
from PIL import Image
import pypdf
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.document import Document
from app.models.document_page import DocumentPage
from app.models.user import User
from app.services.audit_service import audit_service
from app.services.storage_service import storage_service
from app.utils.enums import AuditAction, DocumentStatus
from app.utils.file_validation import sanitize_filename, validate_file

settings = get_settings()


class DocumentService:
    def create_document_from_upload(
        self,
        db: Session,
        file: UploadFile,
        current_user: User,
    ) -> Document:
        """
        Validates uploaded file, saves original in storage, counts/extracts pages,
        and creates Document + DocumentPage database records.
        """
        validate_file(file)

        # Read content and validate size
        file_bytes = file.file.read()
        file_size = len(file_bytes)
        if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES / (1024*1024):.1f} MB",
            )

        clean_name = sanitize_filename(file.filename or "uploaded_document")
        _, ext = os.path.splitext(clean_name.lower())
        file_type = ext.lstrip(".")

        # Save original file
        storage_path = storage_service.save_file(
            file_data=file_bytes,
            destination_filename=clean_name,
            subfolder="originals",
        )

        # Create Document record
        doc = Document(
            user_id=current_user.id,
            original_filename=clean_name,
            storage_path=storage_path,
            file_type=file_type,
            file_size=file_size,
            page_count=1,
            status=DocumentStatus.UPLOADED,
        )
        db.add(doc)
        db.flush()

        # Handle pages
        self._process_document_pages(db, doc, file_bytes, ext)

        audit_service.log(
            db=db,
            action=AuditAction.DOCUMENT_CREATED,
            entity_type="Document",
            entity_id=str(doc.id),
            user_id=current_user.id,
            document_id=doc.id,
            new_value={"filename": clean_name, "pages": doc.page_count},
        )

        return doc

    def _process_document_pages(
        self,
        db: Session,
        doc: Document,
        file_bytes: bytes,
        ext: str,
    ) -> None:
        """Parses PDF pages or image dimensions and inserts DocumentPage records."""
        if ext == ".pdf":
            try:
                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                num_pages = len(reader.pages)
                doc.page_count = num_pages

                for idx in range(num_pages):
                    page_num = idx + 1
                    # In a full PDF pipeline, pages are rendered to images.
                    # We create a placeholder page image or copy for OCR:
                    page_img = Image.new("RGB", (1200, 1600), color="white")
                    img_byte_arr = io.BytesIO()
                    page_img.save(img_byte_arr, format="PNG")
                    page_storage_path = storage_service.save_file(
                        file_data=img_byte_arr.getvalue(),
                        destination_filename=f"doc_{doc.id}_page_{page_num}.png",
                        subfolder="pages",
                    )

                    doc_page = DocumentPage(
                        document_id=doc.id,
                        page_number=page_num,
                        original_image_path=page_storage_path,
                        width=1200,
                        height=1600,
                        status="PENDING",
                    )
                    db.add(doc_page)
            except Exception as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to parse PDF document: {str(exc)}",
                )
        else:
            # Direct Image (.jpg, .jpeg, .png)
            try:
                with Image.open(io.BytesIO(file_bytes)) as img:
                    width, height = img.size

                # Save page image
                page_storage_path = storage_service.save_file(
                    file_data=file_bytes,
                    destination_filename=f"doc_{doc.id}_page_1{ext}",
                    subfolder="pages",
                )

                doc.page_count = 1
                doc_page = DocumentPage(
                    document_id=doc.id,
                    page_number=1,
                    original_image_path=page_storage_path,
                    width=width,
                    height=height,
                    status="PENDING",
                )
                db.add(doc_page)
            except Exception as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to process image file: {str(exc)}",
                )

        db.flush()

    def get_documents(
        self,
        db: Session,
        current_user: User,
        status_filter: Optional[DocumentStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Document], int]:
        query = select(Document)
        # Non-admins only see their own documents
        if current_user.role != "ADMIN" and current_user.role != "VERIFIER":
            query = query.where(Document.user_id == current_user.id)
        if status_filter:
            query = query.where(Document.status == status_filter)

        from sqlalchemy import func
        count_query = select(func.count()).select_from(query.subquery())
        total = db.scalar(count_query) or 0

        query = query.order_by(desc(Document.created_at)).offset(offset).limit(limit)
        return list(db.scalars(query).all()), total

    def get_document_by_id(
        self,
        db: Session,
        document_id: uuid.UUID,
        current_user: Optional[User] = None,
    ) -> Optional[Document]:
        doc = db.get(Document, document_id)
        if not doc:
            return None
        if current_user and current_user.role not in ["ADMIN", "VERIFIER"]:
            if doc.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this document",
                )
        return doc

    def delete_document(
        self,
        db: Session,
        document: Document,
        current_user: User,
    ) -> None:
        doc_id = document.id
        # Delete original file
        storage_service.delete_file(document.storage_path)

        # Delete page files
        for page in document.pages:
            storage_service.delete_file(page.original_image_path)
            if page.enhanced_image_path:
                storage_service.delete_file(page.enhanced_image_path)

        db.delete(document)
        db.flush()

        audit_service.log(
            db=db,
            action=AuditAction.DOCUMENT_DELETED,
            entity_type="Document",
            entity_id=str(doc_id),
            user_id=current_user.id,
        )


document_service = DocumentService()
