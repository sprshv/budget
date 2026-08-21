# Phase 2 — Bank Linking
Goal: user can connect a real bank account and see their accounts.

Subagent types: Backend for 2.1-2.4, Full-stack for 2.5-2.6.

---

Task 2.1 — Plaid link token (Backend)
- POST /api/v1/plaid/link-token — authenticated, creates Plaid link token for current user
- Frontend: PlaidLink component using react-plaid-link, triggers on "Connect account" button

Task 2.2 — Public token exchange + account storage (Backend)
- POST /api/v1/plaid/exchange-token — exchange public token, encrypt access token with Fernet, store in financial_accounts
- Fetch account details from Plaid, populate financial_accounts rows with institution name, type, balances

Task 2.3 — Initial transaction sync (Backend)
- Service: pull up to 24 months of historical transactions from Plaid for newly linked account
- Normalize merchant names, run auto-categorization, store in transactions table
- Deduplication check before every insert using plaid_transaction_id

Task 2.4 — Plaid webhook handler (Backend)
- POST /api/v1/plaid/webhook — verify Plaid-Verification-Token signature before processing
- Handle TRANSACTIONS_SYNC: incremental pull using stored plaid_cursor
- Handle ITEM_ERROR: set account sync_status to reauth_required, create notification

Task 2.5 — Connection health + relink flow (Full-stack)
- Backend: GET /api/v1/accounts/health — accounts with sync_status = reauth_required
- Frontend: banner when account needs relinking, triggers Plaid Link in update mode

Task 2.6 — Account management UI (Full-stack)
- Frontend: /accounts page — all linked accounts with balance, institution logo, last synced, account type badge, remove button
- Backend: DELETE /api/v1/accounts/:id — removes account and all associated transactions

---

After all tasks:
1. Run standard Security subagent from security-checklist.md
2. Run Phase 2 Plaid-specific checkpoint from security-checklist.md