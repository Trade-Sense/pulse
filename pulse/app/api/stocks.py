from typing import Dict

from fastapi import APIRouter, HTTPException

from pulse.app.api.dependencies import ApiDependencies

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/{symbol}", response_model=[])
async def get_sentiment(symbol: str) -> Dict[str, str]:
    """
    Retrieves the sentiment score for a given stock symbol based on recent news.
    """
    symbol_info = ApiDependencies.invoker.services.symbol_cache.get_ticker_info(symbol)
    if not symbol_info:
        raise HTTPException(status_code=400, detail="Symbol does not exist")
    return {"Hello": "World"}


@router.get("/{symbol}/news")
async def get_stock_news(symbol: str) -> None:
    """
    Fetches the latest news articles related to a specific stock symbol.
    """
    symbol_info = ApiDependencies.invoker.services.symbol_cache.get_ticker_info(symbol)
    if not symbol_info:
        raise HTTPException(status_code=400, detail="Symbol does not exist")

    print("Hello world")


@router.post("/sentiment/analyze")
async def analyze_article() -> None:
    """
    Accepts text input (e.g., news articles) and returns the sentiment score.
    """
    print("Hello world")
