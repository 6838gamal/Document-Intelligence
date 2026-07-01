import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = (
    os.environ.get("DOCIQ_DATABASE_URL")
    or os.environ.get("DATABASE_URL")
    or "sqlite:///./dociq.db"
)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {}
engine_kwargs = {}

if "sqlite" in DATABASE_URL:
    connect_args = {"check_same_thread": False}
else:
    # Remote PostgreSQL — keep connections alive and recycle them before
    # the server-side idle timeout drops them (Render closes idle at ~5 min).
    engine_kwargs = {
        "pool_pre_ping": True,   # test connection before using it
        "pool_recycle": 280,     # recycle every ~4.5 min
        "pool_size": 5,
        "max_overflow": 10,
    }

engine = create_engine(DATABASE_URL, connect_args=connect_args, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
