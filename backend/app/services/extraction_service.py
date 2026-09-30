import re
import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_page import DocumentPage
from app.models.extracted_field import ExtractedField
from app.models.ocr_region import OCRRegion
from app.models.ocr_result import OCRResult
from app.utils.enums import (
    CANONICAL_FIELD_NAMES,
    ValidationStatus,
    VerificationStatus,
)


class ExtractionService:
    # Heuristic and regex extraction patterns for Hindi & English land records
    FIELD_PATTERNS = {
        "owner_name": [
            r"(?:खातेदार\s*का\s*नाम|मालिक\s*का\s*नाम|भूमिधर\s*का\s*नाम|Owner\s*Name)[:\s]+([^\n,/]+)",
        ],
        "father_husband_name": [
            r"(?:पिता/पति\s*का\s*नाम|पिता\s*का\s*नाम|पति\s*का\s*नाम|Father/Husband\s*Name)[:\s]+([^\n,/]+)",
        ],
        "khata_number": [
            r"(?:खाता\s*संख्या|खाता\s*नं|खतौनी\s*खाता\s*संख्या|Khata\s*No\.?)[:\s]+([A-Za-z0-9\-/]+)",
        ],
        "khasra_number": [
            r"(?:खसरा\s*संख्या|खसरा\s*नं|गाटा\s*संख्या|Khasra\s*No\.?)[:\s]+([A-Za-z0-9\-/]+)",
        ],
        "survey_number": [
            r"(?:सर्वे\s*संख्या|सर्वे\s*नं|Survey\s*No\.?)[:\s]+([A-Za-z0-9\-/]+)",
        ],
        "area": [
            r"(?:क्षेत्रफल|रकबा|Area)[:\s]+([0-9\.]+\s*(?:हेक्टेयर|hec|hectare|बीघा|bigha|sq\s*mt|sqm)?)",
        ],
        "village": [
            r"(?:ग्राम|मौजा|Village)[:\s]+([^\n,/\s]+)",
        ],
        "tehsil": [
            r"(?:तहसील|Tehsil)[:\s]+([^\n,/\s]+)",
        ],
        "district": [
            r"(?:जनपद|जिला|District)[:\s]+([^\n,/\s]+)",
        ],
        "land_classification": [
            r"(?:भूमि\s*श्रेणी|श्रेणी|Land\s*Classification)[:\s]+([^\n,/]+)",
        ],
        "ownership_type": [
            r"(?:स्वामित्व\s*प्रकार|प्रकार|Ownership\s*Type)[:\s]+([^\n,/]+)",
        ],
        "mutation_number": [
            r"(?:नामांतरण\s*संख्या|दाखिल\s*खारिज\s*संख्या|Mutation\s*No\.?)[:\s]+([A-Za-z0-9\-/]+)",
        ],
        "registration_number": [
            r"(?:पंजीकरण\s*संख्या|रजिस्ट्री\s*संख्या|Registration\s*No\.?)[:\s]+([A-Za-z0-9\-/]+)",
        ],
    }

    @staticmethod
    def parse_area(area_text: Optional[str]) -> Tuple[Optional[float], Optional[str]]:
        """Extracts structured numeric value and unit from raw area text."""
        if not area_text:
            return None, "hectare"

        unit = "hectare"
        lower = area_text.lower()
        if "बीघा" in area_text or "bigha" in lower:
            unit = "bigha"
        elif "हेक्टेयर" in area_text or "hectare" in lower or "hec" in lower:
            unit = "hectare"
        elif "sq" in lower or "वर्ग" in area_text:
            unit = "sq_meter"

        # Match numeric float
        match = re.search(r"(\d+(?:\.\d+)?)", area_text)
        if match:
            try:
                return float(match.group(1)), unit
            except ValueError:
                pass
        return None, unit

    def extract_fields_for_document(
        self,
        db: Session,
        document: Document,
    ) -> List[ExtractedField]:
        """
        Extracts canonical fields across all document pages and OCR regions.
        Traces each field to its source page and OCR region.
        """
        # Load all pages and OCR results
        pages = list(
            db.scalars(
                select(DocumentPage)
                .where(DocumentPage.document_id == document.id)
                .order_by(DocumentPage.page_number)
            ).all()
        )

        extracted_records: List[ExtractedField] = []

        # Map to find field matches
        found_fields: Dict[str, Dict[str, Any]] = {}

        for page in pages:
            ocr_results = list(
                db.scalars(
                    select(OCRResult).where(OCRResult.document_page_id == page.id)
                ).all()
            )

            for ocr in ocr_results:
                regions = list(
                    db.scalars(
                        select(OCRRegion).where(OCRRegion.ocr_result_id == ocr.id)
                    ).all()
                )

                # Search through regions
                for field_name in CANONICAL_FIELD_NAMES:
                    if field_name in found_fields:
                        continue  # Already found earlier

                    patterns = self.FIELD_PATTERNS.get(field_name, [])
                    for reg in regions:
                        for pat in patterns:
                            match = re.search(pat, reg.text, re.IGNORECASE)
                            if match:
                                val = match.group(1).strip()
                                found_fields[field_name] = {
                                    "raw_value": reg.text.strip(),
                                    "extracted_value": val,
                                    "confidence": reg.confidence,
                                    "source_page_id": page.id,
                                    "source_ocr_region_id": reg.id,
                                }
                                break
                        if field_name in found_fields:
                            break

                # Also search raw_text if not found in regions
                for field_name in CANONICAL_FIELD_NAMES:
                    if field_name in found_fields:
                        continue
                    patterns = self.FIELD_PATTERNS.get(field_name, [])
                    for pat in patterns:
                        match = re.search(pat, ocr.raw_text, re.IGNORECASE)
                        if match:
                            val = match.group(1).strip()
                            found_fields[field_name] = {
                                "raw_value": match.group(0).strip(),
                                "extracted_value": val,
                                "confidence": ocr.confidence,
                                "source_page_id": page.id,
                                "source_ocr_region_id": None,
                            }
                            break

        # Save all 13 canonical fields into ExtractedField table
        for field_name in CANONICAL_FIELD_NAMES:
            if field_name in found_fields:
                info = found_fields[field_name]
                extracted_field = ExtractedField(
                    document_id=document.id,
                    field_name=field_name,
                    raw_value=info["raw_value"],
                    extracted_value=info["extracted_value"],
                    confidence=info["confidence"],
                    source_page_id=info["source_page_id"],
                    source_ocr_region_id=info["source_ocr_region_id"],
                    validation_status=ValidationStatus.VALID,
                    verification_status=VerificationStatus.UNVERIFIED,
                )
            else:
                # Value not found
                extracted_field = ExtractedField(
                    document_id=document.id,
                    field_name=field_name,
                    raw_value=None,
                    extracted_value=None,
                    confidence=0.0,
                    source_page_id=None,
                    source_ocr_region_id=None,
                    validation_status=ValidationStatus.NOT_FOUND,
                    verification_status=VerificationStatus.UNVERIFIED,
                )
            db.add(extracted_field)
            extracted_records.append(extracted_field)

        db.flush()
        return extracted_records


extraction_service = ExtractionService()
