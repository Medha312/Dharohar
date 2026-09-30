import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict

from app.utils.enums import GISSource


class GISReferenceBase(BaseModel):
    cadastral_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    geometry: Optional[str] = None  # GeoJSON string or polygon coords
    source: GISSource = GISSource.SYSTEM
    confidence: Optional[float] = None


class GISReferenceCreate(GISReferenceBase):
    pass


class GISReferenceUpdate(BaseModel):
    cadastral_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    geometry: Optional[str] = None
    source: Optional[GISSource] = None
    confidence: Optional[float] = None


class GISReferenceRead(GISReferenceBase):
    id: uuid.UUID
    land_record_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GeoJSONGeometry(BaseModel):
    type: str = "Point"
    coordinates: List[Any]


class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: Optional[Dict[str, Any]] = None
    properties: Dict[str, Any] = {}


class GeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature] = []
