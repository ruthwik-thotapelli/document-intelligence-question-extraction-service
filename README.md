<div align="center">

# 🧠 Document Intelligence & AI Question Extraction

**A Highly Scalable, Event-Driven Backend System for Automated Examination Processing**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-316192.svg?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D.svg?style=flat&logo=redis&logoColor=white)](https://redis.io/)
[![Celery](https://img.shields.io/badge/Celery-5.3-37814A.svg?style=flat&logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![Gemini 1.5 Flash](https://img.shields.io/badge/AI-Gemini_1.5_Vision-EA4335.svg?style=flat&logo=google&logoColor=white)](https://ai.google.dev/)
[![Docker Compose](https://img.shields.io/badge/Docker-Compose-2496ED.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)

[**Architecture**](#%EF%B8%8F-system-architecture) • [**Key Features**](#-key-features) • [**API Reference**](#-api-endpoints) • [**Local Deployment**](#-local-deployment) • [**Evaluation Guide**](#-evaluation-guide)

---
</div>

> **Mission:** Move learning beyond traditional methods by converting raw, unstructured examination papers (PDFs, skewed scans, images) into highly structured, machine-readable JSON data—instantly and asynchronously.

---

## ⚡ Key Features

### 1. Robust Asynchronous Pipeline
Built for high-throughput ingestion. Client uploads return a HTTP `202 Accepted` instantly. Heavy AI-extraction workloads are offloaded to **Celery Workers** backed by a **Redis Broker**, ensuring the FastAPI web server remains highly concurrent and responsive.

### 2. Next-Gen Vision AI Extraction
Traditional OCR engines (like Tesseract) struggle with complex layouts, math formulas, and multi-page questions. This system leverages **Google Gemini 1.5 Flash (Vision)** to natively understand documents visually. It seamlessly extracts questions, multiple-choice options, answers, and context across split pages.

### 3. Enterprise-Grade Security
* **Stateless Auth:** Secure JWT (JSON Web Token) bearer authentication with bcrypt password hashing.
* **Malware Prevention:** Deep file inspection using "Magic Byte" signatures (not just MIME-type spoofing).
* **Path Traversal Protection:** Files are stored using cryptographic UUIDs within isolated user directories.

### 4. Resiliency & Observability
* **RFC 7807 Error Handling:** All API errors adhere to the Problem Details for HTTP APIs standard.
* **Idempotent Workers:** Celery tasks are designed idempotently, allowing safe retries without data duplication if network failures occur.
* **Confidence Scoring:** Every extracted question receives a normalized confidence score (0.0 - 1.0). Low confidence results are automatically flagged for human-in-the-loop (HITL) review.

---

## 🏗️ System Architecture

The architecture separates concerns into highly decoupled layers:

### The Flow of Data
```mermaid
sequenceDiagram
    autonumber
    actor User as 👤 Client
    participant API as 🚀 FastAPI (API Gateway)
    participant DB as 🐘 PostgreSQL
    participant Redis as 🔴 Redis Queue
    participant Celery as ⚙️ Celery Worker
    participant AI as 🧠 Gemini Vision AI

    User->>API: POST /api/v1/documents/upload (PDF/Img)
    API->>API: Validate Magic Bytes & JWT Token
    API->>DB: INSERT Document (status: 'pending')
    API->>Redis: Publish Extraction Event
    API-->>User: 202 Accepted (doc_id)
    
    Celery->>Redis: Consume Extraction Event
    Celery->>DB: UPDATE status -> 'processing'
    Celery->>AI: Send File & Prompt via Google SDK
    AI-->>Celery: Return Structured JSON
    Celery->>DB: INSERT Questions, Options, Context
    Celery->>DB: UPDATE status -> 'completed'
    
    User->>API: GET /api/v1/documents/{doc_id}/questions
    API-->>User: 200 OK (Clean JSON Array)
```

<details>
<summary><b>🔍 View Database Schema (ERD)</b></summary>
<br>

```mermaid
erDiagram
    USERS ||--o{ DOCUMENTS : "owns"
    DOCUMENTS ||--o{ QUESTIONS : "contains"
    DOCUMENTS ||--o| DOCUMENTS : "related_answer_key"

    USERS {
        int id PK
        string email
        string hashed_password
        boolean is_active
    }
    DOCUMENTS {
        int id PK
        string filename
        string file_path
        string status "enum: pending, processing, completed, failed"
        int user_id FK
        int related_doc_id FK
    }
    QUESTIONS {
        int id PK
        int document_id FK
        string question_number
        string text
        jsonb options
        string answer
        float confidence
        jsonb source_pages
    }
```
</details>

---

## 🛠️ Local Deployment

Deploying the entire microservice stack locally takes less than a minute.

### Prerequisites
* **Docker Desktop** (Engine & Compose)
* **Google Gemini API Key** (Get one for free at [Google AI Studio](https://aistudio.google.com/))

### 1. Setup Environment
```bash
git clone https://github.com/ruthwik-thotapelli/document-intelligence-question-extraction-service.git
cd document-intelligence-question-extraction-service

# Create your .env file
cp .env.example .env
```
👉 *Open `.env` and paste your `GEMINI_API_KEY` into the file.*

### 2. Boot the Infrastructure
```bash
# Start all containers in detached mode
docker-compose up --build -d

# Run Alembic database migrations
docker-compose exec web alembic upgrade head
```

### 3. Verify Deployment
* **API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc Format:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🔌 API Endpoints

The API is fully documented via OpenAPI/Swagger. Below is a high-level overview:

| Group | Method | Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **Authentication** | `POST` | `/api/v1/auth/register` | Register a new user |
| | `POST` | `/api/v1/auth/login` | Obtain a JWT Bearer token |
| **Ingestion** | `POST` | `/api/v1/documents/upload` | Upload a PDF/PNG/JPG securely |
| **Querying** | `GET` | `/api/v1/documents/` | List all documents for current user |
| | `GET` | `/api/v1/documents/{id}` | Get document metadata |
| | `GET` | `/api/v1/documents/{id}/status` | Long-poll document processing state |
| **Extraction** | `GET` | `/api/v1/documents/{id}/questions` | Retrieve extracted JSON questions |
| | `GET` | `/api/v1/documents/{id}/answers` | Extract merged Answer Key data |
| **Review** | `GET` | `/api/v1/documents/{id}/warnings` | Flagged low-confidence anomalies |

---

## 🎯 Evaluation Guide (For Reviewers)

To fully validate this submission against the engineering constraints, we recommend the following flow:

1. **Import Postman Collection:** Load `postman/collection.json` into your Postman workspace.
2. **Execute Steps 1 & 2:** Register and Login. Your JWT token is set automatically.
3. **Test Imperfect Scans:** Execute `3a. Upload PDF` and attach `samples/question_paper.pdf`.
4. **Observe Asynchrony:** Hit `4. Check Processing Status`. The API does not block; it delegates to Celery.
5. **Verify AI Accuracy:** Once status is `completed`, hit `5. Get Extracted Questions`. You will notice:
   * **Question 5** spans multiple pages but is merged perfectly.
   * Multiple-choice options are parsed into a distinct JSON array.
   * The **Answer Key** at the end of the document is correctly mapped back to the questions via the `/answers` endpoint.

---
<div align="center">
  <i>Engineered for scale. Built for the Pragati Bharati Backend Evaluation.</i>
</div>
