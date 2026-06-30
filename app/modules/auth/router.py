from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.core.database import get_db
from app.core.models import User, UserRole
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.dependencies import get_theme_lang

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    tl = get_theme_lang(request)
    return templates.TemplateResponse("auth/login.html", {"request": request, **tl})


@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        tl = get_theme_lang(request)
        return templates.TemplateResponse("auth/login.html", {
            "request": request, "error": "بيانات الدخول غير صحيحة", **tl
        }, status_code=400)

    token = create_access_token({"sub": user.email})
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie("access_token", token, httponly=True, max_age=86400)
    response.set_cookie("lang", user.language, max_age=86400)
    response.set_cookie("theme", user.theme, max_age=86400)
    return response


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    department: Optional[str] = None


@router.post("/register")
async def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if len(data.password) < 8:
        raise HTTPException(status_code=400, detail="كلمة المرور يجب أن تكون ٨ أحرف على الأقل")
    existing = db.query(User).filter(User.email == data.email.lower().strip()).first()
    if existing:
        raise HTTPException(status_code=409, detail="البريد الإلكتروني مسجل مسبقاً")
    user = User(
        name=data.name.strip(),
        email=data.email.lower().strip(),
        hashed_password=get_password_hash(data.password),
        role=UserRole.VIEWER,
        department=data.department,
        is_active=True,
        language="ar",
        theme="light",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return JSONResponse({"message": "تم إنشاء الحساب بنجاح", "user_id": user.id}, status_code=201)


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/auth/login", status_code=302)
    response.delete_cookie("access_token")
    # Prevent browser from caching this redirect — ensures back button re-validates with server
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@router.post("/set-theme")
async def set_theme(request: Request, theme: str = Form(...)):
    response = RedirectResponse(url=request.headers.get("referer", "/dashboard"), status_code=302)
    response.set_cookie("theme", theme, max_age=86400 * 30)
    return response


@router.post("/set-lang")
async def set_lang(request: Request, lang: str = Form(...)):
    response = RedirectResponse(url=request.headers.get("referer", "/dashboard"), status_code=302)
    response.set_cookie("lang", lang, max_age=86400 * 30)
    return response
