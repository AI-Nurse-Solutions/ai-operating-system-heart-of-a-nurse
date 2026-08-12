"""
Runtime adapter — architecture §7.1.

Hermes is the runtime today; Florence-X becomes one later. Mission Control talks
to whichever through this interface and never learns which it is talking to.

Hard rule: model credentials live only in the runtime. This module reads state.
It holds no key, no token, and no secret, and it never writes to the runtime.
"""

from __future__ import annotations

import contextlib
import json
import os
import socket
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from urllib.parse import urlparse


class RuntimeAdapter(ABC):
    name = "abstract"

    @abstractmethod
    def gateway_state(self) -> dict:
        """{present, up, liveness, sessions, tokens_in, tokens_out, est_cost_usd,
        hermes_db_bytes, posture}

        `present` and `up` are two different questions and the dashboard asks both:
        a Hermes directory on disk says it is installed, not that it is running.
        Only a liveness probe may set `up`.
        """

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

    # -- liveness ---------------------------------------------------------
    # Installed is not running. A `~/.hermes` directory survives a crash, a
    # reboot, and an uninstall that left its config behind, so presence alone
    # may never light the 'runtime up' lamp — the health strip exists to tell a
    # nurse whether her agents are actually answering, and a lamp that is green
    # whenever the folder exists answers a question nobody asked.
    def _liveness(self) -> tuple[bool, str]:
        """(up, how it was determined). Only positive evidence returns True."""
        endpoint = self._gateway_endpoint()
        if endpoint:
            host, port = endpoint
            try:
                with socket.create_connection((host, port), timeout=0.25):
                    return True, f"gateway accepting connections on {host}:{port}"
            except OSError:
                return False, f"gateway not accepting connections on {host}:{port}"

        for name in ("hermes.pid", "gateway.pid", "run/hermes.pid", "run/gateway.pid"):
            pid_file = self.home / name
            if not pid_file.is_file():
                continue
            try:
                pid = int(pid_file.read_text(encoding="utf-8").strip())
            except (OSError, ValueError):
                return False, f"{name} is unreadable"
            if pid <= 0:
                return False, f"{name} holds no usable pid"
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return False, f"{name} points at pid {pid}, which is not running"
            except PermissionError:
                # Running as another user — it exists, which is what was asked.
                return True, f"pid {pid} from {name} is running"
            except OSError:
                return False, f"{name} points at pid {pid}, which could not be checked"
            return True, f"pid {pid} from {name} is running"

        return False, "no pid file and no gateway address configured"

    def _gateway_endpoint(self) -> tuple[str, int] | None:
        """Host and port to probe, if the Hermes config names one."""
        config = self.home / "config.json"
        if not config.is_file():
            return None
        try:
            data = json.loads(config.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        if not isinstance(data, dict):
            return None

        for key in ("gateway_url", "url", "endpoint"):
            raw = data.get(key)
            if isinstance(raw, str) and raw.strip():
                parsed = urlparse(raw if "//" in raw else f"//{raw}")
                if parsed.hostname and parsed.port:
                    return parsed.hostname, parsed.port
        for key in ("gateway_port", "port"):
            if key not in data:
                continue
            with contextlib.suppress(TypeError, ValueError):
                port = int(data[key])
                if 0 < port < 65536:
                    return str(data.get("host") or "127.0.0.1"), port
        return None

    # -- state ------------------------------------------------------------
    def gateway_state(self) -> dict:
        db_path = self._db_path()
        state = {
            "present": False,
            "up": False,
            "liveness": "runtime absent",
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

        up, how = self._liveness()
        state["present"] = True
        state["up"] = up
        state["liveness"] = how
        state["posture"] = self._posture()
        state["detail"] = (
            f"Hermes home at {self.home} — {'running' if up else 'installed, not running'} "
            f"({how})"
        )
        if db_path:
            state["hermes_db_bytes"] = db_path.stat().st_size
            try:
                # closing(), so a non-sqlite3 exception out of execute() cannot
                # skip the close and leak the handle.
                with contextlib.closing(sqlite3.connect(
                        f"file:{db_path}?mode=ro", uri=True, timeout=3)) as conn:
                    try:
                        row = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()
                        state["sessions"] = row[0] if row else 0
                    except sqlite3.Error:
                        pass
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
            "present": False, "up": False, "liveness": "not implemented",
            "sessions": 0, "tokens_in": 0, "tokens_out": 0,
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
