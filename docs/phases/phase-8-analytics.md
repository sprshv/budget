# Phase 8 — Analytics & Reporting
Goal: user can explore full financial history with charts and export data.

Subagent type: Full-stack for every task.

---

Task 8.1 — Category spending bar chart
- Backend: GET /api/v1/analytics/category-spending — accepts date range, returns spend per category sorted descending
- Frontend: Recharts horizontal bar chart, category color coded, amounts on right

Task 8.2 — Merchant spending summaries
- Backend: GET /api/v1/analytics/merchants — top merchants by total spend for given period, with transaction count
- Frontend: ranked list — merchant name, transaction count, total spend

Task 8.3 — Income vs expenses report
- Backend: GET /api/v1/analytics/income-vs-expenses — monthly totals for last 12 months
- Frontend: Recharts grouped bar chart — income and expense bars side by side per month

Task 8.4 — Year-over-year comparison
- Backend: GET /api/v1/analytics/year-over-year — current year monthly spend vs prior year by category
- Frontend: Recharts line chart with two lines per selected category

Task 8.5 — Tax categorization
- Backend: PATCH /api/v1/transactions/:id — support setting is_tax_deductible + tax_category
- Frontend: tax filter in transaction list, tax category dropdown in transaction detail

Task 8.6 — Year-end tax summary
- Backend: GET /api/v1/analytics/tax-summary — all tax_deductible transactions grouped by tax_category for given year with totals
- Frontend: /tax page — summary table with totals per category, export button

Task 8.7 — CSV export
- Backend: GET /api/v1/transactions/export — CSV of all transactions for given date range, all columns
- Frontend: export button on transactions page with date range picker, triggers download

Task 8.8 — Account balance sparklines
- Backend: GET /api/v1/accounts/:id/history — daily balance snapshots for last 30 days (derived from transaction history)
- Frontend: tiny Recharts sparkline on each account card

---

After all tasks: run Security subagent using standard checklist in security-checklist.md.