"""Handlers package.

`setup_router()` is the single entrypoint used by the application to register all handlers.
"""

from __future__ import annotations

from aiogram import Router


def setup_router() -> Router:
    """Create root router and include all feature routers."""
    root = Router()

    # Import routers lazily to keep module import side-effects predictable.
    from bot.handlers import lectures, menu, points, start, stats

    root.include_router(start.router)
    root.include_router(menu.router)
    root.include_router(lectures.router)
    root.include_router(points.router)
    root.include_router(stats.router)

    return root
