# Phase 3 — Transaction Engine
Goal: transactions are imported, cleaned, categorized, and browsable.

Subagent types: Backend for 3.1-3.4, Full-stack for 3.5-3.11.

---

Task 3.1 — Background sync job (Job)
- APScheduler job running every 4 hours
- Loops through all active accounts, pulls new transactions via Plaid sync API using stored plaid_cursor
- Stores results, triggers categorization, triggers recurring detection

Task 3.2 — Merchant name normalization (Backend)
- Service: convert raw Plaid descriptions ("SQ *COFFEE 449", "AMZN MKTP US*2K3J") into clean names
- Use normalization rules dict + regex patterns, fallback to title-casing raw string

Task 3.3 — Rule-based auto-categorization engine (Backend)
- On every transaction insert: run categorization_rules in priority DESC order
- Fallback to Plaid's provided category (confidence 0.7) if no user rule matches
- Fallback to Uncategorized (confidence 0.3) if no Plaid match
- Store category_id and category_confidence on transaction

Task 3.4 — Duplicate detection (Backend)
- Before inserting: check plaid_transaction_id uniqueness
- For manual transactions: flag potential duplicates (same amount + date + merchant within 1 day), return warning

Task 3.5 — Transaction list endpoint + UI (Full-stack)
- Backend: GET /api/v1/transactions — paginated, filterable by account_id, category_id, date range, amount range, search query, pending
- Frontend: /transactions page — search bar, category filter chips, date range picker, infinite scroll
- Each row: merchant name, category badge (colored), amount (green income / red expense), date

Task 3.6 — Manual transaction entry (Full-stack)
- Backend: POST /api/v1/transactions — create manual transaction, run categorization, check duplicates
- Frontend: "Add transaction" modal — merchant, amount, date, category dropdown, notes

Task 3.7 — Transaction detail + edit (Full-stack)
- Backend: PATCH /api/v1/transactions/:id — update category, notes, tags, is_tax_deductible
- Frontend: transaction detail drawer — editable category dropdown, notes field, tag input

Task 3.8 — Split transactions (Full-stack)
- Backend: POST /api/v1/transactions/:id/split — array of {category_id, amount, notes}, validate splits sum to original, create transaction_splits rows
- Frontend: split UI in transaction detail modal with dynamic split rows

Task 3.9 — Bulk edit (Full-stack)
- Backend: PATCH /api/v1/transactions/bulk — array of transaction IDs + fields to update, validate all IDs belong to current user before updating any
- Frontend: checkbox selection on list, bulk action bar when items selected

Task 3.10 — Custom categorization rules CRUD (Full-stack)
- Backend: GET/POST/PATCH/DELETE /api/v1/categorization-rules
- Frontend: rules management in Settings — form with match field, operator, value, target category

Task 3.11 — Receipt upload (Full-stack)
- Backend: POST /api/v1/transactions/:id/receipt — validate image type + size, upload to Supabase Storage, store URL
- Frontend: upload button in transaction detail, image preview

---

After all tasks:
1. Run standard Security subagent from security-checklist.md
2. Run Phase 3 data integrity checkpoint from security-checklist.md