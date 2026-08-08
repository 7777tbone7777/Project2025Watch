"""Prediction tracking.

Three bugs made this endpoint useless, all of which had to be fixed together:

1. The predictions were numbered placeholders ("Policy Change 1: Energy
   Deregulation") with no relationship to the actual Mandate for Leadership.
2. News search used the prediction text verbatim, so it searched for
   "Project 2025 Policy Change 1: Energy Deregulation" and matched nothing —
   every prediction had zero news matches.
3. Scoring returned its results and never stored them, so the next GET served
   the hardcoded "Not Started" again. Nothing could ever change status.

Now: real proposals with dedicated search keywords, and scores cached in-process
with a TTL. Refresh is kicked off in the background so a request never hangs
waiting on ~20 news+LLM round trips, and a cold container self-heals rather than
serving stale placeholders forever.
"""
import asyncio
import logging
import time
from typing import List, Optional

from fastapi import APIRouter

from app.data.predictions_data import PREDICTIONS
from app.models.schemas import Prediction, PredictionList, ScoreResponse
from app.services.ai_service import score_prediction_status
from app.services.news_service import search_news

log = logging.getLogger(__name__)
router = APIRouter()

# Scores live in memory: this app has no database, and a Railway container has an
# ephemeral filesystem, so a file would not survive a deploy either. The TTL plus
# background refresh means a restart repopulates itself instead of serving the
# hardcoded defaults indefinitely — which is exactly how the old version ended up
# showing February data in August.
CACHE_TTL_SECONDS = 6 * 3600

_scores: dict = {}          # index -> {"result": str, "news_match": str}
_scored_at: float = 0.0
_refreshing = False


def _base(index: int, item: dict, scored: Optional[dict]) -> Prediction:
    return Prediction(
        id=index,
        timeframe=item["timeframe"],
        prediction=item["prediction"],
        agency=item.get("agency", ""),
        source=item.get("source", ""),
        result=(scored or {}).get("result", "Not Started"),
        news_match=(scored or {}).get("news_match", ""),
    )


def get_predictions() -> List[Prediction]:
    return [_base(i, p, _scores.get(i)) for i, p in enumerate(PREDICTIONS)]


def _score_one(index: int, item: dict) -> dict:
    """Search news for a single proposal and score it. Never raises."""
    try:
        # Search the KEYWORDS, not the prediction sentence. Searching the full
        # sentence is what produced zero matches for every prediction.
        query = item.get("keywords") or item["prediction"]
        summaries = search_news(query)
        combined = "\n".join(summaries) if summaries else ""
        status = score_prediction_status(item["prediction"], combined)
        return {"result": status, "news_match": combined}
    except Exception as e:
        log.error("Scoring failed for %r: %s", item["prediction"][:60], e)
        return {"result": "Not Started", "news_match": ""}


def refresh_scores() -> int:
    """Re-score every proposal. Returns how many were scored. Blocking."""
    global _scores, _scored_at
    results = {}
    for i, item in enumerate(PREDICTIONS):
        results[i] = _score_one(i, item)
    _scores = results
    _scored_at = time.time()
    log.info("Scored %d predictions", len(results))
    return len(results)


def _is_stale() -> bool:
    return not _scores or (time.time() - _scored_at) > CACHE_TTL_SECONDS


async def _refresh_in_background() -> None:
    """Refresh without making the caller wait on ~20 news + LLM round trips."""
    global _refreshing
    if _refreshing:
        return
    _refreshing = True
    try:
        await asyncio.to_thread(refresh_scores)
    except Exception as e:
        log.error("Background scoring failed: %s", e)
    finally:
        _refreshing = False


@router.get("/predictions", response_model=PredictionList)
async def list_predictions():
    """Current predictions with their last known status.

    Returns immediately. If the cache is stale a refresh is started in the
    background, so the next poll reflects it — the page never blocks on scoring.
    """
    if _is_stale() and not _refreshing:
        asyncio.create_task(_refresh_in_background())
    return PredictionList(predictions=get_predictions())


@router.post("/predictions/score", response_model=ScoreResponse)
async def score_predictions():
    """Force a re-score now and return the results."""
    count = await asyncio.to_thread(refresh_scores)
    return ScoreResponse(
        predictions=get_predictions(),
        message=f"Scored {count} predictions against current news",
    )


@router.get("/predictions/status")
async def scoring_status():
    """Whether the figures being served are scored, and how old they are."""
    return {
        "scored": bool(_scores),
        "refreshing": _refreshing,
        "age_seconds": None if not _scored_at else int(time.time() - _scored_at),
        "stale": _is_stale(),
        "total_predictions": len(PREDICTIONS),
    }
