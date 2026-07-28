"""Nurse AI OS Integration Contract v1.0.

Six stable interfaces that every external engine must sit behind:

    Orchestration interface        (reference pattern: langchain-ai/langgraph)
    Policy-decision interface      (reference pattern: open-policy-agent/opa)
    Privacy-transformation interface (reference pattern: microsoft/presidio)
    Memory interface               (reference pattern: mem0ai/mem0)
    Knowledge-retrieval interface  (reference pattern: infiniflow/ragflow)
    Observability interface        (reference pattern: langfuse/langfuse)

The contract exists so Nurse AI OS never depends on a vendor directly:
external repositories plug in behind an interface and can be replaced
without touching Florence-X, EDENA, or Mission Control.

All datatypes follow the NIN-NAIO Master Directive v1.1 semantics:
independent risk tier, data class, and action mode dimensions.
Unrestricted autonomy is prohibited. Risk never grants authority.
Action mode never lowers risk. Ambiguity narrows capability and routes
the question to an accountable human.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable

CONTRACT_VERSION = "1.0.0"


class RiskTier(str, Enum):
    """Directive v1.1 risk tiers. Red-P is prohibited; Red-E is exceptional."""

    GREEN = "green"
    YELLOW = "yellow"
    ORANGE = "orange"
    RED_P = "red-p"
    RED_E = "red-e"

    @property
    def rank(self) -> int:
        return {"green": 0, "yellow": 1, "orange": 2, "red-p": 3, "red-e": 3}[self.value]


class DataClass(str, Enum):
    """Directive v1.1 data classes. Sensitivity never disappears."""

    D0 = "D0"  # public, synthetic, or de-identified
    D1 = "D1"  # personal professional
    D2 = "D2"  # confidential organizational
    D3 = "D3"  # regulated or highly sensitive (includes PHI)
    D4 = "D4"  # restricted critical

    @property
    def rank(self) -> int:
        return int(self.value[1:])


class ActionMode(str, Enum):
    """Directive v1.1 action modes. Authority increases only through controls."""

    OBSERVE = "observe"
    DRAFT = "draft"
    RECOMMEND = "recommend"
    PREPARE_ACTION = "prepare_action"
    ACT_WITH_APPROVAL = "act_with_approval"
    CONSTRAINED_AUTONOMY = "constrained_autonomy"
    UNRESTRICTED_AUTONOMY = "unrestricted_autonomy"  # always prohibited

    @property
    def rank(self) -> int:
        order = (
            "observe", "draft", "recommend", "prepare_action",
            "act_with_approval", "constrained_autonomy", "unrestricted_autonomy",
        )
        return order.index(self.value)

    @property
    def has_side_effects(self) -> bool:
        return self.rank >= ActionMode.PREPARE_ACTION.rank


class DataZone(str, Enum):
    """Mission Control data zones. Private content never silently migrates."""

    PRIVATE = "private"  # reflections, confidence, personal goals, draft notes
    SHARED_PROFESSIONAL = "shared_professional"  # project tasks, meeting actions
    EDUCATIONAL_RECORD = "educational_record"  # verified assessments, competency
    INSTITUTIONAL = "institutional"  # approved aggregate measures, policies
    RESTRICTED = "restricted"  # research data, sensitive workforce/clinical data


class Decision(str, Enum):
    """Policy decision outcomes. Fail-closed: unknown always maps to DENY."""

    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


@dataclass(frozen=True)
class Actor:
    """Who is asking. Identity and role arrive before any policy question."""

    actor_id: str
    role: str  # e.g. nurse, student, educator, agent
    tenant: str  # personal:<user> or org:<institution>
    authenticated_org: str | None = None
    approvals: tuple[str, ...] = ()  # recorded approval ids held by this actor


@dataclass(frozen=True)
class GatewayRequest:
    """One governed action moving through the EDENA Policy Gateway."""

    request_id: str
    actor: Actor
    intent: str  # short machine label, e.g. "summarize_policy"
    content: str  # the text payload being processed
    risk_tier: RiskTier
    data_class: DataClass
    action_mode: ActionMode
    target_tenant: str | None = None  # tenant whose data/tools are touched
    data_zone: DataZone = DataZone.PRIVATE  # ambiguity narrows: most protected
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PolicyDecision:
    """OPA-shaped decision document: decision + reasons + obligations."""

    decision: Decision
    reason_codes: tuple[str, ...]
    obligations: tuple[str, ...] = ()  # e.g. "record_approval", "human_review"
    policy_version: str = CONTRACT_VERSION

    @property
    def allowed(self) -> bool:
        return self.decision is Decision.ALLOW


@dataclass(frozen=True)
class PrivacyFinding:
    """One detected identifier. Only metadata is kept — never the raw value."""

    entity_type: str
    start: int
    end: int
    score: float
    recognizer: str


@dataclass(frozen=True)
class PrivacyResult:
    """Result of a privacy transformation pass over one text."""

    transformed_text: str
    findings: tuple[PrivacyFinding, ...]
    action: str  # "pass" | "redact" | "block"

    @property
    def clean(self) -> bool:
        return not self.findings


@dataclass(frozen=True)
class ValidationIssue:
    check: str
    severity: str  # "warn" | "fail"
    message: str


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    issues: tuple[ValidationIssue, ...] = ()

    @property
    def failures(self) -> tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "fail")


@dataclass(frozen=True)
class MemoryRecord:
    """A governed memory. Provenance, scope, and expiry are mandatory."""

    memory_id: str
    tenant: str
    role_scope: str
    content: str
    provenance: str
    created_at: str
    expires_at: str | None = None
    project_scope: str | None = None
    quarantined: bool = False


@dataclass(frozen=True)
class KnowledgeSource:
    """A retrievable document with the governance metadata retrieval must show."""

    source_id: str
    title: str
    doc_type: str  # "policy" | "research" | "local_practice"
    effective_date: str
    expires_date: str | None
    jurisdiction: str
    content: str
    tenant: str


@dataclass(frozen=True)
class KnowledgeAnswer:
    """Grounded retrieval result. No citation, no claim."""

    passages: tuple[dict[str, Any], ...]
    warnings: tuple[str, ...]
    refused: bool = False
    refusal_reason: str | None = None


class PolicyDecisionInterface(abc.ABC):
    """EDENA policy decision point. External engine: Open Policy Agent."""

    @abc.abstractmethod
    def decide(self, request: GatewayRequest) -> PolicyDecision:
        """Return a fail-closed decision document for one request."""


class PrivacyTransformationInterface(abc.ABC):
    """Privacy front door. External engine: Microsoft Presidio."""

    @abc.abstractmethod
    def analyze(self, text: str) -> tuple[PrivacyFinding, ...]:
        """Detect identifiers without storing raw values."""

    @abc.abstractmethod
    def transform(self, text: str, mode: str = "redact") -> PrivacyResult:
        """Redact or mask identifiers before text crosses a boundary."""


class ValidationInterface(abc.ABC):
    """Model traffic validation beneath EDENA. External engine: Guardrails AI."""

    @abc.abstractmethod
    def validate_input(self, request: GatewayRequest) -> ValidationResult: ...

    @abc.abstractmethod
    def validate_output(self, request: GatewayRequest, output: str) -> ValidationResult: ...


class ObservabilityInterface(abc.ABC):
    """Mission Control instrumentation. External engine: Langfuse."""

    @abc.abstractmethod
    def start_trace(self, request: GatewayRequest) -> str:
        """Open a trace for one request; returns the trace id."""

    @abc.abstractmethod
    def record_span(self, trace_id: str, name: str, payload: dict[str, Any]) -> None: ...

    @abc.abstractmethod
    def end_trace(self, trace_id: str, outcome: str) -> None: ...


class MemoryInterface(abc.ABC):
    """Governed professional memory. External engine: Mem0 behind this contract."""

    @abc.abstractmethod
    def remember(self, record: MemoryRecord, consent: str) -> MemoryRecord: ...

    @abc.abstractmethod
    def recall(self, tenant: str, role: str, query: str) -> tuple[MemoryRecord, ...]: ...

    @abc.abstractmethod
    def forget(self, tenant: str, memory_id: str) -> bool: ...

    @abc.abstractmethod
    def correct(self, tenant: str, memory_id: str, content: str, provenance: str) -> MemoryRecord: ...

    @abc.abstractmethod
    def quarantine(self, tenant: str, memory_id: str, reason: str) -> bool: ...


class KnowledgeRetrievalInterface(abc.ABC):
    """Governed document retrieval. External engine: RAGFlow."""

    @abc.abstractmethod
    def index(self, sources: Iterable[KnowledgeSource]) -> int: ...

    @abc.abstractmethod
    def retrieve(self, tenant: str, query: str, today: str) -> KnowledgeAnswer: ...


class OrchestrationInterface(abc.ABC):
    """ADPIE workflow runtime under Florence-X. External engine: LangGraph."""

    @abc.abstractmethod
    def start(self, workflow_id: str, context: dict[str, Any]) -> dict[str, Any]: ...

    @abc.abstractmethod
    def advance(self, workflow_id: str, **inputs: Any) -> dict[str, Any]: ...

    @abc.abstractmethod
    def authorize(self, workflow_id: str, approver: str, approved: bool) -> dict[str, Any]: ...

    @abc.abstractmethod
    def state(self, workflow_id: str) -> dict[str, Any]: ...
