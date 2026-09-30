"""
Tests for Phase 5 — Processing Job System.

Covers:
- POST /api/v1/documents/{id}/process  (trigger)
- GET  /api/v1/documents/{id}/status   (status polling)
- POST /api/v1/documents/{id}/retry    (retry)

Processing is run synchronously in tests via CELERY_ALWAYS_EAGER=True (set in conftest
via monkeypatching) or via the route's fallback inline-execution path when Celery is
unavailable.  Either way the job state is asserted after the call returns.
"""
import io
import base64
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_png() -> bytes:
    png_b64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8"
        "z8BQDwADhQGAWjR9awAAAABJRU5ErkJggg=="
    )
    return base64.b64decode(png_b64)


def _register_and_login(client: TestClient, email: str, role: str = "USER") -> str:
    client.post(
        "/api/v1/auth/register",
        json={"name": "Proc User", "email": email, "password": "TestPass123!", "role": role},
    )
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "TestPass123!"},
    )
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _upload(client: TestClient, token: str) -> str:
    files = {"file": ("test.png", io.BytesIO(_fake_png()), "image/png")}
    resp = client.post("/api/v1/documents", files=files, headers=_auth(token))
    assert resp.status_code == 201
    return resp.json()["id"]


# ---------------------------------------------------------------------------
# Trigger processing
# ---------------------------------------------------------------------------

class TestStartProcessing:
    def test_process_accepted(self, client: TestClient):
        """
        POST /process should return 202 Accepted and create a processing job.
        Celery dispatch is mocked to avoid needing a broker; the route's inline
        fallback runs the pipeline synchronously.
        """
        token = _register_and_login(client, "proc_start@example.com")
        doc_id = _upload(client, token)

        # Patch Celery task so it raises (triggers inline sync fallback in route)
        with patch("app.workers.processing_worker.process_document_task.delay") as mock_delay:
            mock_delay.side_effect = Exception("broker unavailable")
            resp = client.post(f"/api/v1/documents/{doc_id}/process", headers=_auth(token))

        assert resp.status_code == 202
        body = resp.json()
        assert "id" in body
        assert body["document_id"] == doc_id

    def test_process_nonexistent_document(self, client: TestClient):
        token = _register_and_login(client, "proc_notfound@example.com")
        fake_id = "00000000-0000-0000-0000-000000000010"
        resp = client.post(f"/api/v1/documents/{fake_id}/process", headers=_auth(token))
        assert resp.status_code == 404

    def test_process_requires_auth(self, client: TestClient):
        resp = client.post("/api/v1/documents/00000000-0000-0000-0000-000000000010/process")
        assert resp.status_code == 401

    def test_process_other_users_document_denied(self, client: TestClient):
        token_a = _register_and_login(client, "proc_owner@example.com")
        token_b = _register_and_login(client, "proc_other@example.com")
        doc_id = _upload(client, token_a)
        resp = client.post(f"/api/v1/documents/{doc_id}/process", headers=_auth(token_b))
        assert resp.status_code in (403, 404)


# ---------------------------------------------------------------------------
# Status polling
# ---------------------------------------------------------------------------

class TestProcessingStatus:
    def test_status_before_processing(self, client: TestClient):
        token = _register_and_login(client, "proc_status_pre@example.com")
        doc_id = _upload(client, token)
        resp = client.get(f"/api/v1/documents/{doc_id}/status", headers=_auth(token))
        assert resp.status_code == 200
        body = resp.json()
        assert "status" in body
        assert "document_id" in body
        assert body["document_id"] == doc_id

    def test_status_after_processing(self, client: TestClient):
        token = _register_and_login(client, "proc_status_after@example.com")
        doc_id = _upload(client, token)

        with patch("app.workers.processing_worker.process_document_task.delay") as mock_delay:
            mock_delay.side_effect = Exception("broker unavailable")
            client.post(f"/api/v1/documents/{doc_id}/process", headers=_auth(token))

        resp = client.get(f"/api/v1/documents/{doc_id}/status", headers=_auth(token))
        assert resp.status_code == 200
        body = resp.json()
        # Job was created so status should be a known value
        assert body["status"] in ("QUEUED", "PROCESSING", "COMPLETED", "FAILED")

    def test_status_nonexistent_document(self, client: TestClient):
        token = _register_and_login(client, "proc_status_none@example.com")
        fake_id = "00000000-0000-0000-0000-000000000011"
        resp = client.get(f"/api/v1/documents/{fake_id}/status", headers=_auth(token))
        assert resp.status_code == 404

    def test_status_requires_auth(self, client: TestClient):
        resp = client.get("/api/v1/documents/00000000-0000-0000-0000-000000000010/status")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Retry
# ---------------------------------------------------------------------------

class TestRetryProcessing:
    def test_retry_creates_new_job(self, client: TestClient):
        token = _register_and_login(client, "proc_retry@example.com")
        doc_id = _upload(client, token)

        with patch("app.workers.processing_worker.process_document_task.delay") as mock_delay:
            mock_delay.side_effect = Exception("broker unavailable")
            # First run
            first_resp = client.post(f"/api/v1/documents/{doc_id}/process", headers=_auth(token))
            assert first_resp.status_code == 202
            # Retry
            retry_resp = client.post(f"/api/v1/documents/{doc_id}/retry", headers=_auth(token))
            assert retry_resp.status_code == 200

        retry_body = retry_resp.json()
        assert retry_body["document_id"] == doc_id
        assert retry_body["retry_count"] >= 1

    def test_retry_nonexistent_document(self, client: TestClient):
        token = _register_and_login(client, "proc_retry_none@example.com")
        fake_id = "00000000-0000-0000-0000-000000000012"
        resp = client.post(f"/api/v1/documents/{fake_id}/retry", headers=_auth(token))
        assert resp.status_code == 404

    def test_retry_requires_auth(self, client: TestClient):
        resp = client.post("/api/v1/documents/00000000-0000-0000-0000-000000000010/retry")
        assert resp.status_code == 401
