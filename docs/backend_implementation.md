# DHAROHAR

## Backend Implementation Specification

Version: 1.0
Backend: Python + FastAPI
Database: PostgreSQL
ORM: SQLAlchemy
Migrations: Alembic
Background Jobs: Celery + Redis
ML: PyTorch / Ultralytics as applicable
Storage: Local filesystem initially, S3-compatible storage later

---

# 1. PROJECT OVERVIEW

Dharohar is a Land Record Digitization System.

The system processes historical land-record documents, including old scanned documents and handwritten Hindi records.

The primary workflow is:

Upload Land Document
→ Page Processing
→ Document Structure Detection
→ Image Enhancement
→ Document Type Detection
→ Language/Script Detection
→ OCR
→ Field Extraction
→ Validation
→ Confidence Scoring
→ Human Verification
→ Final Structured Land Record
→ GIS / Database
→ Dashboard

The system must preserve the complete processing history.

Do NOT overwrite earlier processing stages.

For example:

OCR output:
"राम सिंग"

AI extraction:
"राम सिंह"

Confidence:
0.82

Human verified value:
"राम सिंह"

All three stages should remain traceable.

---

# 2. CURRENT PROJECT STRUCTURE

The GitHub repository is:

dharohar/

The planned repository structure is:

dharohar/
│
├── frontend/
│
├── backend/
│   ├── app/
│   │   ├── **init**.py
│   │   ├── main.py
│   │   │
│   │   ├── core/
│   │   │   ├── **init**.py
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   │
│   │   ├── api/
│   │   │   ├── **init**.py
│   │   │   ├── router.py
│   │   │   └── routes/
│   │   │       ├── **init**.py
│   │   │       ├── health.py
│   │   │       ├── auth.py
│   │   │       ├── users.py
│   │   │       ├── documents.py
│   │   │       ├── processing.py
│   │   │       ├── results.py
│   │   │       ├── verification.py
│   │   │       ├── land_records.py
│   │   │       ├── gis.py
│   │   │       └── admin.py
│   │   │
│   │   ├── db/
│   │   │   ├── **init**.py
│   │   │   ├── database.py
│   │   │   └── base.py
│   │   │
│   │   ├── models/
│   │   │   ├── **init**.py
│   │   │   ├── user.py
│   │   │   ├── document.py
│   │   │   ├── document_page.py
│   │   │   ├── processing_job.py
│   │   │   ├── ocr_result.py
│   │   │   ├── ocr_region.py
│   │   │   ├── extracted_field.py
│   │   │   ├── validation_issue.py
│   │   │   ├── verification.py
│   │   │   ├── land_record.py
│   │   │   ├── gis_reference.py
│   │   │   ├── model_version.py
│   │   │   └── audit_log.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── **init**.py
│   │   │   ├── auth.py
│   │   │   ├── user.py
│   │   │   ├── document.py
│   │   │   ├── processing.py
│   │   │   ├── ocr.py
│   │   │   ├── field.py
│   │   │   ├── validation.py
│   │   │   ├── verification.py
│   │   │   ├── land_record.py
│   │   │   ├── gis.py
│   │   │   └── common.py
│   │   │
│   │   ├── services/
│   │   │   ├── document_service.py
│   │   │   ├── storage_service.py
│   │   │   ├── processing_service.py
│   │   │   ├── enhancement_service.py
│   │   │   ├── ocr_service.py
│   │   │   ├── extraction_service.py
│   │   │   ├── validation_service.py
│   │   │   ├── verification_service.py
│   │   │   ├── land_record_service.py
│   │   │   ├── gis_service.py
│   │   │   └── audit_service.py
│   │   │
│   │   ├── workers/
│   │   │   └── processing_worker.py
│   │   │
│   │   └── utils/
│   │       ├── file_validation.py
│   │       └── enums.py
│   │
│   ├── tests/
│   │
│   ├── alembic/
│   │
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
│
├── ml/
│   ├── enhancement/
│   │   ├── training/
│   │   └── inference/
│   │
│   └── ocr/
│       ├── training/
│       └── inference/
│
├── models/
│   ├── enhancement/
│   └── ocr/
│
├── infrastructure/
│
├── docs/
│
├── .github/
│   └── workflows/
│
├── .env.example
├── .gitignore
└── README.md

---

# 3. CURRENT STATUS

Phase 1 has already started.

FastAPI is running successfully.

The following currently works:

GET /

GET /api/v1/health

Swagger documentation:

/docs

Current backend command:

uvicorn app.main:app --reload

Do NOT recreate the project from scratch.

Inspect the existing repository before making changes.

Preserve working code unless there is a strong architectural reason to change it.

---

# 4. TECHNOLOGY STACK

## Backend

Python 3.11+ preferred.

FastAPI.

Uvicorn.

Pydantic v2.

pydantic-settings.

SQLAlchemy 2.x.

Alembic.

PostgreSQL.

psycopg / psycopg2 as PostgreSQL driver.

Celery.

Redis.

Pytest.

HTTPX for API tests.

---

