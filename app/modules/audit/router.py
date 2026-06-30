from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import require_auth, get_theme_lang
from app.core.models import AuditLog

router = APIRouter(prefix="/audit", tags=["audit"])
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
async def audit_trail(request: Request, db: Session = Depends(get_db), user=Depends(require_auth)):
    tl = get_theme_lang(request)
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(100).all()
    return templates.TemplateResponse("audit/trail.html", {
        "request": request, "user": user, "logs": logs, **tl
    })
