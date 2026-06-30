from sqlalchemy.orm import Session
from app.core.models import User, UserRole
from app.core.security import get_password_hash


def seed_database(db: Session):
    if db.query(User).count() > 0:
        return

    users = [
        User(name="أحمد الراشدي", email="admin@dociq.io",
             hashed_password=get_password_hash("admin123"),
             role=UserRole.SUPER_ADMIN, department="الإدارة العليا",
             language="ar", theme="light"),
        User(name="سارة المنصوري", email="manager@dociq.io",
             hashed_password=get_password_hash("manager123"),
             role=UserRole.MANAGER, department="إدارة المستندات",
             language="ar", theme="light"),
    ]
    for u in users:
        db.add(u)
    db.commit()
