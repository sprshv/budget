from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
import httpx
from app.dependencies.auth import get_current_user
from app.config import settings

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/auth", tags=["sessions"])


def _supabase_admin_headers() -> dict:
    return {
        "apikey": settings.SUPABASE_SECRET_KEY,
    }


@router.get("/sessions")
@limiter.limit("30/minute")
async def list_sessions(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """List all active sessions for the current user."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.SUPABASE_URL}/auth/v1/admin/users/{current_user['id']}/sessions",
                headers=_supabase_admin_headers(),
            )
            if resp.status_code == 404:
                return {"sessions": []}
            resp.raise_for_status()
            data = resp.json()
            sessions = data if isinstance(data, list) else data.get("sessions", [])
            return {"sessions": sessions}
    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not retrieve sessions",
        )


@router.delete("/sessions/{session_id}", status_code=204)
@limiter.limit("10/minute")
async def revoke_session(
    request: Request,
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Revoke a specific session."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{settings.SUPABASE_URL}/auth/v1/admin/users/{current_user['id']}/sessions/{session_id}",
                headers=_supabase_admin_headers(),
            )
            if resp.status_code in (404, 200, 204):
                return None
            resp.raise_for_status()
            return None
    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not revoke session",
        )
