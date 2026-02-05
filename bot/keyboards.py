"""Keyboard builders."""

from __future__ import annotations

from typing import Sequence

from aiogram.types import InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


BTN_ADD_POINTS = "➕ Добавить баллы"
BTN_STATS = "Посмотреть статистику"
BTN_BACK = "⬅️ Назад"

CB_LECTURE_PREFIX = "lecture:"
CB_ACTIVITY_PREFIX = "activity:"
CB_BACK = "back"

ACTIVITY_TYPE_LABELS: dict[str, str] = {
    "questions": "Вопросы",
    "typo": "Опечатка",
    "professor": "Баллы от Хлопина",
}


def main_menu_keyboard():
    """Build the main menu reply keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_ADD_POINTS)],
            [KeyboardButton(text=BTN_STATS)],
        ],
        resize_keyboard=True,
        selective=True,
    )


def lectures_keyboard(date_labels: Sequence[str]):
    """Build lecture selection inline keyboard from date labels."""
    builder = InlineKeyboardBuilder()
    for date_label in date_labels:
        builder.button(
            text=date_label,
            callback_data=f"{CB_LECTURE_PREFIX}{date_label}",
        )
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text=BTN_BACK, callback_data=CB_BACK))
    return builder.as_markup()


def activity_types_keyboard():
    """Build activity type selection inline keyboard."""
    builder = InlineKeyboardBuilder()
    for activity_type, label in ACTIVITY_TYPE_LABELS.items():
        builder.button(text=label, callback_data=f"{CB_ACTIVITY_PREFIX}{activity_type}")
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text=BTN_BACK, callback_data=CB_BACK))
    return builder.as_markup()


def back_keyboard():
    """Build a simple 'Back' inline keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text=BTN_BACK, callback_data=CB_BACK)
    builder.adjust(1)
    return builder.as_markup()
