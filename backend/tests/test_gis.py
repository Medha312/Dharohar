"""
Tests for Phase 13 — GIS.

Covers:
- GET   /api/v1/land-records/{id}/gis        (get GIS for record)
- POST  /api/v1/land-records/{id}/gis        (create GIS, verifier/admin only)
- PATCH /api/v1/land-records/{id}/gis        (update GIS, verifier/admin only)
- GET   /api/v1/gis/parcels                  (GeoJSON feature collection)

GIS is optional — tests that don't have an actual land record use fake UUIDs and
assert 404.  Tests that need a real record create one via the processing pipeline.
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
        json={"name": "GIS User", "email": email, "password": "TestPass123!", "role": role},
    )
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "TestPass123!"},
    )
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _upload_and_process(client: TestClient, token: str) -> str:
    """Upload a document and run the pipeline synchronously (Celery mocked). Returns doc_id."""
    files = {"file": ("gis_doc.png", io.BytesIO(_fake_png()), "image/png")}
    doc_id = client.post("/api/v1/documents", files=files, headers=_auth(token)).json()["id"]
    with patch("app.workers.processing_worker.process_document_task.delay") as m:
        m.side_effect = Exception("no broker")
        client.post(f"/api/v1/documents/{doc_id}/process", headers=_auth(token))
    return doc_id


def _get_land_record_id(client: TestClient, token: str, doc_id: str) -> str | None:
    """Return the land record id for a processed document, or None if not yet created."""
    resp = client.get(f"/api/v1/documents/{doc_id}/land-record", headers=_auth(token))
    if resp.status_code == 200:
        return resp.json()["id"]
    return None


# ---------------------------------------------------------------------------
# GET /land-records/{id}/gis
# ---------------------------------------------------------------------------

class TestGetGIS:
    def test_get_gis_nonexistent_land_record(self, client: TestClient):
        token = _register_and_login(client, "gis_get_nolr@example.com")
        fake_id = "00000000-0000-0000-0000-000000000040"
        resp = client.get(f"/api/v1/land-records/{fake_id}/gis", headers=_auth(token))
        assert resp.status_code == 404

    def test_get_gis_no_gis_attached(self, client: TestClient):
        """Land record exists but no GIS reference has been created yet."""
        user_token = _register_and_login(client, "gis_get_nogis_u@example.com", role="USER")
        verifier_token = _register_and_login(client, "gis_get_nogis_v@example.com", role="VERIFIER")

        doc_id = _upload_and_process(client, user_token)
        lr_id = _get_land_record_id(client, user_token, doc_id)
        if lr_id is None:
            pytest.skip("Pipeline did not produce a LandRecord (routed to verification)")

        resp = client.get(f"/api/v1/land-records/{lr_id}/gis", headers=_auth(user_token))
        # No GIS attached yet → 404
        assert resp.status_code == 404

    def test_get_gis_requires_auth(self, client: TestClient):
        fake_id = "00000000-0000-0000-0000-000000000040"
        resp = client.get(f"/api/v1/land-records/{fake_id}/gis")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /land-records/{id}/gis  (verifier / admin only)
# ---------------------------------------------------------------------------

class TestCreateGIS:
    _GIS_PAYLOAD = {
        "latitude": 26.8467,
        "longitude": 80.9462,
        "cadastral_id": "CADASTRAL-001",
        "source": "MANUAL",
        "confidence": 0.95,
    }

    def test_create_gis_by_user_rejected(self, client: TestClient):
        token = _register_and_login(client, "gis_create_user@example.com", role="USER")
        fake_id = "00000000-0000-0000-0000-000000000041"
        resp = client.post(
            f"/api/v1/land-records/{fake_id}/gis",
            json=self._GIS_PAYLOAD,
            headers=_auth(token),
        )
        assert resp.status_code == 403

    def test_create_gis_nonexistent_land_record(self, client: TestClient):
        token = _register_and_login(client, "gis_create_nolr@example.com", role="VERIFIER")
        fake_id = "00000000-0000-0000-0000-000000000042"
        resp = client.post(
            f"/api/v1/land-records/{fake_id}/gis",
            json=self._GIS_PAYLOAD,
            headers=_auth(token),
        )
        assert resp.status_code == 404

    def test_create_gis_success(self, client: TestClient):
        user_token = _register_and_login(client, "gis_create_u@example.com", role="USER")
        verifier_token = _register_and_login(client, "gis_create_v@example.com", role="VERIFIER")

        doc_id = _upload_and_process(client, user_token)
        lr_id = _get_land_record_id(client, user_token, doc_id)
        if lr_id is None:
            pytest.skip("Pipeline did not produce a LandRecord")

        resp = client.post(
            f"/api/v1/land-records/{lr_id}/gis",
            json=self._GIS_PAYLOAD,
            headers=_auth(verifier_token),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["land_record_id"] == lr_id
        assert body["latitude"] == pytest.approx(26.8467, rel=1e-4)
        assert body["longitude"] == pytest.approx(80.9462, rel=1e-4)
        assert body["source"] == "MANUAL"

    def test_create_gis_requires_auth(self, client: TestClient):
        fake_id = "00000000-0000-0000-0000-000000000041"
        resp = client.post(f"/api/v1/land-records/{fake_id}/gis", json=self._GIS_PAYLOAD)
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# PATCH /land-records/{id}/gis
# ---------------------------------------------------------------------------

class TestUpdateGIS:
    def test_update_gis_nonexistent(self, client: TestClient):
        token = _register_and_login(client, "gis_upd_none@example.com", role="VERIFIER")
        fake_id = "00000000-0000-0000-0000-000000000043"
        resp = client.patch(
            f"/api/v1/land-records/{fake_id}/gis",
            json={"confidence": 0.50},
            headers=_auth(token),
        )
        assert resp.status_code == 404

    def test_update_gis_by_user_rejected(self, client: TestClient):
        token = _register_and_login(client, "gis_upd_user@example.com", role="USER")
        fake_id = "00000000-0000-0000-0000-000000000043"
        resp = client.patch(
            f"/api/v1/land-records/{fake_id}/gis",
            json={"confidence": 0.50},
            headers=_auth(token),
        )
        assert resp.status_code == 403

    def test_update_gis_success(self, client: TestClient):
        user_token = _register_and_login(client, "gis_upd_u@example.com", role="USER")
        verifier_token = _register_and_login(client, "gis_upd_v@example.com", role="VERIFIER")

        doc_id = _upload_and_process(client, user_token)
        lr_id = _get_land_record_id(client, user_token, doc_id)
        if lr_id is None:
            pytest.skip("Pipeline did not produce a LandRecord")

        # First create GIS
        client.post(
            f"/api/v1/land-records/{lr_id}/gis",
            json={"latitude": 26.8, "longitude": 80.9, "source": "MANUAL"},
            headers=_auth(verifier_token),
        )

        # Then update confidence
        resp = client.patch(
            f"/api/v1/land-records/{lr_id}/gis",
            json={"confidence": 0.75},
            headers=_auth(verifier_token),
        )
        assert resp.status_code == 200
        assert resp.json()["confidence"] == pytest.approx(0.75, rel=1e-4)

    def test_update_gis_requires_auth(self, client: TestClient):
        fake_id = "00000000-0000-0000-0000-000000000043"
        resp = client.patch(f"/api/v1/land-records/{fake_id}/gis", json={"confidence": 0.5})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /gis/parcels  (GeoJSON feature collection)
# ---------------------------------------------------------------------------

class TestGetParcels:
    def test_parcels_requires_auth(self, client: TestClient):
        resp = client.get("/api/v1/gis/parcels")
        assert resp.status_code == 401

    def test_parcels_returns_geojson(self, client: TestClient):
        token = _register_and_login(client, "gis_parcels@example.com")
        resp = client.get("/api/v1/gis/parcels", headers=_auth(token))
        assert resp.status_code == 200
        body = resp.json()
        assert body["type"] == "FeatureCollection"
        assert "features" in body
        assert isinstance(body["features"], list)

    def test_parcels_pagination(self, client: TestClient):
        token = _register_and_login(client, "gis_parcels_pag@example.com")
        resp = client.get("/api/v1/gis/parcels?limit=5&offset=0", headers=_auth(token))
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["features"]) <= 5

    def test_parcels_invalid_limit_rejected(self, client: TestClient):
        token = _register_and_login(client, "gis_parcels_inv@example.com")
        resp = client.get("/api/v1/gis/parcels?limit=9999", headers=_auth(token))
        # limit is capped at 500 per the route definition; anything above is 422
        assert resp.status_code == 422

    def test_parcels_features_have_geometry(self, client: TestClient):
        """Any returned feature must conform to GeoJSON structure."""
        user_token = _register_and_login(client, "gis_parcels_feat_u@example.com", role="USER")
        verifier_token = _register_and_login(client, "gis_parcels_feat_v@example.com", role="VERIFIER")

        doc_id = _upload_and_process(client, user_token)
        lr_id = _get_land_record_id(client, user_token, doc_id)
        if lr_id is None:
            pytest.skip("No LandRecord available to attach GIS to")

        client.post(
            f"/api/v1/land-records/{lr_id}/gis",
            json={"latitude": 26.85, "longitude": 80.95, "source": "MANUAL"},
            headers=_auth(verifier_token),
        )

        resp = client.get("/api/v1/gis/parcels", headers=_auth(user_token))
        assert resp.status_code == 200
        features = resp.json()["features"]
        for feature in features:
            assert feature["type"] == "Feature"
            assert "geometry" in feature
            assert "properties" in feature
