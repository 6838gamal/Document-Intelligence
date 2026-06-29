from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import require_auth, get_theme_lang
from app.core.models import Vendor

router = APIRouter(prefix="/vendors", tags=["vendors"])
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
async def vendors(request: Request, db: Session = Depends(get_db), user=Depends(require_auth)):
    tl = get_theme_lang(request)
    vendors = db.query(Vendor).order_by(Vendor.created_at.desc()).all()
    return templates.TemplateResponse("vendors/index.html", {
        "request": request, "user": user, "vendors": vendors, **tl
    })
