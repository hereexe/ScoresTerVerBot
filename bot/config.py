"""Configuration loading (stubs).

Expected source: environment variables and optional `.env` file.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Settings:
    bot_token: str
    mongodb_uri: str
    db_name: str
    admins: set[int]


def load_settings() -> Settings:
    """Load settings from environment and optional `.env` file.

    Required:
    - BOT_TOKEN
    - MONGODB_URI
    Optional:
    - DB_NAME (default: scores_bot)
    - ADMINS (comma-separated TG user IDs)
    """
    load_dotenv()

    bot_token = _require_env("BOT_TOKEN")
    mongodb_uri = _require_env("MONGODB_URI")
    db_name = (os.getenv("DB_NAME") or "scores_bot").strip() or "scores_bot"
    admins = parse_admins(os.getenv("ADMINS"))

    return Settings(
        bot_token=bot_token,
        mongodb_uri=mongodb_uri,
        db_name=db_name,
        admins=admins,
    )


def parse_admins(value: str | None) -> set[int]:
    """Parse `ADMINS` env var (comma-separated TG IDs)."""
    if value is None:
        return set()

    ids: set[int] = set()
    for raw in value.replace(";", ",").split(","):
        part = raw.strip()
        if not part:
            continue
        try:
            tg_id = int(part)
        except ValueError as e:
            raise ValueError(f"ADMINS contains non-integer value: {part!r}") from e
        if tg_id <= 0:
            raise ValueError(f"ADMINS contains invalid TG ID (must be > 0): {part!r}")
        ids.add(tg_id)
    return ids


def _require_env(name: str) -> str:
    value = (os.getenv(name) or "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value
