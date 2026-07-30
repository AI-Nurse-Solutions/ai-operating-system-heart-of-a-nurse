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

```text
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

### Multi-role identity (Mission Control §9)

`identity.py` implements one identity with several role lenses: shared
stores (inbox, calendar, portfolio, projects, competencies) are held
once and filtered per lens, never copied; projects tag to one or
several roles; competencies appear once with role-specific
applications; layouts are remembered per role; cross-role suggestions
are optional and always explained. Permissions flow from the active
role plus the current workspace through `actor_for()` into the EDENA
policy engine — a title grants nothing outside an authenticated
context.

### Knowledge and Evidence Center (Mission Control §3.4)

`evidence.py` deepens governed retrieval into an evidence workflow:
structured PICO/PICOT question building (privacy-screened, with search
terms that feed `GovernedKnowledge.retrieve` directly);
claim-to-source traceability where every claim carries one of the five
evidence labels and source-backed labels require citations that exist
in the same tenant's index — no citation, no claim; assumptions are
stored awaiting confirmation, stay out of the bibliography, and only a
named human with real citations can confirm them; and a deterministic
"what changed" comparison between guideline versions with warnings for
date direction, jurisdiction, and document-type changes. Tracing a
claim replays its sources' full governance metadata, including the
local-policy precedence indicator.

### Healthcare sandbox (Mission Control §17, Phase 3)

`sandbox.py` is a safe place to practice on patient-shaped data with no
patients in it. The reviewed case catalog expands into FHIR-shaped
bundles (the synthetichealth/synthea pattern: generated records whose
numeric-suffix names are unmistakably synthetic) served through a
tenant-scoped read/search surface (the hapifhir/hapi-fhir pattern),
without vendoring either project. The synthetic label is
caller-controlled, so admission never trusts it alone: a strict
schema admits only the five generated resource types with only their
generated fields (free-form demographics have nowhere to live),
Patients must carry the numeric-suffix generation markers and the
sandbox identifier system, every string must still pass the privacy
screen, and governance does not relax because data is synthetic — role
gates and the ADPIE human-authorization gate apply unchanged. Cases
feed the existing contract surfaces: `as_knowledge_sources()` for
governed retrieval and `start_case_workflow()` for the orchestration
runtime.

### Research governance gates (Mission Control §17, Phase 4)

The licensed-clinician packet ships a `research-governance-gates`
module backed by real policy: research *execution* — collecting data,
recruiting participants, submitting to an IRB, sharing a dataset — is
gated by activity class in `config/edena-gateway-policy.json`,
independent of action mode. Execution intents run only in the
restricted data zone, require an authenticated organizational context
matching the current workspace, and require a governance approval
(IRB or equivalent) that is named on the request and recorded for the
actor — an unrelated approval satisfies nothing, and a fabricated
reference is denied outright; every allowed execution carries a
research-governance audit obligation. Drafting a protocol or research
question remains ordinary draft work through the Knowledge and
Evidence Center.

### Judgment layer (the runtime companion to "Humans judge")

`judgment.py` embeds critical, systems, and design thinking in how
answers are allowed to arrive — like EDENA, it lives at the gateway
and is driven by reviewed configuration
(`config/judgment-frames.json`), not by prompt-pack advice. Every
request is matched to a named thinking frame (clinical judgment,
systems lens, design studio, evidence appraisal, or general judgment)
with a deterministic commit-then-compare probe; students are
coach-first by default through the same role-alias table the policy
engine uses, and any user can opt in. Every output is scanned into a
reasoning ledger — visible assumptions, alternatives, and change
conditions — and at consequential tiers (Yellow and above, in
Recommend mode) every output must carry that material or it is
refused at the gateway with `EDENA-JUDGMENT-VISIBILITY`. The gate
keys on the declared action mode, not on detecting verdict wording,
so no phrasing bypasses it. Each result carries the
frame, probe, and a user-facing notice naming the feature, so the
person always knows the structure exists to serve their judgment. The
ledger detects wording, not wisdom: it makes judgment material
present; the human remains the judge.

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
