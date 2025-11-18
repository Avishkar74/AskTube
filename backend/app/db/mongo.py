from typing import Any

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from ..core.config import get_settings
from ..core.logging import logger
import asyncio
import time

DEFAULT_CONNECT_TIMEOUT_MS = 4000
RETRY_ATTEMPTS = 3
RETRY_BACKOFF_SEC = 1.5


async def _attempt_connect(uri: str) -> AsyncIOMotorClient | None:
    try:
        client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=DEFAULT_CONNECT_TIMEOUT_MS)
        # Motor ping
        await client.admin.command("ping")
        return client
    except Exception as e:
        logger.warning(f"Mongo connection attempt failed: {e}")
        return None


async def init_mongo(app: FastAPI) -> None:
    settings = get_settings()
    uri = settings.mongo_uri
    app.state.mongo_error = None
    app.state.mongo_connected = False
    app.state.mongo_client = None
    app.state.db = None

    if not uri:
        app.state.mongo_error = "No Mongo URI configured"
        logger.info("Mongo not configured (mongo uri missing)")
        return

    for attempt in range(1, RETRY_ATTEMPTS + 1):
        client = await _attempt_connect(uri)
        if client:
            app.state.mongo_client = client
            app.state.db = client[settings.mongo_db_name]
            app.state.mongo_connected = True
            logger.info(f"Mongo connected on attempt {attempt}")
            break
        if attempt < RETRY_ATTEMPTS:
            await asyncio.sleep(RETRY_BACKOFF_SEC * attempt)
    if not app.state.mongo_connected:
        app.state.mongo_error = f"Failed to connect after {RETRY_ATTEMPTS} attempts"
        logger.error(app.state.mongo_error)


async def close_mongo(app: FastAPI) -> None:
    client: AsyncIOMotorClient | None = getattr(app.state, "mongo_client", None)
    if client is not None:
        client.close()
    app.state.mongo_client = None
    app.state.db = None
    app.state.mongo_connected = False


def get_db(app: FastAPI) -> AsyncIOMotorDatabase | None:
    return getattr(app.state, "db", None)
