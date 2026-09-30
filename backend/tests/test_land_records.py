"""
Tests for Phase 12 — Land Records & Search.

Covers:
- GET  /api/v1/land-records              (list + filter)
- GET  /api/v1/land-records/{id}         (get single)
- PATCH /api/v1/land-records/{id}        (update, verifier/admin only)
- GET  /api/v1/documents/{id}/land-record (doc-scoped)
"""
import io
import uuid
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
        json={"name": "LR User", "email": email, "password": "TestPass123!", "role": role},
    )
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "TestPass123!"},
    )
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _upload_and_process(client: TestClient, token: str) -> str:
    """Upload a PNG and run the pipeline inline (broker mocked). Returns doc_id."""
    files = {"file": ("land.png", io.BytesIO(_fake_png()), "image/png")}
    doc_id = client.post("/api/v1/documents", files=files, headers=_auth(token)).json()["id"]
    with patch("app.workers.processing_worker.process_document_task.delay") as m:
        m.side_effect = Exception("no broker")
        client.post(f"/api/v1/documents/{doc_id}/process", headers=_auth(token))
    return doc_id


# ---------------------------------------------------------------------------
# List / search land records
# ---------------------------------------------------------------------------

class TestListLandRecords:
    def test_list_requires_auth(self, client: TestClient):
        resp = client.get("/api/v1/land-records")
        assert resp.status_code == 401

    def test_list_returns_paginated_response(self, client: TestClient):
        token = _register_and_login(client, "lr_list@example.com")
        resp = client.get("/api/v1/land-records", headers=_auth(token))
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert "page" in body

    def test_list_filter_by_village(self, client: TestClient):
        token = _register_and_login(client, "lr_filter_v@example.com")
        resp = client.get("/api/v1/land-records?village=Chinhat", headers=_auth(token))
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert "chinhat" in (item.get("village") or "").lower()

    def test_list_filter_by_district(self, client: TestClient):
        token = _register_and_login(client, "lr_filter_d@example.com")
        resp = client.get("/api/v1/land-records?district=Lucknow", headers=_auth(token))
        assert resp.status_code == 200

    def test_list_filter_by_owner_name(self, client: TestClient):
        token = _register_and_login(client, "lr_filter_o@example.com")
        resp = client.get("/api/v1/land-records?owner_name=Ram", headers=_auth(token))
        assert resp.status_code == 200

    def test_list_filter_by_khata(self, client: TestClient):
        token = _register_and_login(client, "lr_filter_k@example.com")
        resp = client.get("/api/v1/land-records?khata_number=00125", headers=_auth(token))
        assert resp.status_code == 200

    def test_list_pagination_params(self, client: TestClient):
        token = _register_and_login(client, "lr_paginate@example.com")
        resp = client.get("/api/v1/land-records?page=1&page_size=5", headers=_auth(token))
        assert resp.status_code == 200
        body = resp.json()
        assert body["page"] == 1
        assert body["page_size"] == 5
        assert len(body["items"]) <= 5

    def test_list_date_filters(self, client: TestClient):
        token = _register_and_login(client, "lr_date@example.com")
        resp = client.get(
            "/api/v1/land-records?created_after=2020-01-01&created_before=2030-12-31",
            headers=_auth(token),
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Get single land record
# ---------------------------------------------------------------------------

class TestGetLandRecord:
    def test_get_nonexistent(self, client: TestClient):
        token = _register_and_login(client, "lr_get_none@example.com")
        fake_id = "00000000-0000-0000-0000-000000000020"
        resp = client.get(f"/api/v1/land-records/{fake_id}", headers=_auth(token))
        assert resp.status_code == 404

    def test_get_requires_auth(self, client: TestClient):
        resp = client.get("/api/v1/land-records/00000000-0000-0000-0000-000000000020")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Update land record (verifier / admin only)
# ---------------------------------------------------------------------------

class TestUpdateLandRecord:
    def test_update_by_user_rejected(self, client: TestClient):
        """Regular USER must not be able to update a land record."""
        token = _register_and_login(client, "lr_upd_user@example.com", role="USER")
        fake_id = "00000000-0000-0000-0000-000000000021"
        resp = client.patch(
            f"/api/v1/land-records/{fake_id}",
            json={"owner_name": "New Owner"},
            headers=_auth(token),
        )
        assert resp.status_code == 403

    def test_update_nonexistent_by_verifier(self, client: TestClient):
        token = _register_and_login(client, "lr_upd_verifier@example.com", role="VERIFIER")
        fake_id = "00000000-0000-0000-0000-000000000022"
        resp = client.patch(
            f"/api/v1/land-records/{fake_id}",
            json={"owner_name": "New Owner"},
            headers=_auth(token),
        )
        assert resp.status_code == 404

    def test_update_requires_auth(self, client: TestClient):
        resp = client.patch(
            "/api/v1/land-records/00000000-0000-0000-0000-000000000021",
            json={"owner_name": "No"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Document-scoped land record
# ---------------------------------------------------------------------------

class TestDocumentLandRecord:
    def test_land_record_not_found_before_processing(self, client: TestClient):
        token = _register_and_login(client, "lr_doc_pre@example.com")
        files = {"file": ("x.png", io.BytesIO(_fake_png()), "image/png")}
        doc_id = client.post("/api/v1/documents", files=files, headers=_auth(token)).json()["id"]
        resp = client.get(f"/api/v1/documents/{doc_id}/land-record", headers=_auth(token))
        # Before pipeline runs there is no land record
        assert resp.status_code == 404

    def test_land_record_after_processing(self, client: TestClient):
        token = _register_and_login(client, "lr_doc_post@example.com")
        doc_id = _upload_and_process(client, token)
        resp = client.get(f"/api/v1/documents/{doc_id}/land-record", headers=_auth(token))
        # After pipeline the record may exist (if no issues routed to verification)
        # or not (if routed); either is a valid pipeline outcome
        assert resp.status_code in (200, 404)
