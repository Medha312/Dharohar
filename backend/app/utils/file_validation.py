import os
from fastapi import HTTPException, UploadFile, status

from app.core.config import get_settings

settings = get_settings()

ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
}


def sanitize_filename(filename: str) -> str:
    cleaned = os.path.basename(filename)
    return cleaned.replace(" ", "_").replace("..", "_")


def validate_file(file: UploadFile) -> None:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    _, ext = os.path.splitext(file.filename.lower())
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Allowed extensions are: {', '.join(settings.ALLOWED_EXTENSIONS)}",
        )

    # Check content type if available
    content_type = file.content_type
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        # If content_type is octet-stream, extension check was already done
        if content_type != "application/octet-stream":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid MIME type '{content_type}' for document upload",
            )
