from datetime import date, datetime
from pathlib import Path
from typing import Optional, Union
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from app.core.config import settings
from app.core.logger import logger


class CertificateGenerationError(Exception):
    """Raised when PDF certificate rendering or saving fails."""
    pass


def generate_certificate_pdf(
    certificate_id: str,
    recipient_name: str,
    event_name: str,
    certificate_title: str = "Certificate of Completion",
    issue_date: Optional[Union[date, datetime, str]] = None,
    job_id: Optional[str] = None,
    output_dir: Optional[Union[str, Path]] = None,
) -> str:
    """
    Generates a single professional PDF certificate for a recipient using ReportLab.

    Args:
        certificate_id: Unique identifier for the certificate (used in safe filename).
        recipient_name: Full name of the recipient to be printed on certificate.
        event_name: Name of the event, workshop, or course.
        certificate_title: Main certificate header title (default: "Certificate of Completion").
        issue_date: Date of certificate issuance (defaults to today's date).
        job_id: Optional parent job UUID for organization/naming.
        output_dir: Target directory to save the PDF. Defaults to settings.storage_path.

    Returns:
        str: Absolute file path to the generated PDF file.

    Raises:
        CertificateGenerationError: If PDF canvas drawing or disk write fails.
    """
    try:
        # 1. Determine and prepare output directory
        target_dir = Path(output_dir) if output_dir else settings.storage_path
        target_dir.mkdir(parents=True, exist_ok=True)

        # 2. Build safe deterministic filename
        prefix = f"{job_id}_" if job_id else ""
        filename = f"{prefix}{certificate_id}.pdf"
        file_path = target_dir / filename

        # 3. Format issue date string
        if issue_date is None:
            formatted_date = datetime.now().strftime("%B %d, %Y")
        elif isinstance(issue_date, (date, datetime)):
            formatted_date = issue_date.strftime("%B %d, %Y")
        else:
            formatted_date = str(issue_date)

        # 4. Canvas setup (Landscape A4: 841.89 x 595.27 points)
        page_width, page_height = landscape(A4)
        c = canvas.Canvas(str(file_path), pagesize=landscape(A4))
        c.setTitle(f"{certificate_title} - {recipient_name}")
        c.setAuthor(settings.APP_NAME)
        c.setSubject(event_name)

        # Color Palette Definitions
        NAVY_PRIMARY = colors.HexColor("#0F2942")     # Deep professional navy
        GOLD_ACCENT = colors.HexColor("#D4AF37")      # Classic metallic gold
        GOLD_LIGHT = colors.HexColor("#F3E5AB")       # Soft gold
        TEXT_MUTED = colors.HexColor("#4A5568")       # Slate gray for body text
        BG_TINT = colors.HexColor("#FDFDFD")          # Clean warm off-white

        # Draw subtle page background
        c.setFillColor(BG_TINT)
        c.rect(0, 0, page_width, page_height, fill=True, stroke=False)

        # 5. Draw Decorative Borders
        # Outer Gold Border
        c.setStrokeColor(GOLD_ACCENT)
        c.setLineWidth(4)
        c.rect(25, 25, page_width - 50, page_height - 50)

        # Inner Thin Navy Border
        c.setStrokeColor(NAVY_PRIMARY)
        c.setLineWidth(1)
        c.rect(32, 32, page_width - 64, page_height - 64)

        # Corner Ornaments (Geometric 4-corner accents)
        corner_offset = 25
        accent_size = 20
        c.setFillColor(GOLD_ACCENT)
        for x, y in [
            (corner_offset, corner_offset),
            (page_width - corner_offset - accent_size, corner_offset),
            (corner_offset, page_height - corner_offset - accent_size),
            (page_width - corner_offset - accent_size, page_height - corner_offset - accent_size),
        ]:
            c.rect(x, y, accent_size, accent_size, fill=True, stroke=False)

        # 6. Header Elements
        center_x = page_width / 2

        # Top Accent Ribbon / Badge text
        c.setFillColor(GOLD_ACCENT)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(center_x, page_height - 75, "★ ★ ★   OFFICIAL CERTIFICATION   ★ ★ ★")

        # Main Certificate Title
        c.setFillColor(NAVY_PRIMARY)
        c.setFont("Helvetica-Bold", 30)
        c.drawCentredString(center_x, page_height - 120, certificate_title.upper())

        # Gold Underline for Title
        c.setStrokeColor(GOLD_ACCENT)
        c.setLineWidth(2)
        c.line(center_x - 180, page_height - 132, center_x + 180, page_height - 132)

        # Presentation Lead text
        c.setFillColor(TEXT_MUTED)
        c.setFont("Helvetica-Oblique", 13)
        c.drawCentredString(center_x, page_height - 170, "This is proudly presented to")

        # 7. Recipient Name (Prominent Hero Element)
        c.setFillColor(NAVY_PRIMARY)
        c.setFont("Helvetica-Bold", 28)
        c.drawCentredString(center_x, page_height - 220, recipient_name)

        # Recipient Name Accent Line
        c.setStrokeColor(GOLD_ACCENT)
        c.setLineWidth(1.5)
        c.line(center_x - 140, page_height - 232, center_x + 140, page_height - 232)

        # 8. Achievement / Course Description
        c.setFillColor(TEXT_MUTED)
        c.setFont("Helvetica", 12)
        c.drawCentredString(
            center_x,
            page_height - 275,
            "for successfully completing and demonstrating demonstrated excellence in",
        )

        # Event / Course Name
        c.setFillColor(NAVY_PRIMARY)
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(center_x, page_height - 315, event_name)

        # 9. Bottom Section: Signatures & Verification
        # Left: Issue Date
        date_x = 120
        c.setStrokeColor(NAVY_PRIMARY)
        c.setLineWidth(0.8)
        c.line(date_x, 110, date_x + 160, 110)
        c.setFillColor(NAVY_PRIMARY)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(date_x + 80, 120, formatted_date)
        c.setFillColor(TEXT_MUTED)
        c.setFont("Helvetica", 9)
        c.drawCentredString(date_x + 80, 95, "DATE OF ISSUANCE")

        # Center: Decorative Seal
        seal_x = center_x
        seal_y = 125
        c.setFillColor(GOLD_LIGHT)
        c.setStrokeColor(GOLD_ACCENT)
        c.setLineWidth(2)
        c.circle(seal_x, seal_y, 35, fill=True, stroke=True)
        c.setFillColor(NAVY_PRIMARY)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(seal_x, seal_y + 6, "SEAL OF")
        c.drawCentredString(seal_x, seal_y - 8, "EXCELLENCE")

        # Right: Authorized Signatory
        sig_x = page_width - 280
        c.setStrokeColor(NAVY_PRIMARY)
        c.setLineWidth(0.8)
        c.line(sig_x, 110, sig_x + 160, 110)
        c.setFillColor(NAVY_PRIMARY)
        c.setFont("Helvetica-Oblique", 14)
        c.drawCentredString(sig_x + 80, 120, "Academic Director")
        c.setFillColor(TEXT_MUTED)
        c.setFont("Helvetica", 9)
        c.drawCentredString(sig_x + 80, 95, "AUTHORIZED SIGNATURE")

        # 10. Footer / Verification ID
        c.setFillColor(TEXT_MUTED)
        c.setFont("Helvetica", 8)
        footer_text = f"Certificate ID: {certificate_id}  |  Verify Authenticity with {settings.APP_NAME}"
        c.drawCentredString(center_x, 42, footer_text)

        # Finalize and write file to disk
        c.showPage()
        c.save()

        logger.info("Generated PDF certificate successfully: %s", file_path)
        return str(file_path.resolve())

    except Exception as exc:
        logger.error("Failed to generate PDF for certificate %s: %s", certificate_id, exc, exc_info=True)
        raise CertificateGenerationError(f"PDF generation failed for '{recipient_name}': {str(exc)}") from exc
