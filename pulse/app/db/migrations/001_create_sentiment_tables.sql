-- Raw events: one row per scored post/comment/article
-- PRIMARY KEY includes ts to satisfy TimescaleDB hypertable partitioning constraint
CREATE TABLE IF NOT EXISTS sentiment_events (
    id           BIGSERIAL,
    symbol       TEXT        NOT NULL,
    ts           TIMESTAMPTZ NOT NULL,
    source       TEXT        NOT NULL,  -- 'alpaca_news' | 'sec' | 'reddit' | 'stocktwits'
    subreddit    TEXT,
    score        FLOAT       NOT NULL,  -- [-1.0, 1.0] FinBERT: p_positive - p_negative
    confidence   FLOAT       NOT NULL,  -- [0.0, 1.0] FinBERT: max(probs)
    engagement   FLOAT,                 -- normalized (upvotes + comments), nullable
    content_hash TEXT        NOT NULL,  -- sha256(source:url_or_id) for app-level dedup
    url          TEXT,
    raw_text     TEXT,                  -- first 500 chars, debugging only
    PRIMARY KEY (id, ts)
);

SELECT create_hypertable('sentiment_events', 'ts', if_not_exists => TRUE);

-- UNIQUE(url) without ts fails on hypertable; use content_hash index + app-level dedup instead
CREATE INDEX IF NOT EXISTS idx_sentiment_events_symbol_ts
    ON sentiment_events (symbol, ts DESC);
CREATE INDEX IF NOT EXISTS idx_sentiment_events_content_hash
    ON sentiment_events (content_hash);

-- Daily aggregate: what dojo queries as separate features
-- Regular table (not hypertable) — low-cardinality, upserted daily
CREATE TABLE IF NOT EXISTS daily_sentiment (
    symbol                 TEXT  NOT NULL,
    date                   DATE  NOT NULL,
    -- Source scores: separate columns, NOT blended — let XGBoost learn the weights
    news_score             FLOAT,
    sec_score              FLOAT,
    reddit_score           FLOAT,
    stocktwits_score       FLOAT,
    -- Divergence: news_bullish + reddit_bearish = institutions selling, retail unaware
    news_reddit_divergence FLOAT,
    -- Mention signals
    mention_count          INT   NOT NULL DEFAULT 0,
    reddit_mention_count   INT   NOT NULL DEFAULT 0,
    mention_velocity       FLOAT,  -- (today - yesterday) / max(yesterday, 1)
    avg_engagement         FLOAT,
    bullish_pct            FLOAT,  -- fraction of events with score > 0.3
    bearish_pct            FLOAT,  -- fraction of events with score < -0.3
    PRIMARY KEY (symbol, date)
);
