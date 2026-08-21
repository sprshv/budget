import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.country_code import CountryCode
from plaid.model.products import Products
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from typing import Optional
from app.config import settings


def get_plaid_client() -> plaid_api.PlaidApi:
    env_map = {
        "sandbox": plaid.Environment.Sandbox,
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
    return plaid_api.PlaidApi(api_client)


async def create_link_token(user_id: str) -> str:
    """Create a Plaid Link token for the given user."""
    client = get_plaid_client()

    request = LinkTokenCreateRequest(
        user=LinkTokenCreateRequestUser(client_user_id=user_id),
        client_name="Budgeting App",
        products=[Products("transactions")],
        country_codes=[CountryCode("US")],
        language="en",
    )

    response = client.link_token_create(request)
    return response["link_token"]


async def exchange_public_token(public_token: str) -> dict:
    """Exchange public token for access token and item_id."""
    client = get_plaid_client()
    request = ItemPublicTokenExchangeRequest(public_token=public_token)
    response = client.item_public_token_exchange(request)
    return {
        "access_token": response["access_token"],
        "item_id": response["item_id"],
    }


async def fetch_accounts(access_token: str) -> list:
    """Fetch accounts for an access token."""
    client = get_plaid_client()
    request = AccountsGetRequest(access_token=access_token)
    response = client.accounts_get(request)

    def _val(v, default=""):
        """Extract plain string from a Plaid SDK enum or return as-is."""
        if v is None:
            return None
        return v.value if hasattr(v, "value") else str(v)

    accounts = []
    for acct in response["accounts"]:
        balances = acct.get("balances", {}) or {}
        accounts.append({
            "account_id": acct.get("account_id"),
            "name": acct.get("name"),
            "official_name": acct.get("official_name"),
            "type": _val(acct.get("type")) or "depository",
            "subtype": _val(acct.get("subtype")),
            "balances": {
                "current": balances.get("current"),
                "available": balances.get("available"),
                "limit": balances.get("limit"),
            },
        })
    return accounts


async def fetch_institution(institution_id: str) -> dict:
    """Fetch institution details by ID."""
    client = get_plaid_client()
    request = InstitutionsGetByIdRequest(
        institution_id=institution_id,
        country_codes=[CountryCode("US")],
    )
    response = client.institutions_get_by_id(request)
    institution = response["institution"]
    return {
        "name": institution.get("name", ""),
        "logo": institution.get("logo"),
    }


async def sync_transactions(access_token: str, cursor: Optional[str] = None) -> dict:
    """
    Fetch new/modified/removed transactions using Plaid's sync endpoint.
    Returns: {added: [...], modified: [...], removed: [...], next_cursor: str, has_more: bool}
    """
    client = get_plaid_client()

    all_added = []
    all_modified = []
    all_removed = []

    while True:
        kwargs = {"access_token": access_token}
        if cursor:
            kwargs["cursor"] = cursor

        request = TransactionsSyncRequest(**kwargs)
        response = client.transactions_sync(request)

        all_added.extend(response.get("added", []))
        all_modified.extend(response.get("modified", []))
        all_removed.extend(response.get("removed", []))

        cursor = response.get("next_cursor", "")
        has_more = response.get("has_more", False)

        if not has_more:
            break

    return {
        "added": all_added,
        "modified": all_modified,
        "removed": all_removed,
        "next_cursor": cursor,
    }