# 5. ARCHITECTURAL PRINCIPLES

The backend must use clear separation of responsibilities.

The primary architecture is:

HTTP Route
→ Service
→ Database / ML / Storage

Routes must NOT contain business logic.

Example:

POST /documents/{id}/process

should call:

processing_service.process_document()

rather than implementing the processing logic directly inside the route.

---

# 6. RESPONSIBILITY OF EACH LAYER

## routes/

Responsible for:

* HTTP methods
* path parameters
* query parameters
* request validation
* authentication dependencies
* calling services
* returning schemas

Routes should remain thin.

---

## schemas/

Responsible for:

* API request models
* API response models
* validation
* serialization

Schemas are NOT database models.

---

## models/

Responsible for:

* SQLAlchemy database tables
* relationships
* indexes
* constraints

---

## services/

Responsible for business logic.

Examples:

document_service.py

storage_service.py

processing_service.py

ocr_service.py

extraction_service.py

validation_service.py

verification_service.py

land_record_service.py

gis_service.py

audit_service.py

---

## workers/

Responsible for background jobs.

Celery should execute long-running document-processing tasks.

---

## core/

Responsible for:

* configuration
* security
* application-wide dependencies

---

## db/

Responsible for:

* database engine
* sessions
* declarative base
* database initialization

---

# 7. DATABASE DESIGN

Primary database:

PostgreSQL.

Do NOT use MongoDB as a second primary application database.

The project has relational workflows and relationships between:

User
Document
Page
OCR
Fields
Validation
Verification
Land Record
GIS
Audit

Therefore PostgreSQL is the primary application database.

---

# 8. UUID STRATEGY

Use UUIDs for primary keys.

Do not use auto-increment integer IDs for primary entities.

Example:

id UUID PRIMARY KEY

Generate UUIDs at the application/database layer consistently.

---

# 9. COMMON TIMESTAMP STRATEGY

Most entities should contain:

created_at
updated_at

Use timezone-aware timestamps.

Prefer UTC internally.

The API may later convert/display timestamps according to user locale.

---

# 10. USER MODEL

Table:

users

Fields:

id
name
email
password_hash
role
is_active
is_verified
created_at
updated_at

Roles:

USER
VERIFIER
ADMIN

Use an enum or controlled representation.

Email should be unique.

---

# 11. DOCUMENT MODEL

A Document represents the original uploaded source.

Fields:

id
user_id
original_filename
storage_path
file_type
file_size
page_count
status
created_at
updated_at

Document status:

UPLOADED
QUEUED
PROCESSING
AWAITING_VERIFICATION
VERIFIED
FAILED

A document belongs to a user.

A document can contain multiple pages.

---

# 12. DOCUMENT PAGE MODEL

Fields:

id
document_id
page_number
original_image_path
enhanced_image_path
width
height
status
document_section
created_at
updated_at

Page numbers must be unique within a document.

Example:

Document 123:

Page 1
Page 2
Page 3

---

# 13. PROCESSING JOB MODEL

Fields:

id
document_id
status
current_stage
progress
error_message
retry_count
started_at
completed_at
created_at
updated_at

Stages:

QUEUED
PAGE_PROCESSING
STRUCTURE_DETECTION
IMAGE_ENHANCEMENT
LANGUAGE_DETECTION
DOCUMENT_TYPE_DETECTION
OCR
FIELD_EXTRACTION
VALIDATION
COMPLETED
FAILED

Progress should be represented as an integer from 0 to 100.

---

# 14. OCR RESULT MODEL

Fields:

id
document_page_id
language
script
raw_text
confidence
model_version_id
processing_time
created_at

OCR result represents the raw OCR output.

Do not overwrite it with corrected text.

---

# 15. OCR REGION MODEL

Fields:

id
ocr_result_id
text
text_type
confidence
x1
y1
x2
y2

text_type:

PRINTED
HANDWRITTEN
UNKNOWN

Bounding boxes are useful for verification UI.

---

# 16. EXTRACTED FIELD MODEL

This is one of the most important tables.

Each canonical field extracted from the document should have a separate record.

Fields:

id
document_id
field_name
raw_value
extracted_value
confidence
source_page_id
source_ocr_region_id
validation_status
verification_status
verified_value
created_at
updated_at

Canonical field names:

owner_name
father_husband_name
khata_number
khasra_number
survey_number
area
village
tehsil
district
land_classification
ownership_type
mutation_number
registration_number

Do not hardcode the values of a record into random database columns at the extraction stage.

Extraction should remain field-level and traceable.

---

# 17. CONFIDENCE

Confidence must be represented as a numeric value.

Recommended range:

0.0 to 1.0

Example:

0.95 = high confidence

0.82 = medium/high confidence

0.42 = low confidence

Do not make confidence a free-form string.

---

# 18. MISSING VALUES

A missing field must be distinguishable from a field containing an empty string.

Use NULL when a value was not found.

The system should eventually distinguish:

NOT_FOUND

from:

FOUND_BUT_LOW_CONFIDENCE

and:

FOUND_BUT_INVALID

---

# 19. AREA REPRESENTATION

