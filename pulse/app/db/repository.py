from datetime import date, datetime
from typing import Optional

import asyncpg  # type: ignore[import]

from pulse.app.models.sentiment import DailySentiment, SentimentEvent


class SentimentRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def event_exists(self, content_hash: str) -> bool:
        async with self._pool.acquire() as conn:
            val = await conn.fetchval(
                "SELECT 1 FROM sentiment_events WHERE content_hash = $1 LIMIT 1",
                content_hash,
            )
            return val is not None

    async def insert_events_bulk(self, events: list[SentimentEvent]) -> int:
        if not events:
            return 0
        async with self._pool.acquire() as conn:
            rows = [
                (
                    e.symbol, e.ts, e.source, e.subreddit,
                    e.score, e.confidence, e.engagement,
                    e.content_hash, e.url, e.raw_text,
                )
                for e in events
            ]
            await conn.executemany(
                """
                INSERT INTO sentiment_events
                    (symbol, ts, source, subreddit, score, confidence,
                     engagement, content_hash, url, raw_text)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT DO NOTHING
                """,
                rows,
            )
            return len(rows)

    async def upsert_daily(self, daily: DailySentiment) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO daily_sentiment
                    (symbol, date, news_score, sec_score, reddit_score, stocktwits_score,
                     news_reddit_divergence, mention_count, reddit_mention_count,
                     mention_velocity, avg_engagement, bullish_pct, bearish_pct)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                ON CONFLICT (symbol, date) DO UPDATE SET
                    news_score             = EXCLUDED.news_score,
                    sec_score              = EXCLUDED.sec_score,
                    reddit_score           = EXCLUDED.reddit_score,
                    stocktwits_score       = EXCLUDED.stocktwits_score,
                    news_reddit_divergence = EXCLUDED.news_reddit_divergence,
                    mention_count          = EXCLUDED.mention_count,
                    reddit_mention_count   = EXCLUDED.reddit_mention_count,
                    mention_velocity       = EXCLUDED.mention_velocity,
                    avg_engagement         = EXCLUDED.avg_engagement,
                    bullish_pct            = EXCLUDED.bullish_pct,
                    bearish_pct            = EXCLUDED.bearish_pct
                """,
                daily.symbol, daily.date,
                daily.news_score, daily.sec_score,
                daily.reddit_score, daily.stocktwits_score,
                daily.news_reddit_divergence,
                daily.mention_count, daily.reddit_mention_count,
                daily.mention_velocity, daily.avg_engagement,
                daily.bullish_pct, daily.bearish_pct,
            )

    async def get_daily(
        self, symbol: str, start: date, end: date
    ) -> list[DailySentiment]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM daily_sentiment
                WHERE symbol = $1 AND date >= $2 AND date <= $3
                ORDER BY date
                """,
                symbol, start, end,
            )
            return [DailySentiment(**dict(r)) for r in rows]

    async def get_events(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        source: Optional[str] = None,
        min_confidence: float = 0.3,
    ) -> list[SentimentEvent]:
        async with self._pool.acquire() as conn:
            if source:
                rows = await conn.fetch(
                    """
                    SELECT * FROM sentiment_events
                    WHERE symbol = $1 AND ts >= $2 AND ts <= $3
                      AND source = $4 AND confidence >= $5
                    ORDER BY ts DESC
                    """,
                    symbol, start, end, source, min_confidence,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT * FROM sentiment_events
                    WHERE symbol = $1 AND ts >= $2 AND ts <= $3
                      AND confidence >= $4
                    ORDER BY ts DESC
                    """,
                    symbol, start, end, min_confidence,
                )
            return [SentimentEvent(**dict(r)) for r in rows]

    async def get_reddit_count_by_date(self, symbol: str, d: date) -> int:
        async with self._pool.acquire() as conn:
            val = await conn.fetchval(
                """
                SELECT COUNT(*) FROM sentiment_events
                WHERE symbol = $1 AND source = 'reddit' AND ts::date = $2
                """,
                symbol, d,
            )
            return int(val) if val else 0

    async def get_latest_sentiment_dates(self) -> dict[str, date | None]:
        """Latest date pulse holds sentiment for, per source and overall — pulse's watermark."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    MAX(date) FILTER (WHERE news_score   IS NOT NULL) AS news,
                    MAX(date) FILTER (WHERE sec_score    IS NOT NULL) AS sec,
                    MAX(date) FILTER (WHERE reddit_score IS NOT NULL) AS reddit,
                    MAX(date)                                          AS any
                FROM daily_sentiment
                """
            )
            return {"news": row["news"], "sec": row["sec"], "reddit": row["reddit"], "any": row["any"]}
