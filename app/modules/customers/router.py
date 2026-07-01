import asyncio
import logging
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.core.dependencies import require_auth, get_theme_lang
from app.core.models import Customer, Document, AuditLog

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/customers", tags=["customers"])
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
async def customers_list(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_auth),
):
    tl = get_theme_lang(request)
    customers = db.query(Customer).order_by(Customer.created_at.desc()).all()
    return templates.TemplateResponse("customers/index.html", {
        "request": request, "user": user, "customers": customers, **tl,
    })


@router.get("/{customer_id}", response_class=HTMLResponse)
async def customer_profile(
    request: Request,
    customer_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_auth),
):
    tl = get_theme_lang(request)
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        return RedirectResponse(url="/customers")

    docs = (
        db.query(Document)
        .filter(
            Document.is_deleted == False,
            or_(
                Document.customer_id == customer_id,
                Document.title.ilike(f"%{customer.name}%"),
            ),
        )
        .order_by(Document.created_at.desc())
        .limit(20)
        .all()
    )

    processed_docs = sum(1 for d in docs if d.extracted_text)
    high_risk_docs = sum(1 for d in docs if d.fraud_risk == "high")
    doc_types = {}
    for d in docs:
        t = d.document_type or d.category or "أخرى"
        doc_types[t] = doc_types.get(t, 0) + 1

    return templates.TemplateResponse("customers/profile.html", {
        "request": request, "user": user, "customer": customer,
        "docs": docs, "total_docs": len(docs),
        "processed_docs": processed_docs,
        "high_risk_docs": high_risk_docs,
        "doc_types": doc_types,
        **tl,
    })


@router.post("/{customer_id}/ai-insights")
async def generate_customer_insights(
    request: Request,
    customer_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_auth),
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        return JSONResponse({"error": "العميل غير موجود"}, status_code=404)

    docs = (
        db.query(Document)
        .filter(
            Document.is_deleted == False,
            Document.extracted_text.isnot(None),
            or_(
                Document.customer_id == customer_id,
                Document.title.ilike(f"%{customer.name}%"),
            ),
        )
        .limit(5)
        .all()
    )

    if not docs:
        return JSONResponse({
            "insights": "لا توجد مستندات مُعالَجة لهذا العميل بعد. ارفع مستندات مرتبطة بالعميل وقم بتحليلها أولاً.",
            "doc_count": 0,
        })

    combined = "\n\n---\n\n".join(
        f"[{d.title} | {d.document_type or d.category}]\n{(d.extracted_text or '')[:1500]}"
        for d in docs
    )

    question = f"""أنت محلل أعمال متخصص. بناءً على مستندات العميل التالية، قدم:
1. ملخصاً تنفيذياً موجزاً للعلاقة التجارية مع هذا العميل
2. أبرز 3 نقاط مستخلصة من المستندات
3. أي مخاطر أو ملاحظات جديرة بالاهتمام

العميل: {customer.name} ({customer.company or 'غير محدد'})
القطاع: {customer.sector or 'غير محدد'}
قيمة العقود: {customer.contract_value or 0:,.0f} ريال

أجب باللغة العربية بشكل منظم واحترافي."""

    from app.services.ai_service import answer_question
    insights = await asyncio.to_thread(answer_question, combined, question, customer.name)

    db.add(AuditLog(
        user_id=user.id, action="CUSTOMER_AI_INSIGHTS",
        resource_type="customer", resource_id=str(customer_id),
        after_data={"doc_count": len(docs)},
        ip_address=request.client.host if request.client else None,
    ))
    db.commit()

    return JSONResponse({"insights": insights, "doc_count": len(docs)})


@router.post("/{customer_id}/chat")
async def chat_with_customer_docs(
    request: Request,
    customer_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_auth),
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        return JSONResponse({"error": "العميل غير موجود"}, status_code=404)

    body = await request.json()
    question = body.get("question", "").strip()
    if not question:
        return JSONResponse({"error": "السؤال فارغ"}, status_code=400)

    docs = (
        db.query(Document)
        .filter(
            Document.is_deleted == False,
            Document.extracted_text.isnot(None),
            or_(
                Document.customer_id == customer_id,
                Document.title.ilike(f"%{customer.name}%"),
            ),
        )
        .limit(5)
        .all()
    )

    if not docs:
        return JSONResponse({
            "answer": "لا توجد مستندات مُعالَجة لهذا العميل بعد.",
            "question": question,
        })

    combined = "\n\n---\n\n".join(
        f"[{d.title}]\n{(d.extracted_text or '')[:2000]}" for d in docs
    )

    from app.services.ai_service import answer_question
    answer = await asyncio.to_thread(answer_question, combined, question, customer.name)

    db.add(AuditLog(
        user_id=user.id, action="CUSTOMER_CHAT",
        resource_type="customer", resource_id=str(customer_id),
        after_data={"question": question[:200]},
        ip_address=request.client.host if request.client else None,
    ))
    db.commit()

    return JSONResponse({"answer": answer, "question": question})
