from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("stats"))
async def stats_command(message: Message) -> None:
    """Start stats flow. TODO: implement."""
    pass


async def choose_stats_lecture(message: Message) -> None:
    """Handle lecture selection for stats. TODO: implement."""
    pass


async def render_lecture_stats(message: Message) -> None:
    """Render group stats for selected lecture. TODO: implement."""
    pass
