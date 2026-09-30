"""
Validation service — Phase 10.

Checks:
  1. Missing critical fields
  2. Low-confidence fields
  3. Format validation (khata, khasra, mutation, registration, area)
  4. Cross-field consistency  (village / tehsil / district across pages)
  5. Cross-page conflict detection (same field extracted from multiple pages
     with contradictory values)
"""
import re
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.document import Document
from app.models.document_page import DocumentPage
from app.models.extracted_field import ExtractedField
from app.models.ocr_result import OCRResult
from app.models.validation_issue import ValidationIssue
from app.utils.enums import Severity, ValidationIssueType, ValidationStatus

settings = get_settings()

# Fields whose absence is immediately HIGH severity
_CRITICAL_FIELDS = {"owner_name", "khata_number", "khasra_number"}

# Fields that must match across pages when found on more than one page
# (key = field_name, value = issue type to raise on mismatch)
_CROSS_PAGE_FIELDS: Dict[str, ValidationIssueType] = {
    "owner_name":    ValidationIssueType.OWNER_MISMATCH,
    "khata_number":  ValidationIssueType.KHATA_MISMATCH,
    "khasra_number": ValidationIssueType.KHASRA_MISMATCH,
    "village":       ValidationIssueType.VILLAGE_MISMATCH,
    "tehsil":        ValidationIssueType.CROSS_FIELD_CONFLICT,
    "district":      ValidationIssueType.CROSS_FIELD_CONFLICT,
    "area":          ValidationIssueType.AREA_MISMATCH,
}

# Format patterns — value must *fully* match
_FORMAT_PATTERNS: Dict[str, Tuple[str, str]] = {
    # field_name → (regex, human description)
    "khata_number":       (r"^[A-Za-z0-9\-_/]+$",          "alphanumeric / - _ /"),
    "khasra_number":      (r"^[A-Za-z0-9\-_/]+$",          "alphanumeric / - _ /"),
    "survey_number":      (r"^[A-Za-z0-9\-_/]+$",          "alphanumeric / - _ /"),
    "mutation_number":    (r"^[A-Za-z0-9\-_/]+$",          "alphanumeric / - _ /"),
    "registration_number":(r"^[A-Za-z0-9\-_/]+$",          "alphanumeric / - _ /"),
}


def _normalise(value: Optional[str]) -> Optional[str]:
    """Strip whitespace and collapse internal spaces for comparison."""
    if value is None:
        return None
    return " ".join(value.strip().split()).lower()


