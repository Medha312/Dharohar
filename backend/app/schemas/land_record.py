import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.utils.enums import VerificationStatus


class AreaDetail(BaseModel):
    value: Optional[float] = None
    unit: Optional[str] = "hectare"


class LandRecordBase(BaseModel):
    owner_name: Optional[str] = None
    father_husband_name: Optional[str] = None
    khata_number: Optional[str] = None
    khasra_number: Optional[str] = None
    survey_number: Optional[str] = None
    area: Optional[float] = None
    area_unit: Optional[str] = "hectare"
    village: Optional[str] = None
    tehsil: Optional[str] = None
    district: Optional[str] = None
    land_classification: Optional[str] = None
    ownership_type: Optional[str] = None
    mutation_number: Optional[str] = None
    registration_number: Optional[str] = None


class LandRecordUpdate(LandRecordBase):
    verification_status: Optional[VerificationStatus] = None


class LandRecordRead(LandRecordBase):
    id: uuid.UUID
    document_id: uuid.UUID
    verification_status: VerificationStatus
    created_at: datetime
    updated_at: datetime
    verified_at: Optional[datetime] = None
    verified_by: Optional[uuid.UUID] = None

    @property
    def structured_area(self) -> AreaDetail:
        return AreaDetail(value=self.area, unit=self.area_unit)

    model_config = ConfigDict(from_attributes=True)
