from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import require_auth, get_theme_lang
from app.core.models import Workflow

router = APIRouter(prefix="/workflows", tags=["workflows"])
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
async def workflows_list(request: Request, db: Session = Depends(get_db), user=Depends(require_auth)):
    tl = get_theme_lang(request)
    workflows = db.query(Workflow).order_by(Workflow.created_at.desc()).all()
    return templates.TemplateResponse("workflows/list.html", {
        "request": request, "user": user, "workflows": workflows, **tl
    })


@router.get("/builder", response_class=HTMLResponse)
async def workflow_builder(request: Request, user=Depends(require_auth)):
    tl = get_theme_lang(request)
    return templates.TemplateResponse("workflows/builder.html", {"request": request, "user": user, **tl})


@router.get("/builder/{wf_id}", response_class=HTMLResponse)
async def workflow_editor(request: Request, wf_id: int, db: Session = Depends(get_db), user=Depends(require_auth)):
    tl = get_theme_lang(request)
    wf = db.query(Workflow).filter(Workflow.id == wf_id).first()
    return templates.TemplateResponse("workflows/builder.html", {
        "request": request, "user": user, "workflow": wf, **tl
    })
