# Phase 4 — Budget System
Goal: user can set monthly budgets and track spending against them.

Subagent type: Full-stack for every task.

---

Task 4.1 — Budget CRUD
- Backend: GET/POST/PATCH/DELETE /api/v1/budgets — scoped to current month by default, accepts period_month + period_year
- Auto-create new month budgets by copying previous month's amounts if user has existing budgets

Task 4.2 — Budget progress calculation
- Backend: GET /api/v1/budgets/progress — per budget: SUM transactions in category for period, return spent + remaining + percentage + status (ok/warning/over)
- Warning threshold at 80% (configurable via budget.alert_threshold), over at 100%

Task 4.3 — Rollover logic
- On month rollover (first sync of new month): calculate unused from previous month where rollover_enabled = true, add to new month's rollover_amount

Task 4.4 — Income budgeting
- Budget support for income categories (is_income = true), track planned vs actual income
- Frontend: income section in budget page separate from expense categories

Task 4.5 — Spending forecast
- Backend: GET /api/v1/budgets/forecast — formula: (spent_so_far / days_elapsed) * days_in_month per category
- Frontend: forecast indicator on each budget card — projected vs limit, color coded

Task 4.6 — Budget history
- Backend: GET /api/v1/budgets/history — last 12 months of budget performance (budgeted vs actual per category per month)
- Frontend: history page with month selector, table or chart view

Task 4.7 — Budget comparison view
- Frontend: side-by-side actual vs budgeted for current month, color coded, sortable by overage amount

Task 4.8 — Custom categories CRUD
- Backend: GET/POST/PATCH/DELETE /api/v1/categories — user-scoped, system categories cannot be deleted
- Frontend: category management in Settings — color picker, icon picker, parent category selector

Task 4.9 — Zero-based budgeting mode
- Backend: GET /api/v1/budgets/zero-based — total income minus sum of all budgets = unallocated amount
- Frontend: toggle on budget page showing unallocated dollars, prompts user to assign them

---

After all tasks: run Security subagent using standard checklist in security-checklist.md.