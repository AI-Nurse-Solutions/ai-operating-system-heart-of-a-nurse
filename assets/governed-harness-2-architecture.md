# Nurse AI OS Governed Harness 2.0

## Executive architecture and evidence statement

**Published:** July 13, 2026  
**Audience:** Chief Nursing Officers, Chief Information Officers, Chief Technology Officers, Chief Medical Information Officers, Chief Information Security Officers, CEOs, nurse informaticists, AI architects, and Nurse Steward Councils  
**Status:** Tested, unsigned implementation candidate — not activated in the default Hermes profile  

> **Architectural statement:** Nurse AI OS is a no-PHI, nurse-governed control plane over the Hermes Agent runtime. Hermes supplies the horizontal agent runtime; EDENA supplies deterministic risk and autonomy semantics; Florence-X supplies bounded orchestration; human approval remains the authority boundary; and tamper-evident evidence makes the system's claims inspectable. The architecture does not authorize patient-specific clinical decisions, EHR access, personnel decisions, payments, credential handling, or unreviewed external action.

## The decision

Nurse AI OS retains **Hermes as its only agent runtime**. OpenClaw, LangGraph, OpenAI Agents SDK, Google ADK, Microsoft Agent Framework, Letta, OpenHands, and PydanticAI were assessed for portable architectural patterns, not installed as parallel runtimes.

This prevents duplication of profiles, context, skills, memory, tools, approvals, cron, delegation, Kanban, and gateway functions already supplied by Hermes. Harness 2.0 adds the missing vertical governance layer: typed capability manifests, effective-policy compilation, EDENA runtime gates, metadata-only provenance, trajectory evaluations, durable governed proposals, restart safety, trust cells, budgets, and connector controls.

## What CNOs should inspect

1. **Human judgment remains final.** AI may advise or draft; it does not adopt policy, make patient-specific clinical decisions, or make named-personnel decisions.
2. **No PHI boundary.** Patient identifiers, chart material, credentials, and synthetic PHI patterns are blocked in canary tests. This is not permission to process PHI.
3. **Nursing governance is operational.** EDENA distinguishes consequence (`risk_tier`) from independence (`autonomy_level`). Red means stop or escalate—not higher autonomy.
4. **Evidence claims are bounded.** Test and adoption evidence may be reported. Patient-outcome, safety-outcome, compliance, and institutional-readiness claims require separate evidence.
5. **Council review remains a gate.** Founder approval is recorded; Nurse Steward Council review and institutional validation are pending and are not implied.

## What CIOs should inspect

1. **Effective capability compilation is monotonic.** Profile, audience, channel, provider, sandbox, trust cell, and runtime policy may remove authority; no downstream layer may restore a denied capability.
2. **Configuration fails closed.** Unknown fields and unmanifested capabilities block. Valid configuration is written atomically; last-known-good state and rejected candidates are retained.
3. **Profiles are not host sandboxes.** Higher-consequence deployments require OS/container isolation and institutional controls in addition to Hermes profiles.
4. **Provenance is metadata-only.** Events contain tool/capability identifiers, reason codes, decision metadata, sequence numbers, and chained hashes—not prompts, tool arguments, results, user identifiers, credentials, or PHI.
5. **Connectors are denied by default.** Canary connectors require HTTPS, explicit host allowlisting, public data, declared capabilities, and no token passthrough.

## What CTOs should inspect

1. **Typed capability manifests.** Every governed tool, skill, MCP server, agent, cron job, or plugin receives an owner, reviewer, source, content hash, risk, autonomy ceiling, data classes, side-effect flag, targets, isolation, budgets, dependencies, expiry, and status.
2. **Runtime enforcement uses Hermes-native hooks.** `pre_tool_call` returns allow, block, or native approval escalation. `transform_tool_result` enforces output budgets.
3. **Errors fail closed in enforcement mode.** Invalid mode, evaluator failure, unknown tool, sensitive content, expired proposal, changed action digest, exhausted budget, and unknown connector all block.
4. **Durable proposals replace suspended model state.** Approval binds the proposal, manifest hash, target, action digest, reviewer role, and time. Payloads are not persisted in the proposal.
5. **Restart behavior depends on side effects.** Read-only idempotent work may resume within its retry ceiling. Side-effecting or non-idempotent work returns to `needs_review`; its approval is cleared.

