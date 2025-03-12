import json
import os
from typing import Dict, Optional

import pulse.assets


class TickerInfo:
    def __init__(self, cik_str: int, ticker: str, title: str) -> None:
        self.cik_str = cik_str
        self.ticker = ticker
        self.title = title

    def __repr__(self) -> str:
        return f"TickerInfo(cik_str={self.cik_str}, ticker='{self.ticker}', title='{self.title}')"


class SymbolCache:
    JSON_PATH = os.path.join(os.path.dirname(pulse.assets.__file__), "company_tickers.json")

    def __init__(self) -> None:
        self._cache: Dict[str, TickerInfo] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        """
        Load data from a JSON file into the cache.
        :param json_path: Path to the JSON file.
        """
        try:
            with open(SymbolCache.JSON_PATH, "r") as file:
                data = json.load(file)
                for entry in data.values():
                    ticker_info = TickerInfo(
                        cik_str=entry["cik_str"], ticker=entry["ticker"], title=entry["title"]
                    )
                    self._cache[ticker_info.ticker] = ticker_info
                print(f"Cache successfully loaded with {len(self._cache)} entries.")
        except FileNotFoundError:
            print(f"Error: File not found at {SymbolCache.JSON_PATH}")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")

    def get_ticker_info(self, ticker: str) -> Optional[TickerInfo]:
        """
        Retrieve TickerInfo by ticker symbol.
        :param ticker: The ticker symbol to look up in the cache.
        :return: A TickerInfo object or None if not found.
        """
        return self._cache.get(ticker)

    def get_all_tickers(self) -> Dict[str, TickerInfo]:
        """
        Retrieve all cached ticker data.
        :return: The entire cache as a dictionary.
        """
        return self._cache
