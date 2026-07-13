from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

try:
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None


class BudgetExceeded(RuntimeError):
    pass


class BudgetManager:
    """Persistent metadata-only call budgets keyed by hashed run and capability."""

    def __init__(self, path: Path):
        self.path = path
        self.lock_path = path.with_suffix(path.suffix + ".lock")

    def consume(self, run_id: str, capability_id: str, max_calls: int) -> int:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        run_hash = hashlib.sha256((run_id or "anonymous-run").encode()).hexdigest()
        key = f"{run_hash}:{capability_id}"
        with self.lock_path.open("a+", encoding="utf-8") as lock:
            if fcntl is not None:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                state = self._load()
                current = int(state.get(key, 0))
                if current >= max_calls:
                    raise BudgetExceeded(f"call budget exhausted for {capability_id}")
                state[key] = current + 1
                self._save(state)
                return state[key]
            finally:
                if fcntl is not None:
                    fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def _load(self) -> dict[str, int]:
        if not self.path.exists():
            return {}
        return {key: int(value) for key, value in json.loads(self.path.read_text(encoding="utf-8")).items()}

    def _save(self, state: dict[str, int]) -> None:
        fd, temporary = tempfile.mkstemp(prefix=self.path.name + ".", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(state, handle, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
