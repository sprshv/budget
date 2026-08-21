import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.financial_account import FinancialAccount
from app.schemas.plaid import ExchangeTokenRequest, ExchangeTokenResponse, LinkTokenResponse
from app.services.encryption_service import encrypt
from app.services.plaid_service import (
    create_link_token,
    exchange_public_token,
    fetch_accounts,
    fetch_institution,
)
from app.services.transaction_sync_service import initial_sync

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/plaid", tags=["plaid"])


@router.post("/link-token", response_model=LinkTokenResponse)
@limiter.limit("20/minute")
async def get_link_token(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Create a Plaid Link token for the authenticated user."""
    try:
        link_token = await create_link_token(current_user["id"])
        return {"link_token": link_token}
    except Exception as e:
        import traceback, logging
        logging.error(f"Plaid link-token error: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not create link token: {e}",
            headers={},
        )


@router.post("/exchange-token", response_model=ExchangeTokenResponse)
@limiter.limit("10/minute")
async def exchange_token(
    request: Request,
    body: ExchangeTokenRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Exchange Plaid public token, store encrypted access token and accounts."""
    try:
        # Exchange public token for access token
        token_data = await exchange_public_token(body.public_token)
        access_token = token_data["access_token"]
        item_id = token_data["item_id"]

        # Fetch accounts from Plaid
        accounts = await fetch_accounts(access_token)

        # Fetch institution info if ID provided
        institution_info = {"name": body.institution_name or "", "logo": None}
        if body.institution_id:
            try:
                institution_info = await fetch_institution(body.institution_id)
            except Exception:
                pass

        # Encrypt the access token before storing
        encrypted_token = encrypt(access_token)

        linked_count = 0
        new_account_ids: list[uuid.UUID] = []
        user_uuid = uuid.UUID(current_user["id"])

        for account in accounts:
            plaid_account_id = account["account_id"]

            # Idempotency check — skip if already linked
            existing = await db.execute(
                select(FinancialAccount).where(
                    FinancialAccount.plaid_account_id == plaid_account_id
                )
            )
            if existing.scalar_one_or_none():
                continue

            balances = account.get("balances", {})
            new_account = FinancialAccount(
                user_id=user_uuid,
                plaid_item_id=item_id,
                plaid_account_id=plaid_account_id,
                plaid_access_token=encrypted_token,
                name=account.get("name", "Account"),
                official_name=account.get("official_name"),
                institution_name=institution_info["name"],
                institution_logo=institution_info["logo"],
                account_type=account.get("type", "depository"),
                account_subtype=account.get("subtype"),
                balance_current=balances.get("current"),
                balance_available=balances.get("available"),
                balance_limit=balances.get("limit"),
                sync_status="ok",
            )
            db.add(new_account)
            new_account_ids.append(new_account.id)
            linked_count += 1

        await db.commit()

        # Kick off initial transaction sync in background
        if new_account_ids:
            background_tasks.add_task(
                initial_sync,
                account_ids=new_account_ids,
                user_id=user_uuid,
            )

        return {
            "accounts_linked": linked_count,
            "message": f"Successfully linked {linked_count} account(s)",
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback, logging
        logging.error(f"exchange-token error: {e}\n{traceback.format_exc()}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not link bank account: {e}",
            headers={},
        )
