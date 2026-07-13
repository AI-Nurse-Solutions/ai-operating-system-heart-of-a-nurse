from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX fallback
    fcntl = None

GENESIS_HASH = "0" * 64


class LedgerError(RuntimeError):
    pass


def _hash_record(record: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in record.items() if key != "event_hash"}
    raw = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


class ProvenanceLedger:
    """Append-only, metadata-only JSONL ledger with a SHA-256 hash chain."""

    def __init__(self, path: Path):
        self.path = path

    def append(self, event: dict[str, Any]) -> dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a+", encoding="utf-8") as handle:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                handle.seek(0)
                lines = [line for line in handle.read().splitlines() if line.strip()]
                if lines:
                    verification = self._verify_lines(lines)
                    previous_hash = verification["terminal_hash"]
                    sequence = verification["count"] + 1
                else:
                    previous_hash = GENESIS_HASH
                    sequence = 1
                record = dict(event)
                record["sequence"] = sequence
                record["previous_hash"] = previous_hash
                record["event_hash"] = _hash_record(record)
                handle.seek(0, os.SEEK_END)
                handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
                return record
            finally:
                if fcntl is not None:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def verify(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"ok": True, "count": 0, "terminal_hash": GENESIS_HASH}
        lines = [line for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
        return self._verify_lines(lines)

    def _verify_lines(self, lines: list[str]) -> dict[str, Any]:
        previous = GENESIS_HASH
        for index, line in enumerate(lines, start=1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise LedgerError(f"invalid JSON at sequence {index}") from exc
            if record.get("sequence") != index:
                raise LedgerError(f"sequence mismatch at {index}")
            if record.get("previous_hash") != previous:
                raise LedgerError(f"previous hash mismatch at {index}")
            actual = _hash_record(record)
            if record.get("event_hash") != actual:
                raise LedgerError(f"event hash mismatch at {index}")
            previous = actual
        return {"ok": True, "count": len(lines), "terminal_hash": previous}