## EDENA 2.0 semantics

```yaml
risk_tier: green | yellow | orange | red
autonomy_level: A0 | A1 | A2 | A3 | A4
```

- **Green:** low-consequence, reversible, no-PHI work.
- **Yellow:** human review before external use or side effects.
- **Orange:** bounded proposal with written scope and explicit approval.
- **Red:** prohibit, stop, or escalate to an authorized human/institutional process.
- **A0:** human-only action.
- **A1:** advisory.
- **A2:** drafting or bounded preparation.
- **A3:** approved bounded execution with budgets and evidence.
- **A4:** supervised autonomous operation; reserved and unavailable in self-service Nurse AI OS.

Risk never grants authority. Autonomy never lowers risk. Ambiguity raises risk and lowers autonomy.

## Implemented controls and evidence

| Control | Implementation evidence |
|---|---|
| Risk/autonomy separation | Approved ADR; Red resolves to block/A0 |
| Capability registry | Four content-hash-verified canary manifests; unmanifested capabilities block |
| Monotonic compiler | Tests prove later layers cannot re-grant removed authority |
| Strict configuration | Unknown fields rejected; atomic writes; last-known-good and rejected-candidate preservation |
| Shadow/runtime gate | Real Hermes plugin loader exercised in a temporary canary home |
| PHI/credential redlines | Synthetic MRN and credential-field cases block; values are not logged |
| Human approval | External side-effect class returns Hermes native `approve` directive |
| Provenance | Append-only JSONL with SHA-256 sequence chain; mutation, deletion, and reordering tests fail verification |
| Trajectory evaluation | Versioned eight-case synthetic dataset; 8/8 passed |
| Governed proposals | Action hash, expiry, approval binding, leases, retry ceiling, tombstones, no persisted action payload |
| Restart safety | Side effects return to review; read-only idempotent work may resume |
| Trust cells | Steward-local, untrusted-intake, and governed-executor ceilings |
| Budgets | Per-run/per-capability call limits and output-size transformation |
| Model routing | Private non-PHI work cannot silently change providers; PHI routing blocks |
| Connectors/MCP | Strict manifest, HTTPS, allowlist, public-data-only canary, no token passthrough |

### Candidate verification result

- Unit tests: **44 passed, 0 failed**
- Synthetic trajectory evaluations: **8 passed, 0 failed**
- Hermes runtime canary: safe read allowed; unknown tool blocked; synthetic PHI blocked; external side effect escalated for approval
- Hermes result-transform hook: passed
- Evaluation dataset: `naio-edena-runtime-core` version `2026.07.13.1`
- Dataset SHA-256: `c8259d32dd85842c95f674050db930c25cfb264874e92a1bb8668bd31da1d223`
- Source-tree SHA-256: `32a4d840bdf124cecfab73d321117642264a87ea2013f347b37ff0769fce9696`

The terminal provenance root is recorded in the machine-readable release evidence. It changes with each evaluation run because events include timestamps and unique IDs.

## Known, assumed, unknown, recommended, decide

### Known

- The source and tests described above execute successfully in the canary environment.
- The plugin loads through Hermes's actual plugin manager.
- The existing signed Phase 23 bundle was not changed.
- The default Hermes profile was not activated with Harness 2.0.

### Assumed

- The local operator and host account remain trusted.
- Hermes native approval behavior remains consistent with the pinned/runtime version tested.
- Institutional deployments will add identity, device, network, retention, procurement, legal, and incident-response controls.

### Unknown

