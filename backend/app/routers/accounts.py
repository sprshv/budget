from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.auth import get_current_user
from app.database import get_db
from app.services.account_service import get_user_accounts, get_accounts_needing_reauth, delete_account
from app.schemas.account import AccountListResponse
import uuid

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=AccountListResponse)
async def list_accounts(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    accounts = await get_user_accounts(uuid.UUID(current_user["id"]), db)
    return {"accounts": accounts, "total": len(accounts)}


@router.get("/health", response_model=AccountListResponse)
async def get_accounts_health(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns accounts with sync_status = reauth_required."""
    accounts = await get_accounts_needing_reauth(uuid.UUID(current_user["id"]), db)
    return {"accounts": accounts, "total": len(accounts)}


@router.delete("/{account_id}", status_code=204)
async def remove_account(
    account_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an account and all associated transactions (CASCADE)."""
    deleted = await delete_account(account_id, uuid.UUID(current_user["id"]), db)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    return None
