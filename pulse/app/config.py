from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class PulseConfig(BaseSettings):
    """Invoke's global app configuration.

    Attributes:
        host: IP address to bind to. Use `0.0.0.0` to serve to your local network.
        port: Port to bind to.
        allow_origins: Allowed CORS origins.
        allow_credentials: Allow CORS credentials.
        allow_methods: Methods allowed for CORS.
        allow_headers: Headers allowed for CORS.
    """

    # WEB
    host: str = Field(
        default="0.0.0.0",
        description="IP address to bind to. Use `0.0.0.0` to serve to your local network.",
    )
    port: int = Field(default=8080, description="Port to bind to.")
    allow_origins: list[str] = Field(default=[], description="Allowed CORS origins.")
    allow_credentials: bool = Field(default=True, description="Allow CORS credentials.")
    allow_methods: list[str] = Field(default=["*"], description="Methods allowed for CORS.")
    allow_headers: list[str] = Field(default=["*"], description="Headers allowed for CORS.")

    # DB — shares forge's TimescaleDB instance by default
    db_url: str = Field(
        default="postgresql://postgres:admin@localhost:5436/forge_dev",
        description="PostgreSQL connection URL",
    )

    # Alpaca (for news ingestion)
    alpaca_api_key: str = Field(default="", description="Alpaca API key")
    alpaca_api_secret: str = Field(default="", description="Alpaca API secret")

    # Reddit OAuth
    reddit_client_id: str = Field(default="", description="Reddit OAuth client ID")
    reddit_client_secret: str = Field(default="", description="Reddit OAuth client secret")
    # Reddit blocks default (curl/python-requests) AND fake-browser (Mozilla/...) UAs,
    # but allows a simple, honest, unique one. Do NOT make this a browser string.
    reddit_user_agent: str = Field(
        default="trade-sense/sentiment-fetch",
        description="Reddit User-Agent for anonymous .json access (honest, non-browser)",
    )

    # Ingestion
    target_symbols: list[str] = Field(
        default=["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"],
        description="Symbols to ingest sentiment for",
    )
    target_subreddits: list[str] = Field(
        default=[
            "wallstreetbets", "stocks", "investing",
            "raceto10million", "options", "StockMarket",
        ],
        description="Subreddits to scrape",
    )
    ingest_lookback_hours: int = Field(default=24, description="Lookback window per ingest run")
    news_ingest_interval_hours: int = Field(default=1, description="How often to auto-ingest Alpaca news")
    reddit_ingest_interval_hours: int = Field(default=4, description="How often to auto-ingest Reddit")
    sec_ingest_interval_hours: int = Field(default=12, description="How often to auto-ingest SEC filings")
    stocktwits_ingest_interval_hours: int = Field(default=4, description="How often to auto-ingest StockTwits")
    sec_user_agent: str = Field(
        default="TradeSense research admin@tradesense.local",
        description="User-Agent for SEC EDGAR — required, SEC returns 403 without one",
    )
    min_confidence: float = Field(default=0.3, description="Discard FinBERT events below this confidence")

    # FinBERT
    finbert_model: str = Field(default="ProsusAI/finbert", description="HuggingFace model ID")
    finbert_max_tokens: int = Field(default=512, description="Max token length per input text")


@lru_cache(maxsize=1)
def get_config() -> PulseConfig:
    return PulseConfig()
