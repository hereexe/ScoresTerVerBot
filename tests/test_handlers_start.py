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

    assert state.state == Onboarding.wait_fiitobot_response
    assert "Пришлите карточку" in message.answers[-1][0]


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
    state = FakeFSMContext(state=Onboarding.wait_fiitobot_response)

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


def test_handle_full_name_accepts_fiitobot_card_without_query() -> None:
    users = FakeCollection("users", docs=[])
    db = FakeDB({"users": users})
    text = (
        "*via @fiitobot*\n"
        "**Ваулин Мефодий Дмитриевич**\n"
        "МЕН-240802\n"
        "ФТ-202-2 (год поступления: 2024)\n"
    )
    message = FakeMessage(from_user=FakeUser(55), text=text)
    state = FakeFSMContext(state=Onboarding.full_name)

    asyncio.run(start_handlers.handle_full_name(message, state, db))

    assert state.state is None
    assert state.data == {}
    assert message.answers[-1][0] == "Готово! Вы авторизованы как Ваулин Мефодий."
    assert any(
        d.get("tg_id") == 55
        and d.get("full_name") == "Ваулин Мефодий"
        and d.get("last_name") == "Ваулин"
        and d.get("first_name") == "Мефодий"
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
    state = FakeFSMContext(state=Onboarding.wait_fiitobot_response)

    asyncio.run(start_handlers.handle_fiitobot_response(message, state, db))

    assert state.state == Onboarding.wait_fiitobot_response
    assert users.docs == []
    assert message.answers[-1][0].startswith("Не удалось распознать карточку.")


def test_handle_fiitobot_response_rejects_mismatch_with_entered_name() -> None:
    users = FakeCollection("users", docs=[])
    db = FakeDB({"users": users})
    text = "Петров"
    message = FakeMessage(from_user=FakeUser(89), text=text)
    state = FakeFSMContext(state=Onboarding.wait_fiitobot_response)

    asyncio.run(start_handlers.handle_fiitobot_response(message, state, db))

    assert state.state == Onboarding.wait_fiitobot_response
    assert users.docs == []
    assert "Не удалось распознать" in message.answers[-1][0]


def test_handle_card_out_of_state_registers_user_without_start() -> None:
    users = FakeCollection("users", docs=[])
    db = FakeDB({"users": users})
    text = "*via @fiitobot*\n**Иванов Иван Сергеевич**\nГруппа"
    message = FakeMessage(from_user=FakeUser(101), text=text)
    state = FakeFSMContext()

    asyncio.run(start_handlers.handle_card_out_of_state(message, state, db))

    assert state.state is None
    assert any(d.get("tg_id") == 101 and d.get("full_name") == "Иванов Иван" for d in users.docs)
    assert message.answers[-1][0] == "Готово! Вы авторизованы как Иванов Иван."


def test_handle_card_out_of_state_ignores_already_registered_user() -> None:
    users = FakeCollection("users", docs=[{"_id": new_object_id(), "tg_id": 202, "full_name": "Старый Пользователь"}])
    db = FakeDB({"users": users})
    text = "*via @fiitobot*\n**Новый Пользователь**"
    message = FakeMessage(from_user=FakeUser(202), text=text)
    state = FakeFSMContext()

    asyncio.run(start_handlers.handle_card_out_of_state(message, state, db))

    assert state.state is None
    assert len(message.answers) == 0
    # Should keep existing user untouched.
    assert any(d.get("tg_id") == 202 and d.get("full_name") == "Старый Пользователь" for d in users.docs)


def test_process_card_skips_lines_with_handle_and_uses_next_line() -> None:
    users = FakeCollection("users", docs=[])
    db = FakeDB({"users": users})
    text = "@fiitobot Иван Иванов\n**Петров Петр Петрович**\nДанные"
    message = FakeMessage(from_user=FakeUser(303), text=text)
    state = FakeFSMContext(state=Onboarding.wait_fiitobot_response)

    asyncio.run(start_handlers.handle_fiitobot_response(message, state, db))

    assert state.state is None
    assert any(d.get("tg_id") == 303 and d.get("full_name") == "Петров Петр" for d in users.docs)
    assert message.answers[-1][0] == "Готово! Вы авторизованы как Петров Петр."
