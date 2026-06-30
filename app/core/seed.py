from sqlalchemy.orm import Session
from app.core.models import User, UserRole
from app.core.security import get_password_hash


def seed_database(db: Session):
    if db.query(User).count() > 0:
        return

    admin = User(
        name="أحمد الراشدي",
        email="admin@dociq.io",
        hashed_password=get_password_hash("admin123"),
        role=UserRole.SUPER_ADMIN,
        department="الإدارة العليا",
        language="ar",
        theme="light",
    )
    db.add(admin)
    db.commit()
