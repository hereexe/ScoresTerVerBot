from __future__ import annotations

import asyncio

from bot.handlers import start as start_handlers
from bot.states import Onboarding

from tests.fakes import FakeCollection, FakeDB, FakeFSMContext, FakeMessage, FakeUser, new_object_id


def test_start_command_existing_user_shows_menu() -> None:
    users = FakeCollection(
        "users",
        docs=[
            {"_id": new_object_id(), "tg_id": 1, "full_name": "Иван Иванов"},
        ],
    )
    db = FakeDB({"users": users})
    message = FakeMessage(from_user=FakeUser(1))
    state = FakeFSMContext()

    asyncio.run(start_handlers.start_command(message, state, db))

    assert state.state is None
    assert state.data == {}
    assert message.answers[-1][0] == "Привет, Иван Иванов!"


def test_start_command_new_user_requests_fiitobot_verification() -> None:
    users = FakeCollection("users", docs=[])
    db = FakeDB({"users": users})
    message = FakeMessage(from_user=FakeUser(123))
    state = FakeFSMContext()

    asyncio.run(start_handlers.start_command(message, state, db))

    assert state.state == Onboarding.full_name
    assert message.answers[-1][0].startswith("Для авторизации отправьте запрос в формате '@fiitobot")


def test_handle_full_name_parses_fiitobot_card_and_upserts_user() -> None:
    users = FakeCollection("users", docs=[])
    db = FakeDB({"users": users})
    text = (
        "Козлов Иван Александрович\n"
        "МЕН-240802\n"
        "ФТ-202-2 (год поступления: 2024)\n"
        "🏫 Школа: 68\n"
    )
    message = FakeMessage(from_user=FakeUser(42), text=text)
    state = FakeFSMContext(state=Onboarding.full_name)

    asyncio.run(start_handlers.handle_full_name(message, state, db))

    assert state.state is None
    assert state.data == {}
    assert message.answers[-1][0] == "Готово! Вы авторизованы как Козлов Иван."
    assert any(
        d.get("tg_id") == 42
        and d.get("full_name") == "Козлов Иван"
        and d.get("last_name") == "Козлов"
        and d.get("first_name") == "Иван"
        and d.get("verified_via") == "fiitobot"
        for d in users.docs
    )


def test_handle_full_name_rejects_not_found_response() -> None:
    users = FakeCollection("users", docs=[])
    db = FakeDB({"users": users})
    text = (
        "Не нашлось никого подходящего :(\n\n"
        "Не унывайте! Найдите кого-нибудь случайного /random!\n"
    )
    message = FakeMessage(from_user=FakeUser(10), text=text)
    state = FakeFSMContext(state=Onboarding.full_name)

    asyncio.run(start_handlers.handle_full_name(message, state, db))

    assert state.state == Onboarding.full_name
    assert users.docs == []
    assert message.answers[-1][0].startswith("Не удалось подтвердить пользователя.")


def test_handle_full_name_rejects_plain_query_without_card() -> None:
    users = FakeCollection("users", docs=[])
    db = FakeDB({"users": users})
    message = FakeMessage(from_user=FakeUser(11), text="@fiitobot Иван Иванов")
    state = FakeFSMContext(state=Onboarding.full_name)

    asyncio.run(start_handlers.handle_full_name(message, state, db))

    assert state.state == Onboarding.full_name
    assert users.docs == []
    assert message.answers[-1][0].startswith("Не удалось подтвердить пользователя.")

