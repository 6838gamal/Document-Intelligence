from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.core.dependencies import require_auth, get_theme_lang

router = APIRouter(prefix="/integrations", tags=["integrations"])
templates = Jinja2Templates(directory="templates")

INTEGRATIONS = [
    {"name": "SAP ERP", "category": "ERP", "status": "connected", "icon": "🏢", "desc": "تكامل مع نظام SAP للموارد المؤسسية"},
    {"name": "Microsoft SharePoint", "category": "Storage", "status": "connected", "icon": "📁", "desc": "مزامنة المستندات مع SharePoint"},
    {"name": "DocuSign", "category": "Signature", "status": "disconnected", "icon": "✍️", "desc": "التوقيع الإلكتروني عبر DocuSign"},
    {"name": "Slack", "category": "Communication", "status": "connected", "icon": "💬", "desc": "إشعارات وتنبيهات عبر Slack"},
    {"name": "Power BI", "category": "Analytics", "status": "disconnected", "icon": "📊", "desc": "لوحات تحليلية متقدمة عبر Power BI"},
    {"name": "Oracle Financials", "category": "Finance", "status": "disconnected", "icon": "💰", "desc": "تكامل مع Oracle للمالية"},
    {"name": "Zoom", "category": "Communication", "status": "connected", "icon": "📹", "desc": "جدولة اجتماعات الاعتماد عبر Zoom"},
    {"name": "SFTP Server", "category": "Storage", "status": "connected", "icon": "🔒", "desc": "نقل آمن للملفات عبر SFTP"},
]


@router.get("", response_class=HTMLResponse)
async def integrations(request: Request, user=Depends(require_auth)):
    tl = get_theme_lang(request)
    return templates.TemplateResponse("integrations/index.html", {
        "request": request, "user": user, "integrations": INTEGRATIONS, **tl
    })
