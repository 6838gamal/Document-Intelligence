---
name: DocIQ AI Pipeline Architecture
description: How the Gemini AI document pipeline works — file storage, background processing, schema migration, chat endpoint.
---

# DocIQ AI Pipeline

## File Storage
- Files saved to `uploads/{uuid}.{ext}` — `file_uuid` column stores UUID stem (no ext)
- `_get_file_path(uuid)` scans uploads/ to find file with that stem — handles any extension
- Served at `GET /documents/{id}/file` via FastAPI FileResponse

## Background Processing
- `_run_ai_pipeline(doc_id, content, filename, title)` runs in `asyncio.to_thread()`
- Called via `asyncio.create_task(asyncio.to_thread(...))` right after DB commit — non-blocking
- Opens its own `SessionLocal()` — does NOT reuse the request's session (which gets closed)
- Sets doc.status = PROCESSING before background task; REVIEWED on success, UPLOADED on failure

## Schema Migration
- `_run_schema_migrations()` runs at startup AFTER `create_all()` in lifespan
- Uses try/except per ALTER TABLE statement — safe for both SQLite and PostgreSQL
- New columns: extracted_text (Text), document_type (VARCHAR 100), fraud_risk (VARCHAR 20), file_uuid (VARCHAR 200)

## Chat Endpoint
- `POST /documents/{id}/chat` accepts JSON `{question: "..."}`, returns `{answer, question}`
- Uses full `doc.extracted_text` for RAG — no chunking needed for typical docs
- Alpine.js frontend handles the chat UI client-side with x-data

## AI Services
- `app/services/ai_service.py` — Gemini AI: classify, extract fields, summarize, fraud detect, Q&A
- `app/services/text_extractor.py` — extracts text from PDF (pypdf), images (Gemini Vision OCR), DOCX, XLSX, TXT
- GEMINI_API_KEY stored as Replit env var

**Why:** Background thread approach avoids blocking the HTTP response while Gemini processes (can take 5-30s). Separate DB session is critical — request session is closed by time thread runs.

**How to apply:** Any new AI feature should use `asyncio.to_thread()` + its own `SessionLocal()` inside the thread function.
