from __future__ import annotations

import asyncio
from datetime import timezone

from bson import ObjectId

from bot.handlers import points as points_handlers
from bot.keyboards import CB_ACTIVITY_PREFIX, CB_LECTURE_PREFIX
from bot.states import AddPoints

from tests.fakes import (
    FakeCallbackQuery,
    FakeCollection,
    FakeDB,
    FakeFSMContext,
    FakeMessage,
    FakeUser,
    new_object_id,
)


def test_start_add_points_flow_requires_registration() -> None:
    users = FakeCollection("users", docs=[])
    lectures = FakeCollection("lectures", docs=[])
    db = FakeDB({"users": users, "lectures": lectures})
    message = FakeMessage(from_user=FakeUser(1))
    state = FakeFSMContext(state=AddPoints.lecture_id, data={"x": "y"})

    asyncio.run(points_handlers.start_add_points_flow(message, state, db))

    assert state.state == AddPoints.lecture_id
    assert "Сначала зарегистрируйтесь" in message.answers[-1][0]


def test_start_add_points_flow_requires_lectures() -> None:
    users = FakeCollection("users", docs=[{"_id": new_object_id(), "tg_id": 1, "full_name": "A B"}])
    lectures = FakeCollection("lectures", docs=[])
    db = FakeDB({"users": users, "lectures": lectures})
    message = FakeMessage(from_user=FakeUser(1))
    state = FakeFSMContext(state=AddPoints.lecture_id)

    asyncio.run(points_handlers.start_add_points_flow(message, state, db))

    assert state.state == AddPoints.lecture_id
    assert "Пока нет лекций" in message.answers[-1][0]


def test_start_add_points_flow_sets_state_and_user_id() -> None:
    user_id = new_object_id()
    users = FakeCollection("users", docs=[{"_id": user_id, "tg_id": 1, "full_name": "A B"}])
    lectures = FakeCollection("lectures", docs=[{"_id": new_object_id(), "date_label": "31.10.2025"}])
    db = FakeDB({"users": users, "lectures": lectures})
    message = FakeMessage(from_user=FakeUser(1))
    state = FakeFSMContext()

    asyncio.run(points_handlers.start_add_points_flow(message, state, db))

    assert state.state == AddPoints.lecture_id
    assert state.data["user_id"] == str(user_id)
    assert message.answers[-1][0] == "Выберите лекцию:"


def test_choose_lecture_rejects_unknown_date_label() -> None:
    lectures = FakeCollection("lectures", docs=[])
    db = FakeDB({"lectures": lectures})
    call = FakeCallbackQuery(data=f"{CB_LECTURE_PREFIX}31.10.2025", message=FakeMessage(from_user=FakeUser(1)))
    state = FakeFSMContext(state=AddPoints.lecture_id)

    asyncio.run(points_handlers.choose_lecture(call, state, db))

    assert call.answered == 1
    assert call.message is not None
    assert "Лекция не найдена" in call.message.answers[-1][0]
    assert state.state == AddPoints.lecture_id


def test_choose_lecture_moves_to_activity_type() -> None:
    lecture_id = new_object_id()
    lectures = FakeCollection("lectures", docs=[{"_id": lecture_id, "date_label": "31.10.2025"}])
    db = FakeDB({"lectures": lectures})
    call = FakeCallbackQuery(data=f"{CB_LECTURE_PREFIX}31.10.2025", message=FakeMessage(from_user=FakeUser(1)))
    state = FakeFSMContext(state=AddPoints.lecture_id, data={"user_id": new_object_id()})

    asyncio.run(points_handlers.choose_lecture(call, state, db))

    assert state.state == AddPoints.activity_type
    assert state.data["lecture_id"] == str(lecture_id)
    assert state.data["lecture_date_label"] == "31.10.2025"
    assert call.message is not None
    assert call.message.answers[-1][0] == "Выберите категорию:"


