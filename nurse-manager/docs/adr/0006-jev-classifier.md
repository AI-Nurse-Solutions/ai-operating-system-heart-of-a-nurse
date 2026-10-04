---
title: "ADR 0006: JEV as an opt-in classifier that advises and can only tighten"
status: Accepted
date: 2026-10-04
decided_by: Robert Domondon (project steward, GOVERNANCE.md §1)
decided_on: 2026-10-04
authorship: Substantially AI-generated (Claude Code) with human review pending
amends: ADR 0004 (narrowly; see Decision 1)
---

# ADR 0006: JEV as an opt-in classifier that advises and can only tighten

## Context

JEV, from TypeSafe AI, is a classifier service. It answers typed
questions about a piece of text it is given:

- yes or no (`noul`), with a probability;
- a choice among named options, with a probability for each;
- a score on a named scale, with a probability for each level.

It never writes text. It is fast and inexpensive per request. Access is
by a key from TypeSafe's early-access program. The request and reply are
JSON over HTTPS to one address (`https://api.typesafe.ai/v1/systemone`),
and each request names a model version.

Build step 4.5 already built a JEV-shaped `DecisionAdapter` and a shadow
harness on synthetic data. Step 4.5b, a live JEV adapter, was blocked on
a steward decision, for two reasons:

- JEV would be a second cloud service beside the one ADR 0004 allows.
- TypeSafe's terms rule out confidential data.

The steward asked for JEV to be integrated "as your fast, low-cost
classifier to handle binary decisions, scoring, and workflow routing".
Four questions followed, and the steward chose an answer to each (see the
decision record).

## Decision

1. **A separate classifier service, admitted narrowly.**
   - JEV is admitted as a classifier only. It never writes, drafts,
     summarizes, or answers in text.
   - This narrowly amends ADR 0004's "exactly one cloud provider". That
     rule still governs services that write text.
   - Build step 4.2b, the one cloud AI service that drafts, stays a
     separate and open steward decision.
2. **Advise and tighten.**
   - JEV suggests a route, an order, and yes-or-no flags.
   - Its answer may add a review step, or refuse a question before an AI
     model sees it. It never removes a review step, approves anything,
     lowers a tier, or changes the EDENA policy's decision.
   - When JEV is unsure, unavailable, or answers outside the contract,
     everything works as it does without JEV, and the manager is told why.
   - EDENA and the manager still decide.
3. **D0/D1 only, after a preview, and off by default.**
   - Only material the workspace's data rules admit (D0 public or
     synthetic, D1 the manager's own permitted material) is sent. The
     privacy screen runs on it again first. D2 and above are never sent.
   - The manager sees the exact request body before anything is sent. The
     request is bound to that preview by hash; any change refuses it.
   - JEV is off in a new workspace, and every job is off until the manager
     turns it on.
   - The manager connects their own key. It is kept in the operating
     system's credential store: the macOS Keychain, the Secret Service on
     Linux, or the Windows Credential Manager. It is never kept in the
     workspace file, an argument, a log, an envelope, a backup, or an
     export. Where no credential store is available, JEV stays off.
   - Neither the address nor the key is ever read from an environment
     variable (ADR 0004, decision 5).
4. **Four jobs, each switched on separately.**
   1. **Action review.** For a proposed action, JEV suggests allow, hold
      for review, or deny beside the policy's decision. When JEV is
      confident its suggestion is stricter, approval waits until the
      manager acknowledges the suggestion. The policy's decision is
      recorded unchanged.
   2. **Refusal pre-check.** Before a project question goes to the AI
      model, JEV checks it for five refused categories:
      - patient information;
      - an individual's performance or conduct;
      - confidential employer material;
      - a clinical decision;
      - a judgment about a named person.

      A confident yes refuses the question, names the category, and offers
      the nearest permitted path. This adds to the deterministic refusal
      set (proposed step P4.3); it does not replace it.
   3. **Workflow routing.** For a request the manager types, JEV suggests
      where in the workspace to start. It only suggests: every place stays
      one click away, and nothing starts by itself.
   4. **Attention ordering.** JEV suggests an order for "Needs my
      judgment". Every item is kept, and the usual order is one click away.
      **No number is ever shown**: no score, no confidence.
5. **The same gates as every assistant.** Each request passes, in order:
   1. the data rules;
   2. EDENA at `recommend` (ADR 0002);
   3. a daily request limit, from 0 to 2000 and 200 by default;
   4. the stop control.

   Each request is recorded before it is sent, in a ledger that keeps
   hashes, outcomes, fixed result keys, and confidences, never the text.
6. **A pinned model.** Requests name `jev-1.13.0`, never `jev-latest`.
   Changing the model is a reviewed code change.

## Consequences

- Migration `0014` adds three tables:
  - `classifier_settings`: JEV is off by default, and no job can be on
    while JEV is not connected;
  - `classifier_requests`: the ledger;
  - `action_classifications`: JEV's suggestion beside the policy decision,
    and the hold.

  `ClassifierService` is the sole writer of all three (contract map §5).
  `ActionBoundary.approve` reads the hold and refuses approval until it is
  acknowledged.
- `credentials.py` adds the credential stores. The macOS and Linux
  stores are tested with the operating-system calls mocked. The Windows
  store has no test here. Each store still has to be checked on a real
  Windows, macOS, and Linux machine before a pilot uses JEV.
- The live adapter for the step 4.5 shadow harness now exists
  (`tools/shadow_report.py --adapter jev`, with the key on standard input).
  It runs only on the pinned synthetic set. Running it against the live
  service needs the steward's key.
- TypeSafe's terms, as read on 2026-10-04, are shown on the AI assistance
  screen:
  - no training on what is sent;
  - retention "as reasonably necessary", with no fixed period, and zero
    retention for enterprise customers only;
  - hosting in the United States;
  - no business associate agreement;
  - output that may be wrong.

  The terms must be re-read before a pilot uses JEV, and whenever the
  pinned model changes.
- JEV adds cost and a dependency only for a manager who connects it.
  Everything works without it, and every JEV failure leaves today's
  behavior in place.

## Decision record

Accepted by the project steward, Robert Domondon, on 2026-10-04, in a
Claude Code session. The request was: "Integrate Jev as your fast,
low-cost classifier to handle binary decisions, scoring, and workflow
routing." The steward then chose these answers:

| Question | The steward's answer |
|---|---|
| What may JEV's answer do? | "Advise and tighten (Recommended)" |
| What may be sent to JEV? | "D0/D1 after preview (Recommended)" |
| Which jobs first? | "Action review suggestion, Refusal pre-check, Workflow routing, Attention ordering" (all four). Attention ordering must never show a number |
| How is it recorded? | "New ADR 0006 (Recommended)" |
