from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import require_auth, get_theme_lang, get_current_user_optional
from app.core.models import Notification, Approval, ApprovalStatus

router = APIRouter(prefix="/notifications", tags=["notifications"])
templates = Jinja2Templates(directory="templates")


@router.get("/count")
async def notifications_count(request: Request, db: Session = Depends(get_db)):
    """Lightweight JSON endpoint — returns real pending-approvals count + recent notifications.
    Used by base.html topbar badge. Returns zeros gracefully if not authenticated."""
    user = get_current_user_optional(request, db)
    if not user:
        return JSONResponse({"pending_approvals": 0, "notifications": []})

    pending = db.query(Approval).filter(Approval.status == ApprovalStatus.PENDING).count()

    recent = (
        db.query(Notification)
        .filter(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(5)
        .all()
    )
    items = [
        {
            "title": n.title,
            "type": n.type or "info",
            "url": n.action_url or "/notifications",
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in recent
    ]
    return JSONResponse({"pending_approvals": pending, "notifications": items})


@router.get("", response_class=HTMLResponse)
async def notifications(request: Request, db: Session = Depends(get_db), user=Depends(require_auth)):
    tl = get_theme_lang(request)
    notifs = db.query(Notification).filter(Notification.user_id == user.id).order_by(
        Notification.created_at.desc()).all()
    return templates.TemplateResponse("notifications/index.html", {
        "request": request, "user": user, "notifications": notifs, **tl
    })
