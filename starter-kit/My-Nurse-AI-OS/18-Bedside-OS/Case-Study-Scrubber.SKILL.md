---
name: case-study-scrubber
description: Helps write teaching cases and de-identifies at the gate — drafting does not begin until the de-identification checklist passes, and re-identifiable fragments are refused outright.
version: 1.0.0
edena_tier: yellow
human_gate: before-external-use
reversibility: reversible
no_phi: true
owner: <your name>
last_reviewed: 2026-07-11
requires: Bedside-Boundary-Header.md
---

# Case Study Scrubber

## Purpose
Nurses carry teaching gold — the presentations, the near-misses, the "I'll never miss that again" moments — and the safe way to share it is a properly de-identified, ideally *composite* teaching case. This skill's defining feature is the **order of operations: the de-identification gate runs first, and drafting is locked until it passes.** Yellow tier: teaching cases get shared, so the nurse approves the final text.

## Boundaries (non-negotiable)
- Bedside-Boundary-Header applies. The gate below is refuse-at-intake: if the raw material is re-identifiable and can't be honestly composited, the case doesn't get written — "that story is too specific to scrub" is a valid and common verdict.
- **Composite by default.** The safest teaching case merges several real patterns into one fictional patient. Fictional details are labeled fictional in the draft; the case never claims to be a specific real event.
- HIPAA's Safe-Harbor list is the *floor*, not the bar: small units, rare conditions, and memorable timelines re-identify even with all 18 identifiers stripped. The standing test is the header's — *if it could identify a patient, it counts.*

## The gate (runs before any drafting)
1. **Source honesty:** is this one patient's story or a pattern seen many times? Single-patient stories get pushed toward compositing or declined.
2. **The re-identification screen:** unit size and community size; condition rarity; time markers (season, holiday, "last Tuesday"); role markers ("our only night-shift respiratory therapist"); sequence-of-events distinctiveness. Any hit → generalize ("a winter shift," "a community hospital med-surg unit") or decline.
3. **The colleague screen:** staff and physicians in the story get the same protection as patients — roles, not people; no performance blame narratives.
4. **Verdict:** `GATE PASSED — compositing plan: <one line>` or `GATE FAILED — <reason>; here's what would make it teachable safely`. Only a passed gate unlocks drafting.

## Procedure (after the gate)
1. Draft the case in teaching structure: learning objectives → stem → progression → decision points → debrief questions (Tanner-style reflection prompts fit here).
2. Label the composite: one line in the header — "Composite teaching case; details fictional."
3. Approval: the nurse reviews with fresh eyes against the gate criteria once more, then owns where it goes (unit education, class, publication — publication may need institutional review; flag it).
4. File to `../Projects/teaching-cases/`.

## Self-audit footer (yellow tier)
After composing any draft, verify against the Boundaries and re-run the gate mentally, then append exactly:

    SELF-AUDIT: {"is_safe": true|false, "checked": ["gate_passed","composite_labeled","no_reidentifiable_detail","colleagues_protected"], "reason": "<10 words max>"}

If is_safe is false or the verdict can't honestly be completed: discard the draft, output "⛔ Self-audit failed: <reason>. Stopping for human review.", and stop.
