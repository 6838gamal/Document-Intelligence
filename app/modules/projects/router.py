from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import require_auth, get_theme_lang
from app.core.models import Project

router = APIRouter(prefix="/projects", tags=["projects"])
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
async def projects(request: Request, db: Session = Depends(get_db), user=Depends(require_auth)):
    tl = get_theme_lang(request)
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    return templates.TemplateResponse("projects/index.html", {
        "request": request, "user": user, "projects": projects, **tl
    })
