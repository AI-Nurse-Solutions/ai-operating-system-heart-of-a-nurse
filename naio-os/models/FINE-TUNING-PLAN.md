---
title: "NAIO Fine-Tuning Plan"
status: "Proposed engineering plan"
version: "0.1"
applicability: "Design record. Publication activates no model, no training run, no dataset, no hosted service, no clinical validation, and no PHI processing."
trained_against: "edena-policy@2.0.0 · florence-x@2.0.0"
---

# NAIO Fine-Tuning Plan

## 1. What this document is

A tightened version of the "family of role-specific adapters" proposal. The
original direction is sound — do not build one general-purpose nursing chatbot —
but as drafted it could not be executed, because it named no base model, no
hardware, no dataset size, no authoring budget, no release threshold, and it
classified against a governance vocabulary this repository does not implement.

This document keeps the architecture and fixes those five things. Where it
disagrees with the draft it says so and says why.

## 2. Honest applicability

Publication of this plan does not create a model, a training corpus, a hosted
endpoint, an institutional authorization, a clinical validation, a regulatory
clearance, or a PHI-processing capability. Nothing here raises a tier ceiling,
weakens a human gate, or amends `naio-os/config/edena-policy.yaml`. Any model
produced under this plan is a **capability**, replaceable at any time, subject to
the same policy the runtime already enforces on every turn.

## 3. The correction that matters most

The draft proposed training a classifier to emit:

```yaml
data_class: D0|D1|D2|D3|D4
edena_tier: Green|Yellow|Orange|Red-P|Red-E
```

Neither vocabulary exists. `edena-policy.yaml` v2.0.0 defines four tiers —
`green`, `yellow`, `orange`, `red` — and no `D0–D4` data taxonomy anywhere in
this repository. Training a model to speak a governance language the runtime
cannot enforce manufactures a **phantom control**: output that looks like
governance, that reviewers will read as governance, and that nothing checks.

Worse, a single `edena_tier` field re-collapses precisely what policy v2 exists
to separate. Its stated design principle:

> agency and autonomy are DIFFERENT LEVERS … A tier governs AUTONOMY ONLY.
> FUNCTIONALITY (which tools load) and PERMISSIONS (what those tools may touch)
> are scoped INDEPENDENTLY … Never collapse the three.

A model that emits one tier and calls it a classification has collapsed all
three. Add reversibility — a cross-cutting class that can *override* the tier,
where "the STRONGER gate wins" — and one scalar cannot carry the decision.

**So: the model does not classify. The policy engine classifies.**

The correct division of labor:

| Component | Owns | Nature |
|---|---|---|
| `edena-policy.yaml` + evaluator | tier ceiling, tool class, permission scope, reversibility, resulting gate | deterministic, testable, versioned |
| Fine-tuned model | reading the nurse's request into the *inputs* that evaluator needs, and writing the rationale a human can audit | learned, fallible, reviewable |
| Human | the judgment at the gate | accountable |

The model proposes `sphere`, `intended action`, `tool classes touched`,
`reversibility`, `hard boundaries implicated`, and a rationale citing the policy
clause. A deterministic evaluator reads `edena-policy.yaml` and computes the
gate. If the model is wrong, the engine still holds, because hard boundaries are
enforced at the harness layer before tier logic runs.

This single change converts the highest-risk item in the plan (item 2, the
triage classifier) from a safety control that could fail silently into a
**retrieval-and-justification** task whose worst failure is a bad proposal a
human reads. That is the difference between a shippable v0.1 and one that should
not ship.

Corollaries:

- **Refusal is not a model safety control.** `hard_boundaries` are enforced
  before the model's opinion is consulted. Train refusal quality as user
  experience — a clean, non-alarmist, useful redirect — never as the mechanism.
- **Structured output should be enforced, not learned.** Every YAML/JSON surface
  in this plan runs under constrained decoding (llama.cpp GBNF, or guided
  decoding server-side). Schema validity then becomes 100% by construction, and
  the fine-tuning budget buys *content* quality instead of brace-matching.
- **Doctrine goes in retrieval, not weights.** A model that memorizes
  `edena-policy@2.0.0` will confidently assert it after the policy moves to 2.1.
  Every released model records `trained_against`, and the runtime warns on
  mismatch. This is what `policy_version_pinned_in_export` already implies for
  souls; models inherit it.

## 4. Gate zero: prove fine-tuning is needed

The plan currently assumes fine-tuning. Before any training run, run a two-week
bake-off on the frozen evaluation set (§8):

1. Base model + system prompt + 8 few-shot examples + constrained decoding.
2. The same, plus retrieval over `edena-policy.yaml` and the role presets.

If (2) clears the release gates, **ship the prompted baseline and stop.** It is
cheaper, has no corpus to maintain, no stale-doctrine risk, and no artifact to
sign. Fine-tune only what the baseline demonstrably misses, and record the
margin — §8 gate 6 requires a ≥15-point absolute win on the primary metric to
justify the ongoing cost of a trained artifact.

This gate is not a formality. On structured-extraction tasks with a good schema,
prompted baselines frequently win.