Area should NOT be stored only as:

"0.2450 ha"

Use structured data.

For example:

value = 0.2450
unit = hectare

The final API can expose:

{
"value": 0.245,
"unit": "hectare"
}

This makes calculations and search possible.

---

# 20. LAND IDENTIFIERS

The following should generally be strings:

khata_number
khasra_number
survey_number
mutation_number
registration_number

Reason:

Values can contain:

/
letters
leading zeros
hyphens

Example:

235/1

MUT-2024-123

REG-00125

Therefore do not automatically convert these to integers.

---

# 21. VALIDATION ISSUE MODEL

Fields:

id
document_id
field_id
issue_type
severity
message
status
created_at
resolved_at

Possible issue types:

OWNER_MISMATCH
KHATA_MISMATCH
KHASRA_MISMATCH
AREA_MISMATCH
VILLAGE_MISMATCH
DATE_MISMATCH
DUPLICATE_RECORD
FORMAT_ERROR
CROSS_FIELD_CONFLICT

Only implement issue types that are actually useful.

Severity:

LOW
MEDIUM
HIGH
CRITICAL

---

# 22. VERIFICATION TASK MODEL

Fields:

id
document_id
assigned_to
status
priority
created_at
started_at
completed_at

Statuses:

PENDING
IN_REVIEW
COMPLETED
REJECTED

The system should route only suspicious or low-confidence fields to human verification where possible.

Do not force human verification for every field unless required by project policy.

---

# 23. VERIFICATION ACTION MODEL

Fields:

id
verification_task_id
field_id
verifier_id
old_value
new_value
action
comment
created_at

Actions:

APPROVED
CORRECTED
REJECTED

Every correction must be auditable.

---

# 24. FINAL LAND RECORD MODEL

LandRecord represents the final structured, verified record.

Fields:

id
document_id

owner_name
father_husband_name
khata_number
khasra_number
survey_number

area
area_unit

village
tehsil
district

land_classification
ownership_type

mutation_number
registration_number

verification_status
created_at
updated_at
verified_at
verified_by

The final record should only represent the structured canonical record.

The extraction history remains in ExtractedField.

---

# 25. GIS MODEL

GIS is optional.

Not every land record will have GIS information.

Fields:

id
land_record_id
cadastral_id
latitude
longitude
geometry
source
confidence
created_at
updated_at

Possible sources:

DOCUMENT
MANUAL
EXTERNAL_DATA
SYSTEM

Do not require GIS for every record.

The system must work even if no coordinates or parcel geometry are available.

---

# 26. MODEL VERSION MODEL

The system must track which model produced an AI result.

Fields:

id
model_type
version
file_reference
framework
created_at
is_active

Examples:

model_type:

ENHANCEMENT
OCR
DOCUMENT_TYPE
OTHER

Example:

model_type = OCR
version = 1.0.0
file_reference = models/ocr/best.pt
framework = pytorch

---

# 27. AUDIT LOG MODEL

Every important modification should be auditable.

Fields:

id
user_id
document_id
entity_type
entity_id
action
old_value
new_value
metadata
created_at

Examples of actions:

DOCUMENT_CREATED
DOCUMENT_UPDATED
FIELD_CORRECTED
FIELD_APPROVED
RECORD_VERIFIED
GIS_UPDATED
USER_UPDATED

The audit trail should answer:

Who changed it?

What changed?

When?

What was the previous value?

What is the new value?

Why, if applicable?

---

# 28. DATABASE RELATIONSHIPS

Conceptually:

USER
│
└──< DOCUMENT
│
├──< DOCUMENT_PAGE
│       │
│       └── OCR_RESULT
│               │
│               └──< OCR_REGION
│
├──< PROCESSING_JOB
│
├──< EXTRACTED_FIELD
│       │
│       └──< VALIDATION_ISSUE
│
├──< VERIFICATION_TASK
│       │
│       └──< VERIFICATION_ACTION
│
├── LAND_RECORD
│       │
│       └── GIS_REFERENCE
│
└──< AUDIT_LOG

MODEL_VERSION
│
├── Enhancement
└── OCR

---

# 29. INDEXING

Create indexes for fields frequently searched.

Likely indexes:

users.email

documents.user_id

documents.status

documents.created_at

document_pages.document_id

document_pages.page_number

processing_jobs.document_id

processing_jobs.status

extracted_fields.document_id

extracted_fields.field_name

land_records.owner_name

land_records.khata_number

land_records.khasra_number

land_records.village

land_records.tehsil

land_records.district

audit_logs.document_id

audit_logs.created_at

Do not create indexes blindly on every column.

---

# 30. API VERSIONING

All application endpoints should use:

/api/v1

Example:

/api/v1/documents

This allows future API versions.

---

# 31. AUTHENTICATION ENDPOINTS

POST /api/v1/auth/register

POST /api/v1/auth/login

POST /api/v1/auth/logout

POST /api/v1/auth/refresh

POST /api/v1/auth/forgot-password

POST /api/v1/auth/reset-password

GET /api/v1/auth/me

