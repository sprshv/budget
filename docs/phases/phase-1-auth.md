# Phase 1 — Foundation
Goal: app runs, user can log in, nothing breaks.

Subagent type: Full-stack for every task.

---

Task 1.1 — Project scaffolding
- FastAPI main.py: app entrypoint, CORS middleware restricted to FRONTEND_URL, GET /health endpoint, global error handler returning { detail, code } shape
- Docker: backend/Dockerfile, frontend/Dockerfile, docker-compose.yml, .dockerignore
- React: app entry, React Router v6 setup, axios instance with JWT interceptor, Supabase client initialization, tokens.css with full design system

Task 1.2 — Supabase Auth: signup + login + logout
- Backend: get_current_user dependency that verifies Supabase JWT. POST /api/v1/auth/logout.
- Frontend: /signup page, /login page, logout button, Supabase session listener keeping Zustand user store in sync

Task 1.3 — Protected routes + onboarding gate
- React protected route wrapper redirecting to /login if no session
- After login: if users.onboarding_complete = false, redirect to /onboarding
- /onboarding page: connect first account, set first budget, mark complete

Task 1.4 — Password reset + email verification
- Backend: handle Supabase auth callback URLs
- Frontend: /forgot-password page, /reset-password page, email verification handler

Task 1.5 — TOTP two-factor authentication
- Backend: POST /api/v1/auth/2fa/setup, POST /api/v1/auth/2fa/verify, store enrolled state on user record
- Frontend: 2FA setup flow (QR code display, verify code input), 2FA prompt on login if enrolled

Task 1.6 — Session management
- Backend: GET /api/v1/auth/sessions (list active sessions), DELETE /api/v1/auth/sessions/:id (revoke)
- Frontend: Settings page section showing active sessions with device info and revoke button

---

After all tasks: run Security subagent using standard checklist in security-checklist.md.