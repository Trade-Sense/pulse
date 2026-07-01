from abc import ABC, abstractmethod

from pulse.app.models.sentiment import SentimentEvent


class BaseIngester(ABC):
    @abstractmethod
    async def ingest(self, symbols: list[str], **kwargs: object) -> list[SentimentEvent]:
        ...
