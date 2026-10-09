import os
from pathlib import Path
from app.services.certificate_generator import generate_certificate_pdf, CertificateGenerationError


def test_generate_certificate_pdf_success(tmp_path):
    """
    Tests that generate_certificate_pdf creates a valid, non-empty PDF file on disk.
    """
    pdf_path = generate_certificate_pdf(
        certificate_id="cert-unit-test-1",
        recipient_name="Alice Test",
        event_name="FastAPI Testing Bootcamp",
        certificate_title="Certificate of Excellence",
        job_id="job-unit-test",
        output_dir=tmp_path,
    )

    assert os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) > 1000  # ReportLab PDFs are ~2.8KB
    assert pdf_path.endswith(".pdf")
    assert "cert-unit-test-1" in pdf_path


def test_generate_certificate_pdf_safe_filename(tmp_path):
    """
    Tests that special characters in recipient names do not affect safe deterministic filenames.
    """
    pdf_path = generate_certificate_pdf(
        certificate_id="cert-special-chars-123",
        recipient_name="O'Connor / Jane & Co.",
        event_name="Special Characters Test",
        job_id="job-safe-test",
        output_dir=tmp_path,
    )

    assert os.path.exists(pdf_path)
    filename = Path(pdf_path).name
    # Filename must use job_id + certificate_id
    assert filename == "job-safe-test_cert-special-chars-123.pdf"
