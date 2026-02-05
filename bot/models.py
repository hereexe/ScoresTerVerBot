"""Domain models (stubs).

These represent documents stored in MongoDB.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional


ActivityType = Literal["questions", "typo", "professor"]


@dataclass(frozen=True, slots=True)
class UserDoc:
    tg_id: int
    full_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    id: Optional[str] = None


@dataclass(frozen=True, slots=True)
class LectureDoc:
    date_label: str
    id: Optional[str] = None


@dataclass(frozen=True, slots=True)
class ActivityDoc:
    user_id: str
    lecture_id: str
    type: ActivityType
    value: float
    timestamp: datetime
    id: Optional[str] = None


def validate_date_label(date_label: str) -> None:
    """Validate lecture date label format (e.g. DD.MM.YYYY).

    Raises:
        ValueError: when date_label is invalid.
    """
    raw = date_label.strip()
    if not raw:
        raise ValueError("date_label is empty")

    try:
        dt = datetime.strptime(raw, "%d.%m.%Y")
    except ValueError as e:
        raise ValueError("date_label must be in format DD.MM.YYYY") from e

    # Round-trip check (normalization safety).
    if dt.strftime("%d.%m.%Y") != raw:
        raise ValueError("date_label must be in normalized format DD.MM.YYYY")


def validate_points(value: float) -> None:
    """Validate points value constraints.

    Policy (can be adjusted later):
    - Must be finite
    - Must be > 0
    - Must be <= 10

    Raises:
        ValueError: when value is invalid.
    """
    if value != value:  # NaN
        raise ValueError("points must be a finite number")
    if value in (float("inf"), float("-inf")):
        raise ValueError("points must be a finite number")
    if value <= 0:
        raise ValueError("points must be > 0")
    if value > 10:
        raise ValueError("points must be <= 10")
