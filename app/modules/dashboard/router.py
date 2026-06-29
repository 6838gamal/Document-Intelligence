from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.dependencies import require_auth, get_theme_lang
from app.core.models import Document, Approval, User, Workflow, DocumentStatus, ApprovalStatus

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db), user=Depends(require_auth)):
    tl = get_theme_lang(request)
    total_docs = db.query(Document).filter(Document.is_deleted == False).count()
    pending_approvals = db.query(Approval).filter(Approval.status == ApprovalStatus.PENDING).count()
    processed_docs = db.query(Document).filter(Document.status == DocumentStatus.APPROVED).count()
    active_workflows = db.query(Workflow).filter(Workflow.status == "active").count()
    recent_docs = db.query(Document).filter(Document.is_deleted == False).order_by(Document.created_at.desc()).limit(6).all()
    pending_list = (db.query(Approval).filter(Approval.status == ApprovalStatus.PENDING)
                    .join(Document).order_by(Approval.created_at.desc()).limit(5).all())

    return templates.TemplateResponse("dashboard/index.html", {
        "request": request, "user": user,
        "total_docs": total_docs,
        "pending_approvals": pending_approvals,
        "processed_docs": processed_docs,
        "active_workflows": active_workflows,
        "recent_docs": recent_docs,
        "pending_list": pending_list,
        "automation_rate": 78,
        "avg_processing_time": "2.4",
        **tl
    })
