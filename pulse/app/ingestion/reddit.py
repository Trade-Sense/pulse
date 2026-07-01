import hashlib
import logging
import re
from datetime import datetime, timedelta, timezone

from pulse.app.ingestion.base import BaseIngester
from pulse.app.models.sentiment import ScoreResult, SentimentEvent
from pulse.app.scoring.finbert import score_batch
from pulse.app.services.symbol_cache import SymbolCache

log = logging.getLogger(__name__)

_FALSE_POSITIVES = frozenset({"I", "A", "FOR", "ARE", "IT", "AT", "BE", "DO", "GO", "CEO", "IPO", "ETF"})


class RedditIngester(BaseIngester):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        user_agent: str,
        symbol_cache: SymbolCache,
        min_confidence: float = 0.3,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._user_agent = user_agent
        self._symbol_cache = symbol_cache
        self._min_confidence = min_confidence

    async def ingest(
        self,
        symbols: list[str],
        *,
        subreddits: list[str],
        lookback_hours: int = 24,
        **kwargs: object,
    ) -> list[SentimentEvent]:
        try:
            import asyncpraw  # type: ignore[import]
        except ImportError:
            log.warning("asyncpraw not installed — skipping Reddit ingestion")
            return []

        reddit = asyncpraw.Reddit(
            client_id=self._client_id,
            client_secret=self._client_secret,
            user_agent=self._user_agent,
        )

        cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        seen: set[str] = set()
        candidates: list[tuple[str, str, str, float]] = []  # (symbol, url, text, created_utc)

        try:
            for sub_name in subreddits:
                subreddit = await reddit.subreddit(sub_name)
                for sym in symbols:
                    ticker_info = self._symbol_cache.get_ticker_info(sym)
                    company_name = ticker_info.title if ticker_info else ""
                    async for post in subreddit.search(
                        sym, time_filter="day", limit=50, sort="new"
                    ):
                        created = datetime.fromtimestamp(post.created_utc, tz=timezone.utc)
                        if created < cutoff:
                            continue
                        text = f"{post.title} {post.selftext or ''}"
                        if not self._mentions_symbol(text, sym, company_name):
                            continue
                        url = f"https://reddit.com{post.permalink}"
                        content_hash = hashlib.sha256(f"reddit:{url}".encode()).hexdigest()
                        if content_hash in seen:
                            continue
                        seen.add(content_hash)
                        engagement = float(post.score + post.num_comments)
                        candidates.append((sym, url, text[:2000], post.created_utc, content_hash, engagement, sub_name))
        finally:
            await reddit.close()

        if not candidates:
            return []

        texts = [c[2] for c in candidates]
        scores: list[ScoreResult] = score_batch(texts)

        events: list[SentimentEvent] = []
        for (sym, url, text, created_utc, content_hash, engagement, sub_name), score_result in zip(candidates, scores):
            if score_result.confidence < self._min_confidence:
                continue
            events.append(
                SentimentEvent(
                    symbol=sym,
                    ts=datetime.fromtimestamp(created_utc, tz=timezone.utc),
                    source="reddit",
                    subreddit=sub_name,
                    score=score_result.score,
                    confidence=score_result.confidence,
                    engagement=engagement,
                    content_hash=content_hash,
                    url=url,
                    raw_text=text[:500],
                )
            )
        return events

    @staticmethod
    def _mentions_symbol(text: str, ticker: str, company_name: str) -> bool:
        if ticker in _FALSE_POSITIVES:
            return False
        if f"${ticker}" in text:
            return True
        if re.search(rf"\b{re.escape(ticker)}\b", text):
            return True
        if company_name and len(company_name) > 3:
            name_part = company_name.split()[0]
            if name_part.lower() in text.lower():
                return True
        return False
