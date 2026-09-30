import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, Uuid, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.utils.enums import ValidationStatus, VerificationStatus

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.document_page import DocumentPage
    from app.models.ocr_region import OCRRegion
    from app.models.validation_issue import ValidationIssue
    from app.models.verification import VerificationAction


class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    field_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    raw_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extracted_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    source_page_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("document_pages.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_ocr_region_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("ocr_regions.id", ondelete="SET NULL"),
        nullable=True,
    )
    validation_status: Mapped[ValidationStatus] = mapped_column(
        SAEnum(
            ValidationStatus,
            name="validation_status",
            native_enum=False,
            length=32,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=ValidationStatus.VALID,
    )
    verification_status: Mapped[VerificationStatus] = mapped_column(
        SAEnum(
            VerificationStatus,
            name="verification_status",
            native_enum=False,
            length=32,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=VerificationStatus.UNVERIFIED,
    )
    verified_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    document: Mapped["Document"] = relationship(
        "Document", back_populates="extracted_fields"
    )
    source_page: Mapped[Optional["DocumentPage"]] = relationship(
        "DocumentPage", back_populates="extracted_fields"
    )
    source_region: Mapped[Optional["OCRRegion"]] = relationship(
        "OCRRegion", back_populates="extracted_fields"
    )
    validation_issues: Mapped[List["ValidationIssue"]] = relationship(
        "ValidationIssue",
        back_populates="field",
        cascade="all, delete-orphan",
    )
    verification_actions: Mapped[List["VerificationAction"]] = relationship(
        "VerificationAction",
        back_populates="field",
        cascade="all, delete-orphan",
    )
