# Phase 7 — Bill & Subscription Tracking
Goal: user sees all upcoming bills and active subscriptions in one place.

Subagent types: Job for 7.5, Full-stack for everything else.

---

Task 7.1 — Recurring transaction detection algorithm (Full-stack)
- Service: analyze transaction history — group by merchant_name, find transactions repeating every 7/14/30/90/365 days within ±3 day tolerance, calculate average amount
- Classify as subscription (consistent amount ±10%) vs bill (variable amount)
- Run on each transaction import batch, update recurring_transactions table
- Backend: GET /api/v1/recurring — list all detected recurring transactions

Task 7.2 — Bills dashboard (Full-stack)
- Backend: GET /api/v1/bills — recurring_transactions where is_bill = true, sorted by next_expected_date, with days_until_due
- Frontend: /bills page — sorted by due date, days until due badge (red if <3 days), mark as paid button

Task 7.3 — Subscriptions dashboard (Full-stack)
- Backend: GET /api/v1/subscriptions — recurring_transactions where is_subscription = true, with monthly and annual cost
- Frontend: /subscriptions page — subscription cards with name, amount, frequency, annual cost. Total monthly spend at top.

Task 7.4 — Bill calendar view (Full-stack)
- Frontend: monthly calendar view on /bills showing all bills on expected due dates
- Clicking a bill opens detail drawer with history and mark-as-paid option

Task 7.5 — Renewal alerts (Job)
- Job: daily check for subscriptions with next_expected_date within remind_days_before days
- Create notification row if alert not already sent for this cycle
- Frontend: alert banner on subscription card when renewal within 3 days

Task 7.6 — Annual subscription cost summary (Full-stack)
- Backend: GET /api/v1/subscriptions/annual-summary — total annual cost, broken down by subscription
- Frontend: "You're spending $X/year on subscriptions" summary card, ranked list by annual cost

---

After all tasks: run Security subagent using standard checklist in security-checklist.md.