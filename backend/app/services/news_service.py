from typing import List
import requests
from app.config import settings

NEWS_API_BASE_URL = "https://newsapi.org/v2/everything"


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
