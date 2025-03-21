from datetime import datetime
from typing import Any

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from pulse.app.db.enums import SentimentSource
from pulse.app.db.inserts import insert_sentiment_score


@pytest.fixture(scope="session", autouse=True)
def mock_session():
    """
    Fixture to set up an in-memory SQLite database for testing.
    """

    # Create an SQLite in-memory engine
    engine = create_engine("sqlite:///:memory:", echo=True)
    # Open a shared connection
    connection = engine.connect()

    # Bind Alembic to the shared connection
    alembic_config = Config("alembic.ini")
    alembic_config.attributes["connection"] = connection
    command.upgrade(alembic_config, "head")

    # Use engine for session binding
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()


def test_insert_sentiment_score(mock_session: Any):
    # Insert data into the sentiment_score table
    insert_sentiment_score(
        mock_session,
        datetime.now(),
        "TEST",
        1,
        "test",
        SentimentSource.reddit,
    )

    # Query the table to verify insertion
    query = text("SELECT * FROM sentiment_score WHERE symbol = :symbol")
    result = mock_session.execute(query, {"symbol": "TEST"}).fetchone()
    assert result is not None
