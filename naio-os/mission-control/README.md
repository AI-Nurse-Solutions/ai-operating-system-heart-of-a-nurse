# NAIO Mission Control — MC-1 · MC-2 · MC-3 · the SOUL bridge

The observation plane for Nurse AI OS. Local-only, stdlib-only, read-mostly.

> Agents propose. Humans judge. Nurses steward.
> No PHI. No patient-specific clinical reasoning. No gate approval here.

## Run it

```bash
./naio-mc doctor      # preflight — python, presets, content, runtime, port
./naio-mc start       # → http://127.0.0.1:8321
./naio-mc self-test   # 84 checks, including the ones that matter
./naio-mc verify      # is this tree the one that was packaged?
./naio-mc configure   # point it at your own vault and SOUL files
./naio-mc notes-check # run the Apple Notes bridge once and see what it returns

./bin/naio-soul-import ~/Downloads/naio-soul.json           # dry run
./bin/naio-soul-import ~/Downloads/naio-soul.json --apply   # make it yours
```

No install step, no dependency to fetch. Python 3.10+ and the standard library.

## What is built

| Phase | Deliverable | State |
|---|---|---|
| **MC-1** | Server + DB + Overview & Agents; `hermes_state` + `system_health`; logging skill + `mc-log`; backups | built |
| **MC-2** | Tasks Kanban + Schedule (read-only cron mirror) + Library | built |
| **MC-3** | Memory tab: Obsidian indexer, `memory_watch`, Apple Notes bridge, promotion pipeline | built |
| **MC-4** | Ledger tab | built ahead of schedule — the data was already there |
| **SOUL bridge** | `naio-soul.json` → real content, replacing sample | built |
| **Editing** | set your season; add the credentials that could lapse | built |

All seven tabs are live. `self-test` runs 84 checks and attacks the rules rather than asserting them: it writes a malicious preset, probes for an endpoint that approves a gate, probes for one that schedules cron, kills a collector for real, and checks that promoting to memory left `SOUL.md` untouched byte-for-byte.

```
mission-control/
├── naio-mc                       entry point: doctor · start · backup · self-test · phi-lint
├── mission_control.py            server, schema, collectors, preset loader, PHI lint
├── adapters/runtime.py           HermesAdapter now, FlorenceXAdapter stub for later
├── config.json                   paths and preferences — never a credential
├── roles/*.json                  8 presets — configuration
├── roles/README.md               the preset contract and the one hard rule
├── content/*.sample.json         what fills the configured slots (sample until the SOUL bridge)
├── index.html                    the Stewardship Home — the Overview tab
├── bin/mc-log                    the CLI the logging skill calls
├── bridges/apple_notes.jxa       macOS capture bridge — titles and folders, never bodies
├── demo-workspace/               labelled demo content so the tabs are explorable
├── demo-vault/                   labelled demo vault
├── proposals/                    memory proposals awaiting your approval in the runtime
├── skills/naio-activity-log/     the skill that tells an agent when and how to log
├── tools/rebuild-governance-kit.sh
├── tests/self_test.py
├── mission_control.db            created on first run
└── backups/                      timestamped restore points
```

## Configuration vs content — the split, stated once

This was the open architectural question. The answer:

- **`roles/<id>.json` is configuration.** Which tabs load, which panels render and in what order, which agents start, which credential rows the standing panel tracks, which privacy regimes the risk briefing surfaces. Structure only. It never contains a sentence a nurse would read as being about her.
- **`content/<id>.*.json` is content.** Mission, season, the three actions, domain signals, momentum figures, the standing panel's actual rows. Today these are `*.sample.json` and the UI says so in a banner on every load. When the SOUL bridge lands, real content is generated from `naio-soul.json` plus the collectors, and the sample files become fixtures for tests.

The UI holds neither. It fetches `/api/role/<id>` and renders what it is given — which is why `self-test` asserts the string `const ROLES` no longer appears in `index.html`. That was the fork risk, and it is closed.

## The one hard rule

**A preset may not raise a tier ceiling.** `tier_ceilings` is not a valid key, and the loader rejects any file containing it with an error that names the rail. `licensure` exists so the standing panel knows which credential rows to render — it is never an input to an autonomy decision.

```
$ ./naio-mc check-presets
  ✗ _evil.json: contains 'tier_ceilings'. A preset may not raise a tier ceiling
    (Rail 3; MISSION-CONTROL-ARCHITECTURE §5.4). Ceilings move only by a logged
    decision in governance-kit/GOVERNANCE.yaml.
```

