# Phase 9 — Insights Engine
Goal: surface actionable financial insights using pure math and SQL. No external AI API.

All insight functions live in backend/app/services/insights_service.py.
All functions return plain Python dicts. Routers serialize via Pydantic.
Insights are calculated on demand (GET request) — no background job needed yet.

Subagent types: Backend for 9.1-9.6, Full-stack for 9.7.

---

Task 9.1 — Spending change detection (Backend)
- Per category: compare current month SUM(amount) vs prior month and 3-month average
- Return: percentage change, direction (up/down), magnitude label (significant if >15%)
- GET /api/v1/insights/spending-changes

Task 9.2 — Anomaly detection (Backend)
- Per category: calculate 90-day rolling mean and std_dev for current user
- Flag transactions where amount > mean + (2 × std_dev)
- GET /api/v1/insights/anomalies — flagged transactions with expected range
- Frontend: unusual purchase badge on flagged transactions in transaction list

Task 9.3 — Month-end spending forecast (Backend)
- Formula: (total_spent_so_far / days_elapsed) * days_in_month per category and overall
- GET /api/v1/insights/forecast
- Frontend: forecast widget on budget page — projected vs limit per category

Task 9.4 — Savings opportunity detection (Backend)
- Find categories where current month spend > 110% of 3-month average
- Rank by overage amount, calculate potential savings
- GET /api/v1/insights/savings-opportunities
- Frontend: "Ways to save" card on dashboard — top 3 opportunities with dollar amounts

Task 9.5 — Budget recommendations (Backend)
- Categories without budget: suggest 3-month average spend as limit
- Existing budgets: flag if consistently too high (never reached 70%) or too low (always exceeded)
- GET /api/v1/insights/budget-recommendations
- Frontend: recommendations section on budget page with one-click apply button

Task 9.6 — Financial health score (Backend)
- Composite 0-100 score:
  - Budget adherence 30% — % of categories that stayed within budget last 3 months
  - Savings rate 25% — (income - expenses) / income last 3 months
  - Debt-to-income 20% — total liability balances / monthly income
  - Emergency fund 15% — liquid savings / monthly expenses (target: 3-6 months)
  - Subscription ratio 10% — total subscriptions / monthly income (target: <10%)
- GET /api/v1/insights/health-score — overall score + per-component breakdown
- Frontend: health score card on dashboard with component bars

Task 9.7 — Insights summary endpoint (Full-stack)
- Backend: GET /api/v1/insights/summary — single endpoint calling all insight functions, returns top insights sorted by relevance/impact
- Frontend: insights panel on dashboard — top 3-5 insights as cards with icon, title, description, and action link

---

After all tasks:
1. Run standard Security subagent from security-checklist.md
2. Run Phase 9 insights isolation checkpoint from security-checklist.md