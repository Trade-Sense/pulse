import asyncio
import hashlib
import logging
import re
from datetime import datetime, timedelta, timezone

# curl_cffi uses libcurl, so its TLS fingerprint matches `curl` — which Reddit
# allows — whereas httpx/requests get a "403 Blocked" even with a valid UA.
from curl_cffi.requests import AsyncSession

from pulse.app.ingestion.base import BaseIngester
from pulse.app.models.sentiment import ScoreResult, SentimentEvent
from pulse.app.scoring.finbert import score_batch

log = logging.getLogger(__name__)

# Uppercase tokens that are common words / slang on these subs, not tickers.
_FALSE_POSITIVES = frozenset(
    {"I", "A", "FOR", "ARE", "IT", "AT", "BE", "DO", "GO", "CEO", "IPO", "ETF",
     "DD", "FD", "YOLO", "HODL", "WSB", "USA", "US", "AI", "EV", "PT", "ATH"}
)
# $TICKER or a standalone 1–5 letter uppercase token, not embedded in a word.
_TICKER_RE = re.compile(r"(?<![A-Za-z0-9])\$?([A-Z]{1,5})(?![A-Za-z])")
_NEW_URL = "https://www.reddit.com/r/{sub}/new.json"


class RedditIngester(BaseIngester):
    """Scrapes recent posts from target subreddits via Reddit's public ``.json``
    endpoints (no OAuth), detects ticker mentions, and scores sentiment.

    Reddit gates anonymous access on client fingerprint (blocking httpx) and
    User-Agent (blocking defaults and fake-browser strings), so this uses
    ``curl_cffi`` (libcurl fingerprint) with a simple honest UA, polls each
    subreddit's ``/new.json`` firehose rather than searching per-ticker, and paces
    hard to stay under the ~10 req/min anonymous limit.

    Note: this works from a residential IP only — datacenter IPs (e.g. cloud) are
    blocked regardless.
    """

    def __init__(
        self,
        user_agent: str,
        min_confidence: float = 0.3,
        max_concurrency: int = 1,
        request_delay: float = 6.0,
        max_pages: int = 3,
    ) -> None:
        self._user_agent = user_agent
        self._min_confidence = min_confidence
        self._sem = asyncio.Semaphore(max_concurrency)
        self._delay = request_delay
        self._max_pages = max_pages

    async def ingest(
        self,
        symbols: list[str],
        *,
        subreddits: list[str],
        lookback_hours: int = 24,
        **kwargs: object,
    ) -> list[SentimentEvent]:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=lookback_hours)).timestamp()
        symbol_set = set(symbols) - _FALSE_POSITIVES

        seen: set[str] = set()
        # (symbol, url, text, created_utc, content_hash, engagement, subreddit)
        candidates: list[tuple[str, str, str, float, str, float, str]] = []

        # impersonate="chrome" presents a full, consistent Chrome TLS fingerprint —
        # curl_cffi's un-impersonated default is still on Reddit's blocklist.
        headers = {"User-Agent": self._user_agent}
        async with AsyncSession(headers=headers, impersonate="chrome") as session:
            for sub in subreddits:
                try:
                    posts = await self._fetch_recent(session, sub, cutoff)
                except Exception as exc:
                    log.warning("Reddit fetch failed for r/%s: %s", sub, exc)
                    continue
                for post in posts:
                    text = f"{post.get('title', '')} {post.get('selftext', '') or ''}"
                    tickers = {m.group(1) for m in _TICKER_RE.finditer(text)} & symbol_set
                    if not tickers:
                        continue
                    url = f"https://reddit.com{post.get('permalink', '')}"
                    created = float(post.get("created_utc", 0))
                    engagement = float(post.get("score", 0) + post.get("num_comments", 0))
                    for sym in tickers:
                        content_hash = hashlib.sha256(f"reddit:{url}:{sym}".encode()).hexdigest()
                        if content_hash in seen:
                            continue
                        seen.add(content_hash)
                        candidates.append(
                            (sym, url, text[:2000], created, content_hash, engagement, sub)
                        )

        if not candidates:
            return []

        scores: list[ScoreResult] = score_batch([c[2] for c in candidates])
        events: list[SentimentEvent] = []
        for (sym, url, text, created, content_hash, engagement, sub), score_result in zip(
            candidates, scores, strict=True
        ):
            if score_result.confidence < self._min_confidence:
                continue
            events.append(
                SentimentEvent(
                    symbol=sym,
                    ts=datetime.fromtimestamp(created, tz=timezone.utc),
                    source="reddit",
                    subreddit=sub,
                    score=score_result.score,
                    confidence=score_result.confidence,
                    engagement=engagement,
                    content_hash=content_hash,
                    url=url,
                    raw_text=text[:500],
                )
            )
        return events

    async def _fetch_recent(self, session: AsyncSession, sub: str, cutoff: float) -> list[dict]:
        """Page through r/{sub}/new.json until posts predate the lookback window."""
        collected: list[dict] = []
        after: str | None = None
        for _ in range(self._max_pages):
            params: dict[str, object] = {"limit": 100}
            if after:
                params["after"] = after
            async with self._sem:
                resp = await session.get(_NEW_URL.format(sub=sub), params=params, timeout=15)
                await asyncio.sleep(self._delay)  # hold the slot to pace under Reddit's limit
            if resp.status_code != 200:
                log.warning(
                    "Reddit returned %s on r/%s — stopping this cycle", resp.status_code, sub
                )
                break
            data = resp.json().get("data", {})
            children = data.get("children", [])
            if not children:
                break
            reached_cutoff = False
            for child in children:
                post = child.get("data", {})
                if float(post.get("created_utc", 0)) < cutoff:
                    reached_cutoff = True
                    continue
                collected.append(post)
            after = data.get("after")
            if reached_cutoff or not after:
                break
        return collected