Ceilings move only through a logged decision in `governance-kit/GOVERNANCE.yaml`, per sphere, on demonstrated evidence.

## API

| Method | Path | Notes |
|---|---|---|
| GET | `/api/health` | version, runtime snapshot, system snapshot, collectors, preset errors |
| GET | `/api/roles` | valid presets, plus any that were rejected and why |
| GET | `/api/role/<id>` | `{preset, content, sample}` |
| GET | `/api/agents` | roll-up per `agent_id`: actions, refusals, failures, last seen |
| GET | `/api/activity` | the log, newest first |
| GET | `/api/gates` | pending gates, with a note that this surface does not resolve them |
| GET | `/api/collectors` | per-collector last-ok, runs, failures, stale flag |
| GET | `/api/phi-lint` | detection backstop over dashboard-owned text |
| POST | `/api/activity` | append one row (what `mc-log` calls) |
| POST | `/api/gates` | surface a pending gate |
| GET | `/api/tasks` · POST · PATCH `/api/tasks/<id>` | the Kanban; lanes come from the preset |
| GET | `/api/schedule` | read-only cron mirror, and it says so in the payload |
| GET | `/api/library` | workspace content index — titles and counts, never bodies |
| GET | `/api/memory` | SOUL change history, vault index, Apple Notes inbox |
| POST | `/api/promote` | capture → task · vault Inbox · **memory proposal** |
| POST | `/api/content/<role>` | write your own season, mission, values, and credential rows |
| GET | `/api/soul` | which roles are real, which are still sample |
| GET | `/api/ledger` | gates, tier usage, refusals, status counts, PHI lint |

There is **no** endpoint that approves, declines, or resolves a gate, and **no** endpoint that schedules a cron job. That is not an omission to be filled in later — the gate lives in the runtime channel where the human already is, and moving it here would break Rail 4. `self-test` probes for such an endpoint and fails if one appears.

## The promotion pipeline

The flagship workflow, and the reason MC-3 matters: **capture is only useful if it reliably becomes action or knowledge.**

A note in the vault or the Apple Notes inbox can go three ways:

| → | What happens |
|---|---|
| **task** | a row in the dashboard's own Kanban, stamped with its source |
| **vault Inbox** | a markdown file in your vault, with a link back to where it came from |
| **memory** | a **proposal** in `proposals/` — *not* a memory write |

That third row is the one to read twice. Mission Control does not and cannot write runtime memory. Promoting to memory produces a file that says so on its face and asks you to approve it in the runtime, where the gate lives. The self-test reads `SOUL.md` and `memory.md` before and after a memory promotion and fails if a single byte moved.

Every promotion stamps `promoted_to` on the note, so the Memory tab can answer *"what happened to that idea I jotted down Tuesday?"*

## What this server deliberately cannot do

- approve a gate

- schedule a cron job (it mirrors the schedule read-only, and the test proves no endpoint can)
- write runtime memory (promotion writes a proposal instead)
- persist a note body — the vault and Notes indexes are metadata only
- hold a secret — credentials live in the runtime; the config here is paths and preferences
- raise a tier ceiling

It binds `127.0.0.1` by hard default. `--bind` anything else and it prints a warning explaining that you are removing the only control that made having no authentication safe.

## Collectors

Six, one thread each, fault-isolated:

| Collector | Interval | What it reads |
|---|---|---|
| `hermes_state` | 30s | runtime gateway, sessions, cron mirror, provider posture (never the key) |
| `system_health` | 30s | CPU, RAM, disk, DB sizes; runs retention |
| `content_index` | 60s | workspace markdown — titles, types, word counts |
| `memory_watch` | 60s | SOUL / memory files — that they changed and by how much, never the diff |
| `obsidian_index` | 5m | vault titles, folders, tags, mtimes — never bodies |
| `apple_notes` | 15m | macOS JXA bridge, configured folders, titles only |

A collector that throws records its error, increments a failure count, and keeps its schedule; the server never notices. Anything whose last success is older than three minutes shows a **stale** badge in the footer strip. A collector with nothing to do on this machine reports **inactive** rather than failed — `apple_notes` on Linux is not a bug. `agent_logs` and `runtime_snapshots` auto-prune after 90 days. **`gate_events` are ledger-grade and never auto-pruned.**

