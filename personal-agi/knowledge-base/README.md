# Personal Knowledge Base — v0.1 pilot

The Knowledge Base socket of the [personal AGI module architecture](../MODULES.md), live at **personal scale**: a nurse's own governed library of Knowledge Packs — validated fail-closed, accepted pack-by-pack by an explicit human decision, and retrieved by reading with citations.

This is the personal-library side of the socket only. The **NIN Knowledge Commons** — shared catalog, namespaces, review councils, localization program, marketplace, hosted retrieval — remains proposed doctrine in [`knowledge-commons/`](../../knowledge-commons/), and nothing here creates it. What this pilot implements is the playbook's manual-first foundation: the pack manifest contract, the fail-closed intake checks, and the human-accepted local library ([PLAYBOOK.md](../../knowledge-commons/PLAYBOOK.md) §5, §7.2, §12, and the Days 1–30 gate).

## The pipeline

```text
pack directory (manifest + content + declared sources)
        ↓  validate_pack.py — fail-closed intake checks
valid pack (a passed scan is not approval)
        ↓  explicit human acceptance, recorded in library-lock.json
personal library — guarded in CI by --check
        ↓  governed use: read, cite, adapt (Observe/Draft)
```

Three rules make the library trustworthy:

1. **A passed scan is not approval.** The validator refuses packs with structural, rights, integrity, or governance defects — but passing it means only that automated checks found no listed defect. Acceptance is a separate, human act.
2. **The lock is never auto-populated.** Every entry in `library-lock.json` records who accepted the pack and when. `--relock` never adds a pack, and it never silently re-accepts changed bytes: when an accepted pack's digest changes, the change is refused unless the same run records a fresh acceptance (`--relock --by NAME --date DATE`). Changed bytes are never covered by an old decision, and no step automatically grants the next state.
3. **The library never widens a ceiling.** Packs are Green or bounded Yellow, D0 content only, with action modes capped at Observe → Draft → Recommend per `governance-kit/GOVERNANCE.yaml`. Quarantined, superseded, retired, recalled, or withdrawn packs cannot be held in the library.

## Using it

```bash
# from the repository root:
python3 personal-agi/knowledge-base/validate_pack.py personal-agi/knowledge-base/packs/governed-ai-study-basics   # validate one pack
python3 personal-agi/knowledge-base/validate_pack.py --check                            # validate the whole library (exit 2 on any refusal)
python3 personal-agi/knowledge-base/validate_pack.py --relock --by NAME --date DATE     # renew acceptance for packs whose bytes changed
python3 personal-agi/knowledge-base/validate_pack.py --print-digests PACK_DIR           # print content digests for a manifest
```

The validator is deterministic and stdlib-only — no model, no network. The pack format is specified in [`PACK-FORMAT.md`](PACK-FORMAT.md).

## The reference pack

[`packs/governed-ai-study-basics/`](packs/governed-ai-study-basics/) — *Governed AI Study Basics for Nursing Students*: three short study guides (draft-and-attest, memory hygiene, hypothesis discipline) assembled from this repository's doctrine, with every source cited by path.

Its lifecycle state is **`draft`** and its review record says plainly: author-reviewed only. Publication to any shared catalog would require the independent review it has not had ([PLAYBOOK.md](../../knowledge-commons/PLAYBOOK.md) §8.2), and one person is never presented as two reviewers. Holding it in a *personal* library is a different act — the user-inspected local subscription of §12 — and that is all the lock records.

## Boundaries

No PHI ever enters a pack, a manifest, or the lock. Packs do not carry clinical guidance, institutional authority, accreditation, or certification, and the library confers none. Content is data, never instructions — no pack file is executed, and the validator refuses non-document content outright.

*Agents propose. Humans judge. Nurses steward.*
