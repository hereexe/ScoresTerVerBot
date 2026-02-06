from __future__ import annotations

import re

from aiogram import F, Router
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
    await state.set_state(Onboarding.wait_fiitobot_response)
    await message.answer("Пришлите карточку из @fiitobot (скопируйте сообщение целиком).")


@router.message(StateFilter(Onboarding.full_name))
async def handle_full_name(message: Message, state: FSMContext, db: Database) -> None:
    """Backward compatibility: attempt to parse @fiitobot card even in old state."""
    await _process_fiitobot_card(message, state, db)


@router.message(StateFilter(Onboarding.wait_fiitobot_response))
async def handle_fiitobot_response(message: Message, state: FSMContext, db: Database) -> None:
    """Handle copied @fiitobot response and register user."""
    await _process_fiitobot_card(message, state, db)


@router.message(F.text.func(lambda t: t is not None and "fiitobot" in t.casefold()))
async def handle_card_out_of_state(message: Message, state: FSMContext, db: Database) -> None:
    """Allow instant authorization if user sends fiitobot card without /start."""
    if message.from_user is None:
        return

    # Skip if already registered.
    users = _users_collection(db)
    if await users.find_one({"tg_id": message.from_user.id}) is not None:
        return

    await state.set_state(Onboarding.wait_fiitobot_response)
    await _process_fiitobot_card(message, state, db)


async def _process_fiitobot_card(message: Message, state: FSMContext, db: Database) -> None:
    """Parse fiitobot card, persist user, or prompt retry."""
    if message.from_user is None:
        return

    full_name = _extract_full_name_from_fiitobot(message.text or "")
    if full_name is None:
        await state.set_state(Onboarding.wait_fiitobot_response)
        await message.answer(
            "Не удалось распознать карточку. "
            "Скопируйте ответ от @fiitobot целиком (без изменений) и отправьте сюда."
        )
        return

    await _register_user(db, tg_id=message.from_user.id, full_name=full_name)
    await state.clear()
    await message.answer(f"Готово! Вы авторизованы как {full_name}.", reply_markup=main_menu_keyboard())


async def _register_user(db: Database, *, tg_id: int, full_name: str) -> None:
    """Persist user profile after successful verification."""
    last_name, first_name = full_name.split(" ", maxsplit=1)

    users = _users_collection(db)
    await users.update_one(
        {"tg_id": tg_id},
        {
            "$set": {
                "tg_id": tg_id,
                "first_name": first_name,
                "last_name": last_name,
                "full_name": full_name,
                "verified_via": "fiitobot",
            }
        },
        upsert=True,
    )


def _extract_full_name_from_fiitobot(text: str) -> str | None:
    normalized_text = text.strip()
    if not normalized_text:
        return None

    if _NOT_FOUND_TEXT.lower() in normalized_text.lower():
        return None

    for line in _candidate_lines(normalized_text):
        parts = [p for p in line.split(" ") if p]
        if len(parts) < 2:
            continue

        last_name = _normalize_name_token(parts[0])
        first_name = _normalize_name_token(parts[1])
        if not last_name or not first_name:
            continue

        if not _NAME_TOKEN_RE.fullmatch(last_name):
            continue
        if not _NAME_TOKEN_RE.fullmatch(first_name):
            continue

        return f"{last_name} {first_name}"

    return None


def _normalize_name_token(value: str) -> str:
    cleaned = " ".join(value.strip().split())
    return cleaned.strip(".,*_>-—")


def _candidate_lines(text: str) -> list[str]:
    candidates: list[str] = []
    for line in text.splitlines():
        candidate = " ".join(line.strip().split())
        if not candidate:
            continue
        candidate = candidate.strip("*_>•-—").strip()
        if not candidate:
            continue
        lowered = candidate.casefold()
        if any(handle in lowered for handle in _FIITBOT_HANDLES):
            continue
        candidates.append(candidate)
    return candidates


def _users_collection(db: Database):
    raw = db.raw
    if hasattr(raw, "get_collection"):
        return raw.get_collection("users")
    return raw["users"]
