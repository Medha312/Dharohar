import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, Uuid, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.utils.enums import GISSource

if TYPE_CHECKING:
    from app.models.land_record import LandRecord


class GISReference(Base):
    __tablename__ = "gis_references"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    land_record_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("land_records.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    cadastral_id: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, index=True
    )
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    geometry: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[GISSource] = mapped_column(
        SAEnum(
            GISSource,
            name="gis_source",
            native_enum=False,
            length=32,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=GISSource.SYSTEM,
    )
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
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
    land_record: Mapped["LandRecord"] = relationship(
        "LandRecord", back_populates="gis_reference"
    )