## 5. Scope: ten directions, cut to two and a half

Nine adapters means nine corpora, nine eval sets, nine version lines, and N×M
interaction bugs — before considering that llama.cpp and Ollama, the local
runtimes this project actually targets, do not hot-swap LoRA adapters cleanly.
Each merged role model is a full-size GGUF on a nurse's laptop.

| # | Draft direction | Disposition | Why |
|---|---|---|---|
| 3 | Workflow specification | **v0.1 — primary** | Narrow, schema-bounded, non-PHI, immediately useful, easy to evaluate |
| 2 | EDENA triage | **v0.1 — as justification, not classification** | See §3; the engine decides, the model explains |
| 9 | Embedding / reranker | **v0.1 — parallel track** | Cheapest, lowest-risk, independently useful; generic embeddings genuinely do fail on governance relevance |
| 1 | Core stewardship posture | Fold into system prompt now; DPO on the v0.1 model later | Posture is a prompt problem until you have real failures to prefer against |
| 5 | Output evaluator | Deterministic validators + rubric harness now; model later | Training an evaluator on the same authored corpus as the generator gives correlated errors — it will pass what the generator gets wrong |
| 4 | Critical-thinking partner | v0.2, via DPO on harvested outputs | Needs real rejected samples, not strawmen (§7) |
| 8 | Tool-calling / permissions | Deferred | Blocked on a stable tool surface; and it is a constrained-decoding plus policy-engine problem, not a weights problem |
| 7 | Career coach | Not a fine-tuning problem | Prompt plus retrieval over the existing role packs |
| 6 | Gold Moment structurer | **Cut from v0.1** | No corpus, no schema, and no consent path exists in this repository. Build the schema and the consented capture path first; a training plan for data that does not exist is not a plan |
| 10 | Multilingual / cultural packs | Deferred behind a reviewer community | Each pack multiplies evaluation cost by the number of languages, and an unreviewed pack is worse than none |

**v0.1 ships one merged multi-task model**, not an adapter family: a single base
plus a `role:` tag in the system prompt covering spec-writing and
triage-justification, trained from one corpus with task labels. One GGUF, one
signature, one eval set, one version line. Split into separate adapters only when
a measured per-task regression proves the tasks are fighting each other — and
serve multi-adapter setups from a server runtime (vLLM multi-LoRA), never from a
nurse's laptop.

## 6. The corpus is the project

The draft never says who writes the examples. That is the entire critical path;
GPUs are not the bottleneck.

| Slice | Count | Authorship |
|---|---|---|
| Workflow specification | 600–900 | ≥3 nurses, each example reviewed by a second |
| Triage justification | 400–600 | Same, plus one governance reviewer |
| Frozen evaluation set | 150 | Authored **before** training, sealed, never trained on |
| Adversarial / injection suite | 40 | Authored by someone who did not write the training slices |

At roughly twelve minutes per example including review, 1,500 examples is about
**300 person-hours**. Budget it explicitly or the project stalls at week three.

Rules on the corpus:

- Non-PHI only, enforced mechanically. `naio-os/models/lint_dataset.py` imports
  `PHI_PATTERNS` from `naio-os/mission-control/adapters/phi.py` — the same list
  the server lint, the SOUL importer, and `naio-mc configure` use — so the
  dataset gate cannot drift from the runtime gate. It is detection, not proof;
  it never substitutes for the reviewer's read.
- Every record carries governance metadata and validates against
  `schema/training-example.schema.json`, whose enums are drawn from
  `edena-policy.yaml` rather than invented.
- Synthetic examples are permitted and labelled `synthetic`; unreviewed
  synthetic examples are not.
- The evaluation set is authored first and sealed. No-peek is a process rule
  with a hash in the model card, not a good intention.

## 7. Method sequence

**SFT with QLoRA first. Nothing else in v0.1.**

Then, and only then, DPO — but on pairs harvested from your own SFT checkpoint,
not hand-written. The draft's example pair ("That sounds like an excellent plan"
versus a probing question) teaches the model to avoid a strawman it would never
have produced. Real preference data comes from sampling k=4 completions from the
v0.1 checkpoint on held-out prompts and having nurses rank them. Roughly 300–500
harvested pairs beats several thousand authored ones.

GRPO stays out until a reward is genuinely programmatic — valid schema, correct
tool selected, no unauthorized call, task completed. On today's surface that
reward would be mostly a schema check that constrained decoding already
guarantees, so it would optimize nothing.

Continued pretraining: not justified. The corpus is far too small, and domain
vocabulary is not the observed failure mode.

## 8. Concrete training configuration

Starting point, to be adjusted from the first run's curves:

- **Base:** an Apache-2.0 8B-class instruct model (e.g. Qwen3-8B) for the
  primary build, plus a 4B-class sibling for low-end laptops. Prefer Apache-2.0
  over a community-licensed base: this project signs and redistributes artifacts
  (`installer_contract.signed_artifacts`, `manifest.sig`), and a redistribution
  clause with naming obligations is a legal review you do not need. Record the
  base's license in `THIRD_PARTY_NOTICES.md` before the first run.
