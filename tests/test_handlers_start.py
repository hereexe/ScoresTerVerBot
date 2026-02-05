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


def test_start_command_new_user_prompts_full_name() -> None:
    users = FakeCollection("users", docs=[])
    db = FakeDB({"users": users})
    message = FakeMessage(from_user=FakeUser(123))
    state = FakeFSMContext()

    asyncio.run(start_handlers.start_command(message, state, db))

    assert state.state == Onboarding.full_name
    assert message.answers[-1][0].startswith("Введите Имя и Фамилию")


def test_handle_full_name_rejects_invalid_input() -> None:
    users = FakeCollection("users", docs=[])
    db = FakeDB({"users": users})
    message = FakeMessage(from_user=FakeUser(10), text="И И")
    state = FakeFSMContext(state=Onboarding.full_name)

    asyncio.run(start_handlers.handle_full_name(message, state, db))

    assert state.state == Onboarding.full_name
    assert users.docs == []
    assert "как минимум имя и фамилию" in message.answers[-1][0]


def test_handle_full_name_upserts_user_and_clears_state() -> None:
    users = FakeCollection("users", docs=[])
    db = FakeDB({"users": users})
    message = FakeMessage(from_user=FakeUser(42), text="  Иван   Иванов  ")
    state = FakeFSMContext(state=Onboarding.full_name)

    asyncio.run(start_handlers.handle_full_name(message, state, db))

    assert state.state is None
    assert state.data == {}
    assert message.answers[-1][0] == "Готово! Вы зарегистрированы как Иван Иванов."
    assert any(d.get("tg_id") == 42 and d.get("full_name") == "Иван Иванов" for d in users.docs)

