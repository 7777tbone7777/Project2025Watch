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
    # Incomplete counts as missing. A deploy mid-run kills the background task and
    # leaves a partial cache behind; testing only for emptiness meant the next
    # startup saw "some scores" and never finished the job, so the proposals that
    # had not been reached stayed blank indefinitely.
    expected = len(predictions.PREDICTIONS)
    if len(predictions._scores) < expected:
        log.info("Cached scores incomplete (%d of %d) — scoring in the background",
                 len(predictions._scores), expected)
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
