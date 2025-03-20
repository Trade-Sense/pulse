from sqlalchemy import TIMESTAMP, Column, Float, Integer, String, Text, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class SentimentScore(Base):
    __tablename__ = "sentiment_score"

    id = Column(Integer, primary_key=True)
    time = Column(TIMESTAMP(timezone=True), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    sentiment_score = Column(Float(), nullable=False)
    sentiment_label = Column(String, nullable=False)
    source = Column(String(20), nullable=False)
    headline = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), default=func.now())

    def __repr__(self):
        return f"id: {self.id} source: {self.source}"
