import hashlib
import logging
from datetime import datetime, timezone

import httpx  # type: ignore[import]

from pulse.app.ingestion.base import BaseIngester
from pulse.app.models.sentiment import SentimentEvent, ScoreResult
from pulse.app.scoring.finbert import score_batch

log = logging.getLogger(__name__)

_NEWS_URL = "https://data.alpaca.markets/v1beta1/news"


class AlpacaNewsIngester(BaseIngester):
    def __init__(self, api_key: str, api_secret: str, min_confidence: float = 0.3) -> None:
        self._headers = {
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": api_secret,
        }
        self._min_confidence = min_confidence

    async def ingest(
        self,
        symbols: list[str],
        *,
        start: datetime,
        end: datetime,
        **kwargs: object,
    ) -> list[SentimentEvent]:
        articles = await self._fetch_all(symbols, start, end)
        if not articles:
            return []

        texts = [self._article_text(a) for a in articles]
        scores: list[ScoreResult] = score_batch(texts)

        events: list[SentimentEvent] = []
        for article, score_result in zip(articles, scores):
            if score_result.confidence < self._min_confidence:
                continue
            url = article.get("url") or ""
            content_hash = hashlib.sha256(f"alpaca_news:{url}".encode()).hexdigest()
            raw = self._article_text(article)[:500]
            ts_raw = article.get("created_at", "")
            try:
                ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                ts = datetime.now(timezone.utc)

            for sym in article.get("symbols", [symbols[0]]):
                if sym not in symbols:
                    continue
                events.append(
                    SentimentEvent(
                        symbol=sym,
                        ts=ts,
                        source="alpaca_news",
                        score=score_result.score,
                        confidence=score_result.confidence,
                        content_hash=hashlib.sha256(f"alpaca_news:{url}:{sym}".encode()).hexdigest(),
                        url=url or None,
                        raw_text=raw,
                    )
                )
        return events

    async def _fetch_all(
        self, symbols: list[str], start: datetime, end: datetime
    ) -> list[dict]:
        articles: list[dict] = []
        params: dict = {
            "symbols": ",".join(symbols),
            "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "limit": 50,
            "sort": "desc",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            while True:
                resp = await client.get(_NEWS_URL, headers=self._headers, params=params)
                resp.raise_for_status()
                data = resp.json()
                batch = data.get("news", [])
                articles.extend(batch)
                token = data.get("next_page_token")
                if not token or not batch:
                    break
                params["page_token"] = token
        return articles

    @staticmethod
    def _article_text(article: dict) -> str:
        headline = article.get("headline", "")
        summary = article.get("summary") or article.get("content") or ""
        return f"{headline}. {summary}"[:512]
