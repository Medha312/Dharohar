import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.document_page import DocumentPage
    from app.models.model_version import ModelVersion
    from app.models.ocr_region import OCRRegion


class OCRResult(Base):
    __tablename__ = "ocr_results"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    document_page_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("document_pages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    language: Mapped[str] = mapped_column(String(32), nullable=False, default="hi")
    script: Mapped[str] = mapped_column(
        String(32), nullable=False, default="Devanagari"
    )
    raw_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    model_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("model_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    processing_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    page: Mapped["DocumentPage"] = relationship(
        "DocumentPage", back_populates="ocr_results"
    )
    regions: Mapped[List["OCRRegion"]] = relationship(
        "OCRRegion",
        back_populates="ocr_result",
        cascade="all, delete-orphan",
    )
    model_version: Mapped[Optional["ModelVersion"]] = relationship(
        "ModelVersion", back_populates="ocr_results"
    )
