from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.database import get_db
from app.core.dependencies import require_auth, get_theme_lang
from app.core.models import Document, KnowledgeArticle
from typing import Optional

router = APIRouter(prefix="/search", tags=["search"])
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
async def search_page(request: Request, db: Session = Depends(get_db), user=Depends(require_auth),
                      q: Optional[str] = None):
    tl = get_theme_lang(request)
    doc_results = []
    kb_results = []
    if q:
        doc_results = db.query(Document).filter(
            or_(Document.title.ilike(f"%{q}%"), Document.category.ilike(f"%{q}%"))
        ).limit(10).all()
        kb_results = db.query(KnowledgeArticle).filter(
            or_(KnowledgeArticle.title.ilike(f"%{q}%"), KnowledgeArticle.content.ilike(f"%{q}%"))
        ).limit(5).all()
    return templates.TemplateResponse("search/index.html", {
        "request": request, "user": user,
        "query": q, "doc_results": doc_results, "kb_results": kb_results,
        "total_results": len(doc_results) + len(kb_results), **tl
    })
