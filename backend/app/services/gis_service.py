import json
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.gis_reference import GISReference
from app.models.land_record import LandRecord
from app.schemas.gis import (
    GeoJSONFeature,
    GeoJSONFeatureCollection,
    GISReferenceCreate,
    GISReferenceUpdate,
)
from app.services.audit_service import audit_service
from app.utils.enums import AuditAction, GISSource


class GISService:
    def get_by_land_record(
        self, db: Session, land_record_id: uuid.UUID
    ) -> Optional[GISReference]:
        return db.scalar(
            select(GISReference).where(GISReference.land_record_id == land_record_id)
        )

    def create_gis_reference(
        self,
        db: Session,
        land_record_id: uuid.UUID,
        gis_in: GISReferenceCreate,
        user_id: Optional[uuid.UUID] = None,
    ) -> GISReference:
        existing = self.get_by_land_record(db, land_record_id)
        if existing:
            return self.update_gis_reference(db, existing, GISReferenceUpdate(**gis_in.model_dump()), user_id)

        gis_ref = GISReference(
            land_record_id=land_record_id,
            cadastral_id=gis_in.cadastral_id,
            latitude=gis_in.latitude,
            longitude=gis_in.longitude,
            geometry=gis_in.geometry,
            source=gis_in.source,
            confidence=gis_in.confidence,
        )
        db.add(gis_ref)
        db.flush()

        audit_service.log(
            db=db,
            action=AuditAction.GIS_UPDATED,
            entity_type="GISReference",
            entity_id=str(gis_ref.id),
            user_id=user_id,
            new_value=gis_in.model_dump(),
        )
        return gis_ref

    def update_gis_reference(
        self,
        db: Session,
        gis_ref: GISReference,
        gis_update: GISReferenceUpdate,
        user_id: Optional[uuid.UUID] = None,
    ) -> GISReference:
        old_val = {
            "cadastral_id": gis_ref.cadastral_id,
            "latitude": gis_ref.latitude,
            "longitude": gis_ref.longitude,
            "geometry": gis_ref.geometry,
        }
        update_data = gis_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                setattr(gis_ref, key, value)

        db.flush()

        audit_service.log(
            db=db,
            action=AuditAction.GIS_UPDATED,
            entity_type="GISReference",
            entity_id=str(gis_ref.id),
            user_id=user_id,
            old_value=old_val,
            new_value=update_data,
        )
        return gis_ref

    def get_parcels_geojson(
        self, db: Session, limit: int = 100, offset: int = 0
    ) -> GeoJSONFeatureCollection:
        query = (
            select(GISReference, LandRecord)
            .join(LandRecord, GISReference.land_record_id == LandRecord.id)
            .offset(offset)
            .limit(limit)
        )
        results = db.execute(query).all()

        features: List[GeoJSONFeature] = []
        for gis_ref, record in results:
            geometry_obj: Optional[Dict[str, Any]] = None
            if gis_ref.geometry:
                try:
                    geometry_obj = json.loads(gis_ref.geometry)
                except Exception:
                    pass
            elif gis_ref.latitude is not None and gis_ref.longitude is not None:
                geometry_obj = {
                    "type": "Point",
                    "coordinates": [gis_ref.longitude, gis_ref.latitude],
                }

            features.append(
                GeoJSONFeature(
                    geometry=geometry_obj,
                    properties={
                        "gis_id": str(gis_ref.id),
                        "land_record_id": str(record.id),
                        "cadastral_id": gis_ref.cadastral_id,
                        "owner_name": record.owner_name,
                        "khata_number": record.khata_number,
                        "khasra_number": record.khasra_number,
                        "village": record.village,
                        "tehsil": record.tehsil,
                        "district": record.district,
                        "area": record.area,
                        "area_unit": record.area_unit,
                    },
                )
            )

        return GeoJSONFeatureCollection(features=features)


gis_service = GISService()
