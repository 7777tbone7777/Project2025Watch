from datetime import date
from fastapi import APIRouter
from app.models.schemas import ProgressList, ProgressItem, AlertStatus
from app.services.news_service import search_news
from app.services.ai_service import analyze_category_progress, AGENDA_CATEGORIES

router = APIRouter()

# Store progress data in memory (in production, use a database)
progress_store = {
    "Federal Agency Capture": {"progress": 50, "last_updated": None},
    "Judicial Defiance": {"progress": 50, "last_updated": None},
    "Suppression of Dissent": {"progress": 50, "last_updated": None},
    "NATO Disengagement": {"progress": 50, "last_updated": None},
    "Media Subversion": {"progress": 50, "last_updated": None},
}


def get_current_date() -> str:
    return date.today().isoformat()


@router.get("/progress", response_model=ProgressList)
async def get_progress():
    """Get progress percentages for 5 agenda categories."""
    current_date = get_current_date()
    items = []
    for category in AGENDA_CATEGORIES:
        data = progress_store.get(category, {"progress": 50, "last_updated": None})
        items.append(
            ProgressItem(
                title=category,
                progress=data["progress"],
                last_updated=data["last_updated"] or "Not analyzed yet",
            )
        )
    return ProgressList(items=items)


@router.post("/progress/analyze", response_model=ProgressList)
async def analyze_progress():
    """Fetch news and analyze progress for all categories using AI."""
    current_date = get_current_date()

    for category in AGENDA_CATEGORIES:
        # Create search query for this category
        search_queries = {
            "Federal Agency Capture": "Trump federal agency firings appointments Schedule F",
            "Judicial Defiance": "Trump court order defiance judicial ruling ignored",
            "Suppression of Dissent": "Trump protesters arrests journalists detained free speech",
            "NATO Disengagement": "Trump NATO alliance withdrawal Europe defense",
            "Media Subversion": "Trump media fake news press freedom journalists",
        }

        query = search_queries.get(category, f"Trump administration {category}")
        news_articles = search_news(query)
        combined_news = "\n".join(news_articles) if news_articles else ""

        if combined_news:
            progress = analyze_category_progress(category, combined_news)
        else:
            # Keep existing progress if no news found
            progress = progress_store[category]["progress"]

        progress_store[category] = {
            "progress": progress,
            "last_updated": current_date,
        }

    # Return updated progress
    items = [
        ProgressItem(
            title=category,
            progress=progress_store[category]["progress"],
            last_updated=progress_store[category]["last_updated"],
        )
        for category in AGENDA_CATEGORIES
    ]
    return ProgressList(items=items)


@router.get("/alerts", response_model=AlertStatus)
async def get_alerts():
    """Get emergency alert status based on progress thresholds."""
    reasons = []

    for category, data in progress_store.items():
        progress = data["progress"]
        if category == "Federal Agency Capture" and progress >= 80:
            reasons.append("Federal agency capture exceeds safe threshold.")
        if category == "Judicial Defiance" and progress >= 70:
            reasons.append("Unconstitutional judicial defiance observed.")
        if category == "Suppression of Dissent" and progress >= 75:
            reasons.append("Active suppression of dissent detected.")

    if reasons:
        return AlertStatus(triggered=True, reason=" | ".join(reasons))
    return AlertStatus(triggered=False, reason="")