Authentication should eventually use JWT-based authentication.

Password must never be stored in plaintext.

Store password hashes only.

---

# 32. USER ENDPOINTS

GET /api/v1/users/me

PATCH /api/v1/users/me

Admin:

GET /api/v1/admin/users

PATCH /api/v1/admin/users/{user_id}

---

# 33. DOCUMENT ENDPOINTS

POST /api/v1/documents

GET /api/v1/documents

GET /api/v1/documents/{document_id}

DELETE /api/v1/documents/{document_id}

GET /api/v1/documents/{document_id}/pages

Document upload must validate:

file type
file size
filename
storage destination

Supported file types initially:

PDF
JPG
JPEG
PNG

Make allowed file types configurable.

---

# 34. PROCESSING ENDPOINTS

POST /api/v1/documents/{document_id}/process

GET /api/v1/documents/{document_id}/status

POST /api/v1/documents/{document_id}/retry

The process endpoint should NOT perform the entire pipeline synchronously.

It should create/enqueue a processing job.

Celery should handle long-running processing.

---

# 35. RESULT ENDPOINTS

GET /api/v1/documents/{document_id}/ocr

GET /api/v1/documents/{document_id}/fields

GET /api/v1/documents/{document_id}/land-record

GET /api/v1/documents/{document_id}/enhanced-pages

---

# 36. VERIFICATION ENDPOINTS

GET /api/v1/verification/tasks

GET /api/v1/verification/tasks/{task_id}

POST /api/v1/verification/tasks/{task_id}/start

PATCH /api/v1/verification/tasks/{task_id}/fields/{field_id}

POST /api/v1/verification/tasks/{task_id}/complete

Only users with VERIFIER or ADMIN permissions should perform verification actions.

---

# 37. LAND RECORD ENDPOINTS

GET /api/v1/land-records

GET /api/v1/land-records/{record_id}

PATCH /api/v1/land-records/{record_id}

Support filtering by:

owner_name
khata_number
khasra_number
survey_number
village
tehsil
district

Also support:

pagination
status filters
date filters

---

# 38. GIS ENDPOINTS

GET /api/v1/land-records/{record_id}/gis

POST /api/v1/land-records/{record_id}/gis

PATCH /api/v1/land-records/{record_id}/gis

GET /api/v1/gis/parcels

Return GeoJSON-compatible data where appropriate.

GIS functionality must remain optional.

---

# 39. DASHBOARD ENDPOINTS

GET /api/v1/dashboard/summary

GET /api/v1/dashboard/recent-documents

GET /api/v1/dashboard/processing

GET /api/v1/dashboard/verification

Dashboard statistics should be generated from actual database data.

---

# 40. ADMIN ENDPOINTS

GET /api/v1/admin/users

PATCH /api/v1/admin/users/{user_id}

GET /api/v1/admin/processing

GET /api/v1/admin/model-versions

POST /api/v1/admin/model-versions

GET /api/v1/admin/audit-logs

Protect admin endpoints using role-based authorization.

---

# 41. STORAGE ARCHITECTURE

Do not store image/PDF binary data directly inside PostgreSQL.

Store files in:

local filesystem initially

or

S3-compatible object storage later.

Database should store:

storage_path

or object storage key.

Create an abstraction:

storage_service.py

so that local storage can later be replaced with S3 without rewriting the document pipeline.

---

# 42. DOCUMENT PROCESSING PIPELINE

The processing pipeline is:

1. Upload document
2. Validate file
3. Store original
4. Create Document record
5. Detect page count
6. Render PDF pages if necessary
7. Create DocumentPage records
8. Detect document structure
9. Enhance images
10. Detect language/script
11. Detect document type
12. Run OCR
13. Store OCR results
14. Extract canonical fields
15. Calculate field confidence
16. Validate extracted fields
17. Detect inconsistencies
18. Create verification tasks for suspicious fields
19. Human verification
20. Create/update final LandRecord
21. Optional GIS mapping
22. Audit all important changes

---

# 43. ML ARCHITECTURE

IMPORTANT:

ML models are NOT separate HTTP microservices.

Do not create:

ml-service
ocr-service
model-server

unless explicitly requested later.

The backend directly loads and calls inference code.

Architecture:

backend
↓
service
↓
ml inference module
↓
best.pt
↓
prediction

---

# 44. TRAINING VS INFERENCE

Training code:

ml/enhancement/training/

ml/ocr/training/

This code is intended to run in environments such as Kaggle.

Inference code:

ml/enhancement/inference/

ml/ocr/inference/

This code is imported by the backend.

Training creates:

best.pt

Production loads:

best.pt

---

# 45. MODEL ARTIFACT RULE

Do not automatically commit large trained models to GitHub.

Use:

models/

for local/development model references.

Later use object storage/model registry if necessary.

The system must record:

model version
framework
model path/reference
creation date

---

# 46. MODEL LOADER DESIGN

Each production model should have a clean interface.

Conceptually:

class EnhancementModel:
load()
predict()

and:

class OCRModel:
load()
predict()

