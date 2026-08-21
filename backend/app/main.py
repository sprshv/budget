from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.routers import health as health_router
from app.routers import auth as auth_router
from app.routers import auth_callbacks as auth_callbacks_router
from app.routers import users as users_router
from app.routers import mfa as mfa_router
from app.routers import sessions as sessions_router
from app.routers import plaid as plaid_router
from app.routers import webhook as webhook_router
from app.routers import accounts as accounts_router
from app.routers import transactions as transactions_router
from app.routers import categorization_rules as categorization_rules_router
from app.routers import budgets as budgets_router
from app.routers import categories as categories_router
from app.routers import dashboard as dashboard_router
from app.routers import goals as goals_router
from app.routers import recurring as recurring_router
from app.routers import bills as bills_router
from app.routers import subscriptions as subscriptions_router
from app.routers import analytics as analytics_router
from app.routers.insights import router as insights_router
from app.routers.notifications import router as notifications_router
from app.jobs.sync_job import run_transaction_sync
from app.jobs.renewal_alert_job import run_renewal_alerts
from app.jobs.bill_reminder_job import run_bill_reminders
from app.jobs.summary_job import send_weekly_summary, send_monthly_summary

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the scheduler
    scheduler.add_job(
        run_transaction_sync,
        trigger=IntervalTrigger(hours=4),
        id="transaction_sync",
        replace_existing=True,
        misfire_grace_time=600,
    )
    scheduler.add_job(
        run_renewal_alerts,
        trigger=IntervalTrigger(hours=24),
        id="renewal_alerts",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.add_job(
        run_bill_reminders,
        "cron",
        hour=8,
        minute=0,
        id="bill_reminders",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.add_job(
        send_weekly_summary,
        "cron",
        day_of_week="mon",
        hour=8,
        minute=0,
        id="weekly_summary",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.add_job(
        send_monthly_summary,
        "cron",
        day=1,
        hour=8,
        minute=0,
        id="monthly_summary",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    yield
    # Shutdown
    scheduler.shutdown(wait=False)


app = FastAPI(title="Budgeting App API", version="1.0.0", lifespan=lifespan)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware — restricted to FRONTEND_URL only
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "code": "INTERNAL_ERROR"},
    )


# HTTP exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": "HTTP_ERROR"},
    )


# Health endpoint at root level
@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


# Include routers under /api/v1
app.include_router(health_router.router, prefix="/api/v1")
app.include_router(auth_router.router, prefix="/api/v1")
app.include_router(auth_callbacks_router.router, prefix="/api/v1")
app.include_router(users_router.router, prefix="/api/v1")
app.include_router(mfa_router.router, prefix="/api/v1")
app.include_router(sessions_router.router, prefix="/api/v1")
app.include_router(plaid_router.router, prefix="/api/v1")
app.include_router(webhook_router.router, prefix="/api/v1")
app.include_router(accounts_router.router, prefix="/api/v1")
app.include_router(transactions_router.router, prefix="/api/v1")
app.include_router(categorization_rules_router.router, prefix="/api/v1")
app.include_router(budgets_router.router, prefix="/api/v1")
app.include_router(categories_router.router, prefix="/api/v1")
app.include_router(dashboard_router.router, prefix="/api/v1")
app.include_router(goals_router.router, prefix="/api/v1")
app.include_router(recurring_router.router, prefix="/api/v1")
app.include_router(bills_router.router, prefix="/api/v1")
app.include_router(subscriptions_router.router, prefix="/api/v1")
app.include_router(analytics_router.router, prefix="/api/v1")
app.include_router(insights_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
