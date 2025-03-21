from datetime import datetime

from sqlalchemy.orm import Session

from pulse.app.db.enums import SentimentSource
from pulse.app.db.models import SentimentScore


def insert_sentiment_score(
    session: Session,
    time: datetime,
    symbol: str,
    score: float,
    label: str,
    source: SentimentSource,
    headline: str | None = None,
) -> None:
    # TODO: Add additional checks. Score should be between -1 and 1
    sentiment_score = SentimentScore(
        time=time,
        symbol=symbol,
        score=score,
        label=label,
        source=source,
        headline=headline,
    )

    session.add(sentiment_score)
    session.commit()
