from fastapi import APIRouter
from app.models.schemas import ProgressList, ProgressItem, AlertStatus

router = APIRouter()

PROGRESS_DATA = [
    {"title": "Federal Agency Capture", "progress": 82, "last_updated": "2025-04-17"},
    {"title": "Judicial Defiance", "progress": 73, "last_updated": "2025-04-17"},
    {"title": "Suppression of Dissent", "progress": 78, "last_updated": "2025-04-17"},
    {"title": "NATO Disengagement", "progress": 43, "last_updated": "2025-04-17"},
    {"title": "Media Subversion", "progress": 54, "last_updated": "2025-04-17"},
]


@router.get("/progress", response_model=ProgressList)
async def get_progress():
    """Get progress percentages for 5 agenda categories."""
    items = [
        ProgressItem(
            title=p["title"],
            progress=p["progress"],
            last_updated=p["last_updated"],
        )
        for p in PROGRESS_DATA
    ]
    return ProgressList(items=items)


@router.get("/alerts", response_model=AlertStatus)
async def get_alerts():
    """Get emergency alert status based on progress thresholds."""
    reasons = []

    for item in PROGRESS_DATA:
        if item["title"] == "Federal Agency Capture" and item["progress"] >= 80:
            reasons.append("Federal agency capture exceeds safe threshold.")
        if item["title"] == "Judicial Defiance" and item["progress"] >= 70:
            reasons.append("Unconstitutional judicial defiance observed.")
        if item["title"] == "Suppression of Dissent" and item["progress"] >= 75:
            reasons.append("Active suppression of dissent detected.")

    if reasons:
        return AlertStatus(triggered=True, reason=" | ".join(reasons))
    return AlertStatus(triggered=False, reason="")
