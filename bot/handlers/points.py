from __future__ import annotations

from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from bson import ObjectId

from bot.db import Database
from bot.keyboards import (
    ACTIVITY_TYPE_LABELS,
    CB_ACTIVITY_PREFIX,
    CB_BACK,
    CB_LECTURE_PREFIX,
    activity_types_keyboard,
    back_keyboard,
    lectures_keyboard,
    main_menu_keyboard,
)
from bot.states import AddPoints

router = Router()


@router.message(Command("add_points"))
async def add_points_command(message: Message, state: FSMContext, db: Database) -> None:
    """Start add-points FSM flow."""
    await start_add_points_flow(message, state, db)

async def start_add_points_flow(message: Message, state: FSMContext, db: Database) -> None:
    """Shared entrypoint for add-points flow (command or menu)."""
    if message.from_user is None:
        return

    user = await _users_collection(db).find_one({"tg_id": message.from_user.id})
    if user is None:
        await message.answer("Сначала зарегистрируйтесь через /start.")
        return

    date_labels = await _list_lecture_date_labels(db)
    if not date_labels:
        await message.answer("Пока нет лекций. Попросите администратора добавить дату через /add_lecture.")
        return

    await state.clear()
    await state.set_state(AddPoints.lecture_id)
    await state.update_data(user_id=str(user["_id"]))
    await message.answer("Выберите лекцию:", reply_markup=lectures_keyboard(date_labels))

@router.callback_query(StateFilter(AddPoints.lecture_id), F.data == CB_BACK)
async def back_from_lecture(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.answer()
    if call.message:
        await call.message.answer("Главное меню:", reply_markup=main_menu_keyboard())


@router.callback_query(StateFilter(AddPoints.lecture_id), F.data.startswith(CB_LECTURE_PREFIX))
async def choose_lecture(call: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Handle lecture selection callback."""
    await call.answer()
    if call.data is None or call.message is None:
        return

    date_label = call.data.removeprefix(CB_LECTURE_PREFIX)
    lecture = await _lectures_collection(db).find_one({"date_label": date_label})
    if lecture is None:
        await call.message.answer("Лекция не найдена. Обновите список и попробуйте снова.")
        return

    await state.update_data(lecture_id=str(lecture["_id"]), lecture_date_label=date_label)
    await state.set_state(AddPoints.activity_type)
    await call.message.answer("Выберите категорию:", reply_markup=activity_types_keyboard())

@router.callback_query(StateFilter(AddPoints.activity_type), F.data == CB_BACK)
async def back_from_activity_type(call: CallbackQuery, state: FSMContext, db: Database) -> None:
    await call.answer()
    if call.message is None:
        return

    date_labels = await _list_lecture_date_labels(db)
    await state.set_state(AddPoints.lecture_id)
    await call.message.answer("Выберите лекцию:", reply_markup=lectures_keyboard(date_labels))


@router.callback_query(StateFilter(AddPoints.activity_type), F.data.startswith(CB_ACTIVITY_PREFIX))
async def choose_activity_type(call: CallbackQuery, state: FSMContext) -> None:
    """Handle activity type selection callback."""
    await call.answer()
    if call.data is None or call.message is None:
        return

    activity_type = call.data.removeprefix(CB_ACTIVITY_PREFIX)
    if activity_type not in ACTIVITY_TYPE_LABELS:
        await call.message.answer("Неизвестная категория. Попробуйте еще раз.")
        return

    await state.update_data(activity_type=activity_type)
    await state.set_state(AddPoints.value)
    await call.message.answer("Введите количество баллов (например: 2 или 1.5).", reply_markup=back_keyboard())


@router.callback_query(StateFilter(AddPoints.value), F.data == CB_BACK)
async def back_from_value(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    if call.message is None:
        return

    await state.set_state(AddPoints.activity_type)
    await call.message.answer("Выберите категорию:", reply_markup=activity_types_keyboard())

@router.message(StateFilter(AddPoints.value))
async def input_points_value(message: Message, state: FSMContext, db: Database) -> None:
    """Handle numeric points input and persist the activity."""
    if message.from_user is None:
        return

    if not message.text:
        await message.answer("Отправьте число (например: 2 или 1.5).")
        return

    value = _parse_float(message.text)
    if value is None or value <= 0:
        await message.answer("Нужно положительное число (например: 2 или 1.5).")
        return

    data = await state.get_data()
    try:
        user_id = ObjectId(data["user_id"])
        lecture_id = ObjectId(data["lecture_id"])
        activity_type = str(data["activity_type"])
    except Exception:
        await state.clear()
        await message.answer("Сессия ввода устарела. Начните заново: /add_points.")
        return

    if activity_type not in ACTIVITY_TYPE_LABELS:
        await state.clear()
        await message.answer("Сессия ввода устарела. Начните заново: /add_points.")
        return

    await save_activity(
        db,
        user_id=user_id,
        lecture_id=lecture_id,
        activity_type=activity_type,
        value=float(value),
    )

    lecture_date_label = data.get("lecture_date_label") or ""
    label = ACTIVITY_TYPE_LABELS[activity_type]
    await state.clear()
    await message.answer(
        f"Сохранено: {lecture_date_label} — {label}: {_fmt_points(float(value))}",
        reply_markup=main_menu_keyboard(),
    )


def _parse_float(text: str) -> float | None:
    raw = text.strip().replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return None


def _fmt_points(value: float) -> str:
    # Avoid trailing .0 when value is an integer.
    return f"{value:g}"


def _users_collection(db: Database):
    raw = db.raw
    if hasattr(raw, "get_collection"):
        return raw.get_collection("users")
    return raw["users"]


def _lectures_collection(db: Database):
    raw = db.raw
    if hasattr(raw, "get_collection"):
        return raw.get_collection("lectures")
    return raw["lectures"]


def _activities_collection(db: Database):
    raw = db.raw
    if hasattr(raw, "get_collection"):
        return raw.get_collection("activities")
    return raw["activities"]


async def save_activity(
    db: Database,
    *,
    user_id: ObjectId,
    lecture_id: ObjectId,
    activity_type: str,
    value: float,
) -> None:
    """Persist activity document."""
    await _activities_collection(db).insert_one(
        _build_activity_doc(user_id=user_id, lecture_id=lecture_id, activity_type=activity_type, value=float(value))
    )


async def _list_lecture_date_labels(db: Database) -> list[str]:
    docs = await _lectures_collection(db).find({}, {"date_label": 1}).to_list(length=1000)
    labels = [d.get("date_label") for d in docs if d.get("date_label")]
    return sorted(labels, key=_safe_parse_date, reverse=True)


def _safe_parse_date(date_label: str) -> datetime:
    try:
        return datetime.strptime(date_label, "%d.%m.%Y")
    except ValueError:
        # Put unknown formats to the end while keeping a deterministic order.
        return datetime.min


def _build_activity_doc(*, user_id: ObjectId, lecture_id: ObjectId, activity_type: str, value: float) -> dict:
    return {
        "user_id": user_id,
        "lecture_id": lecture_id,
        "type": activity_type,
        "value": float(value),
        "timestamp": datetime.now(tz=timezone.utc),
    }
