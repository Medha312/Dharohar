import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Float, ForeignKey, String, Text, Uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.utils.enums import TextType

if TYPE_CHECKING:
    from app.models.extracted_field import ExtractedField
    from app.models.ocr_result import OCRResult


class OCRRegion(Base):
    __tablename__ = "ocr_regions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    ocr_result_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("ocr_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    text_type: Mapped[TextType] = mapped_column(
        SAEnum(
            TextType,
            name="text_type",
            native_enum=False,
            length=32,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=TextType.PRINTED,
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    x1: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    y1: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    x2: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    y2: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Relationships
    ocr_result: Mapped["OCRResult"] = relationship(
        "OCRResult", back_populates="regions"
    )
    extracted_fields: Mapped[List["ExtractedField"]] = relationship(
        "ExtractedField", back_populates="source_region"
    )
