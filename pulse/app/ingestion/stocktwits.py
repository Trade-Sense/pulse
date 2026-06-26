import hashlib
import logging
from datetime import datetime, timezone

import httpx  # type: ignore[import]

from pulse.app.ingestion.base import BaseIngester
from pulse.app.models.sentiment import ScoreResult, SentimentEvent
from pulse.app.scoring.finbert import score_batch

log = logging.getLogger(__name__)

_STOCKTWITS_URL = "https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"


class StockTwitsIngester(BaseIngester):
    def __init__(self, min_confidence: float = 0.3) -> None:
        self._min_confidence = min_confidence

    async def ingest(self, symbols: list[str], **kwargs: object) -> list[SentimentEvent]:
        events: list[SentimentEvent] = []
        async with httpx.AsyncClient(timeout=15) as client:
            for sym in symbols:
                try:
                    msgs = await self._fetch(client, sym)
                except Exception as exc:
                    log.warning("StockTwits fetch failed for %s: %s", sym, exc)
                    continue
                if not msgs:
                    continue

                texts = [m.get("body", "")[:512] for m in msgs]
                scores: list[ScoreResult] = score_batch(texts)

                for msg, score_result in zip(msgs, scores):
                    if score_result.confidence < self._min_confidence:
                        continue
                    msg_id = str(msg.get("id", ""))
                    content_hash = hashlib.sha256(f"stocktwits:{sym}:{msg_id}".encode()).hexdigest()
                    ts_raw = msg.get("created_at", "")
                    try:
                        ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                    except (ValueError, AttributeError):
                        ts = datetime.now(timezone.utc)

                    events.append(
                        SentimentEvent(
                            symbol=sym,
                            ts=ts,
                            source="stocktwits",
                            score=score_result.score,
                            confidence=score_result.confidence,
                            content_hash=content_hash,
                            raw_text=msg.get("body", "")[:500],
                        )
                    )
        return events

    @staticmethod
    async def _fetch(client: httpx.AsyncClient, symbol: str) -> list[dict]:
        resp = await client.get(_STOCKTWITS_URL.format(symbol=symbol))
        resp.raise_for_status()
        return resp.json().get("messages", [])
