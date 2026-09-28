"""Make the package importable when tests run from any working directory."""

import sys
from datetime import datetime, timedelta
from itertools import count
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def fixed_clock(start: str = "2026-09-30T09:00:00+00:00"):
    """A deterministic clock that advances one second per reading."""
    base = datetime.fromisoformat(start)
    ticks = count()
    return lambda: (base + timedelta(seconds=next(ticks))).isoformat()
