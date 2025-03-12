from pulse.app.config import PulseConfig


class ApiDependencies:
    """Contains and initializes all dependencies for the API"""

    @staticmethod
    def initialize(config: PulseConfig) -> None:
        print("Hello world")
