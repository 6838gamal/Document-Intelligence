from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import require_auth, get_theme_lang
from app.core.models import User

router = APIRouter(prefix="/users", tags=["users"])
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
async def user_management(request: Request, db: Session = Depends(get_db), user=Depends(require_auth)):
    tl = get_theme_lang(request)
    users = db.query(User).order_by(User.created_at.desc()).all()
    return templates.TemplateResponse("users/management.html", {
        "request": request, "user": user, "users": users, **tl
    })


@router.get("/roles", response_class=HTMLResponse)
async def roles_permissions(request: Request, user=Depends(require_auth)):
    tl = get_theme_lang(request)
    return templates.TemplateResponse("users/roles.html", {"request": request, "user": user, **tl})
