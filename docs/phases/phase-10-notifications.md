# Phase 10 — Notifications
Goal: user gets alerted about things that matter without being spammed.

Subagent types: Job for 10.2-10.7, Full-stack for 10.1 and 10.8.

---

Task 10.1 — Notification storage + delivery (Full-stack)
- Backend:
  - Notification creation service (internal — not a public endpoint, called by other services)
  - GET /api/v1/notifications — paginated, unread first
  - PATCH /api/v1/notifications/:id/read
  - PATCH /api/v1/notifications/read-all
- Frontend: notification bell in nav with unread count badge, notification drawer with list

Task 10.2 — Budget limit warnings (Job)
- After each transaction sync: check all budgets
- If category crosses alert_threshold (default 80%): create notification if alert_sent = false for this period, set alert_sent = true
- Also trigger when budget exceeded (100%)

Task 10.3 — Bill due reminders (Job)
- Daily check: recurring_transactions with next_expected_date within remind_days_before days
- Create notification if not already sent for this cycle
- Notification includes: bill name, expected amount, due date

Task 10.4 — Low balance alerts (Job)
- After each sync: check all checking/savings accounts
- If balance_available < user threshold (default $100, from notification_preferences): create notification

Task 10.5 — Large purchase alerts (Job)
- On every transaction insert: if amount > user threshold (default $500, from notification_preferences): create notification immediately

Task 10.6 — Unusual spending alerts (Job)
- After anomaly detection runs (calls insights_service.get_anomalies): for each newly flagged transaction create notification

Task 10.7 — Weekly + monthly summaries (Job)
- Weekly job (Monday 8am): total spent last 7 days, top category, vs prior week
- Monthly job (1st of month 8am): prior month income, total spent, net savings, budget performance summary, top merchant

Task 10.8 — Notification preferences UI (Full-stack)
- Backend: GET/PATCH /api/v1/notifications/preferences — per notification_type: push_enabled, email_enabled, threshold_amount
- Frontend: /settings/notifications — toggles per notification type, threshold inputs for low balance and large purchase

---

After all tasks: run Security subagent using standard checklist in security-checklist.md.
Then run Final Security Audit from security-checklist.md.

---

## After All Phases Complete
1. Review build-log.md — attempt all [SKIP] tasks now
2. Run full test suite: pytest in backend, npm run build in frontend
3. Verify no secrets hardcoded anywhere — run secrets scan from final security audit
4. Confirm all Plaid calls go through backend only
5. Confirm RLS policies active on all tables in Supabase dashboard
6. Run final security audit from security-checklist.md
7. Update build-log.md with [BUILD COMPLETE] and date