from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("menu"))
async def menu_command(message: Message) -> None:
    """Show main menu. TODO: implement."""
    pass


async def add_points_entry(message: Message) -> None:
    """Entry point for adding points from menu. TODO: implement."""
    pass


async def stats_entry(message: Message) -> None:
    """Entry point for stats from menu. TODO: implement."""
    pass
