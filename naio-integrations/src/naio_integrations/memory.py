"""Memory reference adapter (pattern: mem0ai/mem0, behind a governed contract).

Persistent memory is only accepted through the Nurse AI OS memory
contract: remember / ask-before-remembering / do-not-remember, forget,
correct, show provenance, set expiration, restrict by role, project, and
tenant — plus quarantine for questionable memories.

Two protections the upstream engines do not impose by themselves:

* the privacy screen runs before storage, so clinical facts, patient
  identifiers, and credential material never become long-term memory
  by default (they are quarantined instead of stored); and
* recall is mediated by tenant and role, so personal memory and
  institutional memory cannot cross tenant boundaries.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from .contract import MemoryInterface, MemoryRecord
from .privacy import PrivacyScreen

VALID_CONSENT = {"remember", "ask_before_remembering", "do_not_remember"}


class MemoryGovernanceError(ValueError):
    pass


class GovernedMemory(MemoryInterface):
    """In-process governed memory store; a Mem0 backend slots in behind it."""

    def __init__(self, privacy: PrivacyScreen | None = None):
        self.privacy = privacy or PrivacyScreen()
        self._store: dict[str, dict[str, MemoryRecord]] = {}

    def remember(self, record: MemoryRecord, consent: str) -> MemoryRecord:
        if consent not in VALID_CONSENT:
            raise MemoryGovernanceError(f"unknown consent verb: {consent}")
        if consent == "do_not_remember":
            raise MemoryGovernanceError("actor declined memory; nothing stored")
        if consent == "ask_before_remembering":
            raise MemoryGovernanceError(
                "consent is pending; ask the human before storing this memory"
            )
        if not record.provenance:
            raise MemoryGovernanceError("memory without provenance is not storable")
        stored = record
        if self.privacy.analyze(record.content):
            stored = MemoryRecord(
                memory_id=record.memory_id,
                tenant=record.tenant,
                role_scope=record.role_scope,
                content=self.privacy.transform(record.content).transformed_text,
                provenance=record.provenance,
                created_at=record.created_at,
                expires_at=record.expires_at,
                project_scope=record.project_scope,
                quarantined=True,
            )
        self._store.setdefault(stored.tenant, {})[stored.memory_id] = stored
        return stored

    def recall(self, tenant: str, role: str, query: str) -> tuple[MemoryRecord, ...]:
        today = datetime.now(timezone.utc).date()
        results = []
        for record in self._store.get(tenant, {}).values():
            if record.quarantined:
                continue
            if record.role_scope not in ("any", role):
                continue
            if record.expires_at and date.fromisoformat(record.expires_at) < today:
                continue
            if query.lower() in record.content.lower():
                results.append(record)
        return tuple(results)

    def forget(self, tenant: str, memory_id: str) -> bool:
        return self._store.get(tenant, {}).pop(memory_id, None) is not None

    def correct(self, tenant: str, memory_id: str, content: str, provenance: str) -> MemoryRecord:
        existing = self._store.get(tenant, {}).get(memory_id)
        if existing is None:
            raise MemoryGovernanceError("cannot correct a memory that does not exist")
        corrected = MemoryRecord(
            memory_id=existing.memory_id,
            tenant=existing.tenant,
            role_scope=existing.role_scope,
            content=content,
            provenance=provenance,
            created_at=existing.created_at,
            expires_at=existing.expires_at,
            project_scope=existing.project_scope,
            quarantined=existing.quarantined,
        )
        return self.remember(corrected, consent="remember")

    def quarantine(self, tenant: str, memory_id: str, reason: str) -> bool:
        existing = self._store.get(tenant, {}).get(memory_id)
        if existing is None or not reason:
            return False
        self._store[tenant][memory_id] = MemoryRecord(
            memory_id=existing.memory_id,
            tenant=existing.tenant,
            role_scope=existing.role_scope,
            content=existing.content,
            provenance=f"{existing.provenance} | quarantined: {reason}",
            created_at=existing.created_at,
            expires_at=existing.expires_at,
            project_scope=existing.project_scope,
            quarantined=True,
        )
        return True
