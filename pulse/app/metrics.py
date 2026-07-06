"""Pulse application-level Prometheus collectors.

RED baseline (http_request_*) is added by prometheus-fastapi-instrumentator in app.py.
"""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

EVENTS_INGESTED = Counter(
    "pulse_events_ingested_total",
    "Scored sentiment events stored, by source.",
    ["source"],
)

EVENTS_DISCARDED = Counter(
    "pulse_events_discarded_total",
    "Sentiment events dropped, by reason.",
    ["reason"],
)

SOURCE_FETCH_ERRORS = Counter(
    "pulse_source_fetch_errors_total",
    "Upstream source fetch failures, by source.",
    ["source"],
)

FINBERT_BATCHES = Counter(
    "pulse_finbert_batches_total",
    "FinBERT scoring batches run.",
)

FINBERT_TEXTS = Counter(
    "pulse_finbert_texts_scored_total",
    "Individual texts scored by FinBERT.",
)

FINBERT_DURATION = Histogram(
    "pulse_finbert_score_duration_seconds",
    "FinBERT batch scoring latency.",
)

FINBERT_MODEL_LOADED = Gauge(
    "pulse_finbert_model_loaded",
    "1 once the FinBERT pipeline has loaded.",
)

DAILY_UPSERTS = Counter(
    "pulse_daily_upserts_total",
    "daily_sentiment rows upserted.",
)
