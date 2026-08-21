from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.dependencies.auth import get_current_user
from app.database import get_db
from app.services.auth_service import get_or_create_user
from app.schemas.auth import LogoutResponse
from app.schemas.user import UserResponse

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/logout", response_model=LogoutResponse)
@limiter.limit("20/minute")
async def logout(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await get_or_create_user(
        user_id=current_user["id"],
        email=current_user["email"],
        db=db,
    )
    return user
