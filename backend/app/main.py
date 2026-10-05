import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import predictions, geopolitical, progress, reports

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Restore cached scores, and rebuild them if the cache did not survive.

    Scores are held in memory, so a restart emptied them and every proposal
    showed as unscored until somebody pressed the button — and a full pass now
    takes minutes, so that window is not brief. The cache file covers a restart.
    Railway replaces the filesystem on each deploy, so after one the cache is
    gone too, and the only thing that refills the tracker is scoring again.

    Started as a background task: a deploy must not wait minutes for the first
    request to be served.
    """
    predictions._load_scores()
    if not predictions._scores:
        log.info("No cached scores after startup — scoring in the background")
        asyncio.create_task(predictions._refresh_in_background())
    yield


app = FastAPI(
    lifespan=lifespan,
    title="Project 2025 Tracker API",
    description="API for tracking Project 2025 predictions and geopolitical events",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predictions.router, prefix="/api", tags=["predictions"])
app.include_router(geopolitical.router, prefix="/api", tags=["geopolitical"])
app.include_router(progress.router, prefix="/api", tags=["progress"])
app.include_router(reports.router, prefix="/api", tags=["reports"])


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