## PHI lint

A detection control backstopping the policy control. It scans dashboard-owned text — task titles and bodies, log tasks and details, content titles — for MRN shapes, SSN shapes, date-of-birth formats, room and bed numbers, and explicit DOB labels.

```bash
./naio-mc phi-lint     # non-zero if anything is found
```

It is a backstop, not permission. The rule is still the rule.

## Backups

`./naio-mc backup` writes a timestamped copy of `index.html` and the database into `backups/`. Take one before you let anything modify the dashboard. Agents will eventually clobber a file you cared about; a restore point turns that from an incident into an inconvenience.

## Configure it for your own machine

`config.json` ships pointing at `demo-workspace/` and `demo-vault/` so every tab has something to show. Repoint it:

```json
{
  "content_root": "~/NAIO/workspace/content",
  "vault_root":   "~/Obsidian/NurseVault",
  "vault_inbox":  "Inbox",
  "soul_files":   ["~/.hermes/SOUL.md", "~/.hermes/memory.md"],
  "apple_notes_folders": ["Capture", "Shift notes"]
}
```

Paths and preferences only. No credential belongs in this file, and nothing reads one.

The Apple Notes bridge is **macOS only** and indexes only the folders you list. It was written but **not executed on a Mac** — it is honest about that rather than claiming a green test it does not have. On any other platform the collector reports `inactive`, not `failed`, because having nothing to do is not a fault.

Settle it yourself in one command, before you point anything at it:

```bash
./naio-mc notes-check "Inbox" "Shift Notes"
```

It runs the bridge once, writes nothing, and tells you what actually happened — including when macOS refuses the automation request, which it will the first time. On success it prints the folder, title, and date of the first few notes so you can see for yourself that no note body came back. If a body ever does, it fails loudly and tells you not to index Notes until that is fixed.

The suite guards the same rule statically: it reads `bridges/apple_notes.jxa`, strips the comments, and fails if any line asks Notes for a body. That check runs on every platform, including the ones where the bridge cannot.

## The SOUL bridge

`bin/naio-soul-import` turns the nurse's own `naio-soul.json` — exported by the SOUL Quiz, in her browser, never uploaded — into real content, replacing the sample files for that role.

**The schema follows the quiz, not the other way round.** `schema/naio-soul.schema.json` was derived from what `soul-quiz.html` actually emits (`buildOsConfig`), so the bridge honours the file that already exists rather than inventing a format and asking the quiz to change.

Two refusals, before anything is read for content:

1. **A soul file that does not confirm both hard boundaries** — no PHI, no patient-specific clinical reasoning. The quiz will not export one; if it was hand-edited, this refuses it.
2. **Anything PHI-shaped in any free-text field.** Nothing is written, and the offending field is named.

Dry run is the default. `--apply` writes three files:

| File | What it holds |
|---|---|
| `content/<role>.json` | the nurse's own mission, values, spheres, voice, boundaries |
| `governance/tier-ceilings.json` | **her autonomy decision, per sphere** |
| `governance/soul-import-record.json` | what was imported, what was mapped, what is still needed |

### Ceilings go to governance, never to a preset

The soul file carries `tier_ceilings` — and a *preset* carrying that key is rejected outright. That is not a contradiction; it is the whole rule. **A ceiling is the nurse's own logged decision, not a setting we ship.** The importer routes it to `governance/`, and the test suite re-validates every preset afterwards to prove none of it leaked.

### What the bridge will not do

It will not invent numbers. A soul file says who you are. It does not know where your attention went last month, when your ACLS expires, or what your three actions should be today. So the imported content carries `share: null`, empty actions, and an explicit `needs` list — and **the UI renders that as "not measured yet", never as a plausible fiction.**

The banner has three honest states: *sample content*, *your content — with what is still needed named*, and *everything here is measured*. The test suite asserts that imported content contains no numbers at all.

### One vocabulary, end to end

`soul-quiz.html` now offers all eight roles, and emits the **same ids the presets use**. Quiz and preset system share one list, built from one array in the page so the two cannot drift:

