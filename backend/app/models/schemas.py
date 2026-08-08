from pydantic import BaseModel
from typing import List


class Prediction(BaseModel):
    id: int
    timeframe: str
    prediction: str
    result: str
    news_match: str
    # Which department the proposal concerns, and where it is documented, so a
    # reader can verify a status rather than taking the tracker's word for it.
    agency: str = ""
    source: str = ""


class PredictionList(BaseModel):
    predictions: List[Prediction]


class ArticleLink(BaseModel):
    title: str
    url: str


class ProgressItem(BaseModel):
    title: str
    progress: int
    last_updated: str
    articles: List[ArticleLink] = []


class ProgressList(BaseModel):
    items: List[ProgressItem]


class AlertStatus(BaseModel):
    triggered: bool
    reason: str


class GeopoliticalArticle(BaseModel):
    title: str
    date: str
    summary: str
    link: str
    tags: List[str]


class GeopoliticalFeed(BaseModel):
    articles: List[GeopoliticalArticle]


class ScoreResponse(BaseModel):
    predictions: List[Prediction]
    message: str
