from __future__ import annotations

import asyncio

from bot.config import Settings
from bot.handlers import lectures as lectures_handlers
from bot.states import AddLecture

from tests.fakes import FakeCollection, FakeDB, FakeFSMContext, FakeMessage, FakeUser, new_object_id


def _settings(*, admins: set[int]) -> Settings:
    return Settings(
        bot_token="token",
        mongodb_uri="mongodb://example",
        db_name="db",
        admins=admins,
    )


def test_add_lecture_command_rejects_non_admin() -> None:
    message = FakeMessage(from_user=FakeUser(1))
    state = FakeFSMContext(state=AddLecture.date_label)
    settings = _settings(admins={2})

    asyncio.run(lectures_handlers.add_lecture_command(message, state, settings))

    assert state.state == AddLecture.date_label
    assert message.answers[-1][0] == "Недостаточно прав для добавления лекций."


def test_add_lecture_command_sets_state_for_admin() -> None:
    message = FakeMessage(from_user=FakeUser(2))
    state = FakeFSMContext(state=AddLecture.date_label)
    settings = _settings(admins={2})

    asyncio.run(lectures_handlers.add_lecture_command(message, state, settings))

    assert state.state == AddLecture.date_label
    assert message.answers[-1][0].startswith("Введите дату лекции")


def test_handle_lecture_date_rejects_non_admin_and_clears_state() -> None:
    lectures = FakeCollection("lectures", docs=[])
    db = FakeDB({"lectures": lectures})
    message = FakeMessage(from_user=FakeUser(1), text="31.10.2025")
    state = FakeFSMContext(state=AddLecture.date_label)
    settings = _settings(admins={2})

    asyncio.run(lectures_handlers.handle_lecture_date(message, state, settings, db))

    assert state.state is None
    assert message.answers[-1][0] == "Недостаточно прав для добавления лекций."


def test_handle_lecture_date_rejects_invalid_date() -> None:
    lectures = FakeCollection("lectures", docs=[])
    db = FakeDB({"lectures": lectures})
    message = FakeMessage(from_user=FakeUser(2), text="31-10-2025")
    state = FakeFSMContext(state=AddLecture.date_label)
    settings = _settings(admins={2})

    asyncio.run(lectures_handlers.handle_lecture_date(message, state, settings, db))

    assert state.state == AddLecture.date_label
    assert message.answers[-1][0].startswith("Неверная дата")


def test_handle_lecture_date_reports_duplicate() -> None:
    lectures = FakeCollection(
        "lectures",
        docs=[
            {"_id": new_object_id(), "date_label": "31.10.2025"},
        ],
    )
    db = FakeDB({"lectures": lectures})
    message = FakeMessage(from_user=FakeUser(2), text="31.10.2025")
    state = FakeFSMContext(state=AddLecture.date_label)
    settings = _settings(admins={2})

    asyncio.run(lectures_handlers.handle_lecture_date(message, state, settings, db))

    assert state.state is None
    assert message.answers[-1][0] == "Лекция 31.10.2025 уже существует."
    assert len(lectures.docs) == 1


def test_handle_lecture_date_inserts_new_lecture_and_normalizes() -> None:
    lectures = FakeCollection("lectures", docs=[])
    db = FakeDB({"lectures": lectures})
    message = FakeMessage(from_user=FakeUser(2), text="1.1.2025")
    state = FakeFSMContext(state=AddLecture.date_label)
    settings = _settings(admins={2})

    asyncio.run(lectures_handlers.handle_lecture_date(message, state, settings, db))

    assert state.state is None
    assert message.answers[-1][0] == "Лекция 01.01.2025 добавлена."
    assert any(d.get("date_label") == "01.01.2025" for d in lectures.docs)

