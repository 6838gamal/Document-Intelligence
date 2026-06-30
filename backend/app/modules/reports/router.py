from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.dependencies import require_auth, get_theme_lang
from app.core.models import Document, Approval, DocumentStatus, ApprovalStatus

router = APIRouter(prefix="/reports", tags=["reports"])
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
async def reports(request: Request, db: Session = Depends(get_db), user=Depends(require_auth)):
    tl = get_theme_lang(request)
    status_counts = dict(db.query(Document.status, func.count(Document.id))
                         .group_by(Document.status).all())
    category_counts = dict(db.query(Document.category, func.count(Document.id))
                           .group_by(Document.category).filter(Document.category != None).all())
    total = db.query(Document).count()
    approved = db.query(Document).filter(Document.status == DocumentStatus.APPROVED).count()
    automation_rate = round((approved / total * 100) if total else 0, 1)
    return templates.TemplateResponse("reports/index.html", {
        "request": request, "user": user,
        "status_counts": status_counts,
        "category_counts": category_counts,
        "automation_rate": automation_rate,
        "total_docs": total, **tl
    })
