"""Async MongoDB connection management via Motor."""

from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import Settings, get_settings

_client: AsyncIOMotorClient | None = None
_database: AsyncIOMotorDatabase | None = None


def get_client(settings: Settings | None = None) -> AsyncIOMotorClient:
    """Return the active Motor client, creating one if necessary."""
    global _client

    if _client is None:
        cfg = settings or get_settings()
        _client = AsyncIOMotorClient(
            cfg.mongodb_uri,
            serverSelectionTimeoutMS=5000,
        )

    return _client


def get_database(settings: Settings | None = None) -> AsyncIOMotorDatabase:
    """Return the configured database handle."""
    global _database

    if _database is None:
        cfg = settings or get_settings()
        _database = get_client(cfg)[cfg.mongodb_db_name]

    return _database


async def connect_to_mongo(settings: Settings | None = None) -> None:
    """Verify connectivity and initialize the database handle."""
    cfg = settings or get_settings()
    db = get_database(cfg)
    try:
        await db.command("ping")
    except Exception as exc:
        message = str(exc).lower()
        if "bad auth" in message or "authentication failed" in message:
            raise RuntimeError(
                "MongoDB authentication failed. Check MONGODB_URI on Render: "
                "use a Database Access user (not Atlas login email), "
                "URL-encode special characters in the password, and allow "
                "0.0.0.0/0 under Network Access."
            ) from exc
        raise


async def close_mongo_connection() -> None:
    """Gracefully close the Motor client and reset module-level state."""
    global _client, _database

    if _client is not None:
        _client.close()
        _client = None
        _database = None


async def get_products_collection(settings: Settings | None = None) -> Any:
    """Shortcut to the products collection."""
    cfg = settings or get_settings()
    return get_database(cfg)[cfg.products_collection]


async def get_sales_collection(settings: Settings | None = None) -> Any:
    """Shortcut to the sales collection."""
    cfg = settings or get_settings()
    return get_database(cfg)[cfg.sales_collection]


async def get_users_collection(settings: Settings | None = None) -> Any:
    """Shortcut to the users collection."""
    cfg = settings or get_settings()
    return get_database(cfg)[cfg.users_collection]
