import os
import asyncio
import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text as _sa_text
from app.core.database import engine, SessionLocal
from app.core import models
from app.core.seed import seed_database

logger = logging.getLogger(__name__)


def _run_schema_migrations():
    """Safely add new columns to existing tables without data loss."""
    migrations = [
        "ALTER TABLE documents ADD COLUMN extracted_text TEXT",
        "ALTER TABLE documents ADD COLUMN document_type VARCHAR(100)",
        "ALTER TABLE documents ADD COLUMN fraud_risk VARCHAR(20) DEFAULT 'unknown'",
        "ALTER TABLE documents ADD COLUMN file_uuid VARCHAR(200)",
    ]
    with engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(_sa_text(sql))
                conn.commit()
            except Exception:
                pass  # Column already exists — safe to ignore


async def _db_keepalive():
    """Ping DB every 7 min to keep connection alive."""
    while True:
        await asyncio.sleep(7 * 60)
        try:
            def _ping():
                db = SessionLocal()
                try:
                    db.execute(_sa_text("SELECT 1"))
                finally:
                    db.close()
            await asyncio.to_thread(_ping)
            logger.info("[keepalive] ✓ DB ping OK")
        except Exception as exc:
            logger.warning(f"[keepalive] ✗ DB ping failed: {exc}")


from app.modules.auth.router import router as auth_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.documents.router import router as documents_router
from app.modules.approvals.router import router as approvals_router
from app.modules.workflows.router import router as workflows_router
from app.modules.search.router import router as search_router
from app.modules.reports.router import router as reports_router
from app.modules.knowledge.router import router as knowledge_router
from app.modules.agents.router import router as agents_router
from app.modules.users.router import router as users_router
from app.modules.audit.router import router as audit_router
from app.modules.projects.router import router as projects_router
from app.modules.vendors.router import router as vendors_router
from app.modules.customers.router import router as customers_router
from app.modules.notifications.router import router as notifications_router
from app.modules.integrations.router import router as integrations_router
from app.modules.settings.router import router as settings_router
from app.modules.admin_api.router import router as admin_api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    _run_schema_migrations()
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()

    # Ensure uploads directory exists
    os.makedirs("uploads", exist_ok=True)

    _task = asyncio.create_task(_db_keepalive())
    logger.info("[keepalive] Background DB keepalive started")
    yield
    _task.cancel()
    try:
        await _task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Document Intelligence Platform", version="2.0.0", lifespan=lifespan)


class NoCacheHTMLMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        content_type = response.headers.get("content-type", "")
        if "text/html" in content_type:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response


app.add_middleware(NoCacheHTMLMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/admin", StaticFiles(directory="admin", html=True), name="admin")

app.include_router(admin_api_router)
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(documents_router)
app.include_router(approvals_router)
app.include_router(workflows_router)
app.include_router(search_router)
app.include_router(reports_router)
app.include_router(knowledge_router)
app.include_router(agents_router)
app.include_router(users_router)
app.include_router(audit_router)
app.include_router(projects_router)
app.include_router(vendors_router)
app.include_router(customers_router)
app.include_router(notifications_router)
app.include_router(integrations_router)
app.include_router(settings_router)


@app.get("/")
async def root():
    return RedirectResponse(url="/dashboard")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    svg = (
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
        b'<rect width="32" height="32" rx="8" fill="#2563eb"/>'
        b'<path d="M10 10h8l4 4v12H10z" fill="white" opacity=".9"/>'
        b'<path d="M18 10v4h4" fill="none" stroke="#2563eb" stroke-width="1.5"/>'
        b'<path d="M13 17h6M13 20h5" stroke="#2563eb" stroke-width="1.5" stroke-linecap="round"/>'
        b'</svg>'
    )
    from fastapi.responses import Response
    return Response(content=svg, media_type="image/svg+xml",
                    headers={"Cache-Control": "public, max-age=86400"})
