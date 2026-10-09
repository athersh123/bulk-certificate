from app.models.models import Certificate, CertificateStatus


def test_download_certificate_pdf_success(client):
    """
    Tests downloading an existing generated certificate PDF file.
    """
    # 1. Create job
    payload = {
        "event_name": "Download Test",
        "certificate_title": "Certificate of Completion",
        "recipients": [{"name": "Download User", "email": "download@example.com"}],
    }
    create_res = client.post("/jobs", json=payload)
    job_id = create_res.json()["job_id"]

    # 2. Get certificate list
    certs_res = client.get(f"/jobs/{job_id}/certificates")
    assert certs_res.status_code == 200
    cert_id = certs_res.json()[0]["id"]

    # 3. Download the PDF
    download_res = client.get(f"/certificates/{cert_id}")
    assert download_res.status_code == 200
    assert download_res.headers["content-type"] == "application/pdf"
    assert "attachment" in download_res.headers["content-disposition"]
    assert len(download_res.content) > 1000


def test_download_certificate_not_found(client):
    """
    Tests that downloading a non-existent certificate returns HTTP 404.
    """
    response = client.get("/certificates/unknown-cert-uuid-000")
    assert response.status_code == 404
    assert "not exist" in response.json()["detail"].lower()


def test_failed_certificate_download_blocked(client, db_session):
    """
    Tests that requesting a download for a FAILED certificate returns 400 with failure reason.
    """
    # Insert a dummy failed certificate directly into DB
    failed_cert = Certificate(
        job_id="test-job-id",
        recipient_name="Failed Person",
        recipient_email="fail@example.com",
        status=CertificateStatus.FAILED,
        error_message="Simulated font rendering error",
    )
    db_session.add(failed_cert)
    db_session.commit()

    response = client.get(f"/certificates/{failed_cert.id}")
    assert response.status_code == 400
    data = response.json()["detail"]
    assert data["status"] == "FAILED"
    assert "Simulated font rendering error" in data["error"]
