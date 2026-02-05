from __future__ import annotations

import asyncio

from bot.handlers import stats as stats_handlers
from bot.keyboards import CB_LECTURE_PREFIX
from bot.states import Stats

from tests.fakes import FakeCallbackQuery, FakeCollection, FakeDB, FakeFSMContext, FakeMessage, FakeUser, new_object_id


def test_start_stats_flow_requires_lectures() -> None:
    lectures = FakeCollection("lectures", docs=[])
    db = FakeDB({"lectures": lectures})
    message = FakeMessage(from_user=FakeUser(1))
    state = FakeFSMContext(state=Stats.lecture_id)

    asyncio.run(stats_handlers.start_stats_flow(message, state, db))

    assert state.state == Stats.lecture_id
    assert "Пока нет лекций" in message.answers[-1][0]


def test_start_stats_flow_sets_state_when_lectures_exist() -> None:
    lectures = FakeCollection("lectures", docs=[{"_id": new_object_id(), "date_label": "31.10.2025"}])
    db = FakeDB({"lectures": lectures})
    message = FakeMessage(from_user=FakeUser(1))
    state = FakeFSMContext()

    asyncio.run(stats_handlers.start_stats_flow(message, state, db))

    assert state.state == Stats.lecture_id
    assert message.answers[-1][0] == "Выберите лекцию:"


def test_choose_stats_lecture_rejects_unknown_lecture() -> None:
    lectures = FakeCollection("lectures", docs=[])
    db = FakeDB({"lectures": lectures})
    call = FakeCallbackQuery(data=f"{CB_LECTURE_PREFIX}31.10.2025", message=FakeMessage(from_user=FakeUser(1)))
    state = FakeFSMContext(state=Stats.lecture_id)

    asyncio.run(stats_handlers.choose_stats_lecture(call, state, db))

    assert call.answered == 1
    assert call.message is not None
    assert "Лекция не найдена" in call.message.answers[-1][0]


def test_render_lecture_stats_empty_rows() -> None:
    activities = FakeCollection("activities", docs=[])
    db = FakeDB({"activities": activities})
    message = FakeMessage(from_user=FakeUser(1))

    asyncio.run(stats_handlers.render_lecture_stats(message, db, lecture_id=new_object_id(), date_label="31.10.2025"))

    assert "Записей пока нет" in message.answers[-1][0]


def test_render_lecture_stats_formats_group_totals_and_top() -> None:
    activities = FakeCollection("activities", docs=[])
    activities.aggregate_result = [
        {"full_name": "Alice", "total": 3.0, "by_type": {"questions": 2.0, "typo": 1.0}},
        {"full_name": "Bob", "total": 1.5, "by_type": {"professor": 1.5}},
    ]
    db = FakeDB({"activities": activities})
    message = FakeMessage(from_user=FakeUser(1))

    asyncio.run(stats_handlers.render_lecture_stats(message, db, lecture_id=new_object_id(), date_label="31.10.2025"))

    text = message.answers[-1][0]
    assert "Статистика за лекцию 31.10.2025:" in text
    assert "- Вопросы: 2" in text
    assert "- Опечатка: 1" in text
    assert "- Баллы от Хлопина: 1.5" in text
    assert "- Всего: 4.5" in text
    assert "1. Alice — 3" in text
    assert "2. Bob — 1.5" in text