- Performance under institutional concurrency and heterogeneous endpoints.
- False-positive/false-negative rates beyond the synthetic evaluation set.
- Council acceptability, usability burden, and nurse adoption at scale.
- Institution-specific regulatory, privacy, labor, and clinical-safety requirements.

### Recommended

- Expand adversarial evaluation before broader activation.
- Review the redline vocabulary with nurses, privacy, security, legal, informatics, and affected workers.
- Pilot with public/synthetic data in a dedicated profile and isolated workspace.
- Treat any model, tool, manifest, policy, or connector change as a new evaluation event.
- Require signed release evidence before distribution.

### Decide

The matching private key for the existing public trust anchor is not available in this build environment. Harness 2.0 is therefore **unsigned**. The trust anchor was not rotated. A signed release requires an authorized human key ceremony and independent fingerprint verification.

## Boundaries

Harness 2.0 is not:

- Clinical decision support
- Medical advice
- An EHR integration
- A HIPAA audit or certification
- Institutional approval
- A security certification
- Evidence of improved patient outcomes
- Permission to use PHI, confidential employer data, or credentials

## Primary sources

1. American Nurses Association, “The Ethical Use of Artificial Intelligence in Nursing Practice,” OJIN 30(2), May 2025: https://ojin.nursingworld.org/table-of-contents/volume-30-2025/number-2-may-2025/the-ethical-use-of-artificial-intelligence-in-nursing-practice/
2. ANA official position statements: https://www.nursingworld.org/practice-policy/nursing-excellence/official-position-statements/
3. WHO, *Ethics and governance of artificial intelligence for health: guidance on large multi-modal models* (2024): https://www.who.int/publications/i/item/9789240084759
4. NIST AI 600-1, *Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile* (2024): https://doi.org/10.6028/NIST.AI.600-1
5. OWASP, *Top 10 for Agentic Applications 2026*: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/
6. Hermes Agent — hooks: https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks
7. Hermes Agent — plugins: https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins
8. Hermes Agent — profiles: https://hermes-agent.nousresearch.com/docs/user-guide/profiles
9. Hermes Agent — Kanban: https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban
10. Hermes Agent official repository: https://github.com/NousResearch/hermes-agent
11. OpenClaw — security: https://docs.openclaw.ai/gateway/security
12. OpenClaw — configuration: https://docs.openclaw.ai/gateway/configuration
13. OpenClaw — restart recovery: https://docs.openclaw.ai/gateway/restart-recovery
14. OpenAI Agents SDK — guardrails: https://openai.github.io/openai-agents-python/guardrails/
15. OpenAI Agents SDK — human-in-the-loop: https://openai.github.io/openai-agents-python/human_in_the_loop/
16. LangGraph — persistence: https://docs.langchain.com/oss/python/langgraph/persistence
17. LangGraph — interrupts: https://docs.langchain.com/oss/python/langgraph/interrupts
18. Google Agent Development Kit — callbacks: https://google.github.io/adk-docs/callbacks/types-of-callbacks/
19. Microsoft Agent Framework — human-in-the-loop: https://learn.microsoft.com/en-us/agent-framework/workflows/human-in-the-loop
20. PydanticAI — deferred tools: https://ai.pydantic.dev/deferred-tools/
21. PydanticAI — evaluations: https://ai.pydantic.dev/evals/
22. Letta — stateful agents: https://docs.letta.com/guides/core-concepts/stateful-agents/
23. OpenHands — security: https://docs.openhands.dev/sdk/guides/security
24. Model Context Protocol — security best practices: https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices
25. Model Context Protocol — authorization: https://modelcontextprotocol.io/docs/tutorials/security/authorization

## Inspection links

- Machine-readable release evidence: `../naio-harness-v2/evidence/release-evidence.json`
- Harness source, tests, schemas, policies, plugin, and documentation: `../naio-harness-v2/`
- Previous professional-guidance architecture report: `../architecture-report.html`

*Agents propose. Humans judge. Nurses steward.*
