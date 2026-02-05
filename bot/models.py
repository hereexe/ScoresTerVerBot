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
    """Validate lecture date label format (e.g. DD.MM.YYYY). TODO: implement."""
    raise NotImplementedError


def validate_points(value: float) -> None:
    """Validate points value constraints. TODO: implement."""
    raise NotImplementedError
