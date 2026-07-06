import os
import time
from functools import lru_cache
from typing import Any

from pulse.app import metrics
from pulse.app.models.sentiment import ScoreResult

_MIN_TEXT_LEN = 15
# FinBERT scoring is bursty/batch — no need to grab every core. Cap CPU threads.
_TORCH_THREADS = int(os.getenv("TORCH_NUM_THREADS", "4"))


@lru_cache(maxsize=1)
def _get_pipeline() -> Any:
    import torch
    from transformers import pipeline  # type: ignore[import]

    torch.set_num_threads(_TORCH_THREADS)
    pipe = pipeline(
        "text-classification",
        model="ProsusAI/finbert",
        top_k=None,
    )
    metrics.FINBERT_MODEL_LOADED.set(1)
    return pipe


def score_batch(texts: list[str], max_length: int = 512) -> list[ScoreResult]:
    """Score a batch of texts with FinBERT. Returns one ScoreResult per input."""
    if not texts:
        return []
    pipe = _get_pipeline()
    metrics.FINBERT_BATCHES.inc()
    metrics.FINBERT_TEXTS.inc(len(texts))
    t0 = time.perf_counter()
    results: list[Any] = pipe(texts, truncation=True, max_length=max_length)
    metrics.FINBERT_DURATION.observe(time.perf_counter() - t0)
    out: list[ScoreResult] = []
    for item in results:
        probs = {r["label"]: r["score"] for r in item}
        score = probs.get("positive", 0.0) - probs.get("negative", 0.0)
        confidence = max(probs.values()) if probs else 0.0
        out.append(ScoreResult(score=round(score, 6), confidence=round(confidence, 6)))
    return out
