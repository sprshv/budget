# CLAUDE.md — Budgeting App

This file defines the stack, conventions, and rules for this project.
Read this before every session. Follow these decisions — do not deviate without being told to.

---

## Project Overview

A full-stack personal finance / budgeting app that replicates and extends Intuit Mint.
Users link bank accounts, track transactions, set budgets, monitor goals, detect subscriptions,
and get data-driven spending insights powered by pure logic and math — no external AI API.

---

## Stack

| Layer | Choice |
|---|---|
| Frontend | React (Vite) |
| Backend | Python 3.11+ / FastAPI |
| Database | PostgreSQL (via Supabase) |
| Auth | Supabase Auth (JWT, OAuth, MFA) |
| Bank Linking | Plaid API |
| Insights Engine | Pure Python logic (stats, SQL aggregations) |
| Background Jobs | APScheduler (in-process) or Railway cron |
| Deployment | Railway (backend + DB) + Vercel (frontend) |
| ORM | SQLAlchemy 2.0 (async) |
| Validation | Pydantic v2 |
| Testing | Pytest + React Testing Library |

---

## Folder Structure

```
/
├── frontend/                  # React app (Vite)
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   ├── pages/             # Route-level page components
│   │   ├── hooks/             # Custom React hooks
│   │   ├── api/               # API call functions (axios)
│   │   ├── store/             # Global state (Zustand)
│   │   └── utils/             # Helper functions
│   └── .env.local
│
├── backend/                   # FastAPI app
│   ├── app/
│   │   ├── main.py            # App entrypoint, middleware, router registration
│   │   ├── config.py          # Settings via pydantic-settings
│   │   ├── database.py        # SQLAlchemy async engine + session
│   │   ├── models/            # SQLAlchemy ORM models (one file per table group)
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   ├── routers/           # FastAPI routers (one file per feature)
│   │   ├── services/          # Business logic (one file per feature)
│   │   ├── jobs/              # Background/cron jobs
│   │   └── utils/             # Shared utilities
│   ├── tests/
│   ├── alembic/               # DB migrations
│   └── .env
│
└── CLAUDE.md
```

---

## Architecture Rules

### General
- **Never put business logic in routers.** Routers handle HTTP only. All logic goes in services.
- **Never put DB queries in routers.** Queries go in services or a dedicated repository layer.
- **All secrets in environment variables.** Never hardcode API keys, tokens, or credentials.
- **Validate all input with Pydantic.** Every request body and query param must have a schema.
- **Return consistent error shapes.** All errors return `{ "detail": "message", "code": "ERROR_CODE" }`.

### Security (non-negotiable)
- **All Plaid API calls go through the backend.** Never call Plaid from the frontend.
- **Never expose Plaid access tokens to the client.** Store them encrypted in the DB.
- **Verify Supabase JWT on every protected endpoint** using the `get_current_user` dependency.
- **Encrypt sensitive fields at rest** (Plaid access tokens, account numbers) using Fernet.
- **Rate limit all auth endpoints** using `slowapi`.
- **Use parameterized queries only.** Never format SQL strings manually.
- **Add CORS** restricted to frontend domain only (no wildcard in production).
- **Use HTTPS only** in production. Enforce via Railway settings.
- **Helmet equivalent** — set security headers in FastAPI middleware.

### Database
- Use **async SQLAlchemy** with `asyncpg` driver throughout.
- Every table has: `id` (UUID), `created_at`, `updated_at`.
- Use **Alembic** for all schema changes. Never modify tables manually.
- **Row-level security** via Supabase RLS policies — users can only access their own rows.
- Foreign keys always have explicit `ondelete` behavior defined.

### API Design
- REST. Versioned under `/api/v1/`.
- Resource-based URLs: `/api/v1/transactions`, `/api/v1/budgets`, etc.
- GET = read, POST = create, PATCH = partial update, DELETE = remove.
- Paginate all list endpoints: `?limit=50&offset=0`.
- Return 201 for creation, 204 for deletion, 200 for everything else.

