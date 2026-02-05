"""MongoDB access layer.

Uses `motor` (async MongoDB driver) and provides:
- a lightweight `Database` wrapper for DI (dependency injection)
- collection helpers
- idempotent index creation
"""

from __future__ import annotations

from dataclasses import dataclass

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase


@dataclass(frozen=True, slots=True)
class Database:
    """A thin wrapper around Motor client + database object."""

    client: AsyncIOMotorClient
    db: AsyncIOMotorDatabase

    @property
    def raw(self) -> AsyncIOMotorDatabase:
        # Backwards-compat: handlers currently access `db.raw` directly.
        return self.db

    def close(self) -> None:
        self.client.close()


async def connect(mongodb_uri: str, db_name: str) -> Database:
    """Create MongoDB client, verify connectivity, and return wrapped DB object."""
    client = AsyncIOMotorClient(
        mongodb_uri,
        serverSelectionTimeoutMS=5_000,
    )
    # Fail fast on invalid credentials / unreachable cluster.
    await client.admin.command("ping")
    db = client.get_database(db_name)
    return Database(client=client, db=db)


async def ensure_indexes(db: Database) -> None:
    """Create required indexes (idempotent)."""
    await users_collection(db).create_index("tg_id", unique=True)
    await lectures_collection(db).create_index("date_label", unique=True)

    # Common query/aggregation paths.
    await activities_collection(db).create_index("lecture_id")
    await activities_collection(db).create_index("user_id")
    await activities_collection(db).create_index("type")


def users_collection(db: Database) -> AsyncIOMotorCollection:
    """Return users collection handle."""
    return db.db.get_collection("users")


def lectures_collection(db: Database) -> AsyncIOMotorCollection:
    """Return lectures collection handle."""
    return db.db.get_collection("lectures")


def activities_collection(db: Database) -> AsyncIOMotorCollection:
    """Return activities collection handle."""
    return db.db.get_collection("activities")
