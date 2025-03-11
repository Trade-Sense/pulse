from fastapi import APIRouter

from . import stocks

api_router = APIRouter()
api_router.include_router(stocks.router, prefix="/api")
