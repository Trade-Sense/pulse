from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
        default="0.0.0.0",
        description="IP address to bind to. Use `0.0.0.0` to serve to your local network.",
    )
    port: int = Field(default=8080, description="Port to bind to.")
    allow_origins: list[str] = Field(default=[], description="Allowed CORS origins.")
    allow_credentials: bool = Field(default=True, description="Allow CORS credentials.")
    allow_methods: list[str] = Field(default=["*"], description="Methods allowed for CORS.")
    allow_headers: list[str] = Field(default=["*"], description="Headers allowed for CORS.")

    # MODEL
    model_base_url: str = Field(
        default="http://localhost:11434/v1/",
        description="IP address where the language model is serving",
    )

    # REDDIT
    client_id: str = Field(
        default="",
        description="Client ID for reddit",
    )
    client_secret: str = Field(default="", description="Client Secret for reddit,")
    password: str = Field(default="", description="Reddit password")
    user_agent: str = Field(default="", description="Reddit user agent")
    username: str = Field(default="", description="Reddit username")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache(maxsize=1)
def get_config() -> PulseConfig:
    config = PulseConfig()

    return config
