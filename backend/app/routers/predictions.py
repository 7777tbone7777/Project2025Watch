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
import json
import logging
from pathlib import Path
import time
from typing import List, Optional

from fastapi import APIRouter

from app.data.predictions_data import PREDICTIONS
from app.models.schemas import ArticleLink, Prediction, PredictionList, ScoreResponse
from app.services.ai_service import UNKNOWN, score_prediction_with_reasoning
from app.services.wikipedia_service import search_with_links as wiki_search
from app.services.federal_register_service import search_with_links as fr_search
from app.services.news_service import search_news_with_links

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
        reasoning=(scored or {}).get("reasoning", ""),
        articles=[ArticleLink(**a) for a in (scored or {}).get("articles", [])],
    )


def get_predictions() -> List[Prediction]:
    return [_base(i, p, _scores.get(i)) for i, p in enumerate(PREDICTIONS)]


def _score_one(index: int, item: dict) -> dict:
    """Search news for a single proposal and score it. Never raises."""
    try:
        # Search the KEYWORDS, not the prediction sentence. Searching the full
        # sentence is what produced zero matches for every prediction.
        # Two sources, deliberately. The Federal Register is the record of what
        # government actually DID and reaches back to 2025; NewsAPI's free tier
        # only sees about a month, which is why proposals enacted early in the
        # administration scored "Not Started" forever.
        fr_text, fr_links = ("", [])
        if item.get("fr_query"):
            fr_text, fr_links = fr_search(item["fr_query"], per_page=4)

        query = item.get("keywords") or item["prediction"]
        summaries, news_links = search_news_with_links(query, limit=3)
        news_text = "\n".join(summaries) if summaries else ""

        parts = [p for p in (fr_text, ("RECENT NEWS COVERAGE:\n" + news_text) if news_text else "") if p]
        links = fr_links + news_links

        combined = "\n\n".join(parts)
        status, reasoning = score_prediction_with_reasoning(item["prediction"], combined)

        # Second pass only for proposals the first could not settle.
        #
        # An earlier gate tested whether the evidence was SHORT, which stopped
        # working the moment full Federal Register text made it long. Length was
        # never the point: 3,000 characters about Reduction in Force is long and
        # still says nothing about eliminating the Department of Education. What
        # matters is whether the evidence answered the question, and the scorer
        # already reports that.
        #
        # The second source is Wikipedia rather than GDELT. GDELT has the archive
        # depth but allows one request every five seconds and returned 429 well
        # inside that budget, and its article list carries headlines with no text.
        # Wikipedia needs no key, is not meaningfully throttled, and carries prose
        # that settles these cases outright — the CPB defunding was legislation and
        # the Education teardown reported administrative action, so neither appears
        # in the Register as a rule.
        if status in (UNKNOWN, "Not Started"):
            wiki_query = item.get("wiki_query") or item.get("keywords") or item["prediction"]
            wiki_text, wiki_links = wiki_search(wiki_query)
            if wiki_text:
                retry_evidence = "\n\n".join(parts + [wiki_text])
                retry_status, retry_reasoning = score_prediction_with_reasoning(
                    item["prediction"], retry_evidence)
                # Always take the second pass. It saw strictly more evidence, so
                # its answer is the better-informed one even when it is still
                # Unknown — and keeping the first pass instead hid whether the
                # extra source had been consulted at all, which made this
                # impossible to debug from the page: every row read "wiki: no"
                # whether the lookup had run or not.
                combined, status, reasoning = retry_evidence, retry_status, retry_reasoning
                links = links + wiki_links

        # Keep the articles the call was based on, so a status can be checked
        # rather than believed.
        return {"result": status, "news_match": combined,
                "reasoning": reasoning, "articles": links}
    except Exception as e:
        # Second copy of the same mistake: a failed search or scoring call used to
        # be published as "Not Started", which is a claim about the world rather
        # than about us. UNKNOWN keeps them apart, and the message says what broke.
        log.error("Scoring failed for %r: %s", item["prediction"][:60], e, exc_info=True)
        return {"result": UNKNOWN, "news_match": "",
                "reasoning": f"Scoring failed ({type(e).__name__}): {e}", "articles": []}


# Scores live in memory, so a restart emptied them and the page showed every
# proposal as unscored until somebody noticed and pressed the button. A full pass
# now takes minutes, so that gap is not small. The cache file covers restarts;
# Railway's filesystem does not survive a redeploy, which is what the startup
# refresh below is for.
_CACHE = Path(__file__).resolve().parent.parent.parent / "data" / "scores.json"


def _save_scores() -> None:
    try:
        _CACHE.parent.mkdir(parents=True, exist_ok=True)
        _CACHE.write_text(json.dumps({"scored_at": _scored_at,
                                      "scores": {str(k): v for k, v in _scores.items()}}))
    except Exception as e:
        log.warning("Could not cache scores: %s", e)


def _load_scores() -> None:
    """Restore cached scores at startup. Absence is normal, not an error."""
    global _scores, _scored_at
    try:
        if not _CACHE.exists():
            return
        data = json.loads(_CACHE.read_text())
        _scores = {int(k): v for k, v in (data.get("scores") or {}).items()}
        _scored_at = float(data.get("scored_at") or 0)
        log.info("Restored %d cached scores", len(_scores))
    except Exception as e:
        log.warning("Could not restore cached scores: %s", e)


def refresh_scores() -> int:
    """Re-score every proposal. Returns how many were scored. Blocking.

    Results publish one at a time rather than all at the end. A full pass now
    takes minutes — full Federal Register text per proposal, and a throttled
    GDELT lookup for anything the first pass could not decide — and swapping the
    whole set in at the finish means a page polling during that run sees nothing
    change and reasonably concludes the button did nothing.
    """
    global _scores, _scored_at
    results = dict(_scores)
    for i, item in enumerate(PREDICTIONS):
        results[i] = _score_one(i, item)
        _scores = dict(results)
        _scored_at = time.time()
        _save_scores()
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
    """Start a re-score and return immediately with whatever is current.

    Scoring every proposal now costs far more than a request can hold: full
    Federal Register text per proposal, and for anything the first pass could not
    decide, a GDELT lookup bound by one request every five seconds plus a second
    scoring call. Awaiting that returned 502 from the proxy after 56 seconds, and
    a timed-out request looks exactly like a broken one.

    The work continues in the background. Poll /predictions/status and refetch
    when `refreshing` goes false.
    """
    if _refreshing:
        return ScoreResponse(
            predictions=get_predictions(),
            message="Already scoring — results update as each proposal finishes",
        )
    asyncio.create_task(_refresh_in_background())
    return ScoreResponse(
        predictions=get_predictions(),
        message=f"Scoring {len(PREDICTIONS)} proposals in the background",
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
