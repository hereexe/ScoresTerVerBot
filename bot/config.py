"""Configuration loading (stubs).

Expected source: environment variables and optional `.env` file.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    bot_token: str
    mongodb_uri: str
    db_name: str
    admins: set[int]


def load_settings() -> Settings:
    """Load settings from environment/.env. TODO: implement."""
    raise NotImplementedError


def parse_admins(value: str | None) -> set[int]:
    """Parse `ADMINS` env var (comma-separated TG IDs). TODO: implement."""
    raise NotImplementedError
