from datetime import date
from fastapi import APIRouter
from app.models.schemas import ProgressList, ProgressItem, AlertStatus

router = APIRouter()

# Base progress data (in a real app, this would come from a database)
PROGRESS_DATA = [
    {"title": "Federal Agency Capture", "progress": 82},
    {"title": "Judicial Defiance", "progress": 73},
    {"title": "Suppression of Dissent", "progress": 78},
    {"title": "NATO Disengagement", "progress": 43},
    {"title": "Media Subversion", "progress": 54},
]


def get_current_date() -> str:
    return date.today().isoformat()


@router.get("/progress", response_model=ProgressList)
async def get_progress():
    """Get progress percentages for 5 agenda categories."""
    current_date = get_current_date()
    items = [
        ProgressItem(
            title=p["title"],
            progress=p["progress"],
            last_updated=current_date,
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
