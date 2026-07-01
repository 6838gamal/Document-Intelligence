import os
import uuid
import asyncio
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.core.dependencies import require_auth, get_theme_lang
from app.core.models import Document, DocumentStatus, Approval, ApprovalStatus, AuditLog

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])
templates = Jinja2Templates(directory="templates")

UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".txt", ".png", ".jpg", ".jpeg", ".webp"}
MAX_SIZE_MB = 50


def _get_file_path(file_uuid: str) -> Optional[Path]:
    if not file_uuid:
        return None
    for f in UPLOADS_DIR.iterdir():
        if f.stem == file_uuid:
            return f
    return None


def _run_ai_pipeline(doc_id: int, content: bytes, filename: str, title: str):
    """Run full AI pipeline and update DB. Designed to run in a thread."""
    from app.core.database import SessionLocal
    from app.services.text_extractor import extract_text
    from app.services.ai_service import process_document_pipeline

    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            return

        text, page_count = extract_text(content, filename)
        result = process_document_pipeline(text, title, filename)

        classification = result.get("classification", {})
        extracted = result.get("extracted_fields", {})
        summary = result.get("summary", "")
        fraud = result.get("fraud", {})

        confidence = float(classification.get("confidence", 0))

        doc.extracted_text = text
        doc.document_type = classification.get("type", "أخرى")
        doc.confidence_score = confidence
        doc.extracted_data = extracted
        doc.summary = summary
        doc.fraud_risk = fraud.get("risk_level", "unknown")
        doc.page_count = page_count
        doc.status = DocumentStatus.REVIEWED
        db.commit()
        logger.info(f"AI pipeline complete for doc {doc_id}: {doc.document_type} ({confidence}%)")
    except Exception as e:
        logger.error(f"AI pipeline failed for doc {doc_id}: {e}")
        try:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if doc:
                doc.status = DocumentStatus.UPLOADED
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


@router.get("", response_class=HTMLResponse)
async def document_list(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_auth),
    search: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    doc_type: Optional[str] = None,
    page: int = 1,
):
    tl = get_theme_lang(request)
    q = db.query(Document).filter(Document.is_deleted == False)
    if search:
        q = q.filter(or_(
            Document.title.ilike(f"%{search}%"),
            Document.category.ilike(f"%{search}%"),
            Document.document_type.ilike(f"%{search}%"),
            Document.extracted_text.ilike(f"%{search}%"),
        ))
    if status:
        q = q.filter(Document.status == status)
    if category:
        q = q.filter(Document.category == category)
    if doc_type:
        q = q.filter(Document.document_type == doc_type)

    total = q.count()
    docs = q.order_by(Document.created_at.desc()).offset((page - 1) * 10).limit(10).all()
    categories = [r[0] for r in db.query(Document.category).distinct().all() if r[0]]
    doc_types = [r[0] for r in db.query(Document.document_type).distinct().all() if r[0]]

    return templates.TemplateResponse("documents/list.html", {
        "request": request, "user": user, "documents": docs,
        "total": total, "page": page, "pages": (total + 9) // 10,
        "search": search, "filter_status": status, "filter_category": category,
        "filter_doc_type": doc_type,
        "categories": categories, "doc_types": doc_types,
        "statuses": [e.value for e in DocumentStatus], **tl,
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
    user=Depends(require_auth),
):
    tl = get_theme_lang(request)
    file_name = "بدون ملف"
    file_type = "UNKNOWN"
    file_size = 0
    file_uuid_val = None
    content = b""

    if file and file.filename:
        content = await file.read()
        file_size = len(content)

        if file_size > MAX_SIZE_MB * 1024 * 1024:
            return templates.TemplateResponse("documents/upload.html", {
                "request": request, "user": user,
                "error": f"حجم الملف يتجاوز الحد المسموح ({MAX_SIZE_MB} MB)", **tl,
            }, status_code=400)

        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            return templates.TemplateResponse("documents/upload.html", {
                "request": request, "user": user,
                "error": f"نوع الملف غير مدعوم. الأنواع المدعومة: {', '.join(ALLOWED_EXTENSIONS)}", **tl,
            }, status_code=400)

        file_uuid_val = str(uuid.uuid4())
        saved_path = UPLOADS_DIR / f"{file_uuid_val}{ext}"
        saved_path.write_bytes(content)

        file_name = file.filename
        file_type = ext.lstrip(".").upper()

    doc = Document(
        title=title,
        category=category,
        file_name=file_name,
        file_uuid=file_uuid_val,
        file_type=file_type,
        file_size=file_size,
        file_path=str(UPLOADS_DIR / f"{file_uuid_val}{Path(file_name).suffix.lower()}") if file_uuid_val else None,
        status=DocumentStatus.PROCESSING,
        confidence_score=0.0,
        uploader_id=user.id,
        page_count=1,
    )
    db.add(doc)
    db.flush()
    doc_id = doc.id

    log = AuditLog(
        user_id=user.id,
        action="UPLOAD_DOCUMENT",
        resource_type="document",
        resource_id=str(doc_id),
        after_data={"title": title, "category": category, "file_name": file_name},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(log)
    db.commit()

    if content and file_uuid_val:
        asyncio.create_task(
            asyncio.to_thread(_run_ai_pipeline, doc_id, content, file_name, title)
        )

    return RedirectResponse(url=f"/documents/{doc_id}", status_code=302)


@router.get("/{doc_id}/file")
async def serve_file(doc_id: int, db: Session = Depends(get_db), user=Depends(require_auth)):
    doc = db.query(Document).filter(Document.id == doc_id, Document.is_deleted == False).first()
    if not doc or not doc.file_uuid:
        return JSONResponse({"error": "الملف غير موجود"}, status_code=404)
    file_path = _get_file_path(doc.file_uuid)
    if not file_path or not file_path.exists():
        return JSONResponse({"error": "الملف غير موجود على الخادم"}, status_code=404)

    media_types = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".txt": "text/plain",
    }
    media_type = media_types.get(file_path.suffix.lower(), "application/octet-stream")
    return FileResponse(str(file_path), media_type=media_type, filename=doc.file_name)


@router.post("/{doc_id}/process")
async def reprocess_document(
    doc_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_auth),
):
    doc = db.query(Document).filter(Document.id == doc_id, Document.is_deleted == False).first()
    if not doc:
        return JSONResponse({"error": "المستند غير موجود"}, status_code=404)

    if not doc.file_uuid:
        return JSONResponse({"error": "لا يوجد ملف لإعادة المعالجة"}, status_code=400)

    file_path = _get_file_path(doc.file_uuid)
    if not file_path or not file_path.exists():
        return JSONResponse({"error": "الملف غير موجود على الخادم"}, status_code=404)

    doc.status = DocumentStatus.PROCESSING
    db.commit()

    content = file_path.read_bytes()
    asyncio.create_task(
        asyncio.to_thread(_run_ai_pipeline, doc_id, content, doc.file_name, doc.title)
    )

    return JSONResponse({"message": "بدأت إعادة المعالجة", "status": "processing"})