- **Method:** QLoRA over a prequantized 4-bit base (`unsloth/…-bnb-4bit`).
- **LoRA:** r=16, alpha=16, dropout 0, target `q,k,v,o,gate,up,down`.
- **Optimization:** lr 2e-4 SFT / 5e-6 DPO, cosine schedule, 2–3 epochs, batch 2
  × grad-accum 8, max_seq_len 4096, packing off (chat data), gradient
  checkpointing in Unsloth's mode, fixed seed and logged — `florence-x` requires
  reproducibility, so an unlogged seed is a defect.
- **Loss masking:** train on responses only. Loss on the prompt is the single
  most common cause of a model that parrots the instruction back.
- **Hardware:** one 24 GB consumer card is sufficient. An 8B at r=16 on ~1,500
  examples runs in well under an hour, which means the useful cadence is several
  runs per day, not one per week. Verify Unsloth's current multi-GPU support
  before planning any multi-GPU run; assume single-GPU until measured.
- **Export:** merge to 16-bit, then quantize to GGUF (`Q4_K_M` for laptops,
  `Q8_0` for the reference build). Note that QLoRA-then-merge loses a little
  against LoRA over fp16; measure it, do not assume it away.

Treat "2× faster, 70% less VRAM" as vendor marketing. The only numbers that
matter are whether one run fits your card and finishes between two coffees.

## 9. Release gates

Fourteen metrics gate nothing. Six with thresholds do. Every gate is measured on
the sealed evaluation set, and every gate blocks release.

| # | Gate | Threshold |
|---|---|---|
| 1 | Schema validity | 100%. Under constrained decoding anything less is a decoder bug, not a model result |
| 2 | Gate under-proposal — model proposes a weaker human gate than the policy engine computes | ≤2%, and any single instance touching a hard boundary blocks release pending review |
| 3 | Unsupported-claim rate on the grounded slice | ≤5%, scored by two nurse reviewers, inter-rater agreement reported |
| 4 | Indirect prompt injection | 0 successes on the 40-case suite. A model trained to follow structure obediently is *more* injectable, not less — `florence-x.memory_integrity` treats retrieved content as data, and the model must too |
| 5 | Export parity | 100 prompts through the training runtime and through the exported GGUF in the actual local runtime: identical schema validity, ≥95% field agreement. Chat-template drift between training and serving is the most common way a good model ships broken |
| 6 | Beats the prompted baseline | ≥15 points absolute on the primary task metric, no regression on gates 1–5. Otherwise ship the baseline (§4) |

Latency, memory, and cost are recorded on the model card but do not gate.

Note what gate 2 measures and what it does not: because the policy engine is
deterministic and hard boundaries are enforced at the harness layer, a model
error cannot itself produce a tier violation. It produces a bad proposal shown to
a human. Measuring it as though it were a safety control would overstate both the
risk and the model's authority.

## 10. Release artifact

Every release ships:

- The GGUF and its checksum, signed through the existing signing path.
- A model card recording: base model and license, corpus version and record
  count, the sealed eval-set hash, `trained_against: edena-policy@<version>`,
  every gate result with its threshold, the training seed, and known failure
  modes stated plainly.
- The exact system prompt and chat template used at evaluation. A model
  evaluated under one template and served under another has not been evaluated.
- A rollback path: the previous release stays installable, and a policy-version
  mismatch warns rather than silently proceeding.

## 11. First four weeks

| Week | Work |
|---|---|
| 1 | Author and seal the 150-example evaluation set and the 40-case injection suite. Nothing else. |
| 2 | Build the deterministic policy evaluator over `edena-policy.yaml` and the GBNF/JSON schemas. Run the prompted baseline against the sealed set. |
| 3 | Decision point: baseline passes → ship it and stop. Baseline fails → begin corpus authoring against the measured gaps only. |
| 4 | First QLoRA run, export, and export-parity check. Expect to discover the corpus is the constraint. |

The reranker track runs in parallel from week 1 and is independent of this
decision.

## 12. Open questions

These block specific work and are the author's to answer:

1. Who are the three nurse authors and the governance reviewer, and how many
   hours per week do they have? (Blocks §6 entirely.)
2. Does a `D0–D4` data taxonomy belong in `edena-policy.yaml`? If yes it is a
   governance change through the normal channel, made *before* any corpus cites
   it. If no, the plan uses sphere plus hard boundaries plus reversibility, which
   is what the runtime enforces today.
3. Is the target runtime Hermes-with-Ollama, llama.cpp directly, or both?
   Gate 5 cannot be written until this is fixed.
4. What is the Gold Moment consent path? Until it exists, item 6 stays cut.

## 13. What this plan refuses

Consistent with `edena-policy.hard_boundaries`, no model produced under this plan
diagnoses, prescribes, triages an identified patient, generates patient-specific
handoffs, touches an EHR, or makes staffing, employment, credentialing, or
academic-progression decisions. Fine-tuning cannot enforce access control,
prevent data egress, revoke a credential, or confer institutional authority.
Those are runtime and governance functions, and they remain so.

> Agents propose. Humans judge. Nurses steward.
