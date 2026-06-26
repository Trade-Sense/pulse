import logging

from pulse.app.scoring.finbert import _get_pipeline, score_batch
from pulse.app.models.sentiment import ScoreResult

log = logging.getLogger(__name__)

__all__ = ["score_batch", "warm_up", "ScoreResult"]


def warm_up() -> None:
    """Load FinBERT into memory at startup. Blocks until the ~440MB model is ready."""
    log.info("Loading FinBERT model (ProsusAI/finbert)…")
    _get_pipeline()
    log.info("FinBERT ready")