@router.post("/{doc_id}/chat")
async def chat_with_document(
    request: Request,
    doc_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_auth),
):
    doc = db.query(Document).filter(Document.id == doc_id, Document.is_deleted == False).first()
    if not doc:
        return JSONResponse({"error": "المستند غير موجود"}, status_code=404)

    body = await request.json()
    question = body.get("question", "").strip()
    if not question:
        return JSONResponse({"error": "السؤال فارغ"}, status_code=400)

    text = doc.extracted_text or ""
    if not text:
        return JSONResponse({
            "answer": "لا يوجد نص مستخرج من هذا المستند. يرجى معالجة المستند أولاً.",
            "question": question,
        })

    from app.services.ai_service import answer_question
    answer = await asyncio.to_thread(answer_question, text, question, doc.title)

    log = AuditLog(
        user_id=user.id,
        action="CHAT_WITH_DOCUMENT",
        resource_type="document",
        resource_id=str(doc_id),
        after_data={"question": question[:200]},
        ip_address=request.client.host if request.client else None,
    )
    db.add(log)
    db.commit()

    return JSONResponse({"answer": answer, "question": question})


@router.post("/{doc_id}/approve")
async def approve_document(
    request: Request,
    doc_id: int,
    notes: str = Form(""),
    db: Session = Depends(get_db),
    user=Depends(require_auth),
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        return RedirectResponse(url="/documents", status_code=302)

    doc.status = DocumentStatus.APPROVED
    approval = Approval(
        document_id=doc_id,
        approver_id=user.id,
        status=ApprovalStatus.APPROVED,
        notes=notes,
    )
    db.add(approval)
    log = AuditLog(
        user_id=user.id, action="APPROVE_DOCUMENT",
        resource_type="document", resource_id=str(doc_id),
        ip_address=request.client.host if request.client else None,
    )
    db.add(log)
    db.commit()
    return RedirectResponse(url=f"/documents/{doc_id}", status_code=302)


@router.post("/{doc_id}/reject")
async def reject_document(
    request: Request,
    doc_id: int,
    notes: str = Form(""),
    db: Session = Depends(get_db),
    user=Depends(require_auth),
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        return RedirectResponse(url="/documents", status_code=302)

    doc.status = DocumentStatus.REJECTED
    approval = Approval(
        document_id=doc_id,
        approver_id=user.id,
        status=ApprovalStatus.REJECTED,
        notes=notes,
    )
    db.add(approval)
    log = AuditLog(
        user_id=user.id, action="REJECT_DOCUMENT",
        resource_type="document", resource_id=str(doc_id),
        ip_address=request.client.host if request.client else None,
    )
    db.add(log)
    db.commit()
    return RedirectResponse(url=f"/documents/{doc_id}", status_code=302)


@router.post("/{doc_id}/send-approval")
async def send_for_approval(
    request: Request,
    doc_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_auth),
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if doc:
        doc.status = DocumentStatus.PENDING_APPROVAL
        approval = Approval(
            document_id=doc_id,
            approver_id=user.id,
            status=ApprovalStatus.PENDING,
        )
        db.add(approval)
        db.commit()
    return RedirectResponse(url=f"/documents/{doc_id}/review", status_code=302)


@router.post("/{doc_id}/delete")
async def delete_document(
    request: Request,
    doc_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_auth),
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
async def document_detail(
    request: Request,
    doc_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_auth),
):
    tl = get_theme_lang(request)
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        return RedirectResponse(url="/documents")
    approvals = db.query(Approval).filter(Approval.document_id == doc_id).all()
    return templates.TemplateResponse("documents/detail.html", {
        "request": request, "user": user, "doc": doc, "approvals": approvals, **tl,
    })


@router.get("/{doc_id}/review", response_class=HTMLResponse)
async def ai_review(
    request: Request,
    doc_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_auth),
):
    tl = get_theme_lang(request)
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        return RedirectResponse(url="/documents")

    has_file = bool(doc.file_uuid and _get_file_path(doc.file_uuid))
    is_image = doc.file_type and doc.file_type.lower() in {"png", "jpg", "jpeg", "webp"}
    is_pdf = doc.file_type and doc.file_type.lower() == "pdf"

    return templates.TemplateResponse("documents/ai_review.html", {
        "request": request, "user": user, "doc": doc,
        "has_file": has_file, "is_image": is_image, "is_pdf": is_pdf, **tl,
    })
