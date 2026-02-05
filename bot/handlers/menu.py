from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.db import Database
from bot.keyboards import BTN_ADD_POINTS, BTN_STATS, main_menu_keyboard

router = Router()


@router.message(Command("menu"))
async def menu_command(message: Message, state: FSMContext) -> None:
    """Show main menu."""
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_menu_keyboard())


@router.message(F.text == BTN_ADD_POINTS)
async def add_points_entry(message: Message, state: FSMContext, db: Database) -> None:
    """Entry point for adding points from menu."""
    # Local import to avoid circular dependencies at import time.
    from bot.handlers.points import start_add_points_flow

    await start_add_points_flow(message, state, db)


@router.message(F.text == BTN_STATS)
async def stats_entry(message: Message, state: FSMContext, db: Database) -> None:
    """Entry point for stats from menu."""
    from bot.handlers.stats import start_stats_flow

    await start_stats_flow(message, state, db)
