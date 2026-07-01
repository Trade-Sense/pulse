from collections import defaultdict
from datetime import date

from pulse.app.models.sentiment import DailySentiment, SentimentEvent


def aggregate_daily(
    events: list[SentimentEvent],
    prev_day_reddit_counts: dict[str, int],
) -> list[DailySentiment]:
    """Roll raw scored events into daily_sentiment rows, one per (symbol, date)."""
    # Group events by (symbol, date)
    by_key: dict[tuple[str, date], list[SentimentEvent]] = defaultdict(list)
    for e in events:
        by_key[(e.symbol, e.ts.date())].append(e)

    results: list[DailySentiment] = []
    for (symbol, day), day_events in by_key.items():
        source_scores: dict[str, list[float]] = defaultdict(list)
        engagements: list[float] = []
        reddit_count = 0
        bullish = 0
        bearish = 0

        for e in day_events:
            source_scores[e.source].append(e.score)
            if e.engagement is not None:
                engagements.append(e.engagement)
            if e.source == "reddit":
                reddit_count += 1
            if e.score > 0.3:
                bullish += 1
            elif e.score < -0.3:
                bearish += 1

        def avg(vals: list[float]) -> float | None:
            return sum(vals) / len(vals) if vals else None

        news_score = avg(source_scores.get("alpaca_news", []))
        sec_score = avg(source_scores.get("sec", []))
        reddit_score = avg(source_scores.get("reddit", []))
        stocktwits_score = avg(source_scores.get("stocktwits", []))

        divergence: float | None = None
        if news_score is not None and reddit_score is not None:
            divergence = news_score - reddit_score

        prev_reddit = prev_day_reddit_counts.get(symbol, 0)
        velocity = (reddit_count - prev_reddit) / max(prev_reddit, 1)

        total = len(day_events)
        results.append(
            DailySentiment(
                symbol=symbol,
                date=day,
                news_score=news_score,
                sec_score=sec_score,
                reddit_score=reddit_score,
                stocktwits_score=stocktwits_score,
                news_reddit_divergence=divergence,
                mention_count=total,
                reddit_mention_count=reddit_count,
                mention_velocity=velocity,
                avg_engagement=avg(engagements),
                bullish_pct=bullish / total if total else None,
                bearish_pct=bearish / total if total else None,
            )
        )
    return results