### Frontend
- **Axios** for all API calls, with an interceptor that attaches the Supabase JWT.
- **Zustand** for global state (user, accounts, transactions).
- **React Query (TanStack Query)** for server state, caching, and background refetching.
- **React Router v6** for routing.
- Protected routes redirect to `/login` if no valid session.
- Never store tokens in localStorage. Use Supabase's built-in session management.

---

## Feature Modules (build in this order)

1. **Auth** — Supabase signup/login/logout, JWT middleware, protected routes
2. **Plaid Integration** — Link token, public token exchange, account sync, webhooks
3. **Transaction Engine** — Import, categorization rules, merchant normalization, dedup
4. **Budget System** — CRUD budgets, progress calculation, rollover logic
5. **Dashboard** — Net worth, cash flow, spending summary, account cards
6. **Goals** — Savings and debt payoff goals, progress tracking
7. **Bill & Subscription Tracking** — Recurring detection, alerts
8. **Analytics** — Charts, trends, reports, export
9. **Insights Engine** — Pure logic: anomaly detection (std deviation), spending trends (% change), forecasts (pace × days), savings opportunities (category comparisons), budget recommendations (3-month averages)
10. **Notifications** — Budget alerts, bill reminders, low balance warnings

---

## Environment Variables

### Backend (`backend/.env`)
```
DATABASE_URL=postgresql+asyncpg://...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=...
PLAID_CLIENT_ID=...
PLAID_SECRET=...
PLAID_ENV=sandbox
ENCRYPTION_KEY=...         # Fernet key for encrypting Plaid tokens
FRONTEND_URL=http://localhost:5173
```

### Frontend (`frontend/.env.local`)
```
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=...
VITE_PLAID_ENV=sandbox
```

---

## Naming Conventions

| Thing | Convention | Example |
|---|---|---|
| Python files | snake_case | `transaction_service.py` |
| Python classes | PascalCase | `TransactionService` |
| Python functions | snake_case | `get_transactions()` |
| DB tables | snake_case plural | `transactions`, `budget_categories` |
| DB columns | snake_case | `created_at`, `user_id` |
| React components | PascalCase | `BudgetCard.jsx` |
| React hooks | camelCase, use prefix | `useTransactions.js` |
| API endpoints | kebab-case | `/api/v1/budget-categories` |
| Env vars | SCREAMING_SNAKE_CASE | `PLAID_CLIENT_ID` |

---

## Testing Rules

- Every service function has a corresponding pytest test.
- Use `pytest-asyncio` for async tests.
- Mock all external API calls (Plaid) in tests — never hit real APIs in tests.
- Frontend: test all custom hooks and key user flows with React Testing Library.
- Run `pytest` before every commit.

---

## Insights Engine (no LLM — pure logic)

All spending insights are generated from SQL aggregations and Python math. No external AI API.
Implement each insight as a standalone function in `backend/app/services/insights_service.py`.

| Insight | Implementation |
|---|---|
| "You spent X% more on dining" | Compare `SUM(amount)` this month vs last month per category |
| Anomaly detection | Flag transactions > 2 standard deviations from user's 90-day average for that category |
| Month-end forecast | `(total_spent_so_far / days_elapsed) × days_in_month` |
| Savings opportunity | Find categories where spend > 110% of 3-month average |
| Budget recommendation | Use 3-month average spend per category as suggested limit |
| Largest spending categories | `ORDER BY SUM(amount) DESC` for current month |
| Income vs expense trend | Monthly `SUM` grouped by `is_income` flag over last 12 months |
| Subscription cost total | `SUM(average_amount)` from `recurring_transactions` where `is_subscription = true` |

All insight functions return plain Python dicts. The router serializes them via Pydantic.
Insights are recalculated on demand (GET request) — no background job needed until scale requires it.

---

## What NOT to Do

- Do not use `SELECT *` in queries — always specify columns.
- Do not catch bare `Exception` — catch specific exceptions.
- Do not commit `.env` files — they are in `.gitignore`.
- Do not use `any` types in Pydantic schemas.
- Do not make Plaid API calls from frontend code.
- Do not call any external API from frontend code — all third-party calls go through the backend.
- Do not store Plaid access tokens in plaintext.
- Do not skip input validation on any endpoint.
- Do not use `time.sleep()` in async code — use `asyncio.sleep()`.