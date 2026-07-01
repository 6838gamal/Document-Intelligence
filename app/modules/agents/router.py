import asyncio
import logging
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import require_auth, get_theme_lang
from app.core.models import Document, AuditLog

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])
templates = Jinja2Templates(directory="templates")

AGENTS = [
    {"id": 1, "name": "Document Agent",    "name_ar": "وكيل المستندات",    "status": "active",
     "description": "استخراج النص وتحليل المستندات باستخدام Gemini AI",
     "icon": "file-text", "color": "blue"},
    {"id": 2, "name": "OCR Agent",          "name_ar": "وكيل OCR",           "status": "active",
     "description": "استخراج النص من الصور والمستندات الممسوحة ضوئياً",
     "icon": "eye", "color": "indigo"},
    {"id": 3, "name": "Classification Agent","name_ar": "وكيل التصنيف",      "status": "active",
     "description": "تصنيف المستندات تلقائياً (فاتورة، عقد، تقرير...)",
     "icon": "tags", "color": "purple"},
    {"id": 4, "name": "Extraction Agent",   "name_ar": "وكيل الاستخراج",    "status": "active",
     "description": "استخراج الحقول المنظمة من المستندات",
     "icon": "database", "color": "teal"},
    {"id": 5, "name": "Search Agent",       "name_ar": "وكيل البحث",         "status": "active",
     "description": "البحث في محتوى المستندات والنص المستخرج",
     "icon": "search", "color": "green"},
    {"id": 6, "name": "RAG Agent",          "name_ar": "وكيل المعرفة (RAG)", "status": "active",
     "description": "الإجابة على الأسئلة من محتوى المستندات",
     "icon": "brain", "color": "orange"},
    {"id": 7, "name": "Validation Agent",   "name_ar": "وكيل التحقق",        "status": "active",
     "description": "كشف الاحتيال والتحقق من سلامة البيانات",
     "icon": "shield-check", "color": "red"},
    {"id": 8, "name": "Analytics Agent",   "name_ar": "وكيل التحليلات",     "status": "active",
     "description": "تحليل الأداء واستخراج الأنماط التشغيلية",
     "icon": "bar-chart-2", "color": "yellow"},
]


@router.get("", response_class=HTMLResponse)
async def agents_center(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_auth),
):
    tl = get_theme_lang(request)

    total_docs = db.query(Document).filter(Document.is_deleted == False).count()
    processed_docs = db.query(Document).filter(
        Document.is_deleted == False,
        Document.extracted_text.isnot(None),
    ).count()
    chat_count = db.query(AuditLog).filter(AuditLog.action == "CHAT_WITH_DOCUMENT").count()
    reprocess_count = db.query(AuditLog).filter(AuditLog.action == "REPROCESS_DOCUMENT").count()

    stats = {
        "total_docs": total_docs,
        "processed_docs": processed_docs,
        "chat_queries": chat_count,
        "reprocessed": reprocess_count,
    }

    return templates.TemplateResponse("agents/index.html", {
        "request": request,
        "user": user,
        "agents": AGENTS,
        "stats": stats,
        **tl,
    })


@router.post("/ask")
async def global_ask(request: Request, db: Session = Depends(get_db), user=Depends(require_auth)):
    """Global Q&A across all documents."""
    body = await request.json()
    question = body.get("question", "").strip()
    doc_ids = body.get("doc_ids", [])

    if not question:
        return JSONResponse({"error": "السؤال فارغ"}, status_code=400)

    q = db.query(Document).filter(
        Document.is_deleted == False,
        Document.extracted_text.isnot(None),
    )
    if doc_ids:
        q = q.filter(Document.id.in_(doc_ids))

    docs = q.order_by(Document.created_at.desc()).limit(5).all()

    if not docs:
        return JSONResponse({"answer": "لا توجد مستندات مُعالَجة للبحث فيها."})

    combined_text = "\n\n---\n\n".join(
        f"[{d.title}]\n{d.extracted_text[:2000]}" for d in docs
    )

    from app.services.ai_service import answer_question
    answer = await asyncio.to_thread(
        answer_question, combined_text, question, "قاعدة المستندات"
    )

    log = AuditLog(
        user_id=user.id,
        action="GLOBAL_ASK",
        resource_type="agents",
        resource_id="0",
        after_data={"question": question[:200], "doc_count": len(docs)},
        ip_address=request.client.host if request.client else None,
    )
    db.add(log)
    db.commit()

    return JSONResponse({"answer": answer, "sources": [d.title for d in docs]})
