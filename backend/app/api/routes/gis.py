import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUserDep, SessionDep, VerifierOrAdminDep
from app.models.gis_reference import GISReference
from app.schemas.gis import (
    GeoJSONFeatureCollection,
    GISReferenceCreate,
    GISReferenceRead,
    GISReferenceUpdate,
)
from app.services.gis_service import gis_service
from app.services.land_record_service import land_record_service

router = APIRouter()


@router.get("/land-records/{record_id}/gis", response_model=GISReferenceRead)
def get_land_record_gis(
    record_id: uuid.UUID,
    db: SessionDep,
    current_user: CurrentUserDep,
) -> GISReference:
    record = land_record_service.get_record_by_id(db=db, record_id=record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Land record not found",
        )

    gis_ref = gis_service.get_by_land_record(db=db, land_record_id=record_id)
    if not gis_ref:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GIS information not available for this record",
        )
    return gis_ref


@router.post("/land-records/{record_id}/gis", response_model=GISReferenceRead, status_code=status.HTTP_201_CREATED)
def create_land_record_gis(
    record_id: uuid.UUID,
    gis_in: GISReferenceCreate,
    db: SessionDep,
    current_user: VerifierOrAdminDep,
) -> GISReference:
    record = land_record_service.get_record_by_id(db=db, record_id=record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Land record not found",
        )

    gis_ref = gis_service.create_gis_reference(
        db=db,
        land_record_id=record_id,
        gis_in=gis_in,
        user_id=current_user.id,
    )
    db.commit()
    db.refresh(gis_ref)
    return gis_ref


@router.patch("/land-records/{record_id}/gis", response_model=GISReferenceRead)
def update_land_record_gis(
    record_id: uuid.UUID,
    gis_update: GISReferenceUpdate,
    db: SessionDep,
    current_user: VerifierOrAdminDep,
) -> GISReference:
    gis_ref = gis_service.get_by_land_record(db=db, land_record_id=record_id)
    if not gis_ref:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GIS reference not found for this land record",
        )

    updated = gis_service.update_gis_reference(
        db=db,
        gis_ref=gis_ref,
        gis_update=gis_update,
        user_id=current_user.id,
    )
    db.commit()
    db.refresh(updated)
    return updated


@router.get("/gis/parcels", response_model=GeoJSONFeatureCollection)
def get_parcels(
    db: SessionDep,
    current_user: CurrentUserDep,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> GeoJSONFeatureCollection:
    return gis_service.get_parcels_geojson(db=db, limit=limit, offset=offset)
