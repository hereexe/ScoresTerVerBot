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
    await message.answer(
        "Для авторизации отправьте запрос в формате '@fiitobot Имя Фамилия' "
        "и затем пришлите карточку от @fiitobot."
    )


@router.message(StateFilter(Onboarding.full_name))
async def handle_full_name(message: Message, state: FSMContext, db: Database) -> None:
    """Handle query input and switch to waiting @fiitobot response."""
    if message.from_user is None:
        return

    text = message.text or ""
    if "fiitobot" in text.casefold():
        full_name_from_card = _extract_full_name_from_fiitobot(text)
        if full_name_from_card is not None:
            await _register_user(db, tg_id=message.from_user.id, full_name=full_name_from_card)
            await state.clear()
            await message.answer(
                f"Готово! Вы авторизованы как {full_name_from_card}.",
                reply_markup=main_menu_keyboard(),
            )
            return

    expected_full_name = _extract_expected_full_name(text)
    if expected_full_name is None:
        await message.answer(
            "Нужно отправить запрос строго в формате '@fiitobot Имя Фамилия'."
        )
        return

    expected_last_name, expected_first_name = expected_full_name.split(" ", maxsplit=1)
    fiitbot_query = _build_fiitbot_query(f"{expected_first_name} {expected_last_name}")
    await state.update_data(
        expected_last_name=expected_last_name,
        expected_first_name=expected_first_name,
        fiitbot_query=fiitbot_query,
    )
    await state.set_state(Onboarding.wait_fiitobot_response)
    await message.answer("Запрос принят. Теперь пришлите карточку-ответ от @fiitobot.")


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


def _extract_expected_full_name(text: str) -> str | None:
    """Parse user input as '@fiitobot Имя Фамилия' and normalize to 'Фамилия Имя'."""
    normalized_text = " ".join(text.strip().split())
    if not normalized_text:
        return None

    parts = [p for p in normalized_text.split(" ") if p]
    if len(parts) != 3:
        return None

    handle = parts[0].casefold()
    if handle not in {h.casefold() for h in _FIITBOT_HANDLES}:
        return None

    first_name = _normalize_name_token(parts[1])
    last_name = _normalize_name_token(parts[2])
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


def _build_fiitbot_query(value: str) -> str:
    normalized = " ".join(value.strip().split())
    return f"@fiitobot {normalized}"


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
