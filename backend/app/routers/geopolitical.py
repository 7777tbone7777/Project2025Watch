from fastapi import APIRouter
from app.models.schemas import GeopoliticalFeed, GeopoliticalArticle
from app.services.rss_service import fetch_geopolitical_updates

router = APIRouter()


@router.get("/geopolitical", response_model=GeopoliticalFeed)
async def get_geopolitical_feed():
    """Get tagged RSS articles from Reuters/BBC/AP."""
    articles_data = fetch_geopolitical_updates()
    articles = [
        GeopoliticalArticle(
            title=a["title"],
            date=a["date"],
            summary=a["summary"],
            link=a["link"],
            tags=a["tags"],
        )
        for a in articles_data
    ]
    return GeopoliticalFeed(articles=articles)