Do not scatter model-loading code throughout routes.

Model loading should happen in the appropriate service/inference layer.

---

# 47. MODEL CONFIGURATION

Model locations should be configurable.

Example:

ENHANCEMENT_MODEL_PATH=models/enhancement/best.pt

OCR_MODEL_PATH=models/ocr/best.pt

Do not hardcode absolute Windows paths.

---

# 48. CELERY ARCHITECTURE

Redis will act as the message broker initially.

Architecture:

FastAPI
↓
Create ProcessingJob
↓
Celery
↓
Redis
↓
Processing Worker
↓
Processing Service
↓
ML / OCR / Extraction / Validation
↓
PostgreSQL

The HTTP request should return quickly instead of waiting for the entire document pipeline.

---

# 49. PROCESSING JOB BEHAVIOR

When processing starts:

Document:

QUEUED

Then:

PROCESSING

ProcessingJob:

QUEUED
→ PAGE_PROCESSING
→ STRUCTURE_DETECTION
→ IMAGE_ENHANCEMENT
→ LANGUAGE_DETECTION
→ DOCUMENT_TYPE_DETECTION
→ OCR
→ FIELD_EXTRACTION
→ VALIDATION
→ COMPLETED

If an unrecoverable error occurs:

FAILED

Store error_message.

Support retries.

Do not silently swallow exceptions.

---

# 50. CONFIDENCE + HUMAN VERIFICATION LOGIC

The system should support configurable confidence thresholds.

Example conceptual configuration:

HIGH_CONFIDENCE_THRESHOLD = 0.90

LOW_CONFIDENCE_THRESHOLD = 0.70

These are examples only.

Do not assume these values are scientifically validated.

They must eventually be tuned using actual project validation data.

Potential logic:

confidence >= threshold:
likely accepted

confidence below threshold:
verification required

But confidence alone should not be the only trigger.

Also consider:

validation errors
cross-page conflicts
field format errors
contradictory values
document inconsistencies

---

# 51. VALIDATION LOGIC

Validation should include:

## Format validation

Examples:

Khata number format

Khasra number format

Registration number format

Mutation number format

## Cross-field validation

Example:

Village from page 1:

Chinhat

Village from page 3:

Chinhat

No conflict.

But:

Page 1:
Chinhat

Page 3:
Malhaur

Potential inconsistency.

## Cross-page validation

Compare extracted fields across pages.

## Confidence validation

Flag low-confidence fields.

---

# 52. HUMAN VERIFICATION WORKFLOW

Example:

AI extracts:

owner_name = राम सिंह
confidence = 0.93

No verification needed if all validation checks pass.

Another field:

khasra_number = 235/?
confidence = 0.42

Create verification task.

Verifier sees:

Original page
Enhanced page
OCR text
Bounding box
Extracted value
Confidence
Validation issues

Verifier can:

Approve
Correct
Reject

Every action is recorded.

---

# 53. AUDIT REQUIREMENTS

Important operations must create audit records.

Examples:

document uploaded

document deleted

field corrected

field approved

field rejected

land record verified

GIS changed

user role changed

The audit log should contain enough information to reconstruct important changes.

---

# 54. ERROR HANDLING

Create centralized exception handling where useful.

API errors should have consistent structure.

Example:

{
"detail": "Document not found"
}

For validation errors, use FastAPI/Pydantic's standard validation mechanism unless a custom format is genuinely needed.

Do not expose stack traces to API clients in production.

Log internal errors.

---

# 55. LOGGING

Use Python logging.

Avoid print() for production application logs.

Useful events:

document upload

processing started

processing stage changed

processing completed

processing failed

ML inference failure

verification completed

database errors

---

# 56. TESTING STRATEGY

Use pytest.

Tests should be organized approximately as:

tests/
├── conftest.py
├── test_health.py
├── test_auth.py
├── test_documents.py
├── test_processing.py
├── test_extraction.py
├── test_validation.py
├── test_verification.py
├── test_land_records.py
└── test_gis.py

Start testing small.

First:

GET /api/v1/health

Then database.

Then document creation.

Then upload.

Then processing.

---

# 57. API TESTING

Use HTTPX/TestClient.

Every important API endpoint should eventually have tests.

Test:

success

invalid input

unauthorized access

forbidden access

not found

duplicate records

validation failures

---

# 58. DATABASE MIGRATIONS

Use Alembic.

Never manually modify production database tables.

Schema changes should happen through migrations.

Typical workflow:

alembic revision --autogenerate -m "create users table"

alembic upgrade head

Before committing a migration:

Review it manually.

Do not blindly trust autogenerated migrations.

---

# 59. ENVIRONMENT CONFIGURATION

Use:

.env

for local development.

Use:

.env.example

for the repository.

Never commit:

.env

Never hardcode:

passwords
JWT secrets
database passwords
API keys
cloud credentials
absolute local paths

---

# 60. CODE STYLE

Prefer:

clear names
small functions
type hints
docstrings where useful
explicit code
simple architecture

Avoid:

unnecessary abstractions
generic "manager" classes
huge utility files
global mutable state
copy-pasted business logic
business logic inside routes

