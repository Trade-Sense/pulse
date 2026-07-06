import logging
from datetime import datetime, timedelta, timezone

from pulse.app import metrics
from pulse.app.config import PulseConfig
from pulse.app.db.repository import SentimentRepository
from pulse.app.ingestion.news import AlpacaNewsIngester
from pulse.app.ingestion.reddit import RedditIngester
from pulse.app.ingestion.sec import SECIngester
from pulse.app.ingestion.stocktwits import StockTwitsIngester
from pulse.app.models.sentiment import IngestResult, SentimentEvent
from pulse.app.services.aggregator import aggregate_daily

log = logging.getLogger(__name__)


async def run_ingest(
    symbols: list[str],
    cfg: PulseConfig,
    repo: SentimentRepository,
    sources: list[str] | None = None,
    lookback_hours: int | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> IngestResult:
    """Run ingestion for the given sources (default: all). Returns aggregate counts."""
    hours = lookback_hours or cfg.ingest_lookback_hours
    now = datetime.now(timezone.utc)
    end_dt = end or now
    start_dt = start or (now - timedelta(hours=hours))

    all_sources = sources or ["news", "sec", "reddit"]

    ingesters = {
        "news": AlpacaNewsIngester(cfg.alpaca_api_key, cfg.alpaca_api_secret, cfg.min_confidence),
        "sec": SECIngester(cfg.min_confidence, cfg.sec_user_agent),
        "reddit": RedditIngester(cfg.reddit_user_agent, cfg.min_confidence),
        "stocktwits": StockTwitsIngester(cfg.min_confidence),
    }

    all_events: list[SentimentEvent] = []
    errors: list[str] = []

    for source in all_sources:
        ingester = ingesters.get(source)
        if ingester is None:
            continue
        try:
            if source == "reddit":
                events = await ingester.ingest(
                    symbols,
                    subreddits=cfg.target_subreddits,
                    lookback_hours=hours,
                )
            else:
                events = await ingester.ingest(symbols, start=start_dt, end=end_dt)
            all_events.extend(events)
            metrics.EVENTS_INGESTED.labels(source=source).inc(len(events))
            log.info("Ingested %d events from %s", len(events), source)
        except Exception as exc:
            metrics.SOURCE_FETCH_ERRORS.labels(source=source).inc()
            msg = f"{source}: {exc}"
            log.warning("Ingestion failed — %s", msg)
            errors.append(msg)

    inserted = await repo.insert_events_bulk(all_events)

    # Build daily aggregates
    prev_counts: dict[str, int] = {}
    prev_day = (end_dt - timedelta(days=1)).date()
    for sym in symbols:
        prev_counts[sym] = await repo.get_reddit_count_by_date(sym, prev_day)

    daily_rows = aggregate_daily(all_events, prev_counts)
    for row in daily_rows:
        await repo.upsert_daily(row)
        metrics.DAILY_UPSERTS.inc()

    discarded = len(all_events) - inserted
    if discarded > 0:
        metrics.EVENTS_DISCARDED.labels(reason="dedup").inc(discarded)
    return IngestResult(
        ingested=inserted,
        scored=len(all_events),
        discarded=discarded,
        errors=errors,
    )
