import datetime
from typing import Dict, List
import feedparser
from app.services.ai_service import assign_tag_with_ai

RSS_URLS = [
    "http://feeds.reuters.com/Reuters/worldNews",
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://apnews.com/rss/apf-topnews",
]


def fetch_geopolitical_updates() -> List[Dict]:
    """Fetch and tag geopolitical news from RSS feeds."""
    articles = []

    for url in RSS_URLS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:1]:
                title = entry.title
                summary = entry.summary if hasattr(entry, "summary") else ""
                full_text = f"Title: {title}\nSummary: {summary}"

                try:
                    tag = assign_tag_with_ai(full_text)
                except Exception as e:
                    print(f"ERROR: Exception during AI tagging for '{title}': {e}")
                    tag = "Untagged (AI Error)"

                date_str = "N/A"
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    date_str = datetime.datetime(
                        *entry.published_parsed[:6]
                    ).strftime("%Y-%m-%d")

                articles.append({
                    "title": title,
                    "date": date_str,
                    "summary": summary,
                    "link": entry.link,
                    "tags": [tag] if tag and tag != "None" else [],
                })
        except Exception as e:
            print(f"ERROR: Failed to fetch RSS feed from {url}: {e}")

    return articles
