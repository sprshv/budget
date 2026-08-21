# CLAUDE.md

This is the project bible. Read this at the start of every session.
Stack, conventions, and rules are final — do not deviate without being told to.

---

## Project Overview

A full-stack personal finance budgeting app — a modern Mint replacement.
Users link bank accounts, track transactions, set budgets, monitor goals,
detect subscriptions, and get data-driven spending insights powered by
pure Python math and SQL aggregations. No external AI API.

---

## Stack

| Layer | Choice |
|---|---|
| Frontend | React (Vite) |
| Backend | Python 3.11+ / FastAPI |
| Database | PostgreSQL (via Supabase) |
| Auth | Supabase Auth (JWT, OAuth, MFA) |
| Bank Linking | Plaid API |
| Insights | Pure Python logic + SQL aggregations |
| Background Jobs | APScheduler (in-process) |
| ORM | SQLAlchemy 2.0 (async) |
| Validation | Pydantic v2 |
| Testing | Pytest + React Testing Library |
| Containerization | Docker + Docker Compose |
| Deployment | Railway (backend) + Vercel (frontend) + Supabase (DB + Auth) |

---

## Folder Structure

```
/
├── CLAUDE.md
├── schema.sql
├── build-log.md
├── docker-compose.yml
├── .dockerignore
├── docs/
│   ├── phases/
│   │   ├── phase-1-auth.md
│   │   ├── phase-2-plaid.md
│   │   ├── phase-3-transactions.md
│   │   ├── phase-4-budgets.md
│   │   ├── phase-5-dashboard.md
│   │   ├── phase-6-goals.md
│   │   ├── phase-7-bills.md
│   │   ├── phase-8-analytics.md
│   │   ├── phase-9-insights.md
│   │   └── phase-10-notifications.md
│   ├── security-checklist.md
│   └── subagent-format.md
├── frontend/
│   ├── Dockerfile
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── api/
│   │   ├── store/
│   │   ├── utils/
│   │   └── styles/
│   │       └── tokens.css
│   └── .env.local
└── backend/
    ├── Dockerfile
    ├── app/
    │   ├── main.py
    │   ├── config.py
    │   ├── database.py
    │   ├── models/
    │   ├── schemas/
    │   ├── routers/
    │   ├── services/
    │   ├── jobs/
    │   └── utils/
    ├── tests/
    ├── alembic/
    └── .env
```

---

## Architecture Rules

### General
- Never put business logic in routers. Routers handle HTTP only.
- Never put DB queries in routers. Queries go in services.
- All secrets in environment variables. Never hardcode.
- Validate all input with Pydantic. Every endpoint has a schema.
- All errors return `{ "detail": "message", "code": "ERROR_CODE" }`.

### Security (non-negotiable)
- All Plaid API calls go through the backend. Never from frontend.
- Never expose Plaid access tokens to the client.
- Verify Supabase JWT on every protected endpoint via get_current_user dependency.
- Encrypt Plaid access tokens at rest using Fernet.
- Rate limit all auth endpoints using slowapi.
- Parameterized queries only. Never format SQL strings manually.
- CORS restricted to FRONTEND_URL only. No wildcard in production.
- HTTPS only in production.
- Set security headers in FastAPI middleware.

### Database
- Async SQLAlchemy with asyncpg driver throughout.
- Every table has: id (UUID), created_at, updated_at.
- Alembic for all schema changes. Never modify tables manually.
- Row-level security via Supabase RLS — users can only access their own rows.
- Foreign keys always have explicit ondelete behavior.

### API Design
- REST. Versioned under /api/v1/.
- GET = read, POST = create, PATCH = partial update, DELETE = remove.
- Paginate all list endpoints: ?limit=50&offset=0.
- Return 201 for creation, 204 for deletion, 200 for everything else.

### Frontend
- Axios for all API calls with interceptor that attaches Supabase JWT.
- Zustand for global state (user, accounts, transactions).
- React Query (TanStack Query) for server state and caching.
- React Router v6 for routing.
- Protected routes redirect to /login if no valid session.
- Never store tokens in localStorage. Use Supabase session management.
- All charts use Recharts.
- All UI components use shadcn/ui + tokens.css values.

