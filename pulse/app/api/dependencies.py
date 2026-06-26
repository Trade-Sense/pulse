from __future__ import annotations

from typing import Any

from pulse.app.config import PulseConfig, get_config
from pulse.app.db.connection import get_pool


def cfg() -> PulseConfig:
    return get_config()


async def db_pool() -> Any:
    return get_pool()
