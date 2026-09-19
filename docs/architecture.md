# Architecture Documentation

## 1. Overall Architecture

The service follows a **layered, event-driven architecture**:

```
Client → FastAPI (HTTP) → PostgreSQL (metadata)
                      ↓ Celery task
               Redis Broker
                      ↓
               Celery Worker → Gemini Vision API → PostgreSQL (questions)
```

**Layers:**
- **API Layer** (`app/api/`): FastAPI routers, request validation, JWT auth, response serialisation.
- **Service Layer** (`app/services/`): Storage and AI extraction logic — no HTTP concerns.
- **Task Layer** (`app/tasks/`): Celery tasks that orchestrate the extraction pipeline.
- **Data Layer** (`app/models/`): SQLAlchemy ORM models.

---

## 2. Document Processing Approach

1. Client uploads a file via `POST /documents/upload`.
2. The API validates the file (type, size, magic bytes) and saves it with a UUID filename.
3. A `Document` record is inserted with `status = pending`.
4. A Celery task `process_document(doc_id)` is dispatched immediately (non-blocking).
5. The client receives a `202 Accepted` response with the document ID.
6. The Celery worker picks up the task, updates status to `processing`, calls the extraction service, and saves questions to the DB.
7. Final status becomes `completed` or `failed`.

---

## 3. OCR / AI Technology Choice

**Google Gemini 1.5 Flash** (vision model via `google-generativeai`)

**Why Gemini?**
- Natively understands both images and PDFs — no external OCR step needed.
- Handles rotated pages, blurry scans, and handwritten text better than rule-based OCR.
- Structured output mode (`response_mime_type="application/json"`) ensures parseable responses.
- Cost-effective: Flash tier is fast and affordable.

**Fallback**: If no API key is set, a mock extractor returns pre-defined questions for local development.

---

## 4. Storage Design

| Layer | Technology | Notes |
|---|---|---|
| Metadata & Questions | PostgreSQL | JSONB for `options` and `source_pages` |
| Uploaded Files | Local filesystem (`uploads/<user_id>/`) | UUID filenames prevent path traversal |
| Task Results | Redis | Celery backend for task state |

**Production recommendation**: Replace local filesystem with AWS S3 or GCS. Pre-signed URLs for secure file delivery.

---

## 5. Asynchronous Processing

- **Broker**: Redis (task queue)
- **Worker**: Celery (`celery -A app.worker.celery_app worker`)
- **Retry**: Tasks retry up to 3 times with 30-second backoff on transient errors (e.g. API rate limits).
- **Concurrency**: Multiple Celery workers can run concurrently — each processes a separate document.
- **Idempotency**: Tasks check if a document is already `completed` before re-processing.

---

## 6. Question Extraction Strategy

The Gemini model is given a structured prompt requesting:
- Question number (if present)
- Full question text
- Options (MCQ)
- Answer (if answer key present)
- Source page numbers
- A per-question confidence score
- Review notes (OCR errors, split-page questions, etc.)

The model returns a **JSON array** directly. A regex-based post-processor strips any accidental markdown fences before parsing.

---

## 7. Answer Key Association

Two modes:
1. **Same document**: Gemini detects answer keys within the same file (end, beginning, or inline).
2. **Separate document**: Upload the answer key separately and pass `related_doc_id=<question_paper_id>`. The `/answers` endpoint merges questions from both documents.

The `answer_status` field in the response communicates reliability:
- `found` — answer confidently extracted
- `uncertain` — answer found but confidence < 0.6
- `not_found` — no answer detected

---

## 8. Confidence & Review Mechanism

Each question has a `confidence` float (0.0–1.0):

| Range | Meaning |
|---|---|
| 0.9 – 1.0 | Clean, unambiguous extraction |
| 0.6 – 0.89 | Minor inference required (split pages, slight OCR noise) |
| 0.0 – 0.59 | Low confidence — flagged in `/warnings` |

The `GET /documents/{id}/warnings` endpoint surfaces all questions where:
- Confidence < 0.7, OR
- Question number is missing, OR
- No answer was found

---

## 9. Security Considerations

| Risk | Mitigation |
|---|---|
| Unauthorised access | JWT bearer tokens; DB queries filter by `user_id` |
| Malicious uploads | Magic-byte validation (not just MIME/extension) |
| Path traversal | UUID filenames in user-specific subdirectories |
| Large file DoS | 20 MB file size limit enforced before writing to disk |
| API key leakage | Loaded from environment variables; `.env` is gitignored |
| Credential brute-force | bcrypt password hashing (cost factor 12) |

---

## 10. Scalability Considerations

- **Horizontal worker scaling**: Add more Celery workers by running additional containers.
- **Database connection pooling**: SQLAlchemy pool configured; use PgBouncer for high concurrency.
- **File storage**: Migrate to S3/GCS for distributed file access across workers.
- **Redis Cluster**: Use Redis Cluster or Sentinel for HA broker.
- **Rate limiting**: Add via API Gateway or `slowapi` middleware.

---

## 11. Trade-offs & Limitations

| Decision | Trade-off |
|---|---|
| Gemini Vision API | Accurate but costs money and requires internet; local Tesseract is free but far less accurate on complex layouts |
| Synchronous SQLAlchemy | Simpler Celery integration; could migrate to asyncpg for async FastAPI handlers |
| Local file storage | Simple to deploy; not suitable for multi-machine deployments without shared filesystem |
| Single Celery queue | All documents share one queue; could prioritise smaller files with multiple queues |
