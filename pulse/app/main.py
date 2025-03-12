from asyncio import AbstractEventLoop
from typing import Tuple

import uvicorn
from fastapi import FastAPI

from pulse.app.config import get_config


def get_app() -> Tuple[FastAPI, AbstractEventLoop]:
    """Import the app and event loop. We wrap this in a function to more explicitly control when it happens, because
    importing from api_app does a bunch of stuff - it's more like calling a function than importing a module.
    """
    from pulse.app.app import app, loop

    return app, loop


def run_app() -> None:
    """Main entrypoint for the app"""

    app_config = get_config()
    app, loop = get_app()

    config = uvicorn.Config(app=app, host=app_config.host, port=app_config.port, loop="asyncio")
    server = uvicorn.Server(config)

    loop.run_until_complete(server.serve())


if __name__ == "__main__":
    run_app()
