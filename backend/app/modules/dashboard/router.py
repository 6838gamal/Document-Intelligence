from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from datetime import datetime, timedelta, timezone
from app.core.database import get_db
from app.core.dependencies import require_auth, get_theme_lang
from app.core.models import Document, Approval, User, Workflow, AuditLog, DocumentStatus, ApprovalStatus

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db), user=Depends(require_auth)):
    tl = get_theme_lang(request)

    # ── Core counts ──────────────────────────────────────────────
    total_docs = db.query(Document).filter(Document.is_deleted == False).count()
    pending_approvals = db.query(Approval).filter(Approval.status == ApprovalStatus.PENDING).count()
    approved_docs = db.query(Document).filter(Document.status == DocumentStatus.APPROVED).count()
    active_workflows = db.query(Workflow).filter(Workflow.status == "active").count()
    total_users = db.query(User).filter(User.is_active == True).count()

    # ── Automation / approval rate ────────────────────────────────
    approval_rate = round((approved_docs / total_docs * 100) if total_docs > 0 else 0, 1)

    # ── Recent data ───────────────────────────────────────────────
    recent_docs = (
        db.query(Document)
        .filter(Document.is_deleted == False)
        .order_by(Document.created_at.desc())
        .limit(6)
        .all()
    )
    pending_list = (
        db.query(Approval)
        .filter(Approval.status == ApprovalStatus.PENDING)
        .join(Document)
        .order_by(Approval.created_at.desc())
        .limit(5)
        .all()
    )

    # ── Users with doc counts ─────────────────────────────────────
    users_with_stats = (
        db.query(
            User.id, User.name, User.email, User.role,
            User.department, User.is_active, User.created_at,
            func.count(Document.id).label("doc_count"),
        )
        .outerjoin(Document, (Document.uploader_id == User.id) & (Document.is_deleted == False))
        .group_by(User.id, User.name, User.email, User.role, User.department, User.is_active, User.created_at)
        .order_by(func.count(Document.id).desc())
        .all()
    )

    # ── Docs per day (last 14 days) ───────────────────────────────
    since = datetime.now(timezone.utc) - timedelta(days=14)
    docs_timeline = (
        db.query(cast(Document.created_at, Date).label("day"), func.count().label("count"))
        .filter(Document.created_at >= since, Document.is_deleted == False)
        .group_by(cast(Document.created_at, Date))
        .order_by(cast(Document.created_at, Date))
        .all()
    )
    chart_labels = [str(r.day) for r in docs_timeline]
    chart_data = [r.count for r in docs_timeline]

    # ── Recent audit activity ─────────────────────────────────────
    recent_activity = (
        db.query(AuditLog, User.name.label("user_name"))
        .join(User, AuditLog.user_id == User.id)
        .order_by(AuditLog.created_at.desc())
        .limit(8)
        .all()
    )

    return templates.TemplateResponse("dashboard/index.html", {
        "request": request, "user": user,
        "total_docs": total_docs,
        "pending_approvals": pending_approvals,
        "approved_docs": approved_docs,
        "active_workflows": active_workflows,
        "total_users": total_users,
        "approval_rate": approval_rate,
        "recent_docs": recent_docs,
        "pending_list": pending_list,
        "users_with_stats": users_with_stats,
        "chart_labels": chart_labels,
        "chart_data": chart_data,
        "recent_activity": recent_activity,
        **tl
    })
