from __future__ import annotations

import re

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.db import Database
from bot.keyboards import main_menu_keyboard
from bot.states import Onboarding

router = Router()
_NOT_FOUND_TEXT = "Не нашлось никого подходящего"
_NAME_TOKEN_RE = re.compile(r"^[A-Za-zА-Яа-яЁё-]{2,}$")
_FIITBOT_HANDLES = ("@fiitbot", "@fiitobot")


@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext, db: Database) -> None:
    """Handle /start: onboard new users via @fiitobot flow."""
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
    await message.answer("Введите Имя и Фамилию (например: Елисей Яковлев).")


@router.message(StateFilter(Onboarding.full_name))
async def handle_full_name(message: Message, state: FSMContext, db: Database) -> None:
    """Handle name input and switch to waiting @fiitobot response."""
    if message.from_user is None:
        return

    text = message.text or ""
    expected_full_name = _extract_expected_full_name(text)
    if expected_full_name is None:
        await message.answer(
            "Нужно указать имя и фамилию (например: Елисей Яковлев)."
        )
        return

    expected_last_name, expected_first_name = expected_full_name.split(" ", maxsplit=1)
    fiitbot_query = f"@fiitobot {expected_first_name} {expected_last_name}"
    await state.update_data(
        expected_last_name=expected_last_name,
        expected_first_name=expected_first_name,
    )
    await state.set_state(Onboarding.wait_fiitobot_response)
    await message.answer(fiitbot_query)
    await message.answer("Запрос сформирован. Отправьте его в чат @fiitbot и пришлите сюда ответ с карточкой.")


@router.message(StateFilter(Onboarding.wait_fiitobot_response))
async def handle_fiitobot_response(message: Message, state: FSMContext, db: Database) -> None:
    """Handle copied @fiitobot response and register user."""
    if message.from_user is None:
        return

    text = message.text or ""
    full_name = _extract_full_name_from_fiitobot(text)
    if full_name is None:
        await message.answer(
            "Не удалось подтвердить пользователя. "
            "Повторите запрос в @fiitobot и отправьте найденную карточку."
        )
        return

    data = await state.get_data()
    expected_last_name = _normalize_name_token(str(data.get("expected_last_name") or ""))
    expected_first_name = _normalize_name_token(str(data.get("expected_first_name") or ""))
    actual_last_name, actual_first_name = full_name.split(" ", maxsplit=1)
    if not _same_person(
        expected_last_name=expected_last_name,
        expected_first_name=expected_first_name,
        actual_last_name=actual_last_name,
        actual_first_name=actual_first_name,
    ):
        await message.answer(
            "Полученная карточка не совпадает с введенными Имя Фамилией. "
            "Отправьте ответ от @fiitobot именно для вашего запроса."
        )
        return

    last_name, first_name = full_name.split(" ", maxsplit=1)

    users = _users_collection(db)
    await users.update_one(
        {"tg_id": message.from_user.id},
        {
            "$set": {
                "tg_id": message.from_user.id,
                "first_name": first_name,
                "last_name": last_name,
                "full_name": full_name,
                "verified_via": "fiitobot",
            }
        },
        upsert=True,
    )

    await state.clear()
    await message.answer(f"Готово! Вы авторизованы как {full_name}.", reply_markup=main_menu_keyboard())


def _extract_expected_full_name(text: str) -> str | None:
    """Parse user input as 'Имя Фамилия' and normalize to 'Фамилия Имя'."""
    normalized_text = " ".join(text.strip().split())
    if not normalized_text:
        return None

    parts = [p for p in normalized_text.split(" ") if p]
    if len(parts) != 2:
        return None

    first_name = _normalize_name_token(parts[0])
    last_name = _normalize_name_token(parts[1])
    if not first_name or not last_name:
        return None

    if not _NAME_TOKEN_RE.fullmatch(last_name):
        return None
    if not _NAME_TOKEN_RE.fullmatch(first_name):
        return None

    return f"{last_name} {first_name}"


def _extract_full_name_from_fiitobot(text: str) -> str | None:
    normalized_text = text.strip()
    if not normalized_text:
        return None

    if _NOT_FOUND_TEXT.lower() in normalized_text.lower():
        return None

    first_line = _first_non_empty_line(normalized_text)
    if first_line is None:
        return None

    lowered_first_line = first_line.lower()
    if any(lowered_first_line.startswith(handle) for handle in _FIITBOT_HANDLES):
        return None

    parts = [p for p in first_line.split(" ") if p]
    if len(parts) < 2:
        return None

    last_name = _normalize_name_token(parts[0])
    first_name = _normalize_name_token(parts[1])
    if not last_name or not first_name:
        return None

    if not _NAME_TOKEN_RE.fullmatch(last_name):
        return None
    if not _NAME_TOKEN_RE.fullmatch(first_name):
        return None

    return f"{last_name} {first_name}"


def _normalize_name_token(value: str) -> str:
    return " ".join(value.strip().strip(".,").split())


def _same_person(
    *,
    expected_last_name: str,
    expected_first_name: str,
    actual_last_name: str,
    actual_first_name: str,
) -> bool:
    return (
        expected_last_name.casefold() == actual_last_name.casefold()
        and expected_first_name.casefold() == actual_first_name.casefold()
    )


def _first_non_empty_line(text: str) -> str | None:
    for line in text.splitlines():
        candidate = " ".join(line.strip().split())
        if candidate:
            return candidate
    return None


def _users_collection(db: Database):
    raw = db.raw
    if hasattr(raw, "get_collection"):
        return raw.get_collection("users")
    return raw["users"]
