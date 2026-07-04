import asyncio
import hashlib
import logging
from datetime import datetime, timezone

import httpx  # type: ignore[import]

from pulse.app.ingestion.base import BaseIngester
from pulse.app.models.sentiment import ScoreResult, SentimentEvent
from pulse.app.scoring.finbert import score_batch

log = logging.getLogger(__name__)

_EDGAR_URL = "https://efts.sec.gov/LATEST/search-index"


class SECIngester(BaseIngester):
    def __init__(
        self,
        min_confidence: float = 0.3,
        user_agent: str = "TradeSense research admin@tradesense.local",
        max_concurrency: int = 3,
        request_delay: float = 0.3,
    ) -> None:
        self._min_confidence = min_confidence
        # SEC EDGAR rejects requests without a User-Agent (403) and rate-limits to
        # ~10 req/s, blocking the IP on sustained bursts. A semaphore caps parallelism
        # but not *rate*, so also pace each request — together they keep throughput
        # (concurrency / request_delay) safely under SEC's ceiling.
        self._user_agent = user_agent
        self._sem = asyncio.Semaphore(max_concurrency)
        self._delay = request_delay

    async def ingest(
        self,
        symbols: list[str],
        *,
        start: datetime,
        end: datetime,
        **kwargs: object,
    ) -> list[SentimentEvent]:
        tasks = [self._fetch_symbol(sym, start, end) for sym in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        filings: list[tuple[str, dict]] = []
        for sym, result in zip(symbols, results):
            if isinstance(result, Exception):
                log.warning("SEC fetch failed for %s: %s", sym, result)
                continue
            for filing in result:  # type: ignore[union-attr]
                filings.append((sym, filing))

        if not filings:
            return []

        texts = [self._filing_text(f) for _, f in filings]
        scores: list[ScoreResult] = score_batch(texts)

        events: list[SentimentEvent] = []
        for (sym, filing), score_result in zip(filings, scores):
            if score_result.confidence < self._min_confidence:
                continue
            filing_url = filing.get("file_date", "") + filing.get("entity_name", "")
            content_hash = hashlib.sha256(f"sec:{sym}:{filing_url}".encode()).hexdigest()
            ts_raw = filing.get("file_date", "")
            try:
                ts = datetime.strptime(ts_raw, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                ts = datetime.now(timezone.utc)

            events.append(
                SentimentEvent(
                    symbol=sym,
                    ts=ts,
                    source="sec",
                    score=score_result.score,
                    confidence=score_result.confidence,
                    content_hash=content_hash,
                    raw_text=self._filing_text(filing)[:500],
                )
            )
        return events

    async def _fetch_symbol(self, symbol: str, start: datetime, end: datetime) -> list[dict]:
        params = {
            "q": f'"{symbol}"',
            "dateRange": "custom",
            "startdt": start.strftime("%Y-%m-%d"),
            "enddt": end.strftime("%Y-%m-%d"),
            "forms": "8-K",
        }
        headers = {"User-Agent": self._user_agent}
        async with self._sem, httpx.AsyncClient(timeout=10, headers=headers) as client:
            resp = await client.get(_EDGAR_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            await asyncio.sleep(self._delay)  # hold the slot to pace under SEC's limit
            return data.get("hits", {}).get("hits", [])

    @staticmethod
    def _filing_text(filing: dict) -> str:
        src = filing.get("_source", filing)
        form = src.get("form_type", "8-K")
        desc = src.get("period_of_report", "") or src.get("entity_name", "")
        display = src.get("display_date_filed", "")
        return f"{form} filing: {desc} filed {display}"[:512]
