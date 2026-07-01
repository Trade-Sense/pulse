import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pulse.app.api.routes import api_router
from pulse.app.config import get_config
from pulse.app.db.connection import close_pool, get_pool, init_pool
from pulse.app.db.repository import SentimentRepository
from pulse.app.ingestion.pipeline import run_ingest
from pulse.app.scoring.scorer import warm_up

logger = logging.getLogger(__name__)

app_config = get_config()
loop = asyncio.new_event_loop()


async def _news_ingest_job() -> None:
    try:
        result = await run_ingest(
            app_config.target_symbols,
            app_config,
            SentimentRepository(get_pool()),
            sources=["news"],
            lookback_hours=app_config.news_ingest_interval_hours + 1,
        )
        logger.info("Scheduled news ingest: %d events ingested", result.ingested)
    except Exception:
        logger.exception("Scheduled news ingest failed")


async def _reddit_ingest_job() -> None:
    try:
        result = await run_ingest(
            app_config.target_symbols,
            app_config,
            SentimentRepository(get_pool()),
            sources=["reddit"],
            lookback_hours=app_config.ingest_lookback_hours,
        )
        logger.info("Scheduled reddit ingest: %d events ingested", result.ingested)
    except Exception:
        logger.exception("Scheduled reddit ingest failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool(app_config.db_url)
    try:
        warm_up()
    except Exception:
        logger.exception("FinBERT warm-up failed — scoring will be unavailable until resolved")

    now = datetime.now(timezone.utc)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _news_ingest_job,
        trigger="interval",
        hours=app_config.news_ingest_interval_hours,
        id="news_ingest",
        replace_existing=True,
        next_run_time=now,
    )
    scheduler.add_job(
        _reddit_ingest_job,
        trigger="interval",
        hours=app_config.reddit_ingest_interval_hours,
        id="reddit_ingest",
        replace_existing=True,
        next_run_time=now,
    )
    scheduler.start()
    logger.info(
        "News ingest scheduled every %dh, Reddit every %dh — %d symbols (both fire immediately)",
        app_config.news_ingest_interval_hours,
        app_config.reddit_ingest_interval_hours,
        len(app_config.target_symbols),
    )

    yield

    scheduler.shutdown(wait=False)
    await close_pool()


app = FastAPI(title="Pulse — Sentiment Intelligence", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_config.allow_origins,
    allow_credentials=app_config.allow_credentials,
    allow_methods=app_config.allow_methods,
    allow_headers=app_config.allow_headers,
)
app.include_router(api_router)
