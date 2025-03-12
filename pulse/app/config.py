from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class PulseConfig(BaseSettings):
    """Invoke's global app configuration.

    Attributes:
        host: IP address to bind to. Use `0.0.0.0` to serve to your local network.
        port: Port to bind to.
        allow_origins: Allowed CORS origins.
        allow_credentials: Allow CORS credentials.
        allow_methods: Methods allowed for CORS.
        allow_headers: Headers allowed for CORS.
    """

    # WEB
    host: str = Field(
        default="127.0.0.1",
        description="IP address to bind to. Use `0.0.0.0` to serve to your local network.",
    )
    port: int = Field(default=9090, description="Port to bind to.")
    allow_origins: list[str] = Field(default=[], description="Allowed CORS origins.")
    allow_credentials: bool = Field(default=True, description="Allow CORS credentials.")
    allow_methods: list[str] = Field(default=["*"], description="Methods allowed for CORS.")
    allow_headers: list[str] = Field(default=["*"], description="Headers allowed for CORS.")

    # MODEL
    model_base_url: str = Field(
        default="http://localhost:11434/v1/",
        description="IP address where the language model is serving",
    )


@lru_cache(maxsize=1)
def get_config() -> PulseConfig:
    config = PulseConfig()

    return config
