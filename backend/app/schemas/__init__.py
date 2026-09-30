from app.schemas.admin import (
    AuditLogRead,
    DashboardProcessing,
    DashboardSummary,
    DashboardVerification,
    ModelVersionCreate,
    ModelVersionRead,
)
from app.schemas.auth import (
    ForgotPasswordRequest,
    RefreshTokenRequest,
    ResetPasswordRequest,
    Token,
    TokenPayload,
    UserLogin,
    UserRegister,
)
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.document import DocumentDetail, DocumentPageRead, DocumentRead
from app.schemas.field import (
    DocumentFieldsResponse,
    ExtractedFieldRead,
    FieldCorrectionRequest,
)
from app.schemas.gis import (
    GeoJSONFeature,
    GeoJSONFeatureCollection,
    GISReferenceCreate,
    GISReferenceRead,
    GISReferenceUpdate,
)
from app.schemas.land_record import (
    AreaDetail,
    LandRecordBase,
    LandRecordRead,
    LandRecordUpdate,
)
from app.schemas.ocr import DocumentOCRResponse, OCRRegionRead, OCRResultRead
from app.schemas.processing import ProcessingJobRead, ProcessingStatusResponse
from app.schemas.user import UserAdminUpdate, UserBase, UserRead, UserUpdate
from app.schemas.validation import ValidationIssueRead
from app.schemas.verification import (
    VerificationActionRead,
    VerificationFieldActionRequest,
    VerificationTaskDetail,
    VerificationTaskRead,
)

__all__ = [
    "MessageResponse",
    "PaginatedResponse",
    "UserRegister",
    "UserLogin",
    "Token",
    "TokenPayload",
    "RefreshTokenRequest",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "UserBase",
    "UserRead",
    "UserUpdate",
    "UserAdminUpdate",
    "DocumentRead",
    "DocumentDetail",
    "DocumentPageRead",
    "ProcessingJobRead",
    "ProcessingStatusResponse",
    "OCRRegionRead",
    "OCRResultRead",
    "DocumentOCRResponse",
    "ExtractedFieldRead",
    "FieldCorrectionRequest",
    "DocumentFieldsResponse",
    "ValidationIssueRead",
    "VerificationTaskRead",
    "VerificationTaskDetail",
    "VerificationActionRead",
    "VerificationFieldActionRequest",
    "AreaDetail",
    "LandRecordBase",
    "LandRecordRead",
    "LandRecordUpdate",
    "GISReferenceBase",
    "GISReferenceCreate",
    "GISReferenceUpdate",
    "GISReferenceRead",
    "GeoJSONFeature",
    "GeoJSONFeatureCollection",
    "ModelVersionCreate",
    "ModelVersionRead",
    "AuditLogRead",
    "DashboardSummary",
    "DashboardProcessing",
    "DashboardVerification",
]
