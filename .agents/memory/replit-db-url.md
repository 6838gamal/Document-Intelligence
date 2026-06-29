---
name: Replit DATABASE_URL Auto-injection
description: Replit injects DATABASE_URL pointing to PostgreSQL; avoid conflicts with SQLite dev setup
---

## Problem
Replit automatically sets the `DATABASE_URL` environment variable to a PostgreSQL connection string when a DB integration is active (or sometimes even without one). If SQLAlchemy reads this via pydantic-settings, it tries to use psycopg2 which may not be installed.

## Fix
Use a custom environment variable name for the database URL (e.g. `DOCIQ_DATABASE_URL`) and read it with `os.environ.get("DOCIQ_DATABASE_URL", "sqlite:///./dociq.db")` directly in database.py — bypassing pydantic-settings which reads `DATABASE_URL` automatically.

**Why:** pydantic-settings `BaseSettings` reads all env vars by default, so any field named `DATABASE_URL` will pick up Replit's injected value.

**How to apply:** In any FastAPI/SQLAlchemy project on Replit, never use `DATABASE_URL` as the pydantic-settings field name if you want SQLite as the default dev DB.
