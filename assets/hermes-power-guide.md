# The Hermes Power Guide

## Directive v1.1 advanced Community edition

**Status:** Source-controlled guidance for optional advanced Hermes features. Profiles, scheduled jobs, gateways, model routing, and tools are capabilities of a configured runtime—not evidence of clinical readiness, institutional authorization, EDENA enforcement, or autonomous nursing judgment.

**Current operator:** Robert Domondon. NAIO and NIN are project initiatives.

> Keep this path no-PHI. Do not place patient-identifiable, employer-confidential, credential, D2–D4, or regulated operational data in a Community workspace.

## Advance only after the basic path is stable

Use the browser-first Community experience and a bounded D0/D1 workspace first. Add one advanced capability at a time, document why it is needed, and retain an easy way to disable it.

## Profiles

Profiles can separate purposes, files, models, and instructions. Separation is useful only when it is actually configured and tested.

- Give each profile one named purpose.
- Use a dedicated no-PHI folder.
- Keep credentials outside prompts, repositories, and shared files.
- Verify that files and tools unavailable to one profile remain unavailable in practice.
- Do not describe profile separation as institutional isolation or compliance assurance.

## Scheduled work

A scheduled job can run without a person present. That increases operational risk even when the content is non-clinical.

- Start with read-only collection or a draft delivered for review.
- Do not schedule clinical, staffing, patient, employment, legal, financial, or institutional decisions.
- Do not let a scheduled job publish, send, purchase, delete, or modify external systems without a separate, evidenced approval design.
- Add a clear owner, purpose, stop condition, review date, and failure notification.
- Disable the job when its evidence or owner is no longer current.

## Tools and gateways

- Grant the least privilege needed for one task.
- Prefer Observe or Draft before Recommend or Prepare Action.
- Require explicit human approval for external side effects.
- Keep destructive actions unavailable by default.
- Record what was proposed, what the human approved, and what the tool actually returned.
- Treat tool output as evidence to inspect—not proof that the intended outcome occurred.

## Model routing

Choose models by task requirements, privacy terms, evidence needs, and cost—not by a claim that one model is universally safest or most capable. A model change does not change the data class or transfer accountability away from the authorized human.

## Governance boundary

EDENA is the advisory governance control plane for classifying risk, data, and action posture. Written guidance is not mechanical enforcement. A claim that a control is implemented requires a named mechanism, control path, tested environment, and current evidence.

Green supports Observe and Draft with D0/D1 material. Recommend begins at Yellow. Unrestricted autonomy is prohibited. Clinical, institutional, credentialing, conformance, and PHI-eligible use require their own formal authorization gates.

## Advanced preflight

Before enabling any profile, schedule, tool, gateway, or connector, answer:

1. What exact task is allowed?
2. What data classes can enter?
3. What actions can occur without approval?
4. Who reviews and remains accountable?
5. What evidence shows the boundary works?
6. How is the capability disabled or rolled back?
7. What event requires escalation?

If any answer is unclear, do not activate the capability.

## Current sources of truth

- [Directive v1.1](../directive.html)
- [Hermes Configuration Handbook](../hermes-configuration-handbook.html)
- [Remote Hermes, Safely](../remote-hermes-safely.html)
- [Official Hermes documentation](https://hermes-agent.nousresearch.com/docs)

---

Agents propose. Humans judge. Nurses steward.

Robert Domondon · Nurse AI OS · Directive v1.1 advanced Community guidance
