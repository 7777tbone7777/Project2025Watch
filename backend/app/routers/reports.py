from fastapi import APIRouter
from fastapi.responses import FileResponse
from app.services.pdf_service import generate_pdf_report
from app.services.rss_service import fetch_geopolitical_updates
from app.routers.progress import PROGRESS_DATA

router = APIRouter()


@router.get("/report/pdf")
async def download_pdf_report():
    """Download PDF report."""
    events = fetch_geopolitical_updates()
    pdf_path = generate_pdf_report(PROGRESS_DATA, events)
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename="project2025_report.pdf",
    )
