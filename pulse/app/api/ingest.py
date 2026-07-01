from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from pulse.app.api.dependencies import cfg, db_pool
from pulse.app.config import PulseConfig
from pulse.app.db.repository import SentimentRepository
from pulse.app.ingestion.pipeline import run_ingest
from pulse.app.models.sentiment import IngestRequest, IngestResult

router = APIRouter()


class IngestRangeRequest(BaseModel):
    symbols: list[str]
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    lookback_hours: int = 24


@router.post("/news", response_model=IngestResult)
async def ingest_news(
    req: IngestRangeRequest,
    config: PulseConfig = Depends(cfg),
    pool: Any = Depends(db_pool),
) -> IngestResult:
    return await run_ingest(
        req.symbols, config, SentimentRepository(pool),
        sources=["news"], start=req.start, end=req.end,
    )


@router.post("/sec", response_model=IngestResult)
async def ingest_sec(
    req: IngestRangeRequest,
    config: PulseConfig = Depends(cfg),
    pool: Any = Depends(db_pool),
) -> IngestResult:
    return await run_ingest(
        req.symbols, config, SentimentRepository(pool),
        sources=["sec"], start=req.start, end=req.end,
    )


@router.post("/reddit", response_model=IngestResult)
async def ingest_reddit(
    req: IngestRequest,
    config: PulseConfig = Depends(cfg),
    pool: Any = Depends(db_pool),
) -> IngestResult:
    return await run_ingest(
        req.symbols, config, SentimentRepository(pool),
        sources=["reddit"], lookback_hours=req.lookback_hours,
    )


@router.post("/stocktwits", response_model=IngestResult)
async def ingest_stocktwits(
    req: IngestRequest,
    config: PulseConfig = Depends(cfg),
    pool: Any = Depends(db_pool),
) -> IngestResult:
    return await run_ingest(req.symbols, config, SentimentRepository(pool), sources=["stocktwits"])


@router.post("/all", response_model=IngestResult)
async def ingest_all(
    req: IngestRequest,
    config: PulseConfig = Depends(cfg),
    pool: Any = Depends(db_pool),
) -> IngestResult:
    return await run_ingest(
        req.symbols, config, SentimentRepository(pool), lookback_hours=req.lookback_hours,
    )
