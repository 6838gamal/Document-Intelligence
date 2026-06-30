from fastapi import Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token
from app.core.models import User
from typing import Optional


def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    token = request.cookies.get("access_token")
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    user = db.query(User).filter(User.email == payload.get("sub")).first()
    return user


def require_auth(request: Request, db: Session = Depends(get_db)) -> User:
    user = get_current_user_optional(request, db)
    if not user:
        raise HTTPException(status_code=302, headers={"Location": "/auth/login"})
    return user


def get_theme_lang(request: Request):
    theme = request.cookies.get("theme", "light")
    lang = request.cookies.get("lang", "ar")
    return {"theme": theme, "lang": lang, "dir": "rtl" if lang == "ar" else "ltr"}
