from fastapi import APIRouter
from fastapi.responses import FileResponse
from app.services.pdf_service import generate_pdf_report
from app.services.rss_service import fetch_geopolitical_updates
from app.routers.progress import progress_store

router = APIRouter()


@router.get("/report/pdf")
async def download_pdf_report():
    """Download PDF report."""
    events = fetch_geopolitical_updates()

    # Convert progress_store to list format for PDF
    progress_data = [
        {
            "title": category,
            "progress": data["progress"],
            "last_updated": data["last_updated"] or "Not analyzed yet",
        }
        for category, data in progress_store.items()
    ]

    pdf_path = generate_pdf_report(progress_data, events)
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename="project2025_report.pdf",
    )
