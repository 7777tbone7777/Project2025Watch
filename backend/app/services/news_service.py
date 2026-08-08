from typing import List, Dict, Tuple
import logging

import requests
from app.config import settings

log = logging.getLogger(__name__)

# Last failure reason, so callers can report it instead of silently showing zero.
LAST_ERROR = {"reason": ""}


def clear_last_error():
    LAST_ERROR["reason"] = ""


def last_error() -> str:
    return LAST_ERROR["reason"]


NEWS_API_BASE_URL = "https://newsapi.org/v2/everything"


def search_news_with_links(query: str, limit: int = 2) -> Tuple[List[str], List[Dict]]:
    """Search news articles and return both summaries and article links."""
    if not settings.news_api_key:
        print("ERROR: NEWS_API_KEY not configured")
        return [], []

    params = {
        "q": query,
        "language": "en",
        "sortBy": "relevancy",
        "apiKey": settings.news_api_key,
        "pageSize": 5,
    }

    try:
        response = requests.get(NEWS_API_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        summaries = []
        links = []
        if data and data.get("articles"):
            for article in data["articles"]:
                if article.get("description"):
                    summaries.append(f"{article['title']}. {article['description']}")
                    if len(links) < limit and article.get("url"):
                        links.append({
                            "title": article["title"][:80] + "..." if len(article["title"]) > 80 else article["title"],
                            "url": article["url"],
                        })
        return summaries, links

    except Exception as e:
        # Record WHY, so a caller can tell "no coverage exists" from "we could not
        # ask". Returning [] for both made a rate-limited request render as a
        # confident 0% with the caption "No news coverage found".
        detail = str(e)
        if "429" in detail or "too many requests" in detail.lower():
            LAST_ERROR["reason"] = "NewsAPI rate limit reached (100 requests/day on the free tier)"
        else:
            LAST_ERROR["reason"] = f"News lookup failed: {type(e).__name__}"
        log.error("News search failed for %r: %s", query[:60], e)
        return [], []


def search_news(query: str) -> List[str]:
    """Search news articles using NewsAPI."""
    if not settings.news_api_key:
        print("ERROR: NEWS_API_KEY not configured")
        return []

    params = {
        "q": query,
        "language": "en",
        "sortBy": "relevancy",
        "apiKey": settings.news_api_key,
        "pageSize": 5,
    }

    try:
        response = requests.get(NEWS_API_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        articles = []
        if data and data.get("articles"):
            for article in data["articles"]:
                if article.get("description"):
                    articles.append(f"{article['title']}. {article['description']}")
        return articles

    except requests.exceptions.Timeout:
        print(f"ERROR: News API Timeout for '{query}'")
        return []
    except requests.exceptions.HTTPError as e:
        print(f"ERROR: News API HTTP Error for '{query}': {e.response.status_code}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"ERROR: News API Request Exception for '{query}': {e}")
        return []
    except Exception as e:
        print(f"ERROR: Unexpected error in news search for '{query}': {e}")
        return []
