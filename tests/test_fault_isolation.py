from unittest.mock import patch
from app.services.certificate_generator import CertificateGenerationError, generate_certificate_pdf as real_generate


def test_one_certificate_failure_does_not_stop_batch(client):
    """
    Tests fault isolation: When 1 recipient in a batch fails, the remaining recipients
    must still be generated successfully, and the parent job becomes COMPLETED_WITH_ERRORS.
    """
    def mock_generator(certificate_id, recipient_name, *args, **kwargs):
        if recipient_name == "Corrupted User":
            raise CertificateGenerationError("Corrupted font file in template")
        return real_generate(certificate_id, recipient_name, *args, **kwargs)

    with patch("app.services.job_processor.generate_certificate_pdf", side_effect=mock_generator):
        payload = {
            "event_name": "Resilience & Fault Isolation Workshop",
            "certificate_title": "Certificate of Resilience",
            "recipients": [
                {"name": "Valid User 1", "email": "u1@example.com"},
                {"name": "Corrupted User", "email": "corrupt@example.com"},
                {"name": "Valid User 2", "email": "u2@example.com"},
            ],
        }

        # 1. Submit batch
        create_res = client.post("/jobs", json=payload)
        assert create_res.status_code == 202
        job_id = create_res.json()["job_id"]

        # 2. Check Job status
        status_res = client.get(f"/jobs/{job_id}")
        assert status_res.status_code == 200
        job_data = status_res.json()

        assert job_data["total"] == 3
        assert job_data["successful"] == 2
        assert job_data["failed"] == 1
        assert job_data["status"] == "COMPLETED_WITH_ERRORS"
        assert job_data["progress"] == 100.0

        # 3. Check individual certificate statuses
        certs_res = client.get(f"/jobs/{job_id}/certificates")
        assert certs_res.status_code == 200
        certs_by_name = {c["recipient_name"]: c for c in certs_res.json()}

        assert certs_by_name["Valid User 1"]["status"] == "COMPLETED"
        assert certs_by_name["Valid User 1"]["file_path"] is not None

        assert certs_by_name["Corrupted User"]["status"] == "FAILED"
        assert "Corrupted font file" in certs_by_name["Corrupted User"]["error_message"]

        assert certs_by_name["Valid User 2"]["status"] == "COMPLETED"
        assert certs_by_name["Valid User 2"]["file_path"] is not None
