from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class ScoreResult(BaseModel):
    score: float  # [-1.0, 1.0]: p_positive - p_negative
    confidence: float  # [0.0, 1.0]: max(p_positive, p_negative, p_neutral)


class SentimentEvent(BaseModel):
    symbol: str
    ts: datetime
    source: str  # 'alpaca_news' | 'sec' | 'reddit' | 'stocktwits'
    subreddit: Optional[str] = None
    score: float
    confidence: float
    engagement: Optional[float] = None
    content_hash: str
    url: Optional[str] = None
    raw_text: Optional[str] = None


class DailySentiment(BaseModel):
    symbol: str
    date: date
    news_score: Optional[float] = None
    sec_score: Optional[float] = None
    reddit_score: Optional[float] = None
    stocktwits_score: Optional[float] = None
    news_reddit_divergence: Optional[float] = None
    mention_count: int = 0
    reddit_mention_count: int = 0
    mention_velocity: Optional[float] = None
    avg_engagement: Optional[float] = None
    bullish_pct: Optional[float] = None
    bearish_pct: Optional[float] = None


class IngestRequest(BaseModel):
    symbols: list[str]
    lookback_hours: int = Field(default=24)


class IngestResult(BaseModel):
    ingested: int
    scored: int
    discarded: int
    errors: list[str] = Field(default_factory=list)
