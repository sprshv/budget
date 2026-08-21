import json
import logging
from fastapi import APIRouter, Request, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from fastapi import Depends
from app.models.financial_account import FinancialAccount
from app.services.transaction_sync_service import sync_account_transactions
from app.services.notification_service import create_notification
from app.config import settings
import uuid

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/plaid", tags=["webhook"])


async def _verify_plaid_webhook(request: Request, raw_body: bytes) -> bool:
    """
    Verify the Plaid webhook signature using the Plaid-Verification header.
    Uses Plaid's /webhook_verification_key/get to fetch the key and verify.
    Returns True if valid, False if not.
    """
    try:
        import plaid
        from plaid.api import plaid_api
        from plaid.model.webhook_verification_key_get_request import WebhookVerificationKeyGetRequest
        import jwt as pyjwt

        signed_jwt = request.headers.get("Plaid-Verification")
        if not signed_jwt:
            return False

        # Decode header to get key_id
        header = pyjwt.get_unverified_header(signed_jwt)
        key_id = header.get("kid")
        if not key_id:
            return False

        env_map = {
            "sandbox": plaid.Environment.Sandbox,
            "development": plaid.Environment.Development,
            "production": plaid.Environment.Production,
        }
        configuration = plaid.Configuration(
            host=env_map.get(settings.PLAID_ENV, plaid.Environment.Sandbox),
            api_key={
                "clientId": settings.PLAID_CLIENT_ID,
                "secret": settings.PLAID_SECRET,
            },
        )
        api_client = plaid.ApiClient(configuration)
        client = plaid_api.PlaidApi(api_client)

        key_response = client.webhook_verification_key_get(
            WebhookVerificationKeyGetRequest(key_id=key_id)
        )
        key = key_response.key

        # Build JWK dict from Plaid key attributes
        public_key = pyjwt.algorithms.ECAlgorithm.from_jwk(json.dumps({
            "kty": key.kty,
            "crv": key.crv,
            "x": key.x,
            "y": key.y,
        }))

        decoded = pyjwt.decode(
            signed_jwt,
            public_key,
            algorithms=["ES256"],
            options={"verify_exp": True},
        )

        # Verify the body hash matches
        import hashlib
        body_hash = hashlib.sha256(raw_body).hexdigest()
        return decoded.get("request_body_sha256") == body_hash

    except Exception as e:
        logger.warning(f"Webhook verification failed: {e}")
        return False


async def _handle_transactions_sync(payload: dict, db: AsyncSession):
    """Handle TRANSACTIONS webhook — sync using cursor."""
    item_id = payload.get("item_id")
    if not item_id:
        return

    result = await db.execute(
        select(FinancialAccount).where(
            FinancialAccount.plaid_item_id == item_id,
            FinancialAccount.is_active == True,
        )
    )
    accounts = result.scalars().all()

    for account in accounts:
        await sync_account_transactions(account, db, account.user_id)


async def _handle_item_error(payload: dict, db: AsyncSession):
    """Handle ITEM ERROR — mark account as needing reauth and notify user."""
    item_id = payload.get("item_id")
    error = payload.get("error", {})

    if not item_id:
        return

    result = await db.execute(
        select(FinancialAccount).where(
            FinancialAccount.plaid_item_id == item_id,
        )
    )
    accounts = result.scalars().all()

    for account in accounts:
        account.sync_status = "reauth_required"
        await db.flush()

        await create_notification(
            user_id=account.user_id,
            notif_type="reauth_required",
            title="Bank connection needs attention",
            body=f"Your {account.institution_name or account.name} connection needs to be re-linked.",
            db=db,
            metadata={"account_id": str(account.id), "error_code": error.get("error_code")},
        )


@router.post("/webhook", status_code=200)
async def plaid_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    raw_body = await request.body()

    # Verify signature before processing anything
    is_valid = await _verify_plaid_webhook(request, raw_body)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature",
        )

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON")

    webhook_type = payload.get("webhook_type", "")
    webhook_code = payload.get("webhook_code", "")

    logger.info(f"Plaid webhook: {webhook_type}/{webhook_code}")

    if webhook_type == "TRANSACTIONS":
        background_tasks.add_task(_handle_transactions_sync, payload, db)
    elif webhook_type == "ITEM" and webhook_code == "ERROR":
        background_tasks.add_task(_handle_item_error, payload, db)

    return {"status": "received"}
