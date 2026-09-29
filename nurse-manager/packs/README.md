# Packs

A pack is a small, reviewed set of document templates for one part of a
manager's work (build step 5.4). The app shows each pack with who maintains
it and when it is next reviewed. A manager starts a draft from one of its
templates, writes it, and accepts exactly the text they reviewed.

| Pack | Templates |
|---|---|
| `education.json` | Education plan, competency checklist, synthetic case study |
| `committee.json` | Meeting brief, agenda, minutes, and action list; executive brief; policy or procedure draft |
| `communication.json` | Communication plan; email, memo, announcement, or huddle script; presentation or poster outline |

## The manifest

| Field | Rule |
|---|---|
| `schema` | `nurse-manager-pack@1` |
| `id` | The file name without `.json` |
| `title`, `purpose` | Shown to the manager |
| `version` | `major.minor.patch`; recorded with every document started from the pack |
| `maintainer` | Who reviews and updates it, by role |
| `reviewed_on`, `review_by` | Dates; `review_by` comes after `reviewed_on`. After `review_by` the pack is shown as due for review and **starts no new documents** |
| `catalog.schema_version` | The version of `naio-integrations/config/deliverable-templates.json` the pack was reviewed against |
| `templates` | Template id → sha256 of the template's canonical JSON. Templates are reused from that catalog, never copied here |
| `rules` | At least one; printed at the top of every document started from the pack |

The app checks every manifest when it lists packs. A manifest that fails
a check is shown as unavailable with the reason, and is never used.

## Reviewing a pack

1. Read each template in the catalog and the pack's rules.
2. Recompute the pins if a template changed:
   `python3 -c "from nurse_manager.packs import template_sha256, _catalog; c = _catalog(); print({t: template_sha256(c['templates'][t]) for t in ('meeting-pack',)})"`
   (run with `nurse-manager/src` on `PYTHONPATH`).
3. Update `templates`, bump `version`, set `reviewed_on` to today and
   `review_by` to the next review (six months by default), and open a PR.
   `tests/test_packs.py` fails if a pin, a date, or the maintainer is wrong.

Documents already started keep the pack version and template pin they
started from.