---

# 61. IMPORTANT DESIGN RULE

Do not create unnecessary microservices.

This project should initially be a modular monolith:

FastAPI application
+
Celery worker
+
PostgreSQL
+
Redis
+
ML inference modules

That is enough.

Do not introduce:

Kubernetes
Kafka
GraphQL
separate ML HTTP services
service mesh
event streaming infrastructure

unless the project requirements later justify them.

---

# 62. PHASED IMPLEMENTATION PLAN

Implement the backend in the following phases.

Do not attempt all phases in one Cursor request.

---

# PHASE 1 — PROJECT FOUNDATION

Goal:

Get a clean, runnable FastAPI backend.

Already started.

Tasks:

1. Verify repository structure.
2. Verify virtual environment.
3. Configure FastAPI.
4. Create main.py.
5. Create API router.
6. Create health endpoint.
7. Configure environment variables.
8. Add .gitignore.
9. Add README.
10. Add basic tests.
11. Ensure Swagger works.

Expected endpoints:

GET /
GET /api/v1/health

Acceptance criteria:

uvicorn starts.

Swagger loads.

Health endpoint returns 200.

---

# PHASE 2 — DATABASE FOUNDATION

Goal:

Connect FastAPI to PostgreSQL correctly.

Tasks:

1. Install SQLAlchemy.
2. Install PostgreSQL driver.
3. Create database.py.
4. Create Base class.
5. Create session dependency.
6. Configure DATABASE_URL.
7. Configure Alembic.
8. Create initial migration.
9. Create User model.
10. Create user migration.
11. Test database connection.
12. Add database tests.

Do NOT create every model yet.

Start with User.

Acceptance criteria:

FastAPI can connect to PostgreSQL.

Alembic works.

User table exists.

A test can create/read a user.

---

# PHASE 3 — AUTHENTICATION + AUTHORIZATION

Goal:

Implement secure user authentication.

Tasks:

1. Password hashing.
2. JWT access token.
3. Refresh token strategy if needed.
4. Register.
5. Login.
6. Logout strategy.
7. Current-user dependency.
8. Role dependency.
9. USER role.
10. VERIFIER role.
11. ADMIN role.
12. Protected endpoints.

Endpoints:

POST /api/v1/auth/register

POST /api/v1/auth/login

POST /api/v1/auth/logout

POST /api/v1/auth/refresh

GET /api/v1/auth/me

Acceptance criteria:

User can register.

User can login.

Protected route requires authentication.

Verifier-only route rejects USER.

Admin-only route rejects USER and VERIFIER.

---

# PHASE 4 — DOCUMENT MANAGEMENT

Goal:

Allow users to upload and manage source documents.

Tasks:

1. Document model.
2. Document schema.
3. Document service.
4. File validation.
5. Storage service.
6. Local storage implementation.
7. Upload endpoint.
8. List documents.
9. Get document.
10. Delete document.
11. Document page model.
12. PDF page handling.
13. Create DocumentPage records.

Endpoints:

POST /api/v1/documents

GET /api/v1/documents

GET /api/v1/documents/{document_id}

DELETE /api/v1/documents/{document_id}

GET /api/v1/documents/{document_id}/pages

Acceptance criteria:

User uploads PDF.

Original file is stored.

Database stores metadata.

Document is visible through API.

PDF pages can be represented as DocumentPage records.

---

# PHASE 5 — PROCESSING JOB SYSTEM

Goal:

Introduce asynchronous processing.

Tasks:

1. Redis.
2. Celery.
3. ProcessingJob model.
4. ProcessingJob migration.
5. Celery configuration.
6. Worker.
7. Processing status endpoint.
8. Retry endpoint.
9. Job state updates.
10. Error handling.

Endpoints:

POST /api/v1/documents/{document_id}/process

GET /api/v1/documents/{document_id}/status

POST /api/v1/documents/{document_id}/retry

Acceptance criteria:

Calling process creates a job.

Celery receives job.

Worker updates status.

FastAPI does not block during processing.

---

# PHASE 6 — IMAGE/PAGE PROCESSING

Goal:

Prepare pages for ML.

Tasks:

1. PDF rendering.
2. Image loading.
3. Page dimensions.
4. Blank-page detection.
5. Image normalization.
6. Image enhancement service abstraction.
7. Enhanced image storage.
8. Page status updates.

Do not tightly couple this phase to the final trained model yet.

Create a clean interface that can later load best.pt.

---

# PHASE 7 — ML INTEGRATION

Goal:

Integrate actual trained models.

Training happens externally, such as Kaggle.

Backend uses inference code.

Structure:

ml/enhancement/training/

ml/enhancement/inference/

ml/ocr/training/

ml/ocr/inference/

Tasks:

1. Define inference interfaces.
2. Create model loader.
3. Load best.pt.
4. Configure model path.
5. Implement preprocessing.
6. Implement prediction.
7. Convert output into application-friendly structures.
8. Store ModelVersion.
9. Record model version with results.
10. Handle inference errors.
11. Test inference independently.

