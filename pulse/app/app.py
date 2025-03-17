import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pulse.app.api.dependencies import ApiDependencies
from pulse.app.api.routes import api_router
from pulse.app.config import get_config
from pulse.app.services.web_scraper.reddit_scraper import RedditCrawler
from pulse.app.utils.repeat_tasks import repeat_every

app_config = get_config()
loop = asyncio.new_event_loop()

@asynccontextmanager
async def lifespan(app: FastAPI):
    ApiDependencies.initialize(config=app_config)
    reddit_crawler = RedditCrawler(app_config)
    await reddit_crawler.scrape_subreddit()
    yield
    ApiDependencies.shutdown()


app = FastAPI(title="Pulse AI - Sentiment Analyzer", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_config.allow_origins,
    allow_credentials=app_config.allow_credentials,
    allow_methods=app_config.allow_methods,
    allow_headers=app_config.allow_headers,
)
app.include_router(api_router)

@repeat_every(seconds=5)
def print_hello() -> None:
    print("test")
