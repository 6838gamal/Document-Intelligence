---
name: Replit DATABASE_URL Auto-injection
description: Replit injects DATABASE_URL pointing to PostgreSQL; use DOCIQ_DATABASE_URL secret for project's own DB
---

## Problem
Replit automatically sets the `DATABASE_URL` environment variable to a PostgreSQL connection string. If SQLAlchemy reads this via pydantic-settings it conflicts with the project's own DB config.

## Fix
Use a custom env var name `DOCIQ_DATABASE_URL` (stored as a Replit Secret) and read it directly in database.py:
```python
DATABASE_URL = os.environ.get("DOCIQ_DATABASE_URL", "sqlite:///./dociq.db")
```
The project currently points to the user's Render PostgreSQL instance.

## PostgreSQL pool settings (remote DB)
Render closes idle connections after ~5 min. Use these engine kwargs for any remote PG connection:
```python
pool_pre_ping=True, pool_recycle=280, pool_size=5, max_overflow=10
```

**Why:** pydantic-settings `BaseSettings` reads all env vars by default, so any field named `DATABASE_URL` picks up Replit's injected value. Using a distinct name avoids the clash.

**How to apply:** In any FastAPI/SQLAlchemy project on Replit, never use `DATABASE_URL` as the pydantic-settings field name if you want to control which DB is used.
