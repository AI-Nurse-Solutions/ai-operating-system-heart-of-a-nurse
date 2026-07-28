"""Observability reference adapter (pattern: langfuse/langfuse).

Gives Mission Control real instrumentation: every gateway request opens a
trace, every stage (privacy, policy, validation, execution) records a span,
and every trace ends with an outcome. Records are JSONL with a SHA-256
hash chain (same discipline as the NAIO provenance ledger) so the audit
trail is tamper-evident.

Redaction happens BEFORE tracing: spans store metadata — entity types,
reason codes, decisions, counts — never raw payload content. Traces are
separated per tenant so institutional telemetry never mixes with personal
telemetry.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import locking
from .contract import GatewayRequest, ObservabilityInterface

GENESIS_HASH = "0" * 64
_TENANT_SAFE = re.compile(r"[^A-Za-z0-9._-]")

FORBIDDEN_SPAN_KEYS = {"content", "text", "payload", "raw", "value"}


def _find_forbidden_keys(value: Any) -> set[str]:
    """Case-insensitive, recursive sweep for raw-content keys in a payload."""
    leaked: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).casefold() in FORBIDDEN_SPAN_KEYS:
                leaked.add(str(key))
            leaked |= _find_forbidden_keys(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            leaked |= _find_forbidden_keys(item)
    return leaked


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_record(record: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in record.items() if key != "record_hash"}
    raw = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


class GatewayTracer(ObservabilityInterface):
    """Tenant-separated, redacted, hash-chained trace store."""

    def __init__(self, root: Path):
        self.root = root
        self._trace_tenants: dict[str, str] = {}

    def start_trace(self, request: GatewayRequest) -> str:
        trace_id = secrets.token_hex(12)
        self._trace_tenants[trace_id] = request.actor.tenant
        self._append(
            request.actor.tenant,
            {
                "kind": "trace_start",
                "trace_id": trace_id,
                "request_id": request.request_id,
                "actor_role": request.actor.role,
                "intent": request.intent,
                "risk_tier": request.risk_tier.value,
                "data_class": request.data_class.value,
                "action_mode": request.action_mode.value,
                "data_zone": request.data_zone.value,
                "content_length": len(request.content),
            },
        )
        return trace_id

    def record_span(self, trace_id: str, name: str, payload: dict[str, Any]) -> None:
        tenant = self._trace_tenants.get(trace_id)
        if tenant is None:
            raise ValueError("unknown trace id")
        leaked = _find_forbidden_keys(payload)
        if leaked:
            raise ValueError(f"span payload may not carry raw content keys: {sorted(leaked)}")
        self._append(tenant, {"kind": "span", "trace_id": trace_id, "name": name, **payload})

    def end_trace(self, trace_id: str, outcome: str) -> None:
        tenant = self._trace_tenants.pop(trace_id, None)
        if tenant is None:
            raise ValueError("unknown trace id")
        self._append(tenant, {"kind": "trace_end", "trace_id": trace_id, "outcome": outcome})

    def read(self, tenant: str) -> list[dict[str, Any]]:
        path = self._path(tenant)
        if not path.exists():
            return []
        # Readers take the same lock as writers so a concurrent append can
        # never expose a partially written record or a torn hash chain.
        with path.open("a+", encoding="utf-8") as handle:
            locking.acquire(handle)
            try:
                handle.seek(0)
                lines = [
                    line for line in handle.read().splitlines() if line.strip()
                ]
            finally:
                locking.release(handle)
        return [json.loads(line) for line in lines]

    def verify(self, tenant: str) -> dict[str, Any]:
        previous = GENESIS_HASH
        count = 0
        for record in self.read(tenant):
            if record.get("previous_hash") != previous:
                raise ValueError(f"hash chain broken at sequence {count + 1}")
            if record.get("record_hash") != _hash_record(record):
                raise ValueError(f"record hash mismatch at sequence {count + 1}")
            previous = record["record_hash"]
            count += 1
        return {"ok": True, "count": count, "terminal_hash": previous}

    def _path(self, tenant: str) -> Path:
        # Injective mapping: the readable prefix is convenience, the digest
        # guarantees distinct tenants never share an audit stream even when
        # sanitization collapses their names.
        safe = _TENANT_SAFE.sub("_", tenant)
        digest = hashlib.sha256(tenant.encode("utf-8")).hexdigest()[:12]
        return self.root / f"traces-{safe}-{digest}.jsonl"

    def _append(self, tenant: str, event: dict[str, Any]) -> None:
        path = self._path(tenant)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a+", encoding="utf-8") as handle:
            locking.acquire(handle)
            try:
                handle.seek(0)
                lines = [line for line in handle.read().splitlines() if line.strip()]
                previous = (
                    json.loads(lines[-1])["record_hash"] if lines else GENESIS_HASH
                )
                record = dict(event)
                record["timestamp"] = _utcnow()
                record["tenant"] = tenant
                record["previous_hash"] = previous
                record["record_hash"] = _hash_record(record)
                handle.seek(0, os.SEEK_END)
                handle.write(
                    json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
                )
                handle.flush()
                os.fsync(handle.fileno())
            finally:
                locking.release(handle)
