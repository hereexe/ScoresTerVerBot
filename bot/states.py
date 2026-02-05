"""FSM state definitions (stubs)."""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class Onboarding(StatesGroup):
    full_name = State()


class AddLecture(StatesGroup):
    date_label = State()


class AddPoints(StatesGroup):
    lecture_id = State()
    activity_type = State()
    value = State()


class Stats(StatesGroup):
    lecture_id = State()
