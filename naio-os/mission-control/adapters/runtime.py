"""
Runtime adapter — architecture §7.1.

Hermes is the runtime today; Florence-X becomes one later. Mission Control talks
to whichever through this interface and never learns which it is talking to.

Hard rule: model credentials live only in the runtime. This module reads state.
It holds no key, no token, and no secret, and it never writes to the runtime.
"""

from __future__ import annotations

import json
import os
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path


class RuntimeAdapter(ABC):
    name = "abstract"

    @abstractmethod
    def gateway_state(self) -> dict:
        """{up, sessions, tokens_in, tokens_out, est_cost_usd, hermes_db_bytes, posture}"""

    @abstractmethod
    def cron_jobs(self) -> list[dict]:
        """Read-only mirror of the runtime's schedule. Mission Control never schedules."""


class HermesAdapter(RuntimeAdapter):
    """
    Reads a local Hermes install if one is present. Degrades to 'runtime absent'
    rather than raising, because a nurse without Hermes installed should still get
    a working dashboard that tells her the truth about what is missing.
    """

    name = "hermes"

    def __init__(self, home: str | os.PathLike | None = None):
        self.home = Path(home or os.environ.get("HERMES_HOME", "~/.hermes")).expanduser()

    # -- discovery --------------------------------------------------------
    @property
    def present(self) -> bool:
        return self.home.is_dir()

    def _db_path(self) -> Path | None:
        if not self.present:
            return None
        for name in ("hermes.db", "agent.db", "sessions.db"):
            candidate = self.home / name
            if candidate.is_file():
                return candidate
        return None

    # -- state ------------------------------------------------------------
    def gateway_state(self) -> dict:
        db_path = self._db_path()
        state = {
            "up": False,
            "sessions": 0,
            "tokens_in": 0,
            "tokens_out": 0,
            "est_cost_usd": 0.0,
            "hermes_db_bytes": 0,
            "posture": "absent",
            "detail": f"No Hermes install found at {self.home}",
        }
        if not self.present:
            return state

        state["up"] = True
        state["posture"] = self._posture()
        state["detail"] = f"Hermes home at {self.home}"
        if db_path:
            state["hermes_db_bytes"] = db_path.stat().st_size
            try:
                conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=3)
                try:
                    row = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()
                    state["sessions"] = row[0] if row else 0
                except sqlite3.Error:
                    pass
                conn.close()
            except sqlite3.Error:
                pass
        return state

    def _posture(self) -> str:
        """Which provider posture is configured — surfaced read-only. Never the key. (§7.2)"""
        config = self.home / "config.json"
        if not config.is_file():
            return "unknown"
        try:
            data = json.loads(config.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return "unknown"
        provider = str(data.get("provider", "")).lower()
        if "openrouter" in provider:
            return "openrouter"
        if "codex" in provider or data.get("auth") == "chatgpt":
            return "subscription"
        if "openai" in provider:
            return "openai"
        return provider or "unknown"

    def cron_jobs(self) -> list[dict]:
        if not self.present:
            return []
        path = self.home / "cron" / "jobs.json"
        if not path.is_file():
            return []
        try:
            jobs = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
        out = []
        for job in jobs if isinstance(jobs, list) else []:
            out.append({
                "id": str(job.get("id", "")),
                "agent_id": job.get("agent_id", "florence"),
                "label": job.get("label", "(unlabelled)"),
                "schedule": job.get("schedule", ""),
                "next_run_ts": job.get("next_run_ts"),
                "last_run_ts": job.get("last_run_ts"),
                "last_status": job.get("last_status"),
                "ritual": bool(job.get("naio_ritual")),
                "edena_tier": job.get("edena_tier"),
            })
        return out


class FlorenceXAdapter(RuntimeAdapter):
    """Placeholder for when Florence-X becomes a native runtime. Deliberately inert."""

    name = "florence-x"

    def gateway_state(self) -> dict:
        return {
            "up": False, "sessions": 0, "tokens_in": 0, "tokens_out": 0,
            "est_cost_usd": 0.0, "hermes_db_bytes": 0,
            "posture": "not-implemented",
            "detail": "Florence-X is not a runtime yet. Nothing here pretends otherwise.",
        }

    def cron_jobs(self) -> list[dict]:
        return []


def get_adapter() -> RuntimeAdapter:
    which = os.environ.get("NAIO_RUNTIME", "hermes").lower()
    if which in ("florence-x", "florencex", "fx"):
        return FlorenceXAdapter()
    return HermesAdapter()
