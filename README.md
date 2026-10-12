# Bulk Certificate Generator — Backend Assessment

A production-style REST API built with **FastAPI**, **SQLAlchemy**, and **ReportLab** designed to handle bulk certificate generation efficiently, asynchronously, and with per-item fault isolation.

---

## 📌 Quick Evaluation Summary

For evaluators reviewing this submission, here is how the core requirements are addressed:

| Evaluation Criterion | Implementation Details | Key File Reference |
| :--- | :--- | :--- |
| **Framework & Database** | FastAPI + SQLite with SQLAlchemy 2.0 ORM (normalized 1:N schema) | [app/db/database.py](file:///d:/BULK%20ALERT/app/db/database.py), [app/models/models.py](file:///d:/BULK%20ALERT/app/models/models.py) |
| **Bulk Request Handling** | `POST /jobs` accepts batch arrays; returns `202 Accepted` in **< 15ms** | [app/api/v1/endpoints/jobs.py](file:///d:/BULK%20ALERT/app/api/v1/endpoints/jobs.py) |
| **Asynchronous Execution** | FastAPI `BackgroundTasks` processes PDFs in a worker thread without blocking HTTP sockets | [app/services/job_processor.py](file:///d:/BULK%20ALERT/app/services/job_processor.py) |
| **Fault Isolation** | Per-recipient `try...except` loop — a failed certificate records its error and never stops the batch | [app/services/job_processor.py](file:///d:/BULK%20ALERT/app/services/job_processor.py) |
| **PDF Generation** | ReportLab landscape A4 template with dynamic names, event titles, dates, borders, and gold seals | [app/services/certificate_generator.py](file:///d:/BULK%20ALERT/app/services/certificate_generator.py) |
| **Progress Tracking** | `GET /jobs/{id}` returns real-time progress %, counts, and completion status safely (zero-division guarded) | [app/api/v1/endpoints/jobs.py](file:///d:/BULK%20ALERT/app/api/v1/endpoints/jobs.py) |
| **Certificate Retrieval** | `GET /certificates/{id}` directly streams generated PDF files with safe attachment headers | [app/api/v1/endpoints/certificates.py](file:///d:/BULK%20ALERT/app/api/v1/endpoints/certificates.py) |
| **Automated Tests** | 13 automated tests covering validation, rendering, polling, and fault isolation (100% passing) | [tests/](file:///d:/BULK%20ALERT/tests/) |

---

## 🚀 30-Second Quickstart

### 1. Install Dependencies & Run Demo
```powershell
# Clone / open project directory
cd "d:/BULK ALERT"

# Install dependencies
pip install -r requirements.txt

# Run the live interactive terminal demo
python demo.py
```

### 2. Run Automated Test Suite
```powershell
pytest -v
```

### 3. Start the API Server & Web UI Studio
```powershell
uvicorn app.main:app --reload --port 8000
```
- **BulkCert Studio Web UI**: **http://127.0.0.1:8000/** (or **/ui**)
- **Interactive Swagger Docs**: **http://127.0.0.1:8000/docs**
- **Service Health Check**: **http://127.0.0.1:8000/api/v1/health**

---

## 🏗️ System Architecture & Workflow

```
[ Client / Frontend ]
         │
         │  1. POST /jobs (List of Recipients)
         ▼
[ FastAPI Route Handler ] ── 2. Validate Schema (Pydantic v2)
         │
         ├── 3. Atomic Database Insert (Job: PENDING, Certs: PENDING)
         ├── 4. Enqueue Background Task (BackgroundTasks)
         │
         ▼
[ Immediate HTTP Response ] ──> 202 Accepted { job_id, status: "PENDING" } (< 15ms)
         │
         ▼  (Asynchronous Worker Thread)
[ Background Job Processor ]
         │
         ├── Loop through each recipient with dedicated DB session
         │     ├── Try: Render PDF with ReportLab -> Save to disk -> Status: COMPLETED
         │     └── Except: Catch error -> Store error_message -> Status: FAILED
         │     └── Update parent job progress counters (successful / failed)
         │
         └── Finalize Job Status (COMPLETED / COMPLETED_WITH_ERRORS / FAILED)
```

---

## 📁 Repository Layout

```
d:/BULK ALERT/
├── app/
│   ├── main.py                        # FastAPI entry point, lifespan, CORS & global exception handlers
│   ├── core/
│   │   ├── config.py                  # Pydantic Settings (.env configuration loader)
│   │   └── logger.py                  # Structured application logging
│   ├── db/
│   │   └── database.py                # SQLAlchemy engine, SessionLocal & get_db dependency
│   ├── models/
│   │   └── models.py                  # GenerationJob and Certificate ORM models
│   ├── schemas/
│   │   └── schemas.py                 # Pydantic validation & response schemas
│   ├── services/
│   │   ├── certificate_generator.py   # ReportLab PDF template rendering engine
│   │   └── job_processor.py           # Fault-isolated background batch worker
│   └── api/
│       └── v1/
│           ├── api.py                 # Router aggregator
│           └── endpoints/
│               ├── health.py          # /health check
│               ├── jobs.py            # POST /jobs, GET /jobs/{id}
│               └── certificates.py    # GET /certificates/{id}, GET /jobs/{id}/certificates
│
├── generated_certificates/            # Directory where generated PDF files are stored
├── tests/                             # Automated test suite (Pytest + TestClient)
│   ├── conftest.py                    # In-memory SQLite DB fixtures & temp storage management
│   ├── test_pdf_generator.py          # ReportLab rendering unit tests
│   ├── test_jobs_api.py               # Job creation, validation & progress polling tests
│   ├── test_certificates_api.py       # PDF streaming & error guard tests
│   └── test_fault_isolation.py        # Partial failure isolation integration tests
│
├── demo.py                            # Interactive live terminal demo script
├── requirements.txt                   # Production dependencies
├── .env.example                       # Environment template
├── .gitignore                         # Git ignore rules
└── README.md                          # Project documentation
```

---

## 📡 API Reference & Examples

### 1. Submit Bulk Certificate Generation Job
- **Endpoint**: `POST /jobs`
- **Status Code**: `202 Accepted`

```bash
curl -X POST "http://127.0.0.1:8000/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "event_name": "FastAPI Backend Engineering Masterclass",
    "certificate_title": "Certificate of Completion",
    "recipients": [
      { "name": "Athersh JR", "email": "athersh@example.com" },
      { "name": "Amul", "email": "amul@example.com" }
    ]
  }'
```

**Response**:
```json
{
  "job_id": "28e1aaac-1887-4eb0-90e2-8ce4f52e99a8",
  "event_name": "FastAPI Backend Engineering Masterclass",
  "certificate_title": "Certificate of Completion",
  "status": "PENDING",
  "total": 2,
  "message": "Certificate generation job accepted and background processing started.",
  "status_url": "/api/v1/jobs/28e1aaac-1887-4eb0-90e2-8ce4f52e99a8",
  "created_at": "2026-10-09T08:44:42.361369"
}
```

---

### 2. Poll Job Status & Progress
- **Endpoint**: `GET /jobs/{job_id}`
- **Status Code**: `200 OK`

```bash
curl -X GET "http://127.0.0.1:8000/jobs/28e1aaac-1887-4eb0-90e2-8ce4f52e99a8"
```

**Response**:
```json
{
  "job_id": "28e1aaac-1887-4eb0-90e2-8ce4f52e99a8",
  "event_name": "FastAPI Backend Engineering Masterclass",
  "certificate_title": "Certificate of Completion",
  "status": "COMPLETED",
  "total": 2,
  "successful": 2,
  "failed": 0,
  "pending": 0,
  "progress": 100.0,
  "created_at": "2026-10-09T08:44:42.361369",
  "completed_at": "2026-10-09T08:44:42.592100"
}
```

---

### 3. List All Certificates Under a Job
- **Endpoint**: `GET /jobs/{job_id}/certificates`
- **Status Code**: `200 OK`

```bash
curl -X GET "http://127.0.0.1:8000/jobs/28e1aaac-1887-4eb0-90e2-8ce4f52e99a8/certificates"
```

**Response**:
```json
[
  {
    "id": "ab83e9f7-8a3c-4fe5-a4d1-ff4d662f3942",
    "job_id": "28e1aaac-1887-4eb0-90e2-8ce4f52e99a8",
    "recipient_name": "Athersh JR",
    "recipient_email": "athersh@example.com",
    "status": "COMPLETED",
    "file_path": "D:\\BULK ALERT\\generated_certificates\\28e1aaac_ab83e9f7.pdf",
    "download_url": "/certificates/ab83e9f7-8a3c-4fe5-a4d1-ff4d662f3942",
    "error_message": null,
    "created_at": "2026-10-09T08:44:42.361369"
  }
]
```

---

### 4. Download Certificate PDF
- **Endpoint**: `GET /certificates/{certificate_id}`
- **Status Code**: `200 OK` (streams `application/pdf`)

```bash
curl -X GET "http://127.0.0.1:8000/certificates/ab83e9f7-8a3c-4fe5-a4d1-ff4d662f3942" \
  --output "Certificate_Athersh_JR.pdf"
```

---

## 🛡️ Fault Isolation & Edge Cases Handled

1. **Individual Failure Resilience**:
   - The PDF generation step for each recipient runs inside its own `try...except` block.
   - If recipient #2 has corrupted data or triggers an exception, recipient #2 is marked `FAILED` with the exact error message recorded.
   - Recipients #3, #4, etc., continue processing without interruption.
   - The parent job status transitions to `COMPLETED_WITH_ERRORS`.

2. **Input Validation Failures**:
   - Blank names (`"   "`), empty recipient lists (`[]`), and invalid email addresses (`"not-an-email"`) are rejected immediately with `HTTP 422` and clean field-level error messages before touching the database or worker threads.

3. **Failed / In-Progress Certificate Download Protection**:
   - Requesting `GET /certificates/{id}` for a certificate that is still `PENDING`/`PROCESSING` returns `HTTP 409 Conflict`.
   - Requesting a certificate that `FAILED` returns `HTTP 400 Bad Request` with the failure diagnostic, preventing broken file streams.

4. **Security & Path Traversal Prevention**:
   - Files are stored using deterministic UUID prefixes (`{job_id}_{certificate_id}.pdf`) rather than raw user names.
   - Download handlers resolve physical paths against the storage root directory to prevent directory traversal attacks.

---

## 🧪 Automated Testing

The project includes **13 tests** covering unit rendering, schema validation, progress polling, download streaming, and failure isolation:

```powershell
pytest -v
```

```text
tests/test_certificates_api.py::test_download_certificate_pdf_success PASSED
tests/test_certificates_api.py::test_download_certificate_not_found PASSED
tests/test_certificates_api.py::test_failed_certificate_download_blocked PASSED
tests/test_fault_isolation.py::test_one_certificate_failure_does_not_stop_batch PASSED
tests/test_jobs_api.py::test_create_job_success PASSED
tests/test_jobs_api.py::test_create_job_empty_recipients_list PASSED
tests/test_jobs_api.py::test_create_job_invalid_email PASSED
tests/test_jobs_api.py::test_create_job_blank_recipient_name PASSED
tests/test_jobs_api.py::test_create_job_blank_event_name PASSED
tests/test_jobs_api.py::test_get_job_status_completed PASSED
tests/test_jobs_api.py::test_get_job_status_not_found PASSED
tests/test_pdf_generator.py::test_generate_certificate_pdf_success PASSED
tests/test_pdf_generator.py::test_generate_certificate_pdf_safe_filename PASSED

======================= 13 passed in 0.71s ========================
```

---

## 💡 Key Design Decisions

1. **Why FastAPI & Pydantic v2?**
   - High throughput, native async support, automated OpenAPI documentation, and strict C-accelerated schema validation.
2. **Why SQLite + SQLAlchemy 2.0?**
   - Zero-dependency local setup for evaluation, backed by standard SQLAlchemy 2.0 ORM patterns that allow migrating to PostgreSQL in production simply by changing the `DATABASE_URL` environment variable.
3. **Why BackgroundTasks for Bulk Processing?**
   - Generating 500 PDF certificates takes ~5 seconds. Performing this inside an HTTP request would cause browser socket timeouts and poor UX. Using `BackgroundTasks` returns an instant response (`< 15ms`) with a job ID and polling URL.
4. **When to migrate to Celery / Redis?**
   - If batch sizes exceed 10,000 recipients or require horizontal scaling across multiple worker instances, the worker function can be extracted into a Celery task with zero changes to the underlying database models or PDF generator.
