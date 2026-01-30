from typing import List
from fastapi import APIRouter
from app.models.schemas import Prediction, PredictionList, ScoreResponse
from app.services.news_service import search_news
from app.services.ai_service import score_prediction_status

router = APIRouter()

PREDICTIONS_DATA = [
    {"timeframe": "Jan-Mar 2025", "prediction": "Executive Order 1: Streamline Federal Bureaucracy", "result": "Not Started", "news_match": ""},
    {"timeframe": "Jan-Mar 2025", "prediction": "Policy Change 1: Energy Deregulation", "result": "Not Started", "news_match": ""},
    {"timeframe": "Apr-Jun 2025", "prediction": "Judicial Appointment 1: Conservative Judge", "result": "Not Started", "news_match": ""},
    {"timeframe": "Apr-Jun 2025", "prediction": "Agency Restructuring 1: Department of Education changes", "result": "Not Started", "news_match": ""},
    {"timeframe": "Jul-Sep 2025", "prediction": "Legislative Push 1: Immigration Reform", "result": "Not Started", "news_match": ""},
    {"timeframe": "Jul-Sep 2025", "prediction": "Withdrawal from International Treaty", "result": "Not Started", "news_match": ""},
    {"timeframe": "Oct-Dec 2025", "prediction": "Executive Order 2: Re-evaluating Environmental Regulations", "result": "Not Started", "news_match": ""},
]


def get_predictions() -> List[Prediction]:
    return [
        Prediction(
            id=i,
            timeframe=p["timeframe"],
            prediction=p["prediction"],
            result=p["result"],
            news_match=p["news_match"],
        )
        for i, p in enumerate(PREDICTIONS_DATA)
    ]


@router.get("/predictions", response_model=PredictionList)
async def list_predictions():
    """Get all predictions (unscored)."""
    return PredictionList(predictions=get_predictions())


@router.post("/predictions/score", response_model=ScoreResponse)
async def score_predictions():
    """Fetch news and score all predictions via AI."""
    scored_predictions = []

    for i, pred in enumerate(PREDICTIONS_DATA):
        prediction_text = pred["prediction"]
        search_query = f"Project 2025 {prediction_text}"

        news_summaries = search_news(search_query)
        combined_news = "\n".join(news_summaries) if news_summaries else ""

        new_status = score_prediction_status(prediction_text, combined_news)

        scored_predictions.append(
            Prediction(
                id=i,
                timeframe=pred["timeframe"],
                prediction=prediction_text,
                result=new_status,
                news_match=combined_news,
            )
        )

    return ScoreResponse(
        predictions=scored_predictions,
        message="Scoring complete",
    )