def test_choose_activity_type_rejects_unknown_type() -> None:
    call = FakeCallbackQuery(
        data=f"{CB_ACTIVITY_PREFIX}unknown",
        message=FakeMessage(from_user=FakeUser(1)),
    )
    state = FakeFSMContext(state=AddPoints.activity_type)

    asyncio.run(points_handlers.choose_activity_type(call, state))

    assert state.state == AddPoints.activity_type
    assert call.message is not None
    assert "Неизвестная категория" in call.message.answers[-1][0]


def test_choose_activity_type_sets_value_state() -> None:
    call = FakeCallbackQuery(
        data=f"{CB_ACTIVITY_PREFIX}questions",
        message=FakeMessage(from_user=FakeUser(1)),
    )
    state = FakeFSMContext(state=AddPoints.activity_type)

    asyncio.run(points_handlers.choose_activity_type(call, state))

    assert state.state == AddPoints.value
    assert state.data["activity_type"] == "questions"
    assert call.message is not None
    assert "Введите количество баллов" in call.message.answers[-1][0]


def test_input_points_value_rejects_non_positive_number() -> None:
    activities = FakeCollection("activities", docs=[])
    db = FakeDB({"activities": activities})
    message = FakeMessage(from_user=FakeUser(1), text="0")
    state = FakeFSMContext(
        state=AddPoints.value,
        data={
            "user_id": new_object_id(),
            "lecture_id": new_object_id(),
            "activity_type": "questions",
            "lecture_date_label": "31.10.2025",
        },
    )

    asyncio.run(points_handlers.input_points_value(message, state, db))

    assert state.state == AddPoints.value
    assert "Нужно положительное число" in message.answers[-1][0]
    assert activities.inserted_docs == []


def test_input_points_value_clears_state_on_expired_session() -> None:
    activities = FakeCollection("activities", docs=[])
    db = FakeDB({"activities": activities})
    message = FakeMessage(from_user=FakeUser(1), text="2")
    state = FakeFSMContext(state=AddPoints.value, data={})

    asyncio.run(points_handlers.input_points_value(message, state, db))

    assert state.state is None
    assert "Сессия ввода устарела" in message.answers[-1][0]
    assert activities.inserted_docs == []


def test_input_points_value_inserts_activity_and_confirms() -> None:
    activities = FakeCollection("activities", docs=[])
    db = FakeDB({"activities": activities})
    user_id = new_object_id()
    lecture_id = new_object_id()
    message = FakeMessage(from_user=FakeUser(1), text="2")
    state = FakeFSMContext(
        state=AddPoints.value,
        data={
            "user_id": user_id,
            "lecture_id": lecture_id,
            "activity_type": "questions",
            "lecture_date_label": "31.10.2025",
        },
    )

    asyncio.run(points_handlers.input_points_value(message, state, db))

    assert state.state is None
    assert message.answers[-1][0] == "Сохранено: 31.10.2025 — Вопросы: 2"
    assert len(activities.inserted_docs) == 1

    inserted = activities.inserted_docs[0]
    assert inserted["user_id"] == ObjectId(user_id)
    assert inserted["lecture_id"] == ObjectId(lecture_id)
    assert inserted["type"] == "questions"
    assert inserted["value"] == 2.0
    assert inserted["timestamp"].tzinfo == timezone.utc


def test_list_lecture_date_labels_sorts_by_date_descending() -> None:
    lectures = FakeCollection(
        "lectures",
        docs=[
            {"_id": new_object_id(), "date_label": "31.12.2024"},
            {"_id": new_object_id(), "date_label": "01.01.2025"},
            {"_id": new_object_id(), "date_label": "bad"},
        ],
    )
    db = FakeDB({"lectures": lectures})

    labels = asyncio.run(points_handlers._list_lecture_date_labels(db))

    assert labels == ["01.01.2025", "31.12.2024", "bad"]

