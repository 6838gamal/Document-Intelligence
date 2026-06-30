from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta, timezone
import jwt

from app.core.database import get_db
from app.core.models import User, Document, Approval, Workflow, AuditLog, UserRole, ApprovalStatus
from app.core.security import verify_password, create_access_token
from app.core.config import settings

router = APIRouter(prefix="/api/v1", tags=["admin-api"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


# ── Auth ──────────────────────────────────────────────────────────
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_name: str
    user_role: str


def get_api_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_admin(current_user: User = Depends(get_api_user)) -> User:
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user


@router.post("/auth/token", response_model=TokenResponse)
async def api_login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="بيانات الدخول غير صحيحة",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({"sub": user.email})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_name=user.name,
        user_role=user.role
    )


# ── Stats ─────────────────────────────────────────────────────────
@router.get("/stats")
async def get_stats(db: Session = Depends(get_db), _=Depends(require_admin)):
    total_users = db.query(User).filter(User.is_active == True).count()
    total_docs = db.query(Document).filter(Document.is_deleted == False).count()
    pending_approvals = db.query(Approval).filter(Approval.status == ApprovalStatus.PENDING).count()
    active_workflows = db.query(Workflow).filter(Workflow.status == "active").count()
    approved_docs = db.query(Document).filter(Document.status == "approved").count()
    approval_rate = round((approved_docs / total_docs * 100) if total_docs > 0 else 0, 1)

    return {
        "total_users": total_users,
        "total_docs": total_docs,
        "pending_approvals": pending_approvals,
        "active_workflows": active_workflows,
        "approved_docs": approved_docs,
        "approval_rate": approval_rate,
    }


# ── Users ─────────────────────────────────────────────────────────
@router.get("/users")
async def get_users(db: Session = Depends(get_db), _=Depends(require_admin)):
    users = db.query(User).order_by(User.created_at.desc()).all()
    result = []
    for u in users:
        doc_count = db.query(Document).filter(Document.uploader_id == u.id, Document.is_deleted == False).count()
        last_log = (db.query(AuditLog).filter(AuditLog.user_id == u.id)
                    .order_by(AuditLog.created_at.desc()).first())
        result.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "department": u.department or "—",
            "is_active": u.is_active,
            "doc_count": doc_count,
            "last_active": last_log.created_at.isoformat() if last_log else None,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        })
    return {"users": result, "total": len(result)}


@router.patch("/users/{user_id}/toggle")
async def toggle_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="لا يمكنك تعطيل حسابك الخاص")
    user.is_active = not user.is_active
    db.commit()
    return {"id": user.id, "is_active": user.is_active}


# ── Productivity ──────────────────────────────────────────────────
@router.get("/productivity")
async def get_productivity(days: int = 14, db: Session = Depends(get_db), _=Depends(require_admin)):
    since = datetime.now(timezone.utc) - timedelta(days=days)

    docs_by_day = (
        db.query(cast(Document.created_at, Date).label("day"), func.count().label("count"))
        .filter(Document.created_at >= since, Document.is_deleted == False)
        .group_by(cast(Document.created_at, Date))
        .order_by(cast(Document.created_at, Date))
        .all()
    )
    approvals_by_day = (
        db.query(cast(Approval.created_at, Date).label("day"), func.count().label("count"))
        .filter(Approval.created_at >= since)
        .group_by(cast(Approval.created_at, Date))
        .order_by(cast(Approval.created_at, Date))
        .all()
    )

    docs_per_user = (
        db.query(User.name, func.count(Document.id).label("count"))
        .join(Document, Document.uploader_id == User.id)
        .filter(Document.is_deleted == False)
        .group_by(User.id, User.name)
        .order_by(func.count(Document.id).desc())
        .limit(10)
        .all()
    )

    return {
        "docs_timeline": [{"day": str(r.day), "count": r.count} for r in docs_by_day],
        "approvals_timeline": [{"day": str(r.day), "count": r.count} for r in approvals_by_day],
        "docs_per_user": [{"name": r.name, "count": r.count} for r in docs_per_user],
    }


# ── Recent activity ───────────────────────────────────────────────
@router.get("/activity")
async def get_activity(limit: int = 20, db: Session = Depends(get_db), _=Depends(require_admin)):
    logs = (
        db.query(AuditLog, User.name.label("user_name"))
        .join(User, AuditLog.user_id == User.id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "activity": [
            {
                "id": log.AuditLog.id,
                "action": log.AuditLog.action,
                "resource_type": log.AuditLog.resource_type,
                "user_name": log.user_name,
                "ip_address": log.AuditLog.ip_address,
                "created_at": log.AuditLog.created_at.isoformat() if log.AuditLog.created_at else None,
            }
            for log in logs
        ]
    }
