from fastapi import APIRouter, Query
from fastapi.responses import RedirectResponse
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth-callbacks"])


@router.get("/callback")
async def auth_callback(
    type: str = Query(...),
    access_token: str = Query(None),
    refresh_token: str = Query(None),
    error: str = Query(None),
    error_description: str = Query(None),
):
    frontend = settings.FRONTEND_URL

    if error:
        return RedirectResponse(url=f"{frontend}/login?error={error}")

    if type == "recovery":
        return RedirectResponse(
            url=f"{frontend}/reset-password#access_token={access_token}&refresh_token={refresh_token}&type=recovery"
        )

    if type == "signup":
        return RedirectResponse(url=f"{frontend}/verify-email?verified=true")

    return RedirectResponse(url=f"{frontend}/login")
