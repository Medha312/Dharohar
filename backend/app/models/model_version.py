import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, DateTime, String, Uuid, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.utils.enums import ModelType

if TYPE_CHECKING:
    from app.models.ocr_result import OCRResult


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    model_type: Mapped[ModelType] = mapped_column(
        SAEnum(
            ModelType,
            name="model_type",
            native_enum=False,
            length=32,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    file_reference: Mapped[str] = mapped_column(String(512), nullable=False)
    framework: Mapped[str] = mapped_column(String(64), nullable=False, default="pytorch")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    ocr_results: Mapped[List["OCRResult"]] = relationship(
        "OCRResult", back_populates="model_version"
    )
