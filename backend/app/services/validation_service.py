import re
from typing import List, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.document import Document
from app.models.extracted_field import ExtractedField
from app.models.validation_issue import ValidationIssue
from app.utils.enums import Severity, ValidationIssueType, ValidationStatus

settings = get_settings()


class ValidationService:
    def validate_document_fields(
        self,
        db: Session,
        document: Document,
    ) -> List[ValidationIssue]:
        """
        Validates all extracted fields of a document against formatting rules,
        confidence thresholds, and cross-field consistency.
        Creates ValidationIssue records for suspicious or invalid fields.
        """
        fields = list(
            db.scalars(
                select(ExtractedField).where(ExtractedField.document_id == document.id)
            ).all()
        )

        issues: List[ValidationIssue] = []

        field_map = {f.field_name: f for f in fields}

        for field in fields:
            # Check 1: Missing critical fields (e.g. owner_name, khata_number, khasra_number)
            if not field.extracted_value:
                if field.field_name in ["owner_name", "khata_number", "khasra_number"]:
                    issue = ValidationIssue(
                        document_id=document.id,
                        field_id=field.id,
                        issue_type=ValidationIssueType.FORMAT_ERROR,
                        severity=Severity.HIGH,
                        message=f"Critical field '{field.field_name}' could not be detected from document",
                        status="OPEN",
                    )
                    db.add(issue)
                    issues.append(issue)
                    field.validation_status = ValidationStatus.ERROR
                continue

            # Check 2: Low confidence validation
            if (
                field.confidence is not None
                and field.confidence < settings.LOW_CONFIDENCE_THRESHOLD
            ):
                issue = ValidationIssue(
                    document_id=document.id,
                    field_id=field.id,
                    issue_type=ValidationIssueType.LOW_CONFIDENCE,
                    severity=Severity.MEDIUM,
                    message=f"Field '{field.field_name}' has low confidence ({field.confidence:.2f})",
                    status="OPEN",
                )
                db.add(issue)
                issues.append(issue)
                if field.validation_status != ValidationStatus.ERROR:
                    field.validation_status = ValidationStatus.WARNING

            # Check 3: Format validation
            val = field.extracted_value.strip()

            if field.field_name == "khata_number":
                if not re.match(r"^[A-Za-z0-9\-_/]+$", val):
                    issue = ValidationIssue(
                        document_id=document.id,
                        field_id=field.id,
                        issue_type=ValidationIssueType.FORMAT_ERROR,
                        severity=Severity.MEDIUM,
                        message=f"Khata number '{val}' contains suspicious characters",
                        status="OPEN",
                    )
                    db.add(issue)
                    issues.append(issue)
                    field.validation_status = ValidationStatus.WARNING

            elif field.field_name == "khasra_number":
                if not re.match(r"^[A-Za-z0-9\-_/]+$", val):
                    issue = ValidationIssue(
                        document_id=document.id,
                        field_id=field.id,
                        issue_type=ValidationIssueType.FORMAT_ERROR,
                        severity=Severity.MEDIUM,
                        message=f"Khasra number '{val}' contains suspicious characters",
                        status="OPEN",
                    )
                    db.add(issue)
                    issues.append(issue)
                    field.validation_status = ValidationStatus.WARNING

            elif field.field_name == "area":
                # Check if numbers exist in area
                if not re.search(r"\d+", val):
                    issue = ValidationIssue(
                        document_id=document.id,
                        field_id=field.id,
                        issue_type=ValidationIssueType.AREA_MISMATCH,
                        severity=Severity.HIGH,
                        message=f"Area value '{val}' does not contain valid numeric measurement",
                        status="OPEN",
                    )
                    db.add(issue)
                    issues.append(issue)
                    field.validation_status = ValidationStatus.ERROR

        db.flush()
        return issues


validation_service = ValidationService()
