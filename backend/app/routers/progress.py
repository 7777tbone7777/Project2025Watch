"""Agenda-category progress.

Had the same fault as predictions: an in-memory dict that nothing refreshed, so
the page served whatever was last analysed — in practice February figures shown
under an August page, with no indication they were six months old. A container
restart silently reset everything to a hardcoded 50%.

Now cached with a TTL and refreshed in the background, so a cold start
repopulates itself, and each score carries the reasoning behind it.
"""
import asyncio
import logging
import time
from datetime import date

from fastapi import APIRouter

from app.models.schemas import ProgressList, ProgressItem, AlertStatus, ArticleLink
from app.services.news_service import search_news_with_links
from app.services.ai_service import analyze_category_with_reasoning, AGENDA_CATEGORIES

log = logging.getLogger(__name__)
router = APIRouter()

CACHE_TTL_SECONDS = 6 * 3600

# Searches are defined once, next to the categories they serve.
SEARCH_QUERIES = {
    "Federal Agency Capture": '("Schedule F" OR "civil service" OR "federal workers") AND (fired OR appointees OR protections)',
    "Judicial Defiance": '("court order" OR "federal judge" OR ruling) AND (defy OR ignored OR "contempt")',
    "Suppression of Dissent": '(protesters OR journalists OR "free speech") AND (arrested OR detained OR restricted)',
    "NATO Disengagement": '(NATO OR "US troops") AND (Europe AND (withdrawal OR reduce OR commitment))',
    "Media Subversion": '("press freedom" OR "public broadcasting" OR journalists) AND (funding OR access OR revoked)',
}

progress_store = {
    c: {"progress": 0, "last_updated": None, "articles": [], "reasoning": ""}
    for c in AGENDA_CATEGORIES
}
_analyzed_at = 0.0
_refreshing = False


def get_current_date() -> str:
    return date.today().isoformat()


def _items() -> list:
    out = []
    for category in AGENDA_CATEGORIES:
        data = progress_store.get(category, {})
        out.append(
            ProgressItem(
                title=category,
                progress=data.get("progress", 0),
                last_updated=data.get("last_updated") or "Not analyzed yet",
                articles=[ArticleLink(**a) for a in data.get("articles", [])],
                reasoning=data.get("reasoning", ""),
            )
        )
    return out


def refresh_progress() -> int:
    """Re-analyse every category. Blocking; returns how many were analysed."""
    global _analyzed_at
    today = get_current_date()
    for category in AGENDA_CATEGORIES:
        try:
            query = SEARCH_QUERIES.get(category, category)
            summaries, links = search_news_with_links(query, limit=3)
            combined = "\n".join(summaries) if summaries else ""
            score, reasoning = analyze_category_with_reasoning(category, combined)
            progress_store[category] = {
                "progress": score,
                "last_updated": today,
                "articles": links,
                "reasoning": reasoning,
            }
        except Exception as e:
            log.error("Progress analysis failed for %s: %s", category, e)
    _analyzed_at = time.time()
    return len(AGENDA_CATEGORIES)


def _is_stale() -> bool:
    return not _analyzed_at or (time.time() - _analyzed_at) > CACHE_TTL_SECONDS


async def _refresh_in_background() -> None:
    global _refreshing
    if _refreshing:
        return
    _refreshing = True
    try:
        await asyncio.to_thread(refresh_progress)
    except Exception as e:
        log.error("Background progress refresh failed: %s", e)
    finally:
        _refreshing = False


@router.get("/progress", response_model=ProgressList)
async def get_progress():
    """Progress for the 5 agenda categories. Returns immediately; refreshes stale
    data in the background rather than serving months-old figures forever."""
    if _is_stale() and not _refreshing:
        asyncio.create_task(_refresh_in_background())
    return ProgressList(items=_items())


@router.post("/progress/analyze", response_model=ProgressList)
async def analyze_progress():
    """Force a re-analysis now."""
    await asyncio.to_thread(refresh_progress)
    return ProgressList(items=_items())


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
