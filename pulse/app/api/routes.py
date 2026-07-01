from fastapi import APIRouter

from pulse.app.api import health, ingest, sentiment

api_router = APIRouter()
api_router.include_router(health.router, prefix="/api/v1")
api_router.include_router(sentiment.router, prefix="/api/v1/sentiment")
api_router.include_router(ingest.router, prefix="/api/v1/ingest")
