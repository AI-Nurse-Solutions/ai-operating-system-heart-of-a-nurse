---
title: Steward approval of the Go recommendations
date: 2026-10-04
status: Approved for implementation; public decision records pending synchronization
decided_by: Robert Domondon (project steward)
decision_source: Explicit instruction in the coding conversation
authorship: AI-prepared record of the steward's instruction
---

# Approved direction

The steward's instruction was:

> I approve all the Go recommendations. so we can move forward with this important project

This approves the Go choices and their stated conditions in
`08-steward-decision-assessment.md` and the accompanying plain-language
assessment. It authorizes continued implementation and testing. It does
not convert a Wait item to Go, grant access that has not been supplied,
or satisfy a release check before its evidence exists.

## Decision register

| Area | Approved choice | Implementation and verification still required |
|---|---|---|
| I-1 scope | Local personal app; one bounded assistant, human-orchestrated; no-AI workflows; backend business rules | Synchronize ADR 0005 with the approved bounded direction. Acceptance of the entire three-lanes bundle remains waiting on its data conflict. No framework migration or added agents is authorized by this record. |
| I-2 audit | Linked tamper-evident local events; logging failure prevents the associated write/action; separately retained checkpoint with off-device backup | P2.3: migration, append-only enforcement, verification, restore checks, and truthful reporting of legacy unchained events. A local chain is not independently trustworthy if both history and checkpoint are rewritten. |
| I-2 retention | Minimal audit and AI-ledger records kept while the workspace exists | Explain separately retained backups; retain whole-workspace deletion. Mandatory retention and preservation holds remain waiting. |
| I-3 data | Public/synthetic material and nonconfidential personal planning | Apply the narrower personal boundary consistently. No admission of confidential employer/vendor material or patient information. |
| I-3 people | “me” and controlled role labels for new personal-pilot records | Shared backend enforcement and tested preservation of existing records; legacy status stated honestly. Role labels do not authenticate a person. |
| I-3 visible instruction | The exact visible data-rule wording in the assessment, including “Names are not automatically detected.” | Same wording across screens and support guidance; known detection limits tested and stated. |
| I-4 approval surface | Explicit review, approval, run, reject, and revoke for governed local exports | ADR 0002 addendum below; exact-content/destination binding, single-use review tokens, backend owner binding, stale checks, and race tests. Sending, uploading, publishing, and external deletion remain blocked. |
| I-4 evidence export | Governed local-export boundary, preview, explicit approval, and receipt | Add a reviewed effect and tested evidence contract before shipping it. No automatic upload. |
| I-5 refusals | Refuse the named unsafe categories; offer permitted alternatives | Deterministic refusal probes before AI preview; tested cases do not establish perfect detection. |
| I-5 note reuse | Selected kept notes may return to a model only through explicit selection and reviewed preview | Recheck current sources and data rules; provide exclusion; no background reuse. |
| I-5 section drafts | One bounded pack section from permitted project records | Preserve sources, unknowns, AI label, and human acceptance. Resolve any template dependencies before shipping. |
| I-5 change control | Version behavior-governing changes; added data, tools, effects, and autonomy remain substantial changes | Behavior review for consequential prompt changes; narrowing also needs regression checks. |
| I-6 language/design | “Nurse AI OS Manager,” home “Today,” visible “Policy check,” technical names in Help; distinct status words and text plus color; no assistant persona; doctrine-aligned tagline | Apply in coherent UI changes and verify keyboard use, contrast, narrow screens, and support-guide consistency. |
| I-7 measurement | Voluntary local evaluation of outcomes and correction effort | No automatic sharing or unsupported savings claims. Real failure-case collection remains waiting on an allowed consent/rights path. |
| I-7 facts | Prepare factual security materials for pilot users and their designated reviewers | Verified behavior versus limitations clearly separated. Recipient selection and authorization still required before distribution. |
| N-1 authorization | Zone migration requires its named approval held by the actor; Orange requests require the named held approval, not any unrelated approval | Policy and gateway tests, multi-role checks, policy version bump, and compatibility review. This does not enable organization deployment or establish approval expiry/scope verification not present in the contract. |
| Original release steps | Establish project-controlled signing; wire signing/notarization; prepare reproducible candidate; test actual target laptops; manual signature-verified update checks | Accounts, signing identities, hosting/key custody, hardware, applicable authorization, and the release prerequisites remain necessary. Update activation and candidate distribution retain their Wait conditions. |

