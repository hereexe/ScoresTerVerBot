from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from bson import ObjectId

from bot.db import Database
from bot.keyboards import (
    ACTIVITY_TYPE_LABELS,
    CB_BACK,
    CB_LECTURE_PREFIX,
    lectures_keyboard,
    main_menu_keyboard,
)
from bot.states import Stats

router = Router()


@router.message(Command("stats"))
async def stats_command(message: Message, state: FSMContext, db: Database) -> None:
    """Start stats flow."""
    await start_stats_flow(message, state, db)


async def start_stats_flow(message: Message, state: FSMContext, db: Database) -> None:
    """Shared entrypoint for stats flow (command or menu)."""
    date_labels = await _list_lecture_date_labels(db)
    if not date_labels:
        await message.answer("Пока нет лекций. Попросите администратора добавить дату через /add_lecture.")
        return

    await state.clear()
    await state.set_state(Stats.lecture_id)
    await message.answer("Выберите лекцию:", reply_markup=lectures_keyboard(date_labels))


@router.callback_query(StateFilter(Stats.lecture_id), F.data == CB_BACK)
async def back_from_stats_lecture(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.answer()
    if call.message:
        await call.message.answer("Главное меню:", reply_markup=main_menu_keyboard())


@router.callback_query(StateFilter(Stats.lecture_id), F.data.startswith(CB_LECTURE_PREFIX))
async def choose_stats_lecture(call: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Handle lecture selection for stats and render group summary."""
    await call.answer()
    if call.data is None or call.message is None:
        return

    date_label = call.data.removeprefix(CB_LECTURE_PREFIX)
    lecture = await _lectures_collection(db).find_one({"date_label": date_label})
    if lecture is None:
        await call.message.answer("Лекция не найдена. Обновите список и попробуйте снова.")
        return

    await state.clear()
    await render_lecture_stats(call.message, db, lecture_id=lecture["_id"], date_label=date_label)


async def render_lecture_stats(message: Message, db: Database, lecture_id: ObjectId, date_label: str) -> None:
    """Render group stats for selected lecture."""
    activities = _activities_collection(db)

    pipeline = [
        {"$match": {"lecture_id": lecture_id}},
        {"$group": {"_id": {"user_id": "$user_id", "type": "$type"}, "sum": {"$sum": "$value"}}},
        {
            "$group": {
                "_id": "$_id.user_id",
                "total": {"$sum": "$sum"},
                "by_type": {"$push": {"k": "$_id.type", "v": "$sum"}},
            }
        },
        {"$project": {"total": 1, "by_type": {"$arrayToObject": "$by_type"}}},
        {"$lookup": {"from": "users", "localField": "_id", "foreignField": "_id", "as": "user"}},
        {"$unwind": {"path": "$user", "preserveNullAndEmptyArrays": True}},
        {
            "$project": {
                "full_name": {"$ifNull": ["$user.full_name", "<unknown>"]},
                "total": 1,
                "by_type": 1,
            }
        },
        {"$sort": {"total": -1, "full_name": 1}},
    ]

    rows = await activities.aggregate(pipeline).to_list(length=5000)
    if not rows:
        await message.answer(f"Статистика за лекцию {date_label}:\nЗаписей пока нет.", reply_markup=main_menu_keyboard())
        return

    group_totals: dict[str, float] = defaultdict(float)
    group_total_all = 0.0
    for r in rows:
        by_type = r.get("by_type") or {}
        for t, s in by_type.items():
            try:
                group_totals[str(t)] += float(s)
            except (TypeError, ValueError):
                continue
        try:
            group_total_all += float(r.get("total") or 0.0)
        except (TypeError, ValueError):
            pass

    lines: list[str] = [f"Статистика за лекцию {date_label}:"]
    lines.append("Итого по группе:")
    for t in ("questions", "typo", "professor"):
        label = ACTIVITY_TYPE_LABELS.get(t, t)
        lines.append(f"- {label}: {_fmt_points(group_totals.get(t, 0.0))}")
    lines.append(f"- Всего: {_fmt_points(group_total_all)}")
    lines.append("")
    lines.append("Топ студентов:")
    for i, r in enumerate(rows[:20], start=1):
        lines.append(f"{i}. {r.get('full_name','<unknown>')} — {_fmt_points(float(r.get('total') or 0.0))}")
    if len(rows) > 20:
        lines.append(f"... и еще {len(rows) - 20} чел.")

    await message.answer("\n".join(lines), reply_markup=main_menu_keyboard())


def _fmt_points(value: float) -> str:
    return f"{value:g}"


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


async def _list_lecture_date_labels(db: Database) -> list[str]:
    docs = await _lectures_collection(db).find({}, {"date_label": 1}).to_list(length=1000)
    labels = [d.get("date_label") for d in docs if d.get("date_label")]
    return sorted(labels, key=_safe_parse_date, reverse=True)


def _safe_parse_date(date_label: str) -> datetime:
    try:
        return datetime.strptime(date_label, "%d.%m.%Y")
    except ValueError:
        return datetime.min
