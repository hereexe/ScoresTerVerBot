from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def start_command(message: Message) -> None:
    """Handle /start. TODO: implement."""
    pass


async def handle_full_name(message: Message) -> None:
    """Handle full name input during onboarding. TODO: implement."""
    pass
