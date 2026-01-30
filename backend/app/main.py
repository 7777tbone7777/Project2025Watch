from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import predictions, geopolitical, progress, reports

app = FastAPI(
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
