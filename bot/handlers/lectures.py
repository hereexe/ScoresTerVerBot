from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("add_lecture"))
async def add_lecture_command(message: Message) -> None:
    """Start lecture creation flow. TODO: implement."""
    # TODO: check admin permissions, ask for date input, set FSM state.
    pass


async def handle_lecture_date(message: Message) -> None:
    """Handle lecture date input. TODO: implement."""
    # TODO: validate date, insert into DB, confirm to user.
    pass
