import os
from functools import lru_cache
from typing import Any

from pulse.app.models.sentiment import ScoreResult

_MIN_TEXT_LEN = 15
# FinBERT scoring is bursty/batch — no need to grab every core. Cap CPU threads.
_TORCH_THREADS = int(os.getenv("TORCH_NUM_THREADS", "4"))


@lru_cache(maxsize=1)
def _get_pipeline() -> Any:
    import torch
    from transformers import pipeline  # type: ignore[import]

    torch.set_num_threads(_TORCH_THREADS)
    return pipeline(
        "text-classification",
        model="ProsusAI/finbert",
        top_k=None,
    )


def score_batch(texts: list[str], max_length: int = 512) -> list[ScoreResult]:
    """Score a batch of texts with FinBERT. Returns one ScoreResult per input."""
    if not texts:
        return []
    pipe = _get_pipeline()
    results: list[Any] = pipe(texts, truncation=True, max_length=max_length)
    out: list[ScoreResult] = []
    for item in results:
        probs = {r["label"]: r["score"] for r in item}
        score = probs.get("positive", 0.0) - probs.get("negative", 0.0)
        confidence = max(probs.values()) if probs else 0.0
        out.append(ScoreResult(score=round(score, 6), confidence=round(confidence, 6)))
    return out
