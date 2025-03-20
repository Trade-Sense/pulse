from datetime import datetime

from sqlalchemy.orm import Session

from pulse.app.db.enums import SentimentSource
from pulse.app.db.models import SentimentScore


async def insert_sentiment_score(
    session: Session,
    time: datetime,
    symbol: str,
    score: float,
    label: str,
    source: SentimentSource,
    headline: str | None,
) -> None:
    sentiment_score = SentimentScore(
        time=time,
        symbol=symbol,
        sentiment_score=score,
        sentiment_label=label,
        source=source,
        headline=headline,
    )

    session.add(sentiment_score)
    session.commit()