Do not expose models through HTTP services.

---

# PHASE 8 — OCR

Goal:

Store raw OCR output.

Tasks:

1. OCRResult model.
2. OCRRegion model.
3. OCR schemas.
4. OCR service.
5. OCR inference integration.
6. Language/script metadata.
7. Confidence.
8. Bounding boxes.
9. Printed/handwritten classification where available.
10. OCR API.

Endpoint:

GET /api/v1/documents/{document_id}/ocr

Acceptance criteria:

A processed page produces OCRResult.

OCR regions can be stored.

Raw OCR is preserved.

---

# PHASE 9 — FIELD EXTRACTION

Goal:

Extract the canonical land-record fields.

Fields:

owner_name

father_husband_name

khata_number

khasra_number

survey_number

area

village

tehsil

district

land_classification

ownership_type

mutation_number

registration_number

Tasks:

1. ExtractedField model.
2. Schema.
3. Extraction service.
4. Canonical field configuration.
5. Source page tracking.
6. OCR region tracking.
7. Confidence.
8. Missing field handling.
9. Extraction API.

Endpoint:

GET /api/v1/documents/{document_id}/fields

Acceptance criteria:

Each extracted field is traceable to source OCR/page information.

---

# PHASE 10 — VALIDATION + INCONSISTENCY DETECTION

Goal:

Detect suspicious data.

Tasks:

1. ValidationIssue model.
2. Validation service.
3. Format validation.
4. Cross-field validation.
5. Cross-page validation.
6. Confidence-based flags.
7. Duplicate detection where appropriate.
8. Severity levels.
9. Validation status.

Acceptance criteria:

Invalid/suspicious fields generate ValidationIssue records.

---

# PHASE 11 — HUMAN VERIFICATION

Goal:

Allow a human verifier to review suspicious fields.

Tasks:

1. VerificationTask model.
2. VerificationAction model.
3. Task creation.
4. Assignment.
5. Start review.
6. Approve field.
7. Correct field.
8. Reject field.
9. Add comments.
10. Complete task.
11. Audit all actions.

Endpoints:

GET /api/v1/verification/tasks

GET /api/v1/verification/tasks/{task_id}

POST /api/v1/verification/tasks/{task_id}/start

PATCH /api/v1/verification/tasks/{task_id}/fields/{field_id}

POST /api/v1/verification/tasks/{task_id}/complete

---

# PHASE 12 — FINAL LAND RECORD

Goal:

Create the final canonical structured land record.

Tasks:

1. LandRecord model.
2. LandRecord schema.
3. Finalization service.
4. Verification status.
5. Verified timestamp.
6. Verified by user.
7. Link to original document.
8. Preserve extraction history.

Endpoints:

GET /api/v1/documents/{document_id}/land-record

GET /api/v1/land-records

GET /api/v1/land-records/{record_id}

PATCH /api/v1/land-records/{record_id}

Acceptance criteria:

Final record contains the 13 canonical fields.

Original OCR and extracted fields remain unchanged.

---

# PHASE 13 — GIS

Goal:

Associate land records with geographic information when available.

Tasks:

1. GISReference model.
2. Coordinates.
3. Cadastral ID.
4. Geometry.
5. GeoJSON representation.
6. GIS service.
7. GIS endpoints.

Endpoints:

GET /api/v1/land-records/{record_id}/gis

POST /api/v1/land-records/{record_id}/gis

PATCH /api/v1/land-records/{record_id}/gis

GET /api/v1/gis/parcels

GIS must remain optional.

---

# PHASE 14 — SEARCH + DASHBOARD

Goal:

Provide useful application-level querying.

Search by:

owner

khata

khasra

survey number

village

tehsil

district

document ID

Support:

pagination
filtering
sorting

Dashboard:

total documents

processing

completed

failed

awaiting verification

verified

recent documents

verification workload

---

# PHASE 15 — AUDIT + ADMIN

Goal:

Complete governance features.

Tasks:

1. AuditLog model.
2. Audit service.
3. Automatic audit events.
4. Admin users.
5. Model versions.
6. Processing monitoring.
7. Audit search.
8. Role management.

---

# PHASE 16 — TESTING + HARDENING

Goal:

Make backend reliable.

Tasks:

1. Unit tests.
2. Integration tests.
3. API tests.
4. Authentication tests.
5. Database tests.
6. File-upload tests.
7. Processing tests.
8. Validation tests.
9. Verification tests.
10. GIS tests.
11. Error handling.
12. Logging.
13. Security review.
14. Input validation.
15. File-size limits.
16. MIME validation.

---

# PHASE 17 — DOCKER + DEPLOYMENT

Goal:

Make the system reproducible.

Services:

backend

frontend

postgres

redis

celery worker

potentially object storage

Create:

Dockerfile

docker-compose.yml

environment configuration

health checks

deployment documentation

Do not introduce Kubernetes unless later required.

---

# 63. CURSOR WORKING RULES

When using Cursor to implement this project, follow these rules.

## Rule 1

Before modifying code, inspect the existing repository.

