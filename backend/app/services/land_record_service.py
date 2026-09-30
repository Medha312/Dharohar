import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.extracted_field import ExtractedField
from app.models.land_record import LandRecord
from app.services.audit_service import audit_service
from app.services.extraction_service import extraction_service
from app.utils.enums import AuditAction, VerificationStatus


class LandRecordService:
    def create_or_update_from_fields(
        self,
        db: Session,
        document: Document,
        verified_by: Optional[uuid.UUID] = None,
    ) -> LandRecord:
        """
        Creates or updates the canonical LandRecord based on the current extracted & verified fields.
        Preserves original values in ExtractedField.
        """
        fields = list(
            db.scalars(
                select(ExtractedField).where(ExtractedField.document_id == document.id)
            ).all()
        )
        field_dict = {}
        for f in fields:
            # Use verified value if available, otherwise extracted value
            effective_val = (
                f.verified_value
                if f.verification_status == VerificationStatus.CORRECTED
                else (f.extracted_value or f.raw_value)
            )
            field_dict[f.field_name] = effective_val

        area_val, area_unit = extraction_service.parse_area(field_dict.get("area"))

        land_record = db.scalar(
            select(LandRecord).where(LandRecord.document_id == document.id)
        )

        now = datetime.now(timezone.utc)
        if not land_record:
            land_record = LandRecord(
                document_id=document.id,
                owner_name=field_dict.get("owner_name"),
                father_husband_name=field_dict.get("father_husband_name"),
                khata_number=field_dict.get("khata_number"),
                khasra_number=field_dict.get("khasra_number"),
                survey_number=field_dict.get("survey_number"),
                area=area_val,
                area_unit=area_unit or "hectare",
                village=field_dict.get("village"),
                tehsil=field_dict.get("tehsil"),
                district=field_dict.get("district"),
                land_classification=field_dict.get("land_classification"),
                ownership_type=field_dict.get("ownership_type"),
                mutation_number=field_dict.get("mutation_number"),
                registration_number=field_dict.get("registration_number"),
                verification_status=(
                    VerificationStatus.VERIFIED
                    if verified_by
                    else VerificationStatus.UNVERIFIED
                ),
                verified_at=now if verified_by else None,
                verified_by=verified_by,
            )
            db.add(land_record)
        else:
            land_record.owner_name = field_dict.get("owner_name")
            land_record.father_husband_name = field_dict.get("father_husband_name")
            land_record.khata_number = field_dict.get("khata_number")
            land_record.khasra_number = field_dict.get("khasra_number")
            land_record.survey_number = field_dict.get("survey_number")
            land_record.area = area_val
            land_record.area_unit = area_unit or "hectare"
            land_record.village = field_dict.get("village")
            land_record.tehsil = field_dict.get("tehsil")
            land_record.district = field_dict.get("district")
            land_record.land_classification = field_dict.get("land_classification")
            land_record.ownership_type = field_dict.get("ownership_type")
            land_record.mutation_number = field_dict.get("mutation_number")
            land_record.registration_number = field_dict.get("registration_number")
            if verified_by:
                land_record.verification_status = VerificationStatus.VERIFIED
                land_record.verified_at = now
                land_record.verified_by = verified_by

        db.flush()
        return land_record

    def get_records(
        self,
        db: Session,
        owner_name: Optional[str] = None,
        khata_number: Optional[str] = None,
        khasra_number: Optional[str] = None,
        survey_number: Optional[str] = None,
        village: Optional[str] = None,
        tehsil: Optional[str] = None,
        district: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[LandRecord], int]:
        query = select(LandRecord)
        if owner_name:
            query = query.where(LandRecord.owner_name.ilike(f"%{owner_name}%"))
        if khata_number:
            query = query.where(LandRecord.khata_number == khata_number)
        if khasra_number:
            query = query.where(LandRecord.khasra_number == khasra_number)
        if survey_number:
            query = query.where(LandRecord.survey_number == survey_number)
        if village:
            query = query.where(LandRecord.village.ilike(f"%{village}%"))
        if tehsil:
            query = query.where(LandRecord.tehsil.ilike(f"%{tehsil}%"))
        if district:
            query = query.where(LandRecord.district.ilike(f"%{district}%"))
        if status:
            query = query.where(LandRecord.verification_status == status)

        # Count total
        from sqlalchemy import func
        count_query = select(func.count()).select_from(query.subquery())
        total = db.scalar(count_query) or 0

        query = query.order_by(desc(LandRecord.created_at)).offset(offset).limit(limit)
        return list(db.scalars(query).all()), total

    def get_record_by_id(self, db: Session, record_id: uuid.UUID) -> Optional[LandRecord]:
        return db.get(LandRecord, record_id)

    def get_record_by_document(
        self, db: Session, document_id: uuid.UUID
    ) -> Optional[LandRecord]:
        return db.scalar(
            select(LandRecord).where(LandRecord.document_id == document_id)
        )


land_record_service = LandRecordService()
