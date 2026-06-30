import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
from app.core.database import engine, SessionLocal
from app.core import models
from app.core.seed import seed_database
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
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Document Intelligence Platform", version="1.0.0", lifespan=lifespan)


class NoCacheHTMLMiddleware(BaseHTTPMiddleware):
    """Prevent browser from caching HTML pages so back-button after logout re-fetches from server."""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        content_type = response.headers.get("content-type", "")
        if "text/html" in content_type:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response


app.add_middleware(NoCacheHTMLMiddleware)

# CORS: allow_origins=["*"] is valid ONLY when allow_credentials=False.
# Cookie-based client auth is same-origin (no CORS applies).
# Admin API uses Bearer tokens (Authorization header) which does NOT require
# allow_credentials=True — the wildcard origin covers it correctly.
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
