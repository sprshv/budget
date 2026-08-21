# Security Checklist

Run a Security subagent after every phase completes.
No phase starts until the previous phase's security audit passes.

---

## Standard Audit (every phase)

```
SUBAGENT: Security Audit — Phase [N] complete

Report PASS or FAIL for each item:

AUTHENTICATION
- [ ] Every non-public endpoint has get_current_user dependency
- [ ] JWT verified on every request, not just checked for existence
- [ ] No user ID accepted from request body or query params — always from verified JWT
- [ ] Auth endpoints (login, signup, reset, 2FA) rate limited via slowapi

DATA ISOLATION
- [ ] Every DB query filters by user_id from verified JWT — never from request input
- [ ] RLS policies active on all tables touched this phase (verify in Supabase dashboard)
- [ ] No endpoint returns another user's data under any input

INPUT VALIDATION
- [ ] Every request body has a Pydantic schema — no raw dicts reach service layer
- [ ] Every query param has type annotation and validation
- [ ] No manually formatted SQL strings — all queries use SQLAlchemy ORM or parameterized
- [ ] File uploads (if any) validate file type and size before storing

SECRETS & CREDENTIALS
- [ ] No API keys, tokens, or passwords hardcoded anywhere
- [ ] Plaid access tokens Fernet encrypted before storing — never plaintext
- [ ] No sensitive values in logs or error messages returned to client
- [ ] .env files are in .gitignore and not committed

PLAID SECURITY (phases 2+)
- [ ] All Plaid API calls originate from backend only — grep frontend for plaid imports
- [ ] Plaid webhook signature verified before processing any event
- [ ] Plaid access tokens never returned to frontend in any API response

API SECURITY
- [ ] CORS restricted to FRONTEND_URL only — no wildcard
- [ ] Security headers set (X-Content-Type-Options, X-Frame-Options, Strict-Transport-Security)
- [ ] Error responses never expose stack traces, internal paths, or DB errors
- [ ] Pagination limits enforced — no endpoint allows unlimited row fetching

DOCKER
- [ ] No secrets in Dockerfile or docker-compose.yml — all via env_file
- [ ] .env files listed in .dockerignore

Fail = fix immediately, log [SECURITY FIX] to build-log.md, re-audit before proceeding.
Pass = log [SECURITY PASS] Phase N to build-log.md, proceed to next phase.
```

---

## Phase 2 Checkpoint (after Plaid integration complete)

```
SUBAGENT: Security Audit — Plaid specific

- Confirm access tokens encrypted in DB — query one row, verify not readable plaintext
- Confirm webhook endpoint verifies Plaid-Verification-Token header before processing
- Confirm no Plaid credentials in frontend bundle — run npm run build, grep dist/ for PLAID
- Confirm link token endpoint returns 401 for unauthenticated requests
- Confirm exchange token is idempotent — same public token twice = no duplicate accounts
```

---

## Phase 3 Checkpoint (after transaction engine complete)

```
SUBAGENT: Security Audit — Data integrity

- Fetch another user's transaction by manipulating transaction ID in URL — must return 404 not 403
- Create transaction on another user's account by passing different account_id — must fail with 403
- Upload receipt with non-image file type — must be rejected
- Confirm bulk edit validates all transaction IDs belong to current user before updating any
- Confirm split transaction amounts validated server-side to sum to original — not just client-side
```

---

## Phase 9 Checkpoint (after insights engine complete)

```
SUBAGENT: Security Audit — Insights data isolation

- Confirm all insight calculations scoped to current user's transactions only
- Confirm financial health score endpoint returns 401 for unauthenticated requests
- Confirm insights summary endpoint does not cache responses across users
```

---

## Final Security Audit (after all phases and skipped task cleanup)

```
SUBAGENT: Security Audit — Full application

DEPENDENCY AUDIT
- Run pip-audit in backend — flag any known vulnerable packages
- Run npm audit in frontend — flag any high or critical vulnerabilities

SECRETS SCAN
- grep -r "sk_" . → should return nothing (Plaid secret pattern)
- grep -r "PLAID_SECRET" . --include="*.py" --include="*.js" → only in .env and config.py
- grep -r "password" . --include="*.py" → confirm no hardcoded passwords
- grep -r "ANTHROPIC" . → should return nothing (not used in this project)

ENDPOINT AUDIT
- List every FastAPI route in the application
- Confirm every route except these is protected by get_current_user:
    GET /health
    POST /api/v1/plaid/webhook (protected by Plaid signature verification instead)
- Any unprotected route not on this list is a critical failure — fix immediately

DATA EXPOSURE AUDIT
- Review every Pydantic response schema
- Confirm no schema exposes: plaid_access_token, plaid_cursor, encryption keys
- Confirm financial_accounts response never includes plaid_access_token field

RATE LIMITING AUDIT
- Confirm slowapi limits applied to: login, signup, password reset, 2FA verify, Plaid link token
- Login must be no more than 10 attempts per minute per IP

DOCKER AUDIT
- Confirm no secrets hardcoded in Dockerfile or docker-compose.yml
- Confirm .env and .env.local are in .dockerignore
- Confirm production Dockerfile does not include dev dependencies

Log [SECURITY FINAL PASS] or list all failures as [SECURITY FINAL FAIL] with details.
```