from __future__ import annotations

from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.db import Database
from bot.keyboards import main_menu_keyboard
from bot.states import Onboarding

router = Router()


@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext, db: Database) -> None:
    """Handle /start: onboarding or show menu for existing users."""
    if message.from_user is None:
        return

    users = _users_collection(db)
    existing = await users.find_one({"tg_id": message.from_user.id})
    if existing is not None:
        await state.clear()
        full_name = existing.get("full_name") or "студент"
        await message.answer(f"Привет, {full_name}!", reply_markup=main_menu_keyboard())
        return

    await state.clear()
    await state.set_state(Onboarding.full_name)
    await message.answer("Введите Имя и Фамилию (например: Иван Иванов).")


@router.message(StateFilter(Onboarding.full_name))
async def handle_full_name(message: Message, state: FSMContext, db: Database) -> None:
    """Handle full name input during onboarding and create/update user doc."""
    if message.from_user is None:
        return

    if not message.text:
        await message.answer("Отправьте Имя и Фамилию текстом (например: Иван Иванов).")
        return

    full_name = _normalize_full_name(message.text)
    if not _is_valid_full_name(full_name):
        await message.answer("Нужно указать как минимум имя и фамилию (например: Иван Иванов).")
        return

    users = _users_collection(db)
    await users.update_one(
        {"tg_id": message.from_user.id},
        {"$set": {"tg_id": message.from_user.id, "full_name": full_name}},
        upsert=True,
    )

    await state.clear()
    await message.answer(f"Готово! Вы зарегистрированы как {full_name}.", reply_markup=main_menu_keyboard())


def _normalize_full_name(text: str) -> str:
    return " ".join(text.strip().split())


def _is_valid_full_name(full_name: str) -> bool:
    parts = [p for p in full_name.split(" ") if p]
    return len(parts) >= 2 and all(len(p) >= 2 for p in parts[:2])


def _users_collection(db: Database):
    raw = db.raw
    if hasattr(raw, "get_collection"):
        return raw.get_collection("users")
    return raw["users"]
