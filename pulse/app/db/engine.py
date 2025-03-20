import threading
from typing import Generator

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from pulse.app.config import get_config

app_config = get_config()


class SqlEngine:
    _engine: Engine | None = None
    _lock: threading.Lock = threading.Lock()

    @classmethod
    def get_engine(cls) -> Engine:
        if not cls._engine:
            with cls._lock:
                if not cls._engine:
                    cls._engine = cls._init_engine()
        return cls._engine

    @classmethod
    def _init_engine(cls) -> Engine:
        return cls._build_local_connection()

    @staticmethod
    def _build_local_connection() -> Engine:
        url = app_config.database_url
        return create_engine(url, pool_pre_ping=True)


def get_session() -> Generator[Session, None, None]:
    """
    Generate a database session
    """
    with Session(SqlEngine.get_engine()) as session:
        yield session


def run_migrations() -> None:
    engine = get_session()
    alembic_config = Config("alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", app_config.database_url)
    alembic_config.attributes["connection"] = engine
    alembic_config.attributes["configure_logger"] = False
    command.upgrade(alembic_config, "head")

    # alembic_cfg.attributes['connection'] = connection
    # command.upgrade(alembic_cfg, "head")
