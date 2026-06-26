from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from pulse.app.api.dependencies import db_pool
from pulse.app.db.repository import SentimentRepository
from pulse.app.models.sentiment import DailySentiment, SentimentEvent

router = APIRouter()


@router.get("/{symbol}/daily", response_model=list[DailySentiment])
async def get_daily(
    symbol: str,
    start: date = Query(...),
    end: date = Query(...),
    pool: Any = Depends(db_pool),
) -> list[DailySentiment]:
    repo = SentimentRepository(pool)
    return await repo.get_daily(symbol.upper(), start, end)


@router.get("/{symbol}/events", response_model=list[SentimentEvent])
async def get_events(
    symbol: str,
    start: datetime = Query(...),
    end: datetime = Query(...),
    source: Optional[str] = Query(default=None),
    min_confidence: float = Query(default=0.3),
    pool: Any = Depends(db_pool),
) -> list[SentimentEvent]:
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    repo = SentimentRepository(pool)
    return await repo.get_events(symbol.upper(), start, end, source, min_confidence)
