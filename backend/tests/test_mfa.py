"""
Tests for the MFA router (backend/app/routers/mfa.py).

All Supabase HTTP calls are mocked via httpx so no real network traffic occurs.
The get_current_user dependency is overridden directly on the FastAPI app so
tests exercise the full request/response cycle without touching auth.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_app():
    """Create a fresh FastAPI app with the MFA router mounted, identical to
    the production wiring in main.py, but isolated for testing."""
    with (
        patch("sqlalchemy.ext.asyncio.create_async_engine", return_value=MagicMock()),
        patch("sqlalchemy.ext.asyncio.async_sessionmaker", return_value=MagicMock()),
    ):
        from fastapi import FastAPI
        from app.routers import mfa as mfa_router

        app = FastAPI()
        app.include_router(mfa_router.router, prefix="/api/v1")
        return app


FAKE_USER = {"id": "user-uuid-1234", "email": "test@example.com"}


# ---------------------------------------------------------------------------
# Test: /auth/2fa/setup
# ---------------------------------------------------------------------------

def test_setup_2fa_requires_auth():
    """Calling /setup without a Bearer token returns 403 (HTTPBearer rejects it)."""
    app = _make_app()
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post("/api/v1/auth/2fa/setup")
    assert resp.status_code in (401, 403)


def test_setup_2fa_returns_factor_data():
    """A valid JWT + successful Supabase response returns factor_id, totp_uri, qr_code."""
    app = _make_app()

    # Override auth dependency
    from app.dependencies.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER

    supabase_payload = {
        "id": "factor-abc",
        "totp": {
            "uri": "otpauth://totp/BudgetingApp:test@example.com?secret=ABC123",
            "qr_code": "<svg>...</svg>",
            "secret": "ABC123",
        },
    }

    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = supabase_payload

    with patch("httpx.AsyncClient") as MockClient:
        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/api/v1/auth/2fa/setup",
            headers={"Authorization": "Bearer fake-jwt"},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["factor_id"] == "factor-abc"
    assert "totp_uri" in body
    assert "qr_code" in body

    app.dependency_overrides.clear()


def test_setup_2fa_propagates_supabase_error():
    """A non-2xx response from Supabase returns 400 to the client."""
    app = _make_app()

    from app.dependencies.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER

    mock_response = MagicMock()
    mock_response.status_code = 422
    mock_response.json.return_value = {"message": "Factor already enrolled"}

    with patch("httpx.AsyncClient") as MockClient:
        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/api/v1/auth/2fa/setup",
            headers={"Authorization": "Bearer fake-jwt"},
        )

    assert resp.status_code == 400

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Test: /auth/2fa/verify
# ---------------------------------------------------------------------------

def test_verify_2fa_invalid_code_returns_400():
    """A bad TOTP code (Supabase 400) surfaces as 400 to the client."""
    app = _make_app()

    from app.dependencies.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER

    # Challenge succeeds, verify fails
    challenge_resp = MagicMock()
    challenge_resp.status_code = 200
    challenge_resp.json.return_value = {"id": "challenge-id-xyz"}

    verify_resp = MagicMock()
    verify_resp.status_code = 422
    verify_resp.json.return_value = {"message": "Invalid TOTP code"}

    call_count = {"n": 0}

    async def mock_post(*args, **kwargs):
        call_count["n"] += 1
        return challenge_resp if call_count["n"] == 1 else verify_resp

    with patch("httpx.AsyncClient") as MockClient:
        mock_client_instance = AsyncMock()
        mock_client_instance.post = mock_post
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/api/v1/auth/2fa/verify",
            json={"factor_id": "factor-abc", "code": "000000"},
            headers={"Authorization": "Bearer fake-jwt"},
        )

    assert resp.status_code == 400
    assert "Invalid code" in resp.json().get("detail", "")

    app.dependency_overrides.clear()


def test_verify_2fa_valid_code_returns_verified():
    """Correct TOTP code returns verified: True and access_level aal2."""
    app = _make_app()

    from app.dependencies.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER

    challenge_resp = MagicMock()
    challenge_resp.status_code = 200
    challenge_resp.json.return_value = {"id": "challenge-id-xyz"}

    verify_resp = MagicMock()
    verify_resp.status_code = 200
    verify_resp.json.return_value = {"access_token": "new-aal2-token"}

    call_count = {"n": 0}

    async def mock_post(*args, **kwargs):
        call_count["n"] += 1
        return challenge_resp if call_count["n"] == 1 else verify_resp

    with patch("httpx.AsyncClient") as MockClient:
        mock_client_instance = AsyncMock()
        mock_client_instance.post = mock_post
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/api/v1/auth/2fa/verify",
            json={"factor_id": "factor-abc", "code": "123456"},
            headers={"Authorization": "Bearer fake-jwt"},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["verified"] is True
    assert body["access_level"] == "aal2"

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Test: /auth/2fa/unenroll/{factor_id}
# ---------------------------------------------------------------------------

def test_unenroll_2fa_success():
    """A 204 from Supabase yields a 200 with message 'success'."""
    app = _make_app()

    from app.dependencies.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER

    mock_response = MagicMock()
    mock_response.status_code = 204

    with patch("httpx.AsyncClient") as MockClient:
        mock_client_instance = AsyncMock()
        mock_client_instance.delete = AsyncMock(return_value=mock_response)
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete(
            "/api/v1/auth/2fa/unenroll/factor-abc",
            headers={"Authorization": "Bearer fake-jwt"},
        )

    assert resp.status_code == 200
    assert resp.json()["message"] == "2FA removed"

    app.dependency_overrides.clear()


def test_unenroll_2fa_failure_returns_400():
    """A non-2xx from Supabase surfaces as 400."""
    app = _make_app()

    from app.dependencies.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER

    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.json.return_value = {"message": "Factor not found"}

    with patch("httpx.AsyncClient") as MockClient:
        mock_client_instance = AsyncMock()
        mock_client_instance.delete = AsyncMock(return_value=mock_response)
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete(
            "/api/v1/auth/2fa/unenroll/factor-abc",
            headers={"Authorization": "Bearer fake-jwt"},
        )

    assert resp.status_code == 400

    app.dependency_overrides.clear()
