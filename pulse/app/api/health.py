from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends

from pulse.app.api.dependencies import db_pool
from pulse.app.scoring.finbert import _get_pipeline

if TYPE_CHECKING:
    import asyncpg  # type: ignore[import]

router = APIRouter()


@router.get("/health")
async def health(pool: Any = Depends(db_pool)) -> dict:
    db_status = "connected"
    try:
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
    except Exception:
        db_status = "error"

    finbert_status = "ready" if _get_pipeline.cache_info().currsize > 0 else "not_loaded"

    return {"status": "ok", "db": db_status, "finbert": finbert_status}
