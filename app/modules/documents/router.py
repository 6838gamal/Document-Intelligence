from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.database import get_db
from app.core.dependencies import require_auth, get_theme_lang
from app.core.models import Document, DocumentStatus, Approval, ApprovalStatus, AuditLog
from typing import Optional

router = APIRouter(prefix="/documents", tags=["documents"])
templates = Jinja2Templates(directory="templates")

ALLOWED_TYPES = {"application/pdf", "application/msword",
                 "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                 "application/vnd.ms-excel",
                 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                 "text/plain"}
MAX_SIZE_MB = 20


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
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    user=Depends(require_auth)
):
    file_name = "بدون ملف"
    file_type = "UNKNOWN"
    file_size = 0

    if file and file.filename:
        # Read metadata only — do NOT save to disk
        content = await file.read()
        file_size = len(content)

        if file_size > MAX_SIZE_MB * 1024 * 1024:
            tl = get_theme_lang(request)
            return templates.TemplateResponse("documents/upload.html", {
                "request": request, "user": user,
                "error": f"حجم الملف يتجاوز الحد المسموح ({MAX_SIZE_MB} MB)", **tl
            }, status_code=400)

        ext = file.filename.rsplit(".", 1)[-1].upper() if "." in file.filename else "UNKNOWN"
        file_name = file.filename
        file_type = ext
        # Content is processed in memory and not written to disk

    doc = Document(
        title=title,
        category=category,
        file_name=file_name,
        file_type=file_type,
        file_size=file_size,
        file_path=None,          # no disk path
        status=DocumentStatus.PROCESSING,
        confidence_score=0.0,
        uploader_id=user.id,
        page_count=1,
    )
    db.add(doc)
    db.flush()

    # Audit log
    log = AuditLog(
        user_id=user.id,
        action="UPLOAD_DOCUMENT",
        resource_type="document",
        resource_id=str(doc.id),
        after_data={"title": title, "category": category, "file_name": file_name},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(log)
    db.commit()

    return RedirectResponse(url=f"/documents/{doc.id}", status_code=302)


@router.post("/{doc_id}/delete")
async def delete_document(
    request: Request,
    doc_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_auth)
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if doc:
        doc.is_deleted = True
        log = AuditLog(
            user_id=user.id, action="DELETE_DOCUMENT",
            resource_type="document", resource_id=str(doc_id),
            ip_address=request.client.host if request.client else None,
        )
        db.add(log)
        db.commit()
    return RedirectResponse(url="/documents", status_code=302)


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
