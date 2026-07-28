# Nurse AI OS Integration Contract

> Florence-X orchestrates. EDENA governs. Nurse AI OS provides the
> professional environment. Humans retain authority.

Six stable interfaces that every external engine sits behind, plus the
first prototype built on them: the **EDENA Policy Gateway**. No external
repository is merged, forked, or vendored into Nurse AI OS. Each one
plugs in behind exactly one interface, so the OS is protected from vendor
lock-in, abandoned projects, license changes, breaking updates, and
architectural sprawl.

## Status

Reference implementation, no-PHI, education and simulation only. Not
clinical decision support, not a HIPAA control, and not authorized for
patient data, EHR data, personnel decisions, payments, or autonomous
external actions. The privacy screen reduces risk; it never proves
content is de-identified or safe for unrestricted use.

## The six interfaces

| Interface | Module | Reference adapter | Designed for (external engine) |
| --- | --- | --- | --- |
| Policy decision | `policy.py` | `EdenaPolicyEngine` | open-policy-agent/opa |
| Privacy transformation | `privacy.py` | `PrivacyScreen` | microsoft/presidio |
| Validation | `validation.py` | `TrafficValidator` | guardrails-ai/guardrails |
| Observability | `observability.py` | `GatewayTracer` | langfuse/langfuse |
| Memory | `memory.py` | `GovernedMemory` | mem0ai/mem0 |
| Knowledge retrieval | `knowledge.py` | `GovernedKnowledge` | infiniflow/ragflow |
| Orchestration | `orchestration.py` | `AdpieWorkflow` | langchain-ai/langgraph |

(Validation is the sub-interface of policy decision the Directive calls
"controls beneath EDENA"; it ships as its own module so Guardrails can be
swapped without touching the policy engine.)

Phase 3 engines (synthetichealth/synthea, hapifhir/hapi-fhir) and the
Phase 4 reference (Azure-Samples/healthcare-agent-orchestrator) will sit
behind the knowledge-retrieval and orchestration interfaces when the
healthcare sandbox is built; nothing in this contract needs to change for
them.

## The EDENA Policy Gateway

`gateway.py` composes the Phase 1 layers between every user, agent,
model, memory store, and external tool:

```
Request -> Identity and role -> Privacy screen -> EDENA policy ->
Allow / deny / require approval -> Execute -> Validate output -> Audit
```

Rules enforced by the reference policy (`config/edena-gateway-policy.json`),
aligned to the NIN-NAIO Master Directive v1.1 (independent risk tier,
data class, and action mode):

- Green cannot accept patient identifiers — not even redacted.
- Yellow may analyze de-identified institutional information (<= D2).
- Orange requires an authenticated organizational context and a recorded
  approval.
- Red-P is prohibited at every action mode; Red-E cannot execute without
  defined institutional controls (kill switch, audit stream, named
  accountable human).
- Student mode cannot generate patient-specific recommendations and is
  capped at Draft.
- No agent sends, publishes, deletes, purchases, or modifies external
  systems without the required approval.
- Personal memory and institutional memory cannot cross tenant
  boundaries.
- Unrestricted autonomy is prohibited. Ambiguity narrows capability and
  fails closed.

### Data zones (Mission Control alignment)

Requests carry a data zone from the Mission Control specification —
`private`, `shared_professional`, `educational_record`, `institutional`,
`restricted` (default: `private`; ambiguity narrows). Two rules are
enforced at the policy decision point:

- Private reflections never appear in manager, faculty, cohort, or
  executive views (`EDENA-PRIVATE-REFLECTION`).
- Content never silently migrates between zones: a cross-zone move
  requires an explicit, recorded approval (`EDENA-ZONE-MIGRATION`), and
  approved moves are logged.

Note on tier naming: the Mission Control specification uses the public
four-tier shorthand (Green/Yellow/Orange/Red). This package follows
Directive v1.1: spec-Red maps to Red-P (prohibited; blocked with a
minimal safety record), and exceptional controlled high-risk work is
Red-E behind institutional controls.

Every decision is traced to a tenant-separated, hash-chained JSONL audit
stream with redaction applied *before* tracing — spans carry entity
types, reason codes, and counts, never raw content.

## Layer responsibilities

| Layer | Question it answers |
| --- | --- |
| EDENA + policy engine | Is this actor permitted to perform this action under these conditions? |
| Validator | Does this input or output satisfy the required quality and safety constraints? |
| Privacy screen | Does this content contain sensitive or identifying information? |

## Running the tests

```bash
python3 -m unittest discover -s naio-integrations/tests -p 'test_*.py' -v
```

The repo-wide suite (`python3 -m unittest discover -s tests`) also runs a
top-level regression that exercises this package.
