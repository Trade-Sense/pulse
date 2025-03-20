from sqlalchemy import TIMESTAMP, Float, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SentimentScore(Base):
    __tablename__ = "sentiment_score"

    # Columns
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    time: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    symbol: Mapped[str] = mapped_column(String(length=20), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[str] = mapped_column(String(length=20), nullable=False)
    headline: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (Index("idx_symbol", "symbol"),)
