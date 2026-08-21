# Phase 5 — Dashboard
Goal: single screen showing the full financial picture with charts.

Subagent types: Backend for 5.1-5.7, Full-stack for 5.8.

---

Task 5.1 — Net worth calculation (Backend)
- GET /api/v1/dashboard/net-worth — sum asset account balances + manual assets, subtract liability balances + manual liabilities
- Return breakdown: liquid assets, investments, property, total debt, net total

Task 5.2 — Cash flow summary (Backend)
- GET /api/v1/dashboard/cash-flow — current month income total, expense total, net cash flow, vs last month

Task 5.3 — Account overview cards (Backend)
- GET /api/v1/accounts — all accounts with balance_current, balance_available, last_synced_at, institution_name, account_type
- Frontend component: scrollable row of cards, institution logo, name, balance, account type badge, 30-day sparkline

Task 5.4 — Spending breakdown chart (Backend)
- GET /api/v1/dashboard/spending-breakdown — current month spend grouped by category with amount and percentage
- Frontend: Recharts donut chart, legend alongside, center shows total spent, category colors from tokens.css

Task 5.5 — Net worth history chart (Backend)
- GET /api/v1/dashboard/net-worth-history — monthly net worth snapshots for last 12 months
- Frontend: Recharts bar chart with trend line overlay

Task 5.6 — Spending trend chart (Backend)
- GET /api/v1/dashboard/spending-trends — last 6 months income vs expenses as monthly totals
- Frontend: Recharts two-line area chart — income in rgb(34,183,128), expenses in red

Task 5.7 — Recent activity feed (Backend)
- GET /api/v1/transactions?limit=10 — last 10 transactions across all accounts
- Frontend: feed component, each row tappable to open transaction detail drawer

Task 5.8 — Dashboard assembly (Full-stack)
- Assemble all components into /dashboard layout
- Sidebar nav with logo, all nav items, active state using primary color, collapsed/expanded states
- Responsive grid layout
- Skeleton loading states for each panel while data loads
- Error boundaries so one failing widget doesn't crash the page

---

After all tasks: run Security subagent using standard checklist in security-checklist.md.