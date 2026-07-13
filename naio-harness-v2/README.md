# NAIO Harness 2.0

A privacy-first, no-PHI governance plane for Nurse AI OS running over Hermes Agent.

## Status

Existing-trust-anchor signed implementation candidate. Not clinical decision support, not a HIPAA certification, and not authorized for patient data, EHR data, personnel decisions, payments, or autonomous external actions. The detached release-evidence signature preserves the Phase 23 RSA-SHA256 trust anchor; it does not imply Nurse Steward Council or institutional approval.

## Architecture rule

Hermes is the only runtime. NAIO adds deterministic EDENA policy, capability compilation, attestation, provenance, evaluation, governed proposals, and signed release evidence.

## Canonical semantics

- `risk_tier`: Green, Yellow, Orange, Red — consequence and escalation.
- `autonomy_level`: A0–A4 — how independently a bounded capability may operate.

Risk and autonomy are independent. Red never means “highest autonomy.” In Nurse AI OS, Red means stop, prohibit, or escalate to an authorized human/institutional process.

## Development stages

0. Semantic freeze
1. Capability compiler and doctor
2. Shadow runtime gate
3. Fail-closed enforcement
4. Provenance and evaluations
5. Governed proposals and recovery
6. Trust cells, budgets, connectors
7. Council evidence, public documentation, signed release

Agents propose. Humans judge. Nurses steward.