class ValidationService:
    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def validate_document_fields(
        self,
        db: Session,
        document: Document,
    ) -> List[ValidationIssue]:
        """
        Run all validation checks for a document and return every
        ValidationIssue that was created.
        """
        fields: List[ExtractedField] = list(
            db.scalars(
                select(ExtractedField).where(ExtractedField.document_id == document.id)
            ).all()
        )

        issues: List[ValidationIssue] = []
        field_map: Dict[str, ExtractedField] = {f.field_name: f for f in fields}

        # Per-field checks
        for field in fields:
            issues.extend(self._check_missing(db, document, field))
            if field.extracted_value:
                issues.extend(self._check_confidence(db, document, field))
                issues.extend(self._check_format(db, document, field))

        # Cross-field consistency
        issues.extend(self._check_cross_field_consistency(db, document, field_map))

        # Cross-page conflicts
        issues.extend(self._check_cross_page_conflicts(db, document))

        db.flush()
        return issues

    # ------------------------------------------------------------------
    # Check 1 — missing critical fields
    # ------------------------------------------------------------------

    def _check_missing(
        self,
        db: Session,
        document: Document,
        field: ExtractedField,
    ) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        if not field.extracted_value:
            if field.field_name in _CRITICAL_FIELDS:
                issue = ValidationIssue(
                    document_id=document.id,
                    field_id=field.id,
                    issue_type=ValidationIssueType.FORMAT_ERROR,
                    severity=Severity.HIGH,
                    message=(
                        f"Critical field '{field.field_name}' could not be detected "
                        "from the document"
                    ),
                    status="OPEN",
                )
                db.add(issue)
                issues.append(issue)
                field.validation_status = ValidationStatus.ERROR
        return issues

    # ------------------------------------------------------------------
    # Check 2 — low confidence
    # ------------------------------------------------------------------

    def _check_confidence(
        self,
        db: Session,
        document: Document,
        field: ExtractedField,
    ) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        if (
            field.confidence is not None
            and field.confidence < settings.LOW_CONFIDENCE_THRESHOLD
        ):
            issue = ValidationIssue(
                document_id=document.id,
                field_id=field.id,
                issue_type=ValidationIssueType.LOW_CONFIDENCE,
                severity=Severity.MEDIUM,
                message=(
                    f"Field '{field.field_name}' has low confidence "
                    f"({field.confidence:.2f} < {settings.LOW_CONFIDENCE_THRESHOLD})"
                ),
                status="OPEN",
            )
            db.add(issue)
            issues.append(issue)
            if field.validation_status not in (
                ValidationStatus.ERROR,
                ValidationStatus.WARNING,
            ):
                field.validation_status = ValidationStatus.WARNING
        return issues

    # ------------------------------------------------------------------
    # Check 3 — format validation
    # ------------------------------------------------------------------

    def _check_format(
        self,
        db: Session,
        document: Document,
        field: ExtractedField,
    ) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        val = (field.extracted_value or "").strip()
        if not val:
            return issues

        # Identifier fields — must match alphanumeric pattern
        if field.field_name in _FORMAT_PATTERNS:
            pattern, description = _FORMAT_PATTERNS[field.field_name]
            if not re.match(pattern, val):
                issue = ValidationIssue(
                    document_id=document.id,
                    field_id=field.id,
                    issue_type=ValidationIssueType.FORMAT_ERROR,
                    severity=Severity.MEDIUM,
                    message=(
                        f"'{field.field_name}' value '{val}' does not match "
                        f"expected format ({description})"
                    ),
                    status="OPEN",
                )
                db.add(issue)
                issues.append(issue)
                if field.validation_status != ValidationStatus.ERROR:
                    field.validation_status = ValidationStatus.WARNING

        # Area — must contain at least one digit
        elif field.field_name == "area":
            if not re.search(r"\d+", val):
                issue = ValidationIssue(
                    document_id=document.id,
                    field_id=field.id,
                    issue_type=ValidationIssueType.AREA_MISMATCH,
                    severity=Severity.HIGH,
                    message=(
                        f"Area value '{val}' does not contain a valid numeric measurement"
                    ),
                    status="OPEN",
                )
                db.add(issue)
                issues.append(issue)
                field.validation_status = ValidationStatus.ERROR

        return issues

    # ------------------------------------------------------------------
    # Check 4 — cross-field consistency
    # ------------------------------------------------------------------

    def _check_cross_field_consistency(
        self,
        db: Session,
        document: Document,
        field_map: Dict[str, ExtractedField],
    ) -> List[ValidationIssue]:
        """
        Check logical consistency between related fields.

        Current rules:
          • If village is present and tehsil is present, they should not be
            identical (a village cannot be its own tehsil).
          • If tehsil is present and district is present, they should not be
            identical either.
          • owner_name and father_husband_name should not be identical (data
            entry / OCR confusion).
        """
        issues: List[ValidationIssue] = []

        def _val(name: str) -> Optional[str]:
            f = field_map.get(name)
            return _normalise(f.extracted_value) if f and f.extracted_value else None

        village  = _val("village")
        tehsil   = _val("tehsil")
        district = _val("district")
        owner    = _val("owner_name")
        father   = _val("father_husband_name")

        # village == tehsil?
        if village and tehsil and village == tehsil:
            field = field_map.get("village")
            if field:
                issue = ValidationIssue(
                    document_id=document.id,
                    field_id=field.id,
                    issue_type=ValidationIssueType.CROSS_FIELD_CONFLICT,
                    severity=Severity.MEDIUM,
                    message=(
                        f"Village '{village}' and tehsil share the same value — "
                        "possible OCR or extraction error"
                    ),
                    status="OPEN",
                )
                db.add(issue)
                issues.append(issue)
                if field.validation_status not in (ValidationStatus.ERROR,):
                    field.validation_status = ValidationStatus.WARNING

        # tehsil == district?
        if tehsil and district and tehsil == district:
            field = field_map.get("tehsil")
            if field:
                issue = ValidationIssue(
                    document_id=document.id,
                    field_id=field.id,
                    issue_type=ValidationIssueType.CROSS_FIELD_CONFLICT,
                    severity=Severity.MEDIUM,
                    message=(
                        f"Tehsil '{tehsil}' and district share the same value — "
                        "possible OCR or extraction error"
                    ),
                    status="OPEN",
                )
                db.add(issue)
                issues.append(issue)
                if field.validation_status not in (ValidationStatus.ERROR,):
                    field.validation_status = ValidationStatus.WARNING

        # owner == father?
        if owner and father and owner == father:
            field = field_map.get("owner_name")
            if field:
                issue = ValidationIssue(
                    document_id=document.id,
                    field_id=field.id,
                    issue_type=ValidationIssueType.CROSS_FIELD_CONFLICT,
                    severity=Severity.LOW,
                    message=(
                        f"Owner name and father/husband name are identical ('{owner}') — "
                        "possible extraction error"
                    ),
                    status="OPEN",
                )
                db.add(issue)
                issues.append(issue)
                if field.validation_status not in (
                    ValidationStatus.ERROR, ValidationStatus.WARNING
                ):
                    field.validation_status = ValidationStatus.WARNING

        return issues

    # ------------------------------------------------------------------
    # Check 5 — cross-page conflict detection
    # ------------------------------------------------------------------

    def _check_cross_page_conflicts(
        self,
        db: Session,
        document: Document,
    ) -> List[ValidationIssue]:
        """
        For each field in _CROSS_PAGE_FIELDS, collect all ExtractedField records
        that are sourced from different pages.  If the normalised values differ,
        raise a conflict issue.

        This covers the spec's example:
            Page 1: village = Chinhat
            Page 3: village = Malhaur  → conflict
        """
        issues: List[ValidationIssue] = []

        # Gather all extracted fields for this document grouped by field_name
        all_fields: List[ExtractedField] = list(
            db.scalars(
                select(ExtractedField).where(
                    ExtractedField.document_id == document.id,
                    ExtractedField.extracted_value.isnot(None),
                    ExtractedField.source_page_id.isnot(None),
                )
            ).all()
        )

        # Group: field_name → list of (page_id, normalised_value, field_obj)
        grouped: Dict[str, List[Tuple]] = defaultdict(list)
        for f in all_fields:
            if f.field_name in _CROSS_PAGE_FIELDS:
                norm = _normalise(f.extracted_value)
                if norm:
                    grouped[f.field_name].append((f.source_page_id, norm, f))

        for field_name, entries in grouped.items():
            if len(entries) < 2:
                continue  # nothing to compare

            # Collect unique (page_id, value) pairs
            page_values: Dict[str, str] = {}  # page_id → normalised value
            for page_id, norm_val, _ in entries:
                page_id_str = str(page_id)
                if page_id_str not in page_values:
                    page_values[page_id_str] = norm_val

            unique_values = set(page_values.values())
            if len(unique_values) <= 1:
                continue  # all pages agree — no conflict

            # Pages disagree — create one issue per conflicting field record
            issue_type = _CROSS_PAGE_FIELDS[field_name]
            values_summary = ", ".join(
                f"page {i + 1}: '{v}'" for i, v in enumerate(page_values.values())
            )
            for _page_id, _norm_val, field_obj in entries:
                issue = ValidationIssue(
                    document_id=document.id,
                    field_id=field_obj.id,
                    issue_type=issue_type,
                    severity=Severity.HIGH,
                    message=(
                        f"Cross-page conflict for '{field_name}': {values_summary}"
                    ),
                    status="OPEN",
                )
                db.add(issue)
                issues.append(issue)
                if field_obj.validation_status != ValidationStatus.ERROR:
                    field_obj.validation_status = ValidationStatus.WARNING

        return issues


validation_service = ValidationService()
