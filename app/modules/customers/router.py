from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import require_auth, get_theme_lang
from app.core.models import Customer

router = APIRouter(prefix="/customers", tags=["customers"])
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
async def customers(request: Request, db: Session = Depends(get_db), user=Depends(require_auth)):
    tl = get_theme_lang(request)
    customers = db.query(Customer).order_by(Customer.created_at.desc()).all()
    return templates.TemplateResponse("customers/index.html", {
        "request": request, "user": user, "customers": customers, **tl
    })
