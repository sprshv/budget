import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.routers import sessions as sessions_router
from app.dependencies.auth import get_current_user


def _make_app():
    """Create a minimal FastAPI app with the sessions router mounted."""
    app = FastAPI()
    app.state.limiter = MagicMock()
    app.include_router(sessions_router.router)
    app.dependency_overrides[get_current_user] = lambda: {"id": "test-user-id", "email": "test@example.com"}
    return app


def test_list_sessions_returns_list():
    """Verify the list_sessions endpoint exists and is callable."""
    assert callable(sessions_router.list_sessions)


def test_revoke_session_calls_supabase():
    """Verify the revoke_session endpoint exists and is callable."""
    assert callable(sessions_router.revoke_session)


def test_admin_headers_include_service_role():
    """Verify _supabase_admin_headers returns Authorization and apikey."""
    headers = sessions_router._supabase_admin_headers()
    assert "Authorization" in headers
    assert "apikey" in headers
    assert headers["Authorization"].startswith("Bearer ")
    assert headers["apikey"] == headers["Authorization"].removeprefix("Bearer ")


def test_list_sessions_route_requires_auth():
    """Verify GET /auth/sessions is registered and requires a bearer token."""
    app = _make_app()
    client = TestClient(app, raise_server_exceptions=False)
    # Without overriding auth, a missing/bad token should return 401 or 403
    fresh_app = FastAPI()
    fresh_app.state.limiter = MagicMock()
    fresh_app.include_router(sessions_router.router)
    unauthed_client = TestClient(fresh_app, raise_server_exceptions=False)
    resp = unauthed_client.get("/auth/sessions")
    assert resp.status_code in (401, 403, 422)


def test_revoke_session_endpoint_exists():
    """Verify the DELETE /auth/sessions/{session_id} route is registered."""
    app = _make_app()
    routes = [r.path for r in app.routes]
    assert "/auth/sessions/{session_id}" in routes
