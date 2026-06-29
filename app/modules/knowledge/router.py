from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import require_auth, get_theme_lang
from app.core.models import KnowledgeArticle

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
async def knowledge_base(request: Request, db: Session = Depends(get_db), user=Depends(require_auth)):
    tl = get_theme_lang(request)
    articles = db.query(KnowledgeArticle).filter(KnowledgeArticle.is_published == True).order_by(
        KnowledgeArticle.view_count.desc()).all()
    collections = list(set(a.collection for a in articles if a.collection))
    return templates.TemplateResponse("knowledge/index.html", {
        "request": request, "user": user, "articles": articles, "collections": collections, **tl
    })
