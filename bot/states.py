"""FSM state definitions.

This module intentionally contains only state definitions (no business logic).
"""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


__all__ = ["Onboarding", "AddLecture", "AddPoints", "Stats"]


class Onboarding(StatesGroup):
    full_name = State()
    wait_fiitobot_response = State()


class AddLecture(StatesGroup):
    date_label = State()


class AddPoints(StatesGroup):
    lecture_id = State()
    activity_type = State()
    value = State()


class Stats(StatesGroup):
    lecture_id = State()
