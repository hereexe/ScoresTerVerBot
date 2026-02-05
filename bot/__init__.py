"""ScoresTerVerBot package.

Keep this module lightweight: avoid importing heavy dependencies at import time.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version as _pkg_version


def _detect_version() -> str:
    # When the project is not installed as a package, fall back to a static value.
    try:
        return _pkg_version("ScoresTerVerBot")
    except PackageNotFoundError:
        return "0.0.0"


__version__ = _detect_version()


def version() -> str:
    """Return package version string."""
    return __version__


__all__ = ["__version__", "version"]
