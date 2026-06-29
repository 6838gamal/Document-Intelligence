from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.models import User
from app.core.security import verify_password, create_access_token
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


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/auth/login", status_code=302)
    response.delete_cookie("access_token")
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
