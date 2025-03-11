from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pulse.app.config import get_config

app_config = get_config()

app = FastAPI(title="Pulse AI - Sentiment Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_config.allow_origins,
    allow_credentials=app_config.allow_credentials,
    allow_methods=app_config.allow_methods,
    allow_headers=app_config.allow_headers,
)
