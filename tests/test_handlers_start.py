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


def test_handle_full_name_moves_to_waiting_fiitobot_response() -> None:
    users = FakeCollection("users", docs=[])
    db = FakeDB({"users": users})
    message = FakeMessage(from_user=FakeUser(42), text="Елисей Яковлев")
    state = FakeFSMContext(state=Onboarding.full_name)

    asyncio.run(start_handlers.handle_full_name(message, state, db))

    assert state.state == Onboarding.wait_fiitobot_response
    assert state.data["expected_last_name"] == "Яковлев"
    assert state.data["expected_first_name"] == "Елисей"
    assert state.data["fiitbot_query"] == "@fiitobot Елисей Яковлев"
    assert len(message.answers) == 1
    assert message.answers[-1][0].startswith("Запрос авторизации принят.")


def test_handle_full_name_normalizes_query_format() -> None:
    users = FakeCollection("users", docs=[])
    db = FakeDB({"users": users})
    message = FakeMessage(from_user=FakeUser(111), text="  Елисей   Яковлев  ")
    state = FakeFSMContext(state=Onboarding.full_name)

    asyncio.run(start_handlers.handle_full_name(message, state, db))

    assert state.state == Onboarding.wait_fiitobot_response
    assert state.data["fiitbot_query"] == "@fiitobot Елисей Яковлев"
    assert len(message.answers) == 1
    assert message.answers[-1][0].startswith("Запрос авторизации принят.")


def test_handle_full_name_rejects_invalid_name() -> None:
    users = FakeCollection("users", docs=[])
    db = FakeDB({"users": users})
    message = FakeMessage(from_user=FakeUser(10), text="И")
    state = FakeFSMContext(state=Onboarding.full_name)

    asyncio.run(start_handlers.handle_full_name(message, state, db))

    assert state.state == Onboarding.full_name
    assert users.docs == []
    assert "Нужно указать имя и фамилию" in message.answers[-1][0]


def test_handle_fiitobot_response_parses_card_and_upserts_user() -> None:
    users = FakeCollection("users", docs=[])
    db = FakeDB({"users": users})
    text = (
        "Яковлев Елисей Евгеньевич\n"
        "МЕН-240802\n"
        "ФТ-202-2 (год поступления: 2024)\n"
        "🏫 Школа: 68\n"
    )
    message = FakeMessage(from_user=FakeUser(77), text=text)
    state = FakeFSMContext(
        state=Onboarding.wait_fiitobot_response,
        data={"expected_last_name": "Яковлев", "expected_first_name": "Елисей"},
    )

    asyncio.run(start_handlers.handle_fiitobot_response(message, state, db))

    assert state.state is None
    assert state.data == {}
    assert message.answers[-1][0] == "Готово! Вы авторизованы как Яковлев Елисей."
    assert any(
        d.get("tg_id") == 77
        and d.get("full_name") == "Яковлев Елисей"
        and d.get("last_name") == "Яковлев"
        and d.get("first_name") == "Елисей"
        and d.get("verified_via") == "fiitobot"
        for d in users.docs
    )


def test_handle_fiitobot_response_rejects_not_found_response() -> None:
    users = FakeCollection("users", docs=[])
    db = FakeDB({"users": users})
    text = (
        "Не нашлось никого подходящего :(\n\n"
        "Не унывайте! Найдите кого-нибудь случайного /random!\n"
    )
    message = FakeMessage(from_user=FakeUser(88), text=text)
    state = FakeFSMContext(
        state=Onboarding.wait_fiitobot_response,
        data={"expected_last_name": "Яковлев", "expected_first_name": "Елисей"},
    )

    asyncio.run(start_handlers.handle_fiitobot_response(message, state, db))

    assert state.state == Onboarding.wait_fiitobot_response
    assert users.docs == []
    assert message.answers[-1][0].startswith("Не удалось подтвердить пользователя.")


def test_handle_fiitobot_response_rejects_mismatch_with_entered_name() -> None:
    users = FakeCollection("users", docs=[])
    db = FakeDB({"users": users})
    text = (
        "Петров Иван Сергеевич\n"
        "МЕН-240802\n"
    )
    message = FakeMessage(from_user=FakeUser(89), text=text)
    state = FakeFSMContext(
        state=Onboarding.wait_fiitobot_response,
        data={"expected_last_name": "Яковлев", "expected_first_name": "Елисей"},
    )

    asyncio.run(start_handlers.handle_fiitobot_response(message, state, db))

    assert state.state == Onboarding.wait_fiitobot_response
    assert users.docs == []
    assert "не совпадает с введенными" in message.answers[-1][0]
