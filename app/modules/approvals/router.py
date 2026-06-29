from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import require_auth, get_theme_lang
from app.core.models import Approval, ApprovalStatus, Document, AuditLog
from datetime import datetime

router = APIRouter(prefix="/approvals", tags=["approvals"])
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
async def approvals_inbox(request: Request, db: Session = Depends(get_db), user=Depends(require_auth)):
    tl = get_theme_lang(request)
    pending = (db.query(Approval).filter(Approval.status == ApprovalStatus.PENDING)
               .join(Document).order_by(Approval.created_at.desc()).all())
    approved = (db.query(Approval).filter(Approval.status == ApprovalStatus.APPROVED)
                .join(Document).order_by(Approval.completed_at.desc()).limit(10).all())
    rejected = (db.query(Approval).filter(Approval.status == ApprovalStatus.REJECTED)
                .join(Document).order_by(Approval.completed_at.desc()).limit(10).all())
    return templates.TemplateResponse("approvals/inbox.html", {
        "request": request, "user": user,
        "pending": pending, "approved": approved, "rejected": rejected, **tl
    })


@router.post("/{approval_id}/approve")
async def approve(approval_id: int, notes: str = Form(""), db: Session = Depends(get_db), user=Depends(require_auth)):
    approval = db.query(Approval).filter(Approval.id == approval_id).first()
    if approval:
        approval.status = ApprovalStatus.APPROVED
        approval.notes = notes
        approval.completed_at = datetime.utcnow()
        if approval.document:
            approval.document.status = "approved"
        log = AuditLog(user_id=user.id, action="APPROVE_DOCUMENT",
                       resource_type="approval", resource_id=str(approval_id),
                       after_data={"status": "approved", "notes": notes})
        db.add(log)
        db.commit()
    return RedirectResponse(url="/approvals", status_code=302)


@router.post("/{approval_id}/reject")
async def reject(approval_id: int, notes: str = Form(""), db: Session = Depends(get_db), user=Depends(require_auth)):
    approval = db.query(Approval).filter(Approval.id == approval_id).first()
    if approval:
        approval.status = ApprovalStatus.REJECTED
        approval.notes = notes
        approval.completed_at = datetime.utcnow()
        if approval.document:
            approval.document.status = "rejected"
        db.commit()
    return RedirectResponse(url="/approvals", status_code=302)
