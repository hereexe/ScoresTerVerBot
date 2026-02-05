from __future__ import annotations

from datetime import datetime

from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.config import Settings
from bot.db import Database
from bot.keyboards import main_menu_keyboard
from bot.states import AddLecture

router = Router()


@router.message(Command("add_lecture"))
async def add_lecture_command(
    message: Message,
    state: FSMContext,
    settings: Settings,
) -> None:
    """Start lecture creation flow (admin-only)."""
    if message.from_user is None:
        return

    if message.from_user.id not in settings.admins:
        await message.answer("Недостаточно прав для добавления лекций.")
        return

    await state.clear()
    await state.set_state(AddLecture.date_label)
    await message.answer(
        "Введите дату лекции в формате DD.MM.YYYY (например, 31.10.2025).",
        reply_markup=main_menu_keyboard(),
    )


@router.message(StateFilter(AddLecture.date_label))
async def handle_lecture_date(
    message: Message,
    state: FSMContext,
    settings: Settings,
    db: Database,
) -> None:
    """Handle lecture date input and store it in DB (admin-only)."""
    if message.from_user is None:
        return

    if message.from_user.id not in settings.admins:
        await state.clear()
        await message.answer("Недостаточно прав для добавления лекций.")
        return

    if not message.text:
        await message.answer("Отправьте дату лекции текстом в формате DD.MM.YYYY.")
        return

    try:
        date_label = _normalize_date_label(message.text)
    except ValueError:
        await message.answer("Неверная дата. Формат: DD.MM.YYYY (пример: 31.10.2025).")
        return

    lectures = _lectures_collection(db)
    result = await lectures.update_one(
        {"date_label": date_label},
        {"$setOnInsert": {"date_label": date_label}},
        upsert=True,
    )

    await state.clear()

    if result.upserted_id is None:
        await message.answer(f"Лекция {date_label} уже существует.", reply_markup=main_menu_keyboard())
        return

    await message.answer(f"Лекция {date_label} добавлена.", reply_markup=main_menu_keyboard())


def _normalize_date_label(text: str) -> str:
    """Parse user input into normalized `DD.MM.YYYY` string."""
    dt = datetime.strptime(text.strip(), "%d.%m.%Y")
    return dt.strftime("%d.%m.%Y")


def _lectures_collection(db: Database):
    """Return motor collection for lectures without depending on db helpers yet."""
    raw = db.raw
    if hasattr(raw, "get_collection"):
        return raw.get_collection("lectures")
    return raw["lectures"]
