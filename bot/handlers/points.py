from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("add_points"))
async def add_points_command(message: Message) -> None:
    """Start add-points FSM flow. TODO: implement."""
    pass


async def choose_lecture(message: Message) -> None:
    """Handle lecture selection step. TODO: implement."""
    pass


async def choose_activity_type(message: Message) -> None:
    """Handle activity type selection step. TODO: implement."""
    pass


async def input_points_value(message: Message) -> None:
    """Handle numeric points input step. TODO: implement."""
    pass


async def save_activity(message: Message) -> None:
    """Persist activity document. TODO: implement."""
    pass
