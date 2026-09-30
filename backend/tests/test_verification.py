"""
Tests for Phase 11 — Human Verification.

Covers:
- GET  /api/v1/verification/tasks                           (list)
- GET  /api/v1/verification/tasks/{id}                      (detail)
- POST /api/v1/verification/tasks/{id}/start                (start review)
- PATCH /api/v1/verification/tasks/{id}/fields/{field_id}   (approve/correct)
- POST /api/v1/verification/tasks/{id}/complete             (complete task)
- Role restrictions (only VERIFIER / ADMIN may act)
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
        json={"name": "Verif User", "email": email, "password": "TestPass123!", "role": role},
    )
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "TestPass123!"},
    )
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _upload_and_process(client: TestClient, token: str) -> str:
    """Upload a document and run the processing pipeline (Celery broker mocked)."""
    files = {"file": ("verif.png", io.BytesIO(_fake_png()), "image/png")}
    doc_id = client.post("/api/v1/documents", files=files, headers=_auth(token)).json()["id"]
    with patch("app.workers.processing_worker.process_document_task.delay") as m:
        m.side_effect = Exception("no broker")
        client.post(f"/api/v1/documents/{doc_id}/process", headers=_auth(token))
    return doc_id


# ---------------------------------------------------------------------------
# Access control
# ---------------------------------------------------------------------------

class TestVerificationAccessControl:
    def test_list_tasks_rejected_for_user(self, client: TestClient):
        token = _register_and_login(client, "verif_ac_user@example.com", role="USER")
        resp = client.get("/api/v1/verification/tasks", headers=_auth(token))
        assert resp.status_code == 403

    def test_list_tasks_allowed_for_verifier(self, client: TestClient):
        token = _register_and_login(client, "verif_ac_verifier@example.com", role="VERIFIER")
        resp = client.get("/api/v1/verification/tasks", headers=_auth(token))
        assert resp.status_code == 200

    def test_list_tasks_allowed_for_admin(self, client: TestClient):
        token = _register_and_login(client, "verif_ac_admin@example.com", role="ADMIN")
        resp = client.get("/api/v1/verification/tasks", headers=_auth(token))
        assert resp.status_code == 200

    def test_list_tasks_requires_auth(self, client: TestClient):
        resp = client.get("/api/v1/verification/tasks")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# List verification tasks
# ---------------------------------------------------------------------------

class TestListVerificationTasks:
    def test_list_returns_paginated_response(self, client: TestClient):
        token = _register_and_login(client, "verif_list@example.com", role="VERIFIER")
        resp = client.get("/api/v1/verification/tasks", headers=_auth(token))
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert "page" in body

    def test_list_filter_by_status(self, client: TestClient):
        token = _register_and_login(client, "verif_filter_s@example.com", role="VERIFIER")
        resp = client.get("/api/v1/verification/tasks?status=PENDING", headers=_auth(token))
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["status"] == "PENDING"

    def test_list_filter_by_priority(self, client: TestClient):
        token = _register_and_login(client, "verif_filter_p@example.com", role="VERIFIER")
        resp = client.get("/api/v1/verification/tasks?priority=HIGH", headers=_auth(token))
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["priority"] == "HIGH"


# ---------------------------------------------------------------------------
# Get task detail
# ---------------------------------------------------------------------------

class TestGetVerificationTask:
    def test_get_nonexistent_task(self, client: TestClient):
        token = _register_and_login(client, "verif_get_none@example.com", role="VERIFIER")
        fake_id = "00000000-0000-0000-0000-000000000030"
        resp = client.get(f"/api/v1/verification/tasks/{fake_id}", headers=_auth(token))
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Task lifecycle (requires an actual verification task to exist)
# ---------------------------------------------------------------------------

class TestVerificationTaskLifecycle:
    def _ensure_task(self, client: TestClient, verifier_token: str):
        """
        Upload + process a document as a regular user to generate a verification task,
        then return the task id if one was created.
        """
        user_token = _register_and_login(client, "verif_lifecycle_user@example.com", role="USER")
        _upload_and_process(client, user_token)

        resp = client.get("/api/v1/verification/tasks", headers=_auth(verifier_token))
        tasks = resp.json()["items"]
        return tasks[0]["id"] if tasks else None

    def test_start_nonexistent_task(self, client: TestClient):
        token = _register_and_login(client, "verif_start_none@example.com", role="VERIFIER")
        fake_id = "00000000-0000-0000-0000-000000000031"
        resp = client.post(f"/api/v1/verification/tasks/{fake_id}/start", headers=_auth(token))
        assert resp.status_code == 404

    def test_complete_nonexistent_task(self, client: TestClient):
        token = _register_and_login(client, "verif_complete_none@example.com", role="VERIFIER")
        fake_id = "00000000-0000-0000-0000-000000000032"
        resp = client.post(f"/api/v1/verification/tasks/{fake_id}/complete", headers=_auth(token))
        assert resp.status_code == 404

    def test_full_lifecycle_if_task_exists(self, client: TestClient):
        """
        If the processing pipeline produced a verification task (which it will when the
        stub OCR returns low-confidence fields), exercise the full start → approve → complete flow.
        """
        verifier_token = _register_and_login(
            client, "verif_full_v@example.com", role="VERIFIER"
        )
        task_id = self._ensure_task(client, verifier_token)
        if task_id is None:
            pytest.skip("No verification task was created by the pipeline — skipping lifecycle test")

        # Start
        start_resp = client.post(
            f"/api/v1/verification/tasks/{task_id}/start",
            headers=_auth(verifier_token),
        )
        assert start_resp.status_code == 200
        assert start_resp.json()["status"] == "IN_REVIEW"

        # Get task detail to find a field
        detail_resp = client.get(
            f"/api/v1/verification/tasks/{task_id}",
            headers=_auth(verifier_token),
        )
        assert detail_resp.status_code == 200
        fields = detail_resp.json().get("fields", [])
        if not fields:
            pytest.skip("No fields available on this task")

        field_id = fields[0]["id"]

        # Approve the first field
        action_resp = client.patch(
            f"/api/v1/verification/tasks/{task_id}/fields/{field_id}",
            json={"action": "APPROVED", "comment": "Looks correct"},
            headers=_auth(verifier_token),
        )
        assert action_resp.status_code == 200
        assert action_resp.json()["action"] == "APPROVED"

        # Complete the task
        complete_resp = client.post(
            f"/api/v1/verification/tasks/{task_id}/complete",
            headers=_auth(verifier_token),
        )
        assert complete_resp.status_code == 200
        assert complete_resp.json()["status"] == "COMPLETED"
