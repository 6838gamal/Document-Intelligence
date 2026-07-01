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
async def search_page(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_auth),
    q: Optional[str] = None,
    search_type: Optional[str] = "all",
):
    tl = get_theme_lang(request)
    doc_results = []
    kb_results = []

    if q and q.strip():
        q = q.strip()

        if search_type in ("all", "documents"):
            doc_results = (
                db.query(Document)
                .filter(
                    Document.is_deleted == False,
                    or_(
                        Document.title.ilike(f"%{q}%"),
                        Document.category.ilike(f"%{q}%"),
                        Document.document_type.ilike(f"%{q}%"),
                        Document.summary.ilike(f"%{q}%"),
                        Document.extracted_text.ilike(f"%{q}%"),
                    ),
                )
                .order_by(Document.created_at.desc())
                .limit(20)
                .all()
            )

        if search_type in ("all", "knowledge"):
            kb_results = (
                db.query(KnowledgeArticle)
                .filter(
                    KnowledgeArticle.is_published == True,
                    or_(
                        KnowledgeArticle.title.ilike(f"%{q}%"),
                        KnowledgeArticle.content.ilike(f"%{q}%"),
                    ),
                )
                .limit(10)
                .all()
            )

    return templates.TemplateResponse("search/index.html", {
        "request": request,
        "user": user,
        "query": q,
        "search_type": search_type,
        "doc_results": doc_results,
        "kb_results": kb_results,
        "total_results": len(doc_results) + len(kb_results),
        **tl,
    })
