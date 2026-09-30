import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, String, Uuid, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.utils.enums import VerificationStatus

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.gis_reference import GISReference
    from app.models.user import User


class LandRecord(Base):
    __tablename__ = "land_records"

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

    owner_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )
    father_husband_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    khata_number: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, index=True
    )
    khasra_number: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, index=True
    )
    survey_number: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    area: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    area_unit: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, default="hectare"
    )

    village: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, index=True
    )
    tehsil: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, index=True
    )
    district: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, index=True
    )

    land_classification: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True
    )
    ownership_type: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    mutation_number: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    registration_number: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True
    )

    verification_status: Mapped[VerificationStatus] = mapped_column(
        SAEnum(
            VerificationStatus,
            name="land_record_verification_status",
            native_enum=False,
            length=32,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=VerificationStatus.UNVERIFIED,
    )

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
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    verified_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    document: Mapped["Document"] = relationship(
        "Document", back_populates="land_records"
    )
    verifier: Mapped[Optional["User"]] = relationship("User")
    gis_reference: Mapped[Optional["GISReference"]] = relationship(
        "GISReference",
        back_populates="land_record",
        uselist=False,
        cascade="all, delete-orphan",
    )
