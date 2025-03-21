from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pulse.app.services.symbol_cache.symbol_cache import SymbolCache


class InvocationServices:
    """Services that can be used by invocations"""

    def __init__(
        self,
        symbol_cache: SymbolCache,
    ):
        self.symbol_cache = symbol_cache
