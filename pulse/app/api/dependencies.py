from pulse.app.config import PulseConfig
from pulse.app.services.invocation_services import InvocationServices
from pulse.app.services.invoker import Invoker
from pulse.app.services.symbol_cache.symbol_cache import SymbolCache


class ApiDependencies:
    """Contains and initializes all dependencies for the API"""

    invoker: Invoker

    @staticmethod
    def initialize(config: PulseConfig) -> None:
        symbol_cache = SymbolCache()
        services = InvocationServices(symbol_cache=symbol_cache)
        ApiDependencies.invoker = Invoker(services=services)

    @staticmethod
    def shutdown() -> None:
        if ApiDependencies.invoker:
            ApiDependencies.invoker.stop()