### Vertical Slice Order (every task follows this)
1. Alembic migration (if schema change needed)
2. SQLAlchemy model (if new model needed)
3. Pydantic schemas (request + response)
4. Service layer (business logic)
5. FastAPI router (HTTP endpoints)
6. React hook (React Query)
7. React component (shadcn/ui + tokens.css)
8. Tests (pytest + React Testing Library)

### Docker
- Local dev uses Docker Compose — `docker compose up` starts everything
- backend/Dockerfile and frontend/Dockerfile are runtime source of truth
- After adding any pip or npm package: `docker compose up --build`
- Production backend deploys via Railway reading backend/Dockerfile
- Production frontend deploys via Vercel (no Docker needed)

---

## Design System
- Primary color: rgb(34, 183, 128)
- All design tokens in frontend/src/styles/tokens.css
- Never hardcode colors, spacing, or font sizes that exist in tokens.css
- Component library: shadcn/ui
- Charts: Recharts
- Icons: Lucide React
- Font: Inter

### Design Reference
The full UI design is at docs/design/ — open it in a browser
to see all screens. This is the source of truth for layout, spacing,
colors, and component appearance.

Before building any frontend component or page:
1. Read docs/design/
2. Find the section matching the screen being built
3. Extract the exact colors, spacing, layout, and component styles from it
4. Implement using those values via tokens.css — never hardcode
5. If a screen isn't in the design file, use the dashboard section as
   the style baseline

---

## Insights Engine (no LLM — pure logic)
All insights live in backend/app/services/insights_service.py.

| Insight | Implementation |
|---|---|
| Spending change | Compare SUM(amount) this month vs last month per category |
| Anomaly detection | Flag transactions > mean + (2 × std_dev) over 90-day window |
| Month-end forecast | (spent_so_far / days_elapsed) × days_in_month |
| Savings opportunity | Categories where spend > 110% of 3-month average |
| Budget recommendation | 3-month average spend per category as suggested limit |
| Health score | Weighted composite: budget adherence, savings rate, debt-to-income, emergency fund, subscription ratio |

---

## Environment Variables

### backend/.env
```
DATABASE_URL=postgresql+asyncpg://postgres:[password]@db.xxxx.supabase.co:5432/postgres
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=...
PLAID_CLIENT_ID=...
PLAID_SECRET=...
PLAID_ENV=sandbox
ENCRYPTION_KEY=...
FRONTEND_URL=http://localhost:5173
```

### frontend/.env.local
```
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=https://xxxx.supabase.co
VITE_SUPABASE_ANON_KEY=...
VITE_PLAID_ENV=sandbox
```

---

## Naming Conventions

| Thing | Convention | Example |
|---|---|---|
| Python files | snake_case | transaction_service.py |
| Python classes | PascalCase | TransactionService |
| Python functions | snake_case | get_transactions() |
| DB tables | snake_case plural | transactions, budget_categories |
| DB columns | snake_case | created_at, user_id |
| React components | PascalCase | BudgetCard.jsx |
| React hooks | camelCase, use prefix | useTransactions.js |
| API endpoints | kebab-case | /api/v1/budget-categories |
| Env vars | SCREAMING_SNAKE_CASE | PLAID_CLIENT_ID |

---

## Testing Rules
- Every service function has a corresponding pytest test.
- Use pytest-asyncio for async tests.
- Mock all external API calls (Plaid) in tests — never hit real APIs.
- Frontend: test all custom hooks and key user flows with React Testing Library.
- Run pytest before every commit.

---

## Skills
Before any backend task: read /mnt/skills/user/fastapi-slice/SKILL.md
Before any frontend task: read /mnt/skills/user/react-component/SKILL.md
Before any Plaid task: read /mnt/skills/user/plaid-integration/SKILL.md
Before any insights task: read /mnt/skills/user/insights-engine/SKILL.md

---

## What NOT To Do
- Do not use SELECT * in queries — always specify columns
- Do not catch bare Exception — catch specific exceptions
- Do not commit .env files
- Do not use any types in Pydantic schemas
- Do not make Plaid or any third-party API calls from frontend code
- Do not store Plaid access tokens in plaintext
- Do not skip input validation on any endpoint
- Do not use time.sleep() in async code — use asyncio.sleep()
- Do not read ahead to future phase files — only read the current phase
- Do not combine two tasks into one subagent
- Do not start the next phase until the security audit for the current phase passes