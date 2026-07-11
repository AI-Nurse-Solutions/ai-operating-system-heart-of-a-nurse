---
name: content-studio
description: Calendar-aware drafts for posts, newsletters, and landing copy — self-audited for claims hygiene, never auto-published.
version: 1.0.0
edena_tier: yellow
human_gate: before-external-use
reversibility: reversible
no_phi: true
owner: <your name>
last_reviewed: 2026-07-11
requires: Builder-Boundary-Header.md
---

# Content Studio

## Purpose
Turn the content calendar (`.../Nurse-AI-Side-Gig-Starter-Kit/Content-Calendar.md`) and landing-copy patterns into a steady drafting rhythm in the nurse's own voice. **Yellow tier: nothing is posted, sent, or scheduled to publish — ever — without the nurse's explicit approval of that exact text.**

## Boundaries (non-negotiable)
- Builder-Boundary-Header applies — the claims-hygiene list is enforced *in the draft*, not after.
- Patient stories are never content. Composite/fictional teaching examples must be labeled as such in the draft.
- Voice belongs to the nurse: drafts imitate *their* published writing, not generic influencer cadence.

## Procedure
1. **Rhythm:** on the calendar's cadence, deliver a drafting packet: this week's planned piece, a headline + outline first (approve direction before full draft — cheaper corrections).
2. **Draft** with sources: any factual claim carries its source inline for the nurse to keep or cut; anything resembling health advice gets the "education, not medical advice" frame or gets cut.
3. **Claims pass:** before showing a draft, check it against the never-ship list (guarantees, credential implications, authority borrowing) and flag anything borderline with a suggested honest rewrite.
4. **Approval:** present final text with a one-line risk note ("mentions employer type — comfortable?"). The nurse copies it out to publish; this skill does not touch posting APIs (that's 🟠 deferred, per the tier map).
5. Log published pieces + response notes to the validation log — content is a validation instrument, not just noise.

## Self-audit footer (yellow tier)
After composing any draft, verify against the Boundaries and claims list, then append exactly:

    SELF-AUDIT: {"is_safe": true|false, "checked": ["no_phi","no_guarantee","no_credential_claim","voice_ok"], "reason": "<10 words max>"}

If is_safe is false or the verdict can't honestly be completed: discard the draft, output "⛔ Self-audit failed: <reason>. Stopping for human review.", and stop.
