# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run locally
make run           # uv run python -m pulse.app.main

# Tests
make test          # pytest ./tests

# Linting / formatting
make ruff          # ruff check . --fix && ruff format .

# Docker
make serve         # docker-compose up -d --build
make stop
make clean
```

## Architecture

Pulse is a **FastAPI sentiment service**. It ingests text from multiple sources, scores it with FinBERT, and exposes daily sentiment aggregates via HTTP.

### Ingestion pipeline

```
pulse/app/ingestion/
    news.py       ← Alpaca news API
    reddit.py     ← Reddit API (r/wallstreetbets etc.)
    sec.py        ← SEC EDGAR filings
    stocktwits.py ← StockTwits stream
    pipeline.py   ← orchestrates all sources, deduplicates
```

Each ingester inherits from `base.py`. The pipeline runs on demand (POST `/api/v1/ingest/{symbol}`) or on a schedule.

### Scoring

`pulse/app/scoring/finbert.py` — wraps HuggingFace `pipeline("text-classification", model="ProsusAI/finbert")`. **Important**: use `top_k=None` (not the deprecated `return_all_scores=True`) when initializing the pipeline; otherwise newer transformers versions return a dict instead of a list of dicts, causing a `TypeError` on iteration.

`pulse/app/scoring/scorer.py` — aggregates raw FinBERT scores into daily sentiment metrics: `news_score`, `sec_score`, `reddit_score`, `news_reddit_divergence`, `mention_count`, `mention_velocity`, `bullish_pct`, `bearish_pct`.

### API

FastAPI app in `pulse/app/app.py`. Key endpoints:
- `POST /api/v1/ingest/{symbol}` — triggers ingestion and scoring, returns `IngestResult` (field is `ingested`, not `total_ingested`)
- `GET /api/v1/sentiment/{symbol}/daily` — returns daily sentiment scores consumed by dojo and trader-api

### Database

`pulse/app/db/` — stores scored sentiment records. Schema defined in `pulse/app/models/`.

### Config

`pulse/app/config.py` uses `pydantic-settings`. Environment variables override defaults.
