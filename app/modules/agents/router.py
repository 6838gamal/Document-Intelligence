from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.core.dependencies import require_auth, get_theme_lang

router = APIRouter(prefix="/agents", tags=["agents"])
templates = Jinja2Templates(directory="templates")

AGENTS = [
    {"id": 1, "name": "Document Agent", "name_ar": "وكيل المستندات", "status": "active",
     "description": "استخراج وتصنيف بيانات المستندات تلقائياً", "tasks_today": 47,
     "success_rate": 96.2, "avg_time": "1.8s", "icon": "file-text", "color": "blue"},
    {"id": 2, "name": "Approval Agent", "name_ar": "وكيل الاعتماد", "status": "active",
     "description": "توجيه وإدارة مسارات الاعتماد الذكية", "tasks_today": 23,
     "success_rate": 99.1, "avg_time": "0.5s", "icon": "check-circle", "color": "green"},
    {"id": 3, "name": "Search Agent", "name_ar": "وكيل البحث", "status": "active",
     "description": "البحث الدلالي والهجين عبر قاعدة المعرفة", "tasks_today": 312,
     "success_rate": 94.7, "avg_time": "0.3s", "icon": "search", "color": "purple"},
    {"id": 4, "name": "Analytics Agent", "name_ar": "وكيل التحليلات", "status": "idle",
     "description": "تحليل الأداء واستخراج الأنماط التشغيلية", "tasks_today": 8,
     "success_rate": 98.5, "avg_time": "3.2s", "icon": "bar-chart-2", "color": "orange"},
    {"id": 5, "name": "Compliance Agent", "name_ar": "وكيل الامتثال", "status": "active",
     "description": "مراقبة الامتثال التنظيمي وتنبيه المخاطر", "tasks_today": 15,
     "success_rate": 100.0, "avg_time": "2.1s", "icon": "shield", "color": "red"},
    {"id": 6, "name": "Knowledge Agent", "name_ar": "وكيل المعرفة", "status": "idle",
     "description": "تحديث قاعدة المعرفة وإنشاء المحتوى", "tasks_today": 4,
     "success_rate": 97.3, "avg_time": "4.5s", "icon": "brain", "color": "teal"},
]


@router.get("", response_class=HTMLResponse)
async def agents_center(request: Request, user=Depends(require_auth)):
    tl = get_theme_lang(request)
    return templates.TemplateResponse("agents/index.html", {
        "request": request, "user": user, "agents": AGENTS, **tl
    })