| The quiz asks | It emits | The preset it loads |
|---|---|---|
| Nursing student | `student` | `roles/student.json` |
| Staff nurse — bedside / clinical | `bedside` | `roles/bedside.json` |
| Charge nurse / coordinator | `charge` | `roles/charge.json` |
| Nurse educator / faculty | `educator` | `roles/educator.json` |
| Nurse manager / leader | `leader` | `roles/leader.json` |
| Nurse practitioner / APRN | `np` | `roles/np.json` |
| Resident physician (MD / DO) | `resident` | `roles/resident.json` |
| Nurse entrepreneur / side-gig builder | `entrepreneur` | `roles/entrepreneur.json` |
| Something else — I will pick a role later | `other` | defaults to `bedside`, and says so |

The importer no longer guesses for any of the eight. `schema_version` moved to **1.1.0**; a **1.0.0** file exported before this still imports — `staff` maps to `bedside` and the importer tells you it did, rather than silently rewriting your history.

The quiz page also now explains what a role decides, under the question: which panels load, which credentials your standing is tracked against, and which boundary is surfaced first — **and that it never changes how much your agent may do without you.**

## Editing your own content

Two fields a soul file cannot know: what season you are in, and what expires. Both are editable in the Overview tab and written through to `content/<role>.json`.

Three rules the endpoint enforces:

1. **Sample content is never edited in place.** Editing a role still on sample creates a fresh *empty* real file rather than promoting demo data to look like yours.
2. **Only fields a person knows about themselves are writable** — season, mission, values, and credential rows. There is no way to write a measured number through this endpoint, and the test proves a `license.days` patch is rejected.
3. **The PHI lint runs before the write, not after.** A season containing something MRN-shaped is refused with the field named, and nothing lands.

Setting a season removes "season" from the still-needed list, and the banner updates. That list shrinks as the screen becomes true.

## Pointing it at your own files

If you unzipped the [Starter Kit](https://nurse-ai-os.org/start-here.html), the layout is already known — so it is one flag, not four:

```bash
./naio-mc configure --kit ~/My-Nurse-AI-OS            # dry run: shows what it would wire
./naio-mc configure --kit ~/My-Nurse-AI-OS --apply
```

That sets the vault to the kit, the Library to `04-Projects/`, the capture inbox to `03-Memory/inbox/`, and watches every real file in `01-SOUL/` — skipping the `.template.md` files, because a template is not a soul.

It refuses a folder that is not actually a kit rather than configuring nonsense and failing confusingly three screens later. If `01-SOUL/` holds only templates it says so, wires everything else, and tells you to go take the quiz.

Or set them individually:

```bash
./naio-mc configure                                   # show what it is set to now
./naio-mc configure --vault ~/Obsidian/NurseVault \
                    --soul ~/.hermes/SOUL.md          # dry run
./naio-mc configure --vault ~/Obsidian/NurseVault --apply
```

Either way it refuses a path that does not exist, tells you how many files it would index before it indexes any, and **scans filenames for PHI shapes and refuses the whole folder if any match** — naming them, reading no bodies, writing nothing. A vault with `handoff MRN 4471902.md` in it does not get connected by accident.

## Verifying what you are running

```bash
./naio-mc verify
```

`tools/release.py` builds `manifest.json` — a sha256 of every tracked file, the version, and the self-test result **captured at the moment of packaging**. `verify` recomputes and reports drift, separating two cases: code that changed since packaging (a failure, named file by file) and files you are meant to edit like `config.json` and `content/` (expected, reported as such).

**Mission Control is not signed, and it says so in three places** — the manifest, the command output, and here. Checksums prove this tree is unchanged since packaging. They are not provenance, and pretending otherwise is exactly the claim this project keeps refusing to make.

Note the asymmetry, because it cuts both ways: `naio-os` itself *is* signed, and has been since Phase 6 — `manifest.sig`, `release-history.json`, and a fail-closed verifier that refuses a release it cannot verify. Mission Control ships inside that tree without yet participating in that chain. There is no Mission Control release key, so `manifest.json` records `"signed": false` and every surface repeats it. Reading "not signed" here as a statement about naio-os would be just as wrong as reading naio-os's signature as covering Mission Control. Bringing Mission Control under the existing chain is the obvious next step, and it is not done.

### Why this exists

This README once said "56/56" while the suite ran 65. Nobody lied; a number was transcribed by hand into prose and the code moved on. `release.py` now runs the tests, writes the count into the docs, and hashes the tree — in that order, in one command. The claim and the artifact are produced together, so they cannot drift apart again.

## Not yet built

- The quiz's four-role vocabulary (above) — the bridge works, but it is mapping down from eight to four.
- Collector-derived content: seasons, actions, domain shares, and standing rows still come from you rather than from observation.
