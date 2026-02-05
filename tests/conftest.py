from __future__ import annotations

import re
import secrets
import sys
import types
from dataclasses import dataclass
from typing import Any


def _install_aiogram_stub() -> None:
    aiogram = types.ModuleType("aiogram")

    class Router:
        def __init__(self) -> None:
            self.included_routers: list[Any] = []

        def include_router(self, router: Any) -> None:
            self.included_routers.append(router)

        def message(self, *args: Any, **kwargs: Any):
            def decorator(func):
                return func

            return decorator

        def callback_query(self, *args: Any, **kwargs: Any):
            def decorator(func):
                return func

            return decorator

    class _FilterField:
        def __init__(self, name: str) -> None:
            self.name = name

        def __eq__(self, other: Any) -> Any:  # noqa: PLR0911 - intentionally minimal stub
            return ("eq", self.name, other)

        def startswith(self, prefix: str) -> Any:
            return ("startswith", self.name, prefix)

    class _F:
        def __getattr__(self, name: str) -> _FilterField:
            return _FilterField(name)

    aiogram.Router = Router
    aiogram.F = _F()

    filters = types.ModuleType("aiogram.filters")

    @dataclass(slots=True)
    class CommandStart:
        pass

    @dataclass(slots=True)
    class Command:
        command: str

    @dataclass(slots=True)
    class StateFilter:
        state: Any

    filters.CommandStart = CommandStart
    filters.Command = Command
    filters.StateFilter = StateFilter

    fsm = types.ModuleType("aiogram.fsm")
    fsm_context = types.ModuleType("aiogram.fsm.context")
    fsm_state = types.ModuleType("aiogram.fsm.state")

    class FSMContext:  # pragma: no cover - for typing/imports only
        pass

    class State:  # pragma: no cover - for state declarations only
        pass

    class StatesGroup:  # pragma: no cover - for state declarations only
        pass

    fsm_context.FSMContext = FSMContext
    fsm_state.State = State
    fsm_state.StatesGroup = StatesGroup

    types_mod = types.ModuleType("aiogram.types")

    @dataclass(slots=True)
    class KeyboardButton:
        text: str

    @dataclass(slots=True)
    class ReplyKeyboardMarkup:
        keyboard: list[list[KeyboardButton]]
        resize_keyboard: bool = True
        selective: bool = True

    @dataclass(slots=True)
    class InlineKeyboardButton:
        text: str
        callback_data: str

    @dataclass(slots=True)
    class InlineKeyboardMarkup:
        inline_keyboard: list[list[InlineKeyboardButton]]

    class Message:  # pragma: no cover - for typing/imports only
        pass

    class CallbackQuery:  # pragma: no cover - for typing/imports only
        pass

    types_mod.KeyboardButton = KeyboardButton
    types_mod.ReplyKeyboardMarkup = ReplyKeyboardMarkup
    types_mod.InlineKeyboardButton = InlineKeyboardButton
    types_mod.InlineKeyboardMarkup = InlineKeyboardMarkup
    types_mod.Message = Message
    types_mod.CallbackQuery = CallbackQuery

    utils = types.ModuleType("aiogram.utils")
    utils_keyboard = types.ModuleType("aiogram.utils.keyboard")

    class InlineKeyboardBuilder:
        def __init__(self) -> None:
            self._buttons: list[InlineKeyboardButton] = []
            self._extra_rows: list[list[InlineKeyboardButton]] = []
            self._columns: int = 1

        def button(self, *, text: str, callback_data: str) -> None:
            self._buttons.append(InlineKeyboardButton(text=text, callback_data=callback_data))

        def adjust(self, columns: int) -> None:
            self._columns = max(int(columns), 1)

        def row(self, *buttons: InlineKeyboardButton) -> None:
            self._extra_rows.append(list(buttons))

        def as_markup(self) -> InlineKeyboardMarkup:
            rows: list[list[InlineKeyboardButton]] = []
            for i in range(0, len(self._buttons), self._columns):
                rows.append(self._buttons[i : i + self._columns])
            rows.extend(self._extra_rows)
            return InlineKeyboardMarkup(inline_keyboard=rows)

    utils_keyboard.InlineKeyboardBuilder = InlineKeyboardBuilder

    sys.modules["aiogram"] = aiogram
    sys.modules["aiogram.filters"] = filters
    sys.modules["aiogram.fsm"] = fsm
    sys.modules["aiogram.fsm.context"] = fsm_context
    sys.modules["aiogram.fsm.state"] = fsm_state
    sys.modules["aiogram.types"] = types_mod
    sys.modules["aiogram.utils"] = utils
    sys.modules["aiogram.utils.keyboard"] = utils_keyboard

    aiogram.filters = filters
    aiogram.fsm = fsm
    aiogram.types = types_mod
    aiogram.utils = utils
    utils.keyboard = utils_keyboard
    fsm.context = fsm_context
    fsm.state = fsm_state


def _install_motor_stub() -> None:
    motor = types.ModuleType("motor")
    motor_asyncio = types.ModuleType("motor.motor_asyncio")

    class AsyncIOMotorClient:  # pragma: no cover - import shim only
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError("motor is not installed (AsyncIOMotorClient unavailable)")

    class AsyncIOMotorCollection:  # pragma: no cover - import shim only
        pass

    class AsyncIOMotorDatabase:  # pragma: no cover - import shim only
        pass

    motor_asyncio.AsyncIOMotorClient = AsyncIOMotorClient
    motor_asyncio.AsyncIOMotorCollection = AsyncIOMotorCollection
    motor_asyncio.AsyncIOMotorDatabase = AsyncIOMotorDatabase

    sys.modules["motor"] = motor
    sys.modules["motor.motor_asyncio"] = motor_asyncio


def _install_bson_stub() -> None:
    bson = types.ModuleType("bson")

    class ObjectId(str):
        _re = re.compile(r"^[0-9a-fA-F]{24}$")

        def __new__(cls, value: Any = None):
            if value is None:
                value = secrets.token_hex(12)
            if isinstance(value, ObjectId):
                return value
            if not isinstance(value, str):
                value = str(value)
            if not cls._re.match(value):
                raise ValueError("Invalid ObjectId")
            return str.__new__(cls, value.lower())

    bson.ObjectId = ObjectId
    sys.modules["bson"] = bson


try:
    import aiogram  # type: ignore[unused-ignore]  # noqa: F401
except ModuleNotFoundError:
    _install_aiogram_stub()

try:
    import motor  # type: ignore[unused-ignore]  # noqa: F401
except ModuleNotFoundError:
    _install_motor_stub()

try:
    import bson  # type: ignore[unused-ignore]  # noqa: F401
except ModuleNotFoundError:
    _install_bson_stub()

