import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.dependencies.auth import get_current_user

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/auth/2fa", tags=["2fa"])

# --- Supabase admin headers (service-role key) ---
def _admin_headers() -> dict:
    return {
        "apikey": settings.SUPABASE_SECRET_KEY,
        "Content-Type": "application/json",
    }

# --- Supabase user-scoped headers (user's own JWT) ---
def _user_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "apikey": settings.SUPABASE_SECRET_KEY,
        "Content-Type": "application/json",
    }


# ── Schemas ────────────────────────────────────────────────────────────────────

class VerifyTotpRequest(BaseModel):
    factor_id: str
    code: str


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/setup", status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def setup_2fa(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Enroll a new TOTP factor for the authenticated user.
    Returns the QR code SVG, TOTP URI, and factor_id needed to complete setup.
    Uses the Supabase Admin REST API so the service-role key stays server-side.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.SUPABASE_URL}/auth/v1/admin/users/{current_user['id']}/factors",
            headers=_admin_headers(),
            json={
                "factor_type": "totp",
                "issuer": "BudgetingApp",
                "friendly_name": current_user["email"],
            },
        )

    if resp.status_code not in (200, 201):
        error_msg = "Failed to start 2FA setup."
        try:
            error_msg = resp.json().get("message", error_msg)
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )

    data = resp.json()
    totp = data.get("totp", {})
    return {
        "factor_id": data.get("id"),
        "totp_uri": totp.get("uri"),
        "qr_code": totp.get("qr_code"),
        "secret": totp.get("secret"),
    }


@router.post("/verify", status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def verify_2fa(
    request: Request,
    body: VerifyTotpRequest,
    current_user: dict = Depends(get_current_user),  # noqa: ARG001
):
    """
    Verify a TOTP code for the given factor.
    Internally creates a challenge then verifies it — the client only needs to
    supply factor_id and the 6-digit code.
    Uses the user's own JWT so Supabase enforces ownership.
    """
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_headers = _user_headers(token)

    # Step 1: create a challenge
    async with httpx.AsyncClient() as client:
        challenge_resp = await client.post(
            f"{settings.SUPABASE_URL}/auth/v1/factors/{body.factor_id}/challenge",
            headers=user_headers,
            json={},
        )

    if challenge_resp.status_code not in (200, 201):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create MFA challenge. Please try again.",
        )

    challenge_id = challenge_resp.json().get("id")

    # Step 2: verify the code against the challenge
    async with httpx.AsyncClient() as client:
        verify_resp = await client.post(
            f"{settings.SUPABASE_URL}/auth/v1/factors/{body.factor_id}/verify",
            headers=user_headers,
            json={"challenge_id": challenge_id, "code": body.code},
        )

    if verify_resp.status_code not in (200, 201):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid code. Please try again.",
        )

    return {"verified": True, "access_level": "aal2"}


@router.delete("/unenroll/{factor_id}", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def unenroll_2fa(
    request: Request,
    factor_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Remove a TOTP factor from the authenticated user's account."""
    async with httpx.AsyncClient() as client:
        resp = await client.delete(
            f"{settings.SUPABASE_URL}/auth/v1/admin/users/{current_user['id']}/factors/{factor_id}",
            headers=_admin_headers(),
        )

    if resp.status_code not in (200, 204):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to remove 2FA factor.",
        )

    return {"message": "2FA removed"}
