"""MongoDB access layer (stubs).

Use `motor` (async MongoDB driver) and provide helpers for collections and indexes.
"""

from __future__ import annotations

from typing import Any


class Database:
    """Placeholder DB wrapper. TODO: implement."""

    def __init__(self, raw: Any) -> None:
        self.raw = raw


async def connect(mongodb_uri: str, db_name: str) -> Database:
    """Create MongoDB client and return wrapped DB object. TODO: implement."""
    raise NotImplementedError


async def ensure_indexes(db: Database) -> None:
    """Create required indexes (idempotent). TODO: implement."""
    raise NotImplementedError


def users_collection(db: Database) -> Any:
    """Return users collection handle. TODO: implement."""
    raise NotImplementedError


def lectures_collection(db: Database) -> Any:
    """Return lectures collection handle. TODO: implement."""
    raise NotImplementedError


def activities_collection(db: Database) -> Any:
    """Return activities collection handle. TODO: implement."""
    raise NotImplementedError
