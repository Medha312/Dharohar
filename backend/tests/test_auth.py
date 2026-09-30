"""
Tests for Phase 3 — Authentication & Authorization.

Covers:
- POST /api/v1/auth/register
- POST /api/v1/auth/login
- POST /api/v1/auth/refresh
- POST /api/v1/auth/logout
- POST /api/v1/auth/forgot-password
- GET  /api/v1/auth/me
- Role-based access (USER / VERIFIER / ADMIN)
"""
import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _register(client: TestClient, email: str, password: str = "TestPass123!", role: str = "USER") -> dict:
    resp = client.post(
        "/api/v1/auth/register",
        json={"name": "Test User", "email": email, "password": password, "role": role},
    )
    return resp


def _login(client: TestClient, email: str, password: str = "TestPass123!") -> dict:
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    return resp


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class TestRegister:
    def test_register_success(self, client: TestClient):
        resp = _register(client, "newuser_reg@example.com")
        assert resp.status_code == 201
        body = resp.json()
        assert body["email"] == "newuser_reg@example.com"
        assert body["role"] == "USER"
        assert "password_hash" not in body
        assert "id" in body

    def test_register_duplicate_email(self, client: TestClient):
        email = "dup_reg@example.com"
        _register(client, email)
        resp = _register(client, email)
        assert resp.status_code == 400
        assert "already exists" in resp.json()["detail"].lower()

    def test_register_invalid_email(self, client: TestClient):
        resp = client.post(
            "/api/v1/auth/register",
            json={"name": "Bad", "email": "not-an-email", "password": "pass123"},
        )
        assert resp.status_code == 422

    def test_register_missing_fields(self, client: TestClient):
        resp = client.post("/api/v1/auth/register", json={"email": "x@x.com"})
        assert resp.status_code == 422

    def test_register_verifier_role(self, client: TestClient):
        resp = _register(client, "verifier_reg@example.com", role="VERIFIER")
        assert resp.status_code == 201
        assert resp.json()["role"] == "VERIFIER"

    def test_register_admin_role(self, client: TestClient):
        resp = _register(client, "admin_reg@example.com", role="ADMIN")
        assert resp.status_code == 201
        assert resp.json()["role"] == "ADMIN"


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class TestLogin:
    def test_login_success(self, client: TestClient):
        email = "login_ok@example.com"
        _register(client, email)
        resp = _login(client, email)
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"
        assert body["email"] == email

    def test_login_wrong_password(self, client: TestClient):
        email = "login_wp@example.com"
        _register(client, email)
        resp = _login(client, email, password="WrongPass!")
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient):
        resp = _login(client, "ghost@example.com")
        assert resp.status_code == 401

    def test_login_missing_credentials(self, client: TestClient):
        resp = client.post("/api/v1/auth/login", data={})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Token refresh
# ---------------------------------------------------------------------------

class TestRefresh:
    def test_refresh_success(self, client: TestClient):
        email = "refresh_ok@example.com"
        _register(client, email)
        login_resp = _login(client, email)
        refresh_token = login_resp.json()["refresh_token"]

        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body

    def test_refresh_with_access_token_fails(self, client: TestClient):
        email = "refresh_bad@example.com"
        _register(client, email)
        login_resp = _login(client, email)
        # Pass access_token as refresh — should fail because type claim is "access"
        access_token = login_resp.json()["access_token"]

        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})
        assert resp.status_code == 401

    def test_refresh_invalid_token(self, client: TestClient):
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": "not.a.token"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

class TestLogout:
    def test_logout_authenticated(self, client: TestClient):
        email = "logout_ok@example.com"
        _register(client, email)
        token = _login(client, email).json()["access_token"]
        resp = client.post("/api/v1/auth/logout", headers=_auth_header(token))
        assert resp.status_code == 200
        assert "logged out" in resp.json()["message"].lower()

    def test_logout_unauthenticated(self, client: TestClient):
        resp = client.post("/api/v1/auth/logout")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Forgot password
# ---------------------------------------------------------------------------

class TestForgotPassword:
    def test_forgot_password_existing_email(self, client: TestClient):
        email = "forgot_existing@example.com"
        _register(client, email)
        resp = client.post("/api/v1/auth/forgot-password", json={"email": email})
        assert resp.status_code == 200
        # Should not reveal whether the email exists
        assert "sent" in resp.json()["message"].lower()

    def test_forgot_password_nonexistent_email(self, client: TestClient):
        # Must return 200 to prevent email enumeration
        resp = client.post("/api/v1/auth/forgot-password", json={"email": "ghost@example.com"})
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------

class TestAuthMe:
    def test_me_authenticated(self, client: TestClient):
        email = "me_ok@example.com"
        _register(client, email)
        token = _login(client, email).json()["access_token"]
        resp = client.get("/api/v1/auth/me", headers=_auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["email"] == email

    def test_me_unauthenticated(self, client: TestClient):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_me_invalid_token(self, client: TestClient):
        resp = client.get("/api/v1/auth/me", headers=_auth_header("invalid.token.here"))
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Role-based access control
# ---------------------------------------------------------------------------

class TestRoleAccess:
    def _get_token(self, client: TestClient, email: str, role: str = "USER") -> str:
        _register(client, email, role=role)
        return _login(client, email).json()["access_token"]

    def test_admin_endpoint_rejected_for_user(self, client: TestClient):
        token = self._get_token(client, "rbac_user@example.com", role="USER")
        resp = client.get("/api/v1/admin/users", headers=_auth_header(token))
        assert resp.status_code == 403

    def test_admin_endpoint_rejected_for_verifier(self, client: TestClient):
        token = self._get_token(client, "rbac_verifier@example.com", role="VERIFIER")
        resp = client.get("/api/v1/admin/users", headers=_auth_header(token))
        assert resp.status_code == 403

    def test_admin_endpoint_allowed_for_admin(self, client: TestClient):
        token = self._get_token(client, "rbac_admin@example.com", role="ADMIN")
        resp = client.get("/api/v1/admin/users", headers=_auth_header(token))
        # 200 or any non-403/401 is acceptable (DB may be empty)
        assert resp.status_code not in (401, 403)

    def test_verification_endpoint_rejected_for_user(self, client: TestClient):
        token = self._get_token(client, "rbac_user2@example.com", role="USER")
        resp = client.get("/api/v1/verification/tasks", headers=_auth_header(token))
        assert resp.status_code == 403

    def test_verification_endpoint_allowed_for_verifier(self, client: TestClient):
        token = self._get_token(client, "rbac_verifier2@example.com", role="VERIFIER")
        resp = client.get("/api/v1/verification/tasks", headers=_auth_header(token))
        assert resp.status_code not in (401, 403)