## ADR 0002 addendum: the local app as an approval surface

Approved by the same instruction on 2026-10-04:

1. The authenticated local app may collect the manager's explicit approval
   of a permitted local effect. Its approval controls are a deliberate
   exception for this edition to older read-only dashboard guidance.
2. The backend binds approval to the reviewed revision, content hash,
   destination, workspace, and accountable owner. A single-use read token
   binds the app action to the review it presented; it does not prove the
   human read or understood the content.
3. The executor rechecks the binding and policy immediately before acting.
   Reject and revoke cannot race past execution. Terminal outcomes and
   receipts remain truthful; uncertain effects are not automatically retried.
4. Evidence packet export follows this same governed local-effect pattern.
   Its effect must be admitted explicitly and tested before use.
5. No assistant approves itself. No send, post, publish, upload, or external
   deletion is admitted. No institutional authorization is inferred.

This addendum authorizes building the approval surface; it does not claim
its controls are implemented yet. See the build plan for completion evidence.

## Publication and prerequisites

This is a local record of actual steward approval, not a request for repeat
approval. `GOVERNANCE.md` §3's proposal, open-comment, and public issue
record process still applies to substantial changes. No completed comment
period, posted issue decision, merged PR, or published ADR is claimed here.
The record should accompany the implementation when it is submitted.

Wait recommendations remain in force for cloud provider selection, JEV,
hold definitions, the three-lanes bundle, real failure-case collection,
Hermes hosting/session integration, and G7. Signing secrets belong outside
the repository; no purchase, identity verification, or account enrollment
has occurred merely because the route was approved.

## First implemented follow-through: N-1

EDENA policy version 1.0.1 now requires a migration's named approval to be
held by the actor. Orange requests also name the held `approval_id`,
including recommendation requests without side effects. Missing references
remain gated; invented, unrelated, malformed, or whitespace-padded references
are denied. Existing organizational-context and private-reflection checks
still apply. The trusted host remains responsible for approval provenance;
this is not a new production authorization registry.

Validation on 2026-10-04:

- Integration suite: 308 tests passed, including refusal-before-executor,
  separate migration/Orange approval requirements, and multi-role checks.
- Manager suite: 417 tests ran successfully, 4 skipped.
- IPC contract: 137 real envelopes passed ajv and strict TypeScript checks.
- The 24-case synthetic shadow report was refreshed for policy version
  1.0.1; its case labels and decision counts did not change.
- Root suite: 770 tests ran, with 5 failures and 4 errors. The same nine
  test failures occurred on a separate untouched checkout of `b551612`;
  no new failed test was introduced. These concern existing release-kit,
  media-packet, and soul-quiz checks and remain unresolved.
- `git diff --check` passed. Changes remain local and uncommitted.

Next implementation priorities: P2.3 audit-chain integrity, then shared
role-label enforcement and the personal-workspace capture screens. Their
approval is recorded above; implementation and release evidence still need
to be produced.

Completion update: P2.3 and the preceding local implementation are now
combined and verified on `codex/integrated-manager`, as recorded in
[`11-manager-integration-handoff.md`](11-manager-integration-handoff.md).
Shared role-label enforcement and capture screens remain the next feature
work; their approval does not need to be requested again.

Further completion update: shared people-field enforcement is implemented
on `codex/people-fields`, with preservation and disclosure limits recorded
in [`12-people-fields-handoff.md`](12-people-fields-handoff.md). Capture
screens remain next. Publication and release are still pending their gates.

Further completion update: the authorized personal-workspace capture screens
are implemented on `codex/capture-screens`. Verification and the exact
source-versus-release distinction are recorded in
[`13-capture-screens-handoff.md`](13-capture-screens-handoff.md).
The next technical step is packaging the combined implementation into a
macOS download for verification. Existing signing, real-laptop and release
gates remain; no additional provider, installation, dispatch, publication,
or institutional authority follows from this implementation.

Packaging follow-up: developer packaging verification has advanced locally
on `codex/packaged-capture`, recorded in
[`14-packaged-app-verification.md`](14-packaged-app-verification.md).
A Linux standalone executable passed the capture and broader app journeys.
The macOS job is prepared to perform those checks on its native bundle;
it has not run for these local changes. Existing publication, signing,
runtime licensing, hardware, pilot and clinical gates remain unchanged.
