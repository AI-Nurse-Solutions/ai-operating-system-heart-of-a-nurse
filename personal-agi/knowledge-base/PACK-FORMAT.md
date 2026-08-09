# Knowledge Pack format — personal pilot v0.1

The pilot's pack contract is a bounded subset of the Commons manifest specified in [`knowledge-commons/PLAYBOOK.md`](../../knowledge-commons/PLAYBOOK.md) §5. Every pack is a directory:

```text
packs/<pack-id>/
├── pack.json      # the manifest — all twelve groups, defined below
└── content/       # markdown documents only; every file listed in integrity.files
```

Nothing else may appear in a pack directory. The validator refuses unexpected entries, non-markdown content, and files present on disk but missing from the inventory (or listed but missing from disk).

## The twelve manifest groups

`pack.json` must carry all twelve groups from the playbook, as objects. The pilot's required fields per group:

| Group | Required in the pilot |
|---|---|
| `identity` | `id` (lowercase slug, must equal the directory name), `title`, `version` (`MAJOR.MINOR.PATCH`), `state` (a playbook §7.3 triage state) |
| `people` | `creator` |
| `purpose` | `lane` (`learn` / `practice` / `lead` / `build`), non-empty `intended_use` and `prohibited_use` lists |
| `context` | `languages` (non-empty list) |
| `governance` | `edena_tier` (`green` or `yellow`; Orange is held, Red is refused), `data_class` (`"D0"` — the public pack ceiling, PLAYBOOK.md §18), `action_modes` (subset of `observe` / `draft` / `recommend`), `no_phi_attested: true`, `accountable_human`, non-empty `stop_conditions` |
| `evidence` | non-empty `sources` (each with `title` and a repo-relative `path` that resolves, or a `url`), `limitations` (non-empty list), `review_due` (ISO date) |
| `review` | `status`, `independent_review` (an honest statement — never claim review that did not happen) |
| `rights` | `license` (explicitly declared per pack — never inherited from repository documentation), `third_party` list (may be empty) |
| `integrity` | `files`: map of `content/...` path → SHA-256 digest, covering every content file exactly |
| `lifecycle` | `created` (ISO date) |
| `relationships` | present (may be empty) |
| `ai_disclosure` | `assisted` (boolean); when `true`, a non-empty `human_verification` statement |

Deferred to the Commons implementation (not part of this pilot): package signatures, catalog entries, review-record schemas, localization records, `graph/` entity–relation–claim files, `index/` derivatives, and marketplace fields.

## Governance rules the validator enforces

- **Tier ceiling.** `green` and `yellow` validate. `orange` is refused with a hold message (PLAYBOOK.md §8.4 — never down-classified). `red-p` and `red-e` are refused outright.
- **Data ceiling.** Pack content is published, shareable material: `D0` only. Personal working notes with D1 context belong in the memory fabric, not in a pack.
- **Action ceiling.** `observe`, `draft`, `recommend` — the public kit ceiling per `governance-kit/GOVERNANCE.yaml`. A pack cannot grant a wider mode than the core allows.
- **Integrity.** Digest mismatches are refused as stale: no review or acceptance may silently follow changing bytes. Regenerate digests with `--print-digests` and re-inspect before re-accepting.
- **No-PHI.** `no_phi_attested` must be `true`, and content is additionally screened for obvious identifier markers. The scan is a backstop, not a substitute for the attestation.
- **Review expiration is a human duty.** The validator checks that `review_due` is a well-formed date; watching it come due belongs to the monthly memory review, not to CI.

## The library lock

`library-lock.json` is the personal library: the packs a human explicitly accepted, pinned by manifest digest.

```json
{
  "contract": "personal-library-lock v0.1",
  "packs": [
    {
      "id": "<pack-id>",
      "version": "<version at acceptance>",
      "path": "packs/<pack-id>",
      "manifest_sha256": "<sha256 of pack.json>",
      "accepted_by": "<the human who accepted it>",
      "accepted_date": "<ISO date>",
      "state_at_acceptance": "<triage state when accepted>"
    }
  ]
}
```

Because the manifest pins every content digest and the lock pins the manifest digest, an accepted pack is pinned byte-for-byte. `--check` validates every pack in `packs/` (accepted or not) and every lock entry; packs in a removal state — `quarantined`, `superseded`, `retired`, `recalled`, `withdrawn` — are refused as library members per PLAYBOOK.md §11.7.

*Agents propose. Humans judge. Nurses steward.*
