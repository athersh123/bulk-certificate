import pytest


def test_create_job_success(client):
    """
    Tests creating a bulk certificate generation job with valid data.
    Verifies HTTP 202 Accepted status and immediate payload structure.
    """
    payload = {
        "event_name": "FastAPI Workshop 2026",
        "certificate_title": "Certificate of Participation",
        "recipients": [
            {"name": "Alice Smith", "email": "alice@example.com"},
            {"name": "Bob Jones", "email": "bob@example.com"},
        ],
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 202

    data = response.json()
    assert "job_id" in data
    assert data["total"] == 2
    assert data["event_name"] == "FastAPI Workshop 2026"
    assert data["status"] in ["PENDING", "PROCESSING", "COMPLETED"]


def test_create_job_empty_recipients_list(client):
    """
    Tests that submitting a job with zero recipients is rejected with 422.
    """
    payload = {
        "event_name": "Empty Batch Test",
        "certificate_title": "Certificate of Completion",
        "recipients": [],
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error_type"] == "ValidationError"


def test_create_job_invalid_email(client):
    """
    Tests that malformed email addresses are rejected with 422.
    """
    payload = {
        "event_name": "Email Validation Test",
        "recipients": [
            {"name": "Valid User", "email": "valid@example.com"},
            {"name": "Invalid User", "email": "not-an-email"},
        ],
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert any("email" in err["field"] for err in data["errors"])


def test_create_job_blank_recipient_name(client):
    """
    Tests that whitespace-only recipient names are rejected with 422.
    """
    payload = {
        "event_name": "Blank Name Test",
        "recipients": [
            {"name": "   ", "email": "spaces@example.com"},
        ],
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 422


def test_create_job_blank_event_name(client):
    """
    Tests that empty event name strings are rejected with 422.
    """
    payload = {
        "event_name": "",
        "recipients": [
            {"name": "Alice Smith", "email": "alice@example.com"},
        ],
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 422


def test_get_job_status_completed(client):
    """
    Tests retrieving the progress and status of a completed job.
    """
    # 1. Create a 2-recipient job
    payload = {
        "event_name": "Progress Polling Test",
        "certificate_title": "Certificate of Achievement",
        "recipients": [
            {"name": "Recipient 1", "email": "r1@example.com"},
            {"name": "Recipient 2", "email": "r2@example.com"},
        ],
    }
    create_res = client.post("/jobs", json=payload)
    job_id = create_res.json()["job_id"]

    # 2. Fetch job status
    status_res = client.get(f"/jobs/{job_id}")
    assert status_res.status_code == 200
    data = status_res.json()
    assert data["job_id"] == job_id
    assert data["total"] == 2
    assert data["successful"] == 2
    assert data["failed"] == 0
    assert data["progress"] == 100.0
    assert data["status"] == "COMPLETED"
    assert data["completed_at"] is not None


def test_get_job_status_not_found(client):
    """
    Tests that querying an unknown job ID returns HTTP 404 Not Found.
    """
    response = client.get("/jobs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_list_jobs_endpoint(client):
    """
    Tests listing recent jobs via GET /jobs.
    """
    payload = {
        "event_name": "History Listing Test",
        "certificate_title": "Certificate of Completion",
        "recipients": [{"name": "Listed User", "email": "listed@example.com"}],
    }
    client.post("/jobs", json=payload)

    response = client.get("/jobs?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "job_id" in data[0]
    assert "event_name" in data[0]


def test_frontend_serve_index(client):
    """
    Tests that browser GET / with text/html returns the frontend UI.
    """
    response = client.get("/", headers={"Accept": "text/html"})
    assert response.status_code == 200
    assert "BulkCert Studio" in response.text