Do not blindly recreate files.

## Rule 2

Implement only the requested phase.

Do not implement future phases automatically.

## Rule 3

Do not change the architecture without explaining why.

## Rule 4

Do not add unnecessary dependencies.

## Rule 5

Do not create microservices.

## Rule 6

Do not put business logic inside route files.

## Rule 7

Do not put SQLAlchemy models inside schemas.

## Rule 8

Do not put Pydantic schemas inside models.

## Rule 9

Do not hardcode secrets.

## Rule 10

Do not hardcode Windows paths.

## Rule 11

Do not commit trained model files unless explicitly requested.

## Rule 12

Every database schema change must have an Alembic migration.

## Rule 13

Every major feature should have tests.

## Rule 14

Keep functions reasonably small.

## Rule 15

Use type hints.

## Rule 16

Preserve backwards compatibility with existing API endpoints unless explicitly changing them.

---

# 64. CURSOR PROMPT TEMPLATE

For every phase, use a prompt like:

"Read docs/BACKEND_IMPLEMENTATION_SPEC.md first.

We are currently implementing PHASE X.

Inspect the existing repository before changing anything.

Implement only this phase.

Do not implement future phases.

Follow the architecture and database conventions defined in the specification.

After implementation:

1. Explain files created/changed.
2. Explain important design decisions.
3. Show commands needed to run/test it.
4. Add/update tests.
5. Check for import errors.
6. Check that existing endpoints still work.
7. Do not remove existing functionality."

---

# 65. FIRST CURSOR PROMPT

The first Cursor task after creating this specification should be:

"Read docs/BACKEND_IMPLEMENTATION_SPEC.md.

We are currently at PHASE 1.

Inspect the existing repository.

Do not rebuild the project from scratch.

Verify the existing FastAPI setup.

Check that:

GET /
GET /api/v1/health

work correctly.

Check Swagger.

Add basic test infrastructure for the health endpoint if it does not already exist.

Check configuration and .env.example.

Do not implement database models, authentication, Celery, ML, OCR, GIS, or future phases.

After changes, explain exactly what was changed and how to run the tests."

---

# 66. SECOND CURSOR PROMPT — DATABASE

After Phase 1 is stable:

"Read docs/BACKEND_IMPLEMENTATION_SPEC.md.

Implement PHASE 2 only.

Inspect the existing FastAPI code first.

Set up:

SQLAlchemy 2.x
PostgreSQL
Alembic
database engine
session management
declarative Base
database dependency

Then implement only the User model.

Create the appropriate Alembic migration.

Add database tests.

Do not implement authentication yet.

Do not implement Document, OCR, ML, Celery, Redis, GIS, or other future models.

Use UUID primary keys and timezone-aware timestamps according to the specification.

Do not hardcode database credentials.

Update requirements.txt and .env.example as necessary.

After implementation, explain:

1. files created
2. files modified
3. database setup commands
4. migration commands
5. test commands
6. any assumptions."

---

# 67. IMPORTANT IMPLEMENTATION PHILOSOPHY

Dharohar should be built incrementally.

At every phase:

Code
→ Run
→ Test
→ Commit
→ Move to next phase.

Recommended Git commit style:

chore: initialize backend

feat: add database foundation

feat: add authentication

feat: add document management

feat: add processing jobs

feat: add ml inference integration

feat: add ocr pipeline

feat: add field extraction

feat: add validation

feat: add human verification

feat: add land records

feat: add gis integration

feat: add dashboard

feat: add audit logging

test: improve backend coverage

chore: add docker deployment

---

# 68. FINAL BACKEND ARCHITECTURE

The completed backend should conceptually look like:

```
                    FRONTEND
                        │
                        ▼
                   FASTAPI
                        │
          ┌─────────────┴─────────────┐
          │                           │
       ROUTES                      AUTH
          │
          ▼
      SERVICES
          │
 ┌────────┼─────────┬──────────┐
 │        │         │          │
 ▼        ▼         ▼          ▼
```

PostgreSQL  Storage   Celery      ML
│           │
▼           ▼
Redis      best.pt
│
▼
Processing Worker
│
▼
Processing Service
│
┌─────────────┼─────────────┐
▼             ▼             ▼
Enhancement       OCR        Extraction
│
▼
Validation
│
▼
Verification
│
▼
LandRecord
│
▼
GIS

---

# 69. CORE PRODUCT DATA FLOW

The complete data flow is:

User
→ Upload PDF/Image
→ Document
→ Document Pages
→ Enhanced Pages
→ OCR Result
→ OCR Regions
→ Extracted Fields
→ Validation Issues
→ Verification Task
→ Verification Actions
→ Final Land Record
→ GIS Reference
→ Audit Log

Every important stage must remain traceable.

---

# 70. NON-NEGOTIABLE DATA PRINCIPLE

Never destroy source information merely because a later stage has better information.

Keep:

Original document

Original page

Enhanced page

Raw OCR

OCR regions

Extracted value

Confidence

Validation result

Human correction

Final verified value

Audit history

This traceability is a core requirement of Dharohar.
