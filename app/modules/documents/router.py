from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.database import get_db
from app.core.dependencies import require_auth, get_theme_lang
from app.core.models import Document, DocumentStatus, Approval, ApprovalStatus
from typing import Optional

router = APIRouter(prefix="/documents", tags=["documents"])
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
async def document_list(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_auth),
    search: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    page: int = 1
):
    tl = get_theme_lang(request)
    q = db.query(Document).filter(Document.is_deleted == False)
    if search:
        q = q.filter(or_(Document.title.ilike(f"%{search}%"), Document.category.ilike(f"%{search}%")))
    if status:
        q = q.filter(Document.status == status)
    if category:
        q = q.filter(Document.category == category)
    total = q.count()
    docs = q.order_by(Document.created_at.desc()).offset((page - 1) * 10).limit(10).all()
    categories = [r[0] for r in db.query(Document.category).distinct().all() if r[0]]
    return templates.TemplateResponse("documents/list.html", {
        "request": request, "user": user, "documents": docs,
        "total": total, "page": page, "pages": (total + 9) // 10,
        "search": search, "filter_status": status, "filter_category": category,
        "categories": categories, "statuses": [e.value for e in DocumentStatus], **tl
    })


@router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request, user=Depends(require_auth)):
    tl = get_theme_lang(request)
    return templates.TemplateResponse("documents/upload.html", {"request": request, "user": user, **tl})


@router.post("/upload")
async def upload_document(
    request: Request,
    title: str = Form(...),
    category: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(require_auth)
):
    doc = Document(title=title, category=category, file_name=f"{title}.pdf",
                   file_type="PDF", status=DocumentStatus.PROCESSING,
                   confidence_score=0.0, uploader_id=user.id, page_count=1)
    db.add(doc)
    db.commit()
    return RedirectResponse(url=f"/documents/{doc.id}", status_code=302)


@router.get("/{doc_id}", response_class=HTMLResponse)
async def document_detail(request: Request, doc_id: int, db: Session = Depends(get_db), user=Depends(require_auth)):
    tl = get_theme_lang(request)
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        return RedirectResponse(url="/documents")
    approvals = db.query(Approval).filter(Approval.document_id == doc_id).all()
    return templates.TemplateResponse("documents/detail.html", {
        "request": request, "user": user, "doc": doc, "approvals": approvals, **tl
    })


@router.get("/{doc_id}/review", response_class=HTMLResponse)
async def ai_review(request: Request, doc_id: int, db: Session = Depends(get_db), user=Depends(require_auth)):
    tl = get_theme_lang(request)
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        return RedirectResponse(url="/documents")
    return templates.TemplateResponse("documents/ai_review.html", {
        "request": request, "user": user, "doc": doc, **tl
    })
