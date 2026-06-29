from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import require_auth, get_theme_lang
from app.core.models import Notification

router = APIRouter(prefix="/notifications", tags=["notifications"])
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
async def notifications(request: Request, db: Session = Depends(get_db), user=Depends(require_auth)):
    tl = get_theme_lang(request)
    notifs = db.query(Notification).filter(Notification.user_id == user.id).order_by(
        Notification.created_at.desc()).all()
    return templates.TemplateResponse("notifications/index.html", {
        "request": request, "user": user, "notifications": notifs, **tl
    })
