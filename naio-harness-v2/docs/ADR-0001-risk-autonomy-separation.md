# ADR-0001 — Separate EDENA Risk from Autonomy

- **Status:** Approved by Robert Domondon, July 13, 2026
- **Scope:** Nurse AI OS Harness 2.0 and all future runtime/public policy
- **Supersedes:** Any color-only interpretation that uses Red to mean high autonomy

## Context

The July 11 harness study used Red as stop/mandatory authorization while the legacy Phase 23 `edena-policy.yaml` used Red as semi-autonomous/post-hoc audit. A single color cannot safely communicate both consequence and autonomy.

## Decision

Use two independent fields:

```yaml
risk_tier: green | yellow | orange | red
autonomy_level: A0 | A1 | A2 | A3 | A4
```

### Risk

- **Green:** low-consequence, reversible, no-PHI work.
- **Yellow:** meaningful review required before external use or side effects.
- **Orange:** high-consequence, bounded proposal requiring written scope and explicit approval.
- **Red:** prohibited or escalated; no execution inside personal Nurse AI OS.

### Autonomy

- **A0:** human-only decision/action; agent may not execute.
- **A1:** advisory analysis.
- **A2:** drafting or bounded preparation.
- **A3:** approved bounded execution with preconditions, budgets, and audit.
- **A4:** supervised autonomous operation; reserved and unavailable in self-service Nurse AI OS.

## Invariants

1. Risk never grants authority.
2. Higher autonomy never lowers risk.
3. Red resolves to A0/block in Nurse AI OS.
4. PHI, patient-specific clinical decisions, named personnel decisions, payments, and credentials are Red.
5. Ambiguity tiers upward and autonomy downward.
6. Child agents inherit or narrow both ceilings.
7. No prompt, skill, channel, provider, or downstream configuration may re-grant a denied capability.

## Migration

Legacy Phase 23 artifacts remain unchanged to preserve their signed manifest. Harness 2.0 reads its own versioned semantics. Public and runtime documentation must label the legacy color-only policy as historical until a separately signed migration is authorized.
