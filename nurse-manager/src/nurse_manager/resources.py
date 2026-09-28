"""Where the manager core finds its own files, in the repo or in a packaged app.

In the repository the files sit beside the source tree. In a packaged app
(ADR 0003) they are unpacked into the bundle directory, which PyInstaller
exposes as ``sys._MEIPASS``. Every file lookup goes through here, so the
two layouts can never drift apart.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_DIR_NAME = "Nurse AI OS"


def frozen() -> bool:
    return bool(getattr(sys, "frozen", False)) and hasattr(sys, "_MEIPASS")


def manager_root() -> Path:
    """The nurse-manager directory: config, renderer, samples, migrations."""
    if frozen():
        return Path(sys._MEIPASS) / "nurse-manager"  # type: ignore[attr-defined]
    return Path(__file__).resolve().parents[2]


def naio_config(name: str) -> Path:
    """A config file from naio-integrations (privacy recognizers, EDENA policy)."""
    if frozen():
        return Path(sys._MEIPASS) / "naio-integrations" / "config" / name  # type: ignore[attr-defined]
    return Path(__file__).resolve().parents[3] / "naio-integrations" / "config" / name


def user_data_dir() -> Path:
    """Where the manager's records live: outside the replaceable app bundle."""
    override = os.environ.get("NURSE_AI_OS_HOME")
    if override:
        return Path(override)
    home = Path.home()
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA") or home / "AppData" / "Local")
        return base / APP_DIR_NAME
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / APP_DIR_NAME
    base = Path(os.environ.get("XDG_DATA_HOME") or home / ".local" / "share")
    return base / "nurse-ai-os"
