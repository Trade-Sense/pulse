from fastapi import APIRouter

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/{symbol}", response_model=[])
async def get_sentiment(symbol: str) -> None:
    """
    Retrieves the sentiment score for a given stock symbol based on recent news.
    """
    print("Helo world")


@router.get("/{symbol}/news")
async def get_stock_news(symbol: str) -> None:
    """
    Fetches the latest news articles related to a specific stock symbol.
    """
    print("Hello world")


@router.post("/sentiment/analyze")
async def analyze_article() -> None:
    """
    Accepts text input (e.g., news articles) and returns the sentiment score.
    """
    print("Hello world")
