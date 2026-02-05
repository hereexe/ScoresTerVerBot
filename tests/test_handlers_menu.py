from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

from bot.handlers import menu as menu_handlers
from bot.keyboards import BTN_ADD_POINTS, BTN_STATS

from tests.fakes import FakeCollection, FakeDB, FakeFSMContext, FakeMessage, FakeUser


def test_menu_command_clears_state_and_shows_menu() -> None:
    message = FakeMessage(from_user=FakeUser(1))
    state = FakeFSMContext(state="some_state", data={"x": "y"})

    asyncio.run(menu_handlers.menu_command(message, state))

    assert state.state is None
    assert state.data == {}
    assert message.answers[-1][0] == "Главное меню:"


def test_add_points_entry_delegates_to_points_flow(monkeypatch) -> None:
    import bot.handlers.points as points_handlers

    mocked = AsyncMock()
    monkeypatch.setattr(points_handlers, "start_add_points_flow", mocked)

    db = FakeDB({"users": FakeCollection("users"), "lectures": FakeCollection("lectures")})
    message = FakeMessage(from_user=FakeUser(1), text=BTN_ADD_POINTS)
    state = FakeFSMContext()

    asyncio.run(menu_handlers.add_points_entry(message, state, db))

    mocked.assert_awaited_once()


def test_stats_entry_delegates_to_stats_flow(monkeypatch) -> None:
    import bot.handlers.stats as stats_handlers

    mocked = AsyncMock()
    monkeypatch.setattr(stats_handlers, "start_stats_flow", mocked)

    db = FakeDB({"lectures": FakeCollection("lectures"), "activities": FakeCollection("activities")})
    message = FakeMessage(from_user=FakeUser(1), text=BTN_STATS)
    state = FakeFSMContext()

    asyncio.run(menu_handlers.stats_entry(message, state, db))

    mocked.assert_awaited_once()

