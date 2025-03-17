from typing import Any
from unittest.mock import mock_open, patch

import pytest

from pulse.app.services.symbol_cache.symbol_cache import SymbolCache, TickerInfo

# Mock JSON data for tests
MOCK_JSON_DATA = """
{
    "0": {
        "cik_str": 320193,
        "ticker": "AAPL",
        "title": "Apple Inc."
    },
    "1": {
        "cik_str": 789019,
        "ticker": "MSFT",
        "title": "MICROSOFT CORP"
    }
}
"""


@pytest.fixture
def mock_json_file():
    """
    Fixture to mock the JSON file reading.
    """
    with patch("builtins.open", mock_open(read_data=MOCK_JSON_DATA)) as mocked_file:
        yield mocked_file


@pytest.fixture
def mock_path_join():
    """
    Fixture to mock os.path.join to return a fixed path.
    """
    with patch("os.path.join", return_value="mocked_path/company_tickers.json") as mocked_path:
        yield mocked_path


@pytest.fixture
def symbol_cache(mock_json_file: Any, mock_path_join: Any):
    """
    Fixture to initialize SymbolCache with mocked dependencies.
    """
    return SymbolCache()


def test_load_cache(symbol_cache: SymbolCache):
    """
    Test that the cache is loaded correctly from JSON data.
    """
    all_tickers = symbol_cache.get_all_tickers()

    # Expected cache structure
    expected_cache = {
        "AAPL": TickerInfo(cik_str=320193, ticker="AAPL", title="Apple Inc."),
        "MSFT": TickerInfo(cik_str=789019, ticker="MSFT", title="MICROSOFT CORP"),
    }

    # Verify cache size
    assert len(all_tickers) == len(expected_cache)

    # Verify contents of the cache
    for ticker, expected_info in expected_cache.items():
        assert ticker in all_tickers
        assert all_tickers[ticker].cik_str == expected_info.cik_str
        assert all_tickers[ticker].ticker == expected_info.ticker
        assert all_tickers[ticker].title == expected_info.title


def test_get_ticker_info(symbol_cache: SymbolCache):
    """
    Test retrieving information for a specific ticker.
    """
    # Retrieve AAPL info
    aapl_info = symbol_cache.get_ticker_info("AAPL")
    assert aapl_info is not None
    assert aapl_info.cik_str == 320193
    assert aapl_info.ticker == "AAPL"
    assert aapl_info.title == "Apple Inc."

    # Retrieve MSFT info
    msft_info = symbol_cache.get_ticker_info("MSFT")
    assert msft_info is not None
    assert msft_info.cik_str == 789019
    assert msft_info.ticker == "MSFT"
    assert msft_info.title == "MICROSOFT CORP"

    # Test non-existent ticker
    unknown_info = symbol_cache.get_ticker_info("GOOG")
    assert unknown_info is None


def test_get_all_tickers(symbol_cache: SymbolCache):
    """
    Test retrieving all tickers from the cache.
    """
    all_tickers = symbol_cache.get_all_tickers()

    # Verify that all tickers are present in the cache
    assert "AAPL" in all_tickers
    assert "MSFT" in all_tickers
