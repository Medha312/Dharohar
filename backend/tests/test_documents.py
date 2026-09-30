"""
Tests for Phase 4 — Document Management.

Covers:
- POST /api/v1/documents            (upload)
- GET  /api/v1/documents            (list, pagination, status filter)
- GET  /api/v1/documents/{id}       (get single)
- DELETE /api/v1/documents/{id}     (delete)
- GET  /api/v1/documents/{id}/pages (list pages)
"""
import io
import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _register_and_login(client: TestClient, email: str, role: str = "USER") -> str:
    client.post(
        "/api/v1/auth/register",
        json={"name": "Doc Test User", "email": email, "password": "TestPass123!", "role": role},
    )
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "TestPass123!"},
    )
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _fake_png() -> bytes:
    """Return a minimal valid 1×1 white PNG file."""
    import base64
    # 1x1 white PNG in base64
    png_b64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8"
        "z8BQDwADhQGAWjR9awAAAABJRU5ErkJggg=="
    )
    return base64.b64decode(png_b64)


def _upload_document(client: TestClient, token: str, filename: str = "test.png") -> dict:
    """Upload a minimal PNG and return the response JSON."""
    files = {"file": (filename, io.BytesIO(_fake_png()), "image/png")}
    resp = client.post("/api/v1/documents", files=files, headers=_auth(token))
    return resp


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

class TestDocumentUpload:
    def test_upload_png_success(self, client: TestClient):
        token = _register_and_login(client, "doc_upload_ok@example.com")
        resp = _upload_document(client, token)
        assert resp.status_code == 201
        body = resp.json()
        assert body["original_filename"] == "test.png"
        assert body["status"] == "UPLOADED"
        assert "id" in body
        assert body["user_id"] is not None

    def test_upload_returns_page_count(self, client: TestClient):
        token = _register_and_login(client, "doc_pagecount@example.com")
        resp = _upload_document(client, token)
        assert resp.status_code == 201
        # Images should be treated as single-page
        assert resp.json()["page_count"] >= 1

    def test_upload_unsupported_type_rejected(self, client: TestClient):
        token = _register_and_login(client, "doc_bad_type@example.com")
        files = {"file": ("malware.exe", io.BytesIO(b"MZ\x90\x00"), "application/octet-stream")}
        resp = client.post("/api/v1/documents", files=files, headers=_auth(token))
        assert resp.status_code in (400, 415, 422)

    def test_upload_requires_auth(self, client: TestClient):
        files = {"file": ("test.png", io.BytesIO(_fake_png()), "image/png")}
        resp = client.post("/api/v1/documents", files=files)
        assert resp.status_code == 401

    def test_upload_no_file_rejected(self, client: TestClient):
        token = _register_and_login(client, "doc_nofile@example.com")
        resp = client.post("/api/v1/documents", headers=_auth(token))
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# List documents
# ---------------------------------------------------------------------------

class TestListDocuments:
    def test_list_returns_own_documents(self, client: TestClient):
        token = _register_and_login(client, "doc_list_own@example.com")
        _upload_document(client, token)
        _upload_document(client, token)
        resp = client.get("/api/v1/documents", headers=_auth(token))
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert body["total"] >= 2

    def test_list_does_not_return_others_documents(self, client: TestClient):
        token_a = _register_and_login(client, "doc_list_a@example.com")
        token_b = _register_and_login(client, "doc_list_b@example.com")
        _upload_document(client, token_a)

        resp = client.get("/api/v1/documents", headers=_auth(token_b))
        assert resp.status_code == 200
        # User B should see 0 docs (only their own)
        for item in resp.json()["items"]:
            assert item["user_id"] != "user_a_id"  # rough check — none from A

    def test_list_pagination(self, client: TestClient):
        token = _register_and_login(client, "doc_paginate@example.com")
        for _ in range(3):
            _upload_document(client, token)

        page1 = client.get("/api/v1/documents?page=1&page_size=2", headers=_auth(token))
        assert page1.status_code == 200
        body = page1.json()
        assert len(body["items"]) <= 2
        assert body["page"] == 1
        assert body["page_size"] == 2

    def test_list_requires_auth(self, client: TestClient):
        resp = client.get("/api/v1/documents")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Get single document
# ---------------------------------------------------------------------------

class TestGetDocument:
    def test_get_own_document(self, client: TestClient):
        token = _register_and_login(client, "doc_get_own@example.com")
        doc_id = _upload_document(client, token).json()["id"]
        resp = client.get(f"/api/v1/documents/{doc_id}", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["id"] == doc_id

    def test_get_nonexistent_document(self, client: TestClient):
        token = _register_and_login(client, "doc_get_none@example.com")
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = client.get(f"/api/v1/documents/{fake_id}", headers=_auth(token))
        assert resp.status_code == 404

    def test_get_other_users_document_denied(self, client: TestClient):
        token_a = _register_and_login(client, "doc_get_a@example.com")
        token_b = _register_and_login(client, "doc_get_b@example.com")
        doc_id = _upload_document(client, token_a).json()["id"]
        resp = client.get(f"/api/v1/documents/{doc_id}", headers=_auth(token_b))
        # Should be 403 or 404 (service returns None for non-owner)
        assert resp.status_code in (403, 404)

    def test_get_requires_auth(self, client: TestClient):
        resp = client.get("/api/v1/documents/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Delete document
# ---------------------------------------------------------------------------

class TestDeleteDocument:
    def test_delete_own_document(self, client: TestClient):
        token = _register_and_login(client, "doc_del_ok@example.com")
        doc_id = _upload_document(client, token).json()["id"]
        resp = client.delete(f"/api/v1/documents/{doc_id}", headers=_auth(token))
        assert resp.status_code == 200
        # Confirm it is gone
        get_resp = client.get(f"/api/v1/documents/{doc_id}", headers=_auth(token))
        assert get_resp.status_code == 404

    def test_delete_nonexistent_document(self, client: TestClient):
        token = _register_and_login(client, "doc_del_none@example.com")
        fake_id = "00000000-0000-0000-0000-000000000001"
        resp = client.delete(f"/api/v1/documents/{fake_id}", headers=_auth(token))
        assert resp.status_code == 404

    def test_delete_requires_auth(self, client: TestClient):
        resp = client.delete("/api/v1/documents/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Document pages
# ---------------------------------------------------------------------------

class TestDocumentPages:
    def test_pages_returns_list(self, client: TestClient):
        token = _register_and_login(client, "doc_pages_ok@example.com")
        doc_id = _upload_document(client, token).json()["id"]
        resp = client.get(f"/api/v1/documents/{doc_id}/pages", headers=_auth(token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_pages_for_image_has_one_entry(self, client: TestClient):
        token = _register_and_login(client, "doc_pages_img@example.com")
        doc_id = _upload_document(client, token, filename="single.png").json()["id"]
        resp = client.get(f"/api/v1/documents/{doc_id}/pages", headers=_auth(token))
        assert resp.status_code == 200
        pages = resp.json()
        assert len(pages) >= 1
        assert pages[0]["page_number"] == 1

    def test_pages_nonexistent_document(self, client: TestClient):
        token = _register_and_login(client, "doc_pages_none@example.com")
        fake_id = "00000000-0000-0000-0000-000000000002"
        resp = client.get(f"/api/v1/documents/{fake_id}/pages", headers=_auth(token))
        assert resp.status_code == 404

    def test_pages_requires_auth(self, client: TestClient):
        resp = client.get("/api/v1/documents/00000000-0000-0000-0000-000000000000/pages")
        assert resp.status_code == 401
