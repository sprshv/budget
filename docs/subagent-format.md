# Subagent Format

## Types

- **Backend** — migration + model + schema + service + router + pytest tests. Runs `pytest` at end.
- **Frontend** — React hook + component + RTL tests. Runs `npm run build` at end.
- **Full-stack** — complete vertical slice (backend + frontend). Runs both at end.
- **Job** — APScheduler job + service dependencies + tests. No frontend.
- **Migration** — Alembic migration only. For mid-build schema changes not in schema.sql.
- **Security** — audit only. Does not build features. Runs after every phase.

## Rules

- Spawn one subagent per task. Never combine two tasks.
- Never spawn the next subagent until the current one is verified complete.
- Verified complete means: pytest passes, npm run build passes, no errors.
- If a subagent fails after 3 attempts: log [SKIP] to build-log.md and move on.
- Return to all skipped tasks after all phases complete.

## Prompt Format (use this exactly for every subagent)

```
SUBAGENT: [Type] — Task [N.N] [Task Name]

Files to create:
- path/to/file.py
- path/to/file.jsx

Files to modify:
- path/to/existing.py (what changes)

Schema tables: [tables touched]

Build:
[Precise description of what to build]

Done when:
- [specific test passes]
- [specific endpoint returns specific shape]
- [specific component renders specific thing]
```

## Example

```
SUBAGENT: Backend — Task 3.3 Rule-based auto-categorization engine

Files to create:
- backend/app/services/categorization_service.py
- backend/tests/test_categorization_service.py

Files to modify:
- backend/app/services/transaction_service.py (call categorization on insert)

Schema tables: transactions, categorization_rules, categories

Build:
- Function categorize_transaction(transaction, user_id, db) that:
  1. Loads user's categorization_rules ordered by priority DESC
  2. Evaluates each rule against transaction.merchant_name and description
  3. Returns matching category_id and confidence 1.0
  4. Falls back to Plaid category mapping if no rule matches (confidence 0.7)
  5. Falls back to Uncategorized if no Plaid match (confidence 0.3)
- Call this inside transaction_service.create_transaction() after dedup check
- Store result in transactions.category_id and transactions.category_confidence

Done when:
- pytest tests/test_categorization_service.py passes
- POST /api/v1/transactions returns transaction with category assigned
- Transaction matching a user rule uses that rule's category with confidence 1.0
```