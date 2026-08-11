# NAIO Mission Control — Architecture Blueprint

> *Carry the lamp. Keep the ledger. Now watch the lamp burn.*
>
> **Version:** 0.1 (draft for review) · **Date:** 2026-07-19 · **Author:** Robert Domondon / Nurse AI OS
> **Status:** Proposed architecture — nothing in this document mutates a running Hermes install.

---

## 1. What this is

NAIO Mission Control is the **observation and command deck for Nurse AI OS** — a local desktop dashboard that gives any nurse a single window into what their governed AI agent(s) are doing, what they've produced, what's scheduled, and what's waiting on human judgment.

It is the fourth plane of the NAIO architecture. The existing NAIO spec defines three:

- **Control plane** — what is *allowed* (EDENA tiers, Florence-X doctrine, human gates)
- **Cognition plane** — how *thinking* happens (harnesses, memory, model routing)
- **Execution plane** — how *work* gets done (skills, agents, cron rituals)

Mission Control adds the **Observation plane** — how the nurse *sees and steers* all of the above. It is deliberately thin: it reads what the other planes already produce and writes only to its own small database. It can *surface* a human gate; it never *bypasses* one.

**Doctrine carried forward:** Agents propose. Humans judge. Nurses steward. No PHI, no patient-specific clinical decisions, no replacement for licensed judgment — at every tier, on every tab.

### 1.1 Why a nurse needs this (the problem)

Most AI setups are a black box: a prompt goes in, something comes back, and the nurse has no idea what happened in between — which model ran, what it touched, what it saved, what it's scheduled to do at 3 a.m. For a *governed* OS that is unacceptable. EDENA's evidence trail and Florence-X's "verify before claim" only mean something if the nurse can actually *see* the evidence without SSH-ing into anything.

Mission Control is also the **jumping-off point for personalization**: the same dashboard reshapes itself around the roles a nurse holds (bedside, charge, educator, student, entrepreneur, leader), driven by the SOUL Quiz output that NAIO already produces.

---

## 2. Design principles

1. **Local-first, laptop-first.** V1 is a desktop/laptop install (macOS first — required for Apple Notes; Windows/Linux follow without the Notes bridge). No VPS required. Everything binds to `127.0.0.1` only. Optional Tailscale later for phone access — never a public port.
2. **Runs light.** One small Python server (stdlib + SQLite), one `index.html`. No Node toolchain, no build step, no ORM, no framework to maintain. A nurse's aging MacBook should not notice it's running.
3. **Read-mostly.** The dashboard *observes* Hermes; it does not become a second brain-stem. Its only writes are to its own SQLite file (tasks, note index, settings, gate acknowledgments) and, through explicit user action, promotions into the Obsidian vault.
4. **Solo agent now, team-shaped from day one.** Every table, log line, and UI card is keyed by `agent_id`, even while there is exactly one agent (Florence). When specialist agents arrive, they appear — no schema migration, no redesign.
5. **Personalization is configuration, not code.** **Roles** are JSON presets that select tabs, cards, and starter agents. New roles are added by writing a preset, not by forking the dashboard.
6. **Everything auditable, nothing autonomous.** The dashboard displays cron rituals; it does not schedule them. It displays gate requests; the approval still happens in the Hermes channel (Telegram/terminal) where the gate lives. It versions and backs itself up before any self-modification.
7. **Runtime-agnostic core.** Hermes Agent is the runtime today; **Florence-X as a native runtime is a future target**. All runtime touchpoints go through one adapter module so swapping runtimes is a one-file change (see §7.1).

---

## 3. System overview

```
                         ┌────────────────────────────────────────────────┐
                         │            NURSE (licensed human)               │
                         │   Telegram app · Terminal · Browser (dashboard) │
                         └────────┬───────────────┬───────────────┬───────┘
                                  │               │               │
                     chat + gates │      TUI/CLI  │      observe  │ HTTP (localhost only)
                                  ▼               ▼               ▼
┌──────────────────────────────────────────────┐   ┌──────────────────────────────────────┐
│         HERMES DESKTOP (runtime)              │   │   NAIO MISSION CONTROL (this system) │
│  ┌────────────────────────────────────────┐  │   │  ┌────────────────────────────────┐  │
│  │ Gateway  ◄── Telegram bot (BotFather,   │  │   │  │  mission_control.py            │  │
│  │            single allowed user ID)      │  │   │  │  Python 3 stdlib HTTP server   │  │
│  ├────────────────────────────────────────┤  │   │  │  127.0.0.1:8321                │  │
│  │ Agent loop: Florence (v1)               │  │   │  ├────────────────────────────────┤  │
│  │  + future: Preceptor · Scholar ·        │  │   │  │  Collectors (read-only pulls)  │  │
│  │    Scribe · Advocate  (see §10)         │  │   │  │  · Hermes adapter   (§7.1)     │  │
│  ├────────────────────────────────────────┤  │   │  │  · Obsidian indexer (§7.5)     │  │
│  │ NAIO control plane overlay              │  │   │  │  · Apple Notes bridge (§7.4)   │  │
│  │  EDENA runtime · human gates ·          │  │   │  │  · System health probe         │  │
│  │  SOUL.md + per-sphere SOUL              │  │   │  ├────────────────────────────────┤  │
│  ├────────────────────────────────────────┤  │   │  │  mission_control.db (SQLite)   │  │
│  │ Workspace folder                        │  │   │  ├────────────────────────────────┤  │
│  │  memory.md · daily logs · content/ ·    │  │   │  │  index.html  (single file UI)  │  │
│  │  cron jobs · session transcripts        │  │   │  └────────────────────────────────┘  │
│  └────────────────────────────────────────┘  │   └──────────────────────────────────────┘
│         │ model API calls                     │                    ▲
│         ▼                                     │                    │ file reads (no writes)
│  OpenRouter ──or── OpenAI                     │        ┌───────────┴───────────┐
│  (API key)        (API key, or ChatGPT        │        │  OBSIDIAN VAULT        │
│                    subscription via Codex     │        │  (markdown on disk —   │
│                    sign-in)                   │        │  NAIO knowledge memory)│
└──────────────────────────────────────────────┘        └────────────────────────┘
                                                          ▲
                                                          │ AppleScript/JXA export (macOS)
                                                        ┌─┴──────────────────────┐
                                                        │  APPLE NOTES            │
                                                        │  (capture inbox)        │
                                                        └────────────────────────┘
```

Key relationships:

- **Hermes is the only component that talks to AI models.** Mission Control never holds a model API key and never sends prompts on its own. (One narrow exception path exists in Phase 4+ — "Ask Florence" deep links that open Telegram or the terminal with a pre-filled prompt; the *runtime* still executes it.)
- **Telegram is the command channel; the dashboard is the map.** You steer in chat, you see the whole battlefield in Mission Control.
- **Apple Notes → capture. Obsidian → keep. Hermes memory → operate.** Three memory layers with explicit, human-approved promotion between them (§7.4–7.6).

---

## 4. Component architecture

### 4.1 Server — `mission_control.py`

A single-process Python 3.11+ application using only the standard library (`http.server`/`socketserver` or a minimal `asyncio` loop, `sqlite3`, `json`, `subprocess`, `plistlib`). No pip installs required for core function.

Responsibilities:

| Concern | Behavior |
|---|---|
| HTTP API | `GET /api/*` endpoints returning JSON for the UI; `POST` only for dashboard-owned data (tasks, note promotions, settings, acknowledgments) |
| Static | Serves `index.html` and `/assets` |
| Collectors | Background thread per collector, each on its own poll interval, each fault-isolated (a dead collector shows a stale badge; it never kills the server) |
| Live tail | Server-Sent Events (`GET /api/events`) streaming new agent-log lines and gateway status changes to the UI — no page refresh |
| Bind | `127.0.0.1` **hard-coded** default; changing it requires an explicit `--bind` flag and prints a red warning |
| Versioning | Semantic version shown in the UI footer; automatic timestamped backup of `index.html` + DB into `backups/` before any self-update (lesson learned the hard way in the source builds: agents *will* eventually clobber your dashboard — always keep a restore point) |

### 4.2 Collectors (the read-only ingest layer)

| Collector | Source | Interval | Writes to |
|---|---|---|---|
| `agent_activity` | Agent log table (agents append via a logging skill, §6.2) | event-driven | `agent_logs` |
| `hermes_state` | Hermes adapter: gateway status, sessions, token usage, cron job list, model config | 30 s | `runtime_snapshots`, `cron_jobs` |
| `content_index` | `workspace/content/<agent>/` markdown files | 60 s | `content_index` |
| `memory_watch` | `SOUL.md`, `memory.md`, per-sphere SOUL files (mtime + diff summary) | 60 s | `memory_events` |
| `obsidian_index` | Vault folder (configurable path) — titles, tags, links, mtimes only | 5 min | `notes_index` |
| `apple_notes` | JXA bridge (macOS only) — configured folders only | 15 min / manual | `notes_index` |
| `system_health` | CPU, RAM, disk, DB sizes, Hermes process up/down | 30 s | `runtime_snapshots` |
| `gate_watch` | Pending human-gate requests surfaced by the runtime | 15 s | `gate_events` |

### 4.3 UI — `index.html` (single file)

Vanilla JS + CSS (a small chart helper may be inlined). Responsive layout so the same page works when reached from a phone over Tailscale later — same interface everywhere, which is what makes managing agents from anywhere possible.

**Tabs (v1):**

1. **Overview** — the "walk past the station and know everything" screen: gateway status, active agent(s), tasks today, errors, tokens/spend estimate, next cron ritual, pending human gates (always visually loudest — gates outrank everything), system health strip, live activity ticker.
2. **Agents** — one card per agent: name, role, EDENA tier ceiling per sphere, model in use, last action, 7-day activity sparkline, success rate. With one agent this is Florence's vitals board; with five it becomes the team roster. A collapsed **Org view** (orchestrator → specialists) ships hidden behind a flag until multi-agent is enabled.
3. **Tasks** — Kanban (To-do / In-progress / Done), each task assignable to *me* or *an agent*. Tasks created here can be dispatched to Hermes as a prompt via deep link (Phase 4). This is the nurse's own tracker, not the agent's internal to-do list.
4. **Schedule** — cron rituals calendar: NAIO stewardship rituals (the lamp, the ledger) plus any agent-created jobs, with next-run times, tier tags, and last-run outcome. Read-only; the "edit" affordance is a copy-able prompt to paste into chat.
5. **Memory** — the three memory layers side by side: Hermes `SOUL.md`/`memory.md` (with change history from `memory_events`), the Obsidian vault index, and the Apple Notes inbox — plus the **promotion buttons** (§7.6). This tab is what makes memory *governed* instead of mysterious.
6. **Library** — every long-form document the agents produce, pulled from `workspace/content/<agent>/`, filterable by agent, date, and type. Agents are instructed (via skill + memory rule) to save long output as dated markdown files here instead of dumping walls of text into chat.
7. **Ledger** — the EDENA evidence trail view: gate events (asked/approved/declined, by whom, when), tier usage over time, boundary refusals, weekly ledger summaries. This is the tab you'd show an educator, a manager, or a skeptic.

**Cross-cutting UI rules:**

- Pending human gates render as a persistent banner on *every* tab until resolved.
- Every number that comes from a collector shows a freshness dot (green <2× interval, amber, red/stale).
- Large numbers truncate (1.2M, 1.3k); sections breathe; version number in the footer.
- A **role switcher** in the header applies the role preset (§5) instantly — no restart.

### 4.4 What Mission Control deliberately does NOT do

- Does not hold model API keys, call OpenRouter/OpenAI, or run prompts.
- Does not schedule, edit, or delete cron jobs.
- Does not approve gates (it *shows* them and deep-links to the channel where approval happens).
- Does not write into `~/.hermes` or the Hermes workspace (single exception: the append-only agent log, and even that is written *by agents through the logging skill*, not by the dashboard).
- Does not store PHI, and runs a PHI-pattern lint on its own DB as a nightly self-check (§8).

---

## 5. Role personalization layer

The same Mission Control serves a new grad, a charge nurse, a professor, and a nurse entrepreneur — because the dashboard is a *shell* and the roles are *presets*.

### 5.1 Where roles come from

The SOUL Quiz already emits `naio-soul.json` (schema-validated, no PHI). Mission Control reads the spheres/roles from that file at install and maps them to one or more **role presets**. A nurse can also toggle roles manually in Settings.

### 5.2 Role preset contract

```json
{
  "role_id": "educator",
  "label": "Educator / Faculty",
  "tabs": ["overview", "agents", "tasks", "schedule", "library", "ledger", "memory"],
  "overview_cards": ["gates", "tasks_today", "next_ritual", "content_recent", "cohort_week"],
  "starter_agents": ["florence", "scholar", "scribe"],
  "task_lanes": ["To-do", "In-progress", "Waiting on students", "Done"],
  "library_filters": ["lesson-plan", "rubric", "handout"],
  "ritual_pack": "educator",
  "tier_note": "Cohort-mode boundaries apply: no certification claims, no auto-scoring."
}
```

### 5.3 Initial role presets (v1 ships all as JSON, dashboard code identical)

| Role | Emphasis on the dashboard |
|---|---|
| **Bedside / Staff nurse** | Shift-friendly overview, personal tasks, knowledge inbox (Notes→Obsidian), CE/study library, wellbeing ritual card |
| **Charge / Coordinator** | Tasks board front and center, schedule tab, checklist-style content, escalation notes |
| **Student / New grad (incl. CCRN path)** | Study pipeline, spaced-repetition ritual card, Scholar agent starter, evidence-of-learning ledger view |
| **Educator / Faculty** | Cohort week card, lesson library, Scribe+Scholar starters, Phase-11 cohort boundaries surfaced |
| **Entrepreneur / Side-gig** | Content pipeline (research→draft→publish), marketing-style library filters, spend-per-token card |
| **Leader / Manager / Informatics** | Ledger tab first-class, adoption/outcomes cards, governance ritual pack, org view enabled early |
| **Nurse practitioner** | Credential-heavy standing panel (APRN, prescriptive authority, DEA, collaborative agreement), pharmacology CME tracking, scope-vs-autonomy note surfaced |
| **MD resident** | Duty-hour attestation and milestone rows, boards/ITE study pipeline, loan-certification deadlines, nursing-authored-doctrine note surfaced |

> **Naming.** These were called "hats" in earlier drafts. They are **roles**: a hat is flimsy and blows away in the wind; a role speaks to the core. The rename is not cosmetic — a role carries standing, accountability, and credentials, which is exactly what the preset now configures.

Adding a role = adding one JSON file + optionally one ritual pack + optionally one starter-agent SOUL template. This is the "jumping point for personalization" requirement made concrete.


### 5.4 The rule a role preset may never break

A preset selects tabs, cards, agents, rituals, and the credential rows a role has to keep current. It **may not raise a tier ceiling**, and no dashboard control exposes one. Scope of practice and agent autonomy are separate axes: an NP preset and a student preset differ in what they *display* and *track*, never in how much the agent may do unreviewed. Ceilings move only through a logged decision in `GOVERNANCE.yaml`, on demonstrated evidence, per sphere. (Rail 3, `DOCTRINE.md`.)

Two presets carry a standing note rendered on the Overview tab, because they address readers the earlier doctrine did not: the **nurse practitioner** preset surfaces *scope is not autonomy*, and the **MD resident** preset surfaces *whose rules these are*. Both are preset content, not code.
---

## 6. Data model (SQLite — `mission_control.db`)

All tables carry `agent_id` from day one (principle 4). Retention jobs keep the DB light: `agent_logs` and `runtime_snapshots` auto-prune after a configurable window (default 90 days; ledger-relevant `gate_events` are **never** auto-pruned).

```sql
-- Every action any agent takes, appended via the logging skill
CREATE TABLE agent_logs (
  id INTEGER PRIMARY KEY,
  ts TEXT NOT NULL,                -- ISO-8601
  agent_id TEXT NOT NULL,          -- 'florence' in v1
  task TEXT NOT NULL,              -- short human-readable action
  detail TEXT,                     -- optional longer note / artifact path
  model TEXT,                      -- model actually used (never 'unknown': the skill requires it)
  status TEXT CHECK(status IN ('completed','failed','refused','in_progress')),
  edena_tier TEXT,                 -- tier the action ran under
  sphere TEXT                      -- SOUL sphere it belongs to
);

-- The nurse's Kanban
CREATE TABLE tasks (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  body TEXT,
  lane TEXT NOT NULL DEFAULT 'todo',
  assignee TEXT NOT NULL DEFAULT 'me',   -- 'me' or an agent_id
  role_id TEXT,
  source TEXT,                     -- 'manual' | 'apple_note:<id>' | 'agent:<id>'
  created_ts TEXT, updated_ts TEXT, done_ts TEXT
);

-- Unified index over Obsidian vault + Apple Notes (metadata only, bodies stay at source)
CREATE TABLE notes_index (
  id INTEGER PRIMARY KEY,
  source TEXT CHECK(source IN ('obsidian','apple_notes')),
  external_id TEXT,                -- vault-relative path, or Notes item id
  title TEXT, folder TEXT, tags TEXT,
  modified_ts TEXT, indexed_ts TEXT,
  promoted_to TEXT                 -- NULL | 'task:<id>' | 'obsidian:<path>' | 'memory'
);

-- Changes observed in SOUL.md / memory.md / sphere files
CREATE TABLE memory_events (
  id INTEGER PRIMARY KEY,
  ts TEXT, file TEXT, change_summary TEXT, diff_lines INTEGER
);

-- Human-gate audit trail (ledger-grade; never auto-pruned)
CREATE TABLE gate_events (
  id INTEGER PRIMARY KEY,
  ts TEXT, agent_id TEXT, sphere TEXT, edena_tier TEXT,
  request TEXT,                    -- what the agent asked to do
  outcome TEXT CHECK(outcome IN ('pending','approved','declined','expired')),
  resolved_ts TEXT, resolved_via TEXT   -- 'telegram' | 'terminal'
);

-- Cron rituals + jobs mirrored from the runtime (read-only mirror)
CREATE TABLE cron_jobs (
  id INTEGER PRIMARY KEY,
  runtime_job_id TEXT, agent_id TEXT, label TEXT,
  schedule TEXT, next_run_ts TEXT, last_run_ts TEXT, last_status TEXT,
  is_naio_ritual INTEGER DEFAULT 0, edena_tier TEXT
);

-- Long-form artifacts in workspace/content/
CREATE TABLE content_index (
  id INTEGER PRIMARY KEY,
  agent_id TEXT, path TEXT UNIQUE, title TEXT, doc_type TEXT,
  created_ts TEXT, modified_ts TEXT, word_count INTEGER
);

-- Rolling health/usage samples
CREATE TABLE runtime_snapshots (
  id INTEGER PRIMARY KEY, ts TEXT,
  gateway_up INTEGER, sessions INTEGER, tokens_in INTEGER, tokens_out INTEGER,
  est_cost_usd REAL, cpu_pct REAL, ram_pct REAL, disk_pct REAL,
  hermes_db_bytes INTEGER, mc_db_bytes INTEGER
);

CREATE TABLE settings ( key TEXT PRIMARY KEY, value TEXT );
```

### 6.2 The logging skill (how rows actually appear)

Agents don't magically log; they are *instructed* to. NAIO ships a tier-tagged `SKILL.md` — `naio-activity-log` — that requires every agent, after every completed/failed/refused task, to append one line to `agent_logs` via a tiny CLI helper (`mc-log <agent> <status> <tier> "<task>" --model <model>`). The instruction also lives in each agent's permanent memory so it survives compaction. The dashboard's Agents tab makes gaps obvious: an agent that worked but didn't log shows a "silent work" warning — which in practice is how you catch instruction drift early.

---

## 7. Integration contracts

### 7.1 Runtime adapter — Hermes today, Florence-X tomorrow

All runtime access goes through `adapters/runtime.py`, a single module exposing:

```
get_gateway_status() · list_agents() · get_model_config() · list_cron_jobs()
get_usage() · list_sessions_meta() · workspace_path() · pending_gates()
```

**HermesAdapter (v1)** implements these against Hermes Desktop's local surfaces: the `~/.hermes` config/workspace folders, its local status endpoints, and its session/usage stores. Where Hermes exposes a local dashboard API, we read it; where it doesn't, we read files. Nothing is written.

**FlorenceXAdapter (future)** implements the same eight calls when Florence-X matures from doctrine (`florence-x.yaml`) into a native runtime. Because the dashboard, DB, and UI only know the adapter interface, swapping the core program is a configuration change — this is the explicit "core program is Hermes, or Florence X in the future" requirement.

### 7.2 Model providers — OpenRouter / OpenAI

Model credentials live **only** in the runtime (Hermes setup flow), never in Mission Control. Supported postures, surfaced read-only on the Agents tab:

| Posture | How | Dashboard shows |
|---|---|---|
| **OpenRouter API key** | Hermes provider config; lets nurses pick cost-appropriate models and set fallbacks | model slug, est. $ per day (from token counts × published rates table) |
| **OpenAI API key** | Hermes provider config | same |
| **ChatGPT subscription (Codex sign-in)** | Hermes's OpenAI-Codex auth flow (sign in with the ChatGPT account; permitted usage of a paid plan) | "subscription" badge instead of $ estimate |

Florence-X model policy (no-PHI posture, evidence-preferring defaults) remains a control-plane concern; the dashboard displays which policy is active so drift is visible.

### 7.3 Telegram

Telegram is the primary conversational channel (BotFather bot, locked to the nurse's Telegram user ID, home channel set — exactly the hardened setup NAIO documents). Mission Control's integration is deliberately shallow:

- Shows gateway/bot up-down and last-message age on Overview.
- Every gate banner and task card has an **"Open in Telegram"** deep link (`tg://` URL to the bot chat) — optionally pre-filling a routed command like `/florence <task title>` once router shortcuts are configured.
- When multi-agent arrives, per-agent routing (`/scout`-style slash commands) appears on agent cards.
- The dashboard never sends Telegram messages itself and never stores the bot token.

### 7.4 Apple Notes (macOS)

Apple Notes is where nurses actually capture things at 2 a.m. — so treat it as the **capture inbox**, not a database.

- **Bridge:** a JXA (JavaScript for Automation) script run via `osascript`, invoked by the `apple_notes` collector. Scope-limited to folders the nurse explicitly selects in Settings (e.g., "NAIO Inbox"); first run triggers the macOS Automation permission prompt for Notes.
- **Reads:** note id, title, folder, and modified date. **No body, ever** — not persisted, and not read transiently either: the JXA bridge never calls `note.body()`, and previews and promotions work from metadata alone. A promoted note carries its title and a link back to the source; the words stay in Notes.
- **Promotions (explicit human click, §7.6):** note → Task, note → Obsidian (written as markdown into an `Inbox/` folder of the vault), note → candidate memory (rendered as a *proposed* `memory.md` addition the nurse pastes/approves in chat — the dashboard never edits Hermes memory directly).
- **Non-macOS:** collector reports "unavailable on this OS"; everything else works.

### 7.5 Obsidian

The Obsidian vault is NAIO's on-demand knowledge memory, and it needs no plugin: **a vault is just markdown on disk.**

- Settings holds the vault path. The `obsidian_index` collector walks it (respecting `.obsidian/` ignores), indexing titles, tags, folder structure, and backlink counts.
- The Memory tab renders the index with an `obsidian://open?vault=...&file=...` deep link per note, so one click lands in the real app.
- Dashboard writes are limited to **new files in `Inbox/`** (Apple Notes promotions and "save this chat artifact to vault" actions). It never edits existing vault notes.
- Because Hermes can read the vault too (on-demand memory per the NAIO component map), the vault becomes the shared knowledge substrate between nurse, dashboard, and agent — with the nurse's file system as the single source of truth.

### 7.6 The memory promotion pipeline (the flagship workflow)

```
Apple Notes (capture)  ──promote──►  Task (Kanban)          [dashboard writes its own DB]
        │
        └──promote──►  Obsidian Inbox/ (keep)               [dashboard writes one new file]
                              │
                              └──propose──►  Hermes memory   [nurse approves in chat;
                                             (operate)        runtime writes memory.md]
```

Each promotion stamps `notes_index.promoted_to`, so the Memory tab can answer "what happened to that idea I jotted down Tuesday?" This pipeline is the single most valuable idea borrowed from the source builds — capture is only useful if it reliably becomes action or knowledge.

### 7.7 Terminal window integration

Two complementary modes, both v1:

- **Launchers:** buttons that open the nurse's real terminal with the right thing running — "Open Hermes chat (TUI)" (`hermes` in Terminal.app via `open`/AppleScript on macOS), "Tail gateway logs," "Run NAIO self-test" (`install.sh --self-test`). The nurse's terminal, not an emulated one — real environment, real keybindings, real trust.
- **Embedded read-only tail:** the Overview activity ticker streams recent gateway/agent log lines over SSE into a terminal-styled panel. Read-only in v1 (an interactive embedded terminal is a Phase 5 candidate via `pty` + xterm.js, flagged off by default because it widens the attack surface).

---

## 8. Security & PHI posture

| Layer | Control |
|---|---|
| Network | `127.0.0.1` bind, hard default, **and the bind is enforced at the request**: every `GET`, `POST` and `PATCH` is refused with 403 unless its `Host` header is the address the server was bound to and it carries no `Origin`. A loopback bind on its own is not a control — it does not stop a page the nurse already has open from POSTing to `http://127.0.0.1:8321`, and it does not stop DNS rebinding, neither of which needs a preflight. There is no auth *because* nothing should be reachable, so those two headers are what makes that true. `--bind` still requires an explicit flag and prints a warning, and adds that one address to the allowed set — enough for the Tailscale path, and nothing wider. |
| Secrets | Zero secrets in Mission Control. Bot tokens, API keys, Codex auth all live in the runtime's credential store. The dashboard's config contains paths and preferences only. |
| PHI | Inherits NAIO hard boundary: no PHI at any tier. Concretely: note bodies are not persisted; a nightly PHI-pattern lint (names+MRN patterns, DOB formats, room-bed patterns) runs over `tasks`, `agent_logs.detail`, and `content_index` titles and raises a red Ledger flag on hits — a *detection* control backstopping the *policy* control. |
| Human gates | Gate approval never moves into the dashboard. Surfacing yes, acting no — preserving the runtime's non-removable gate chain for Green/Yellow. |
| Reversibility | Timestamped backups of `index.html` + DB before self-update; SQLite snapshot on schedule; restore = copy a file back. Aligns with `recovery.py` philosophy: snapshots local, restores explicit. |
| Supply chain | Stdlib-only core keeps the dependency surface near zero. Anything optional (charts) is vendored into the repo, not fetched at runtime. |
| Audit | `gate_events` and ledger views are append-only and excluded from retention pruning. |

---

## 9. Install & run (target UX)

```bash
# Preflight (python3, macOS version, Hermes present, vault path)
naio-mc doctor

# Install into ~/NAIO/mission-control, register launch agent (login item)
naio-mc install --role bedside --vault "~/Obsidian/NurseVault"

# Run (or it just starts at login)
naio-mc start        # → http://127.0.0.1:8321
```

Distributed the NAIO way: carried inside the existing bundle rather than inventing a second update channel.

**Mission Control speaks the signing chain's language; it is not yet signed with its key.** naio-os has been signed since Phase 6, and the parent bundle carries its own checksums and `bootstrap.sh` verification. Mission Control now implements the same contract — detached RSA-SHA256 over `manifest.json`, the same public key, the same fail-closed verifier — but the private half of `naio-os-release-key-2026-06` is not in this repository and must not be, so builds cut here are unsigned and say so. §11 is the two-command step that closes it. Directory layout:

```
~/NAIO/mission-control/
├── mission_control.py      # server + collectors
├── adapters/runtime.py     # Hermes adapter (Florence-X later)
├── bridges/apple_notes.jxa
├── skills/naio-activity-log/SKILL.md
├── bin/mc-log              # tiny CLI the logging skill calls
├── roles/*.json             # role presets
├── index.html              # the whole UI
├── assets/
├── mission_control.db
└── backups/
```

---

## 10. Multi-agent readiness (designed now, enabled later)

When a nurse's roles justify a team, NAIO renders additional agents the same way it renders Florence — each with its own SOUL, workspace, memory, and tier ceiling (no cross-contamination), coordinated by an orchestrator. The nursing-flavored roster template:

| Agent | Role (analog in source builds) | Example duties |
|---|---|---|
| **Florence** | Orchestrator | routing, coordination, weekly ledger, gate discipline |
| **Preceptor** | — (nursing-native) | onboarding help, skill drilling, checklist coaching |
| **Scholar** | Scout / researcher | evidence lookups, CE digests, morning literature cron |
| **Scribe** | Scribe / writer | drafts, handouts, policies-in-plain-language, blog/content |
| **Advocate** | Reach / marketer | community posts, newsletter, outreach (entrepreneur roles) |
| **Builder** | Dev | maintains Mission Control itself, under backup + gate rules |

What's already in place for them: `agent_id` on every table; per-agent Library folders; per-agent activity cards and sparklines; the hidden Org view; router-shortcut display on agent cards; shared-team-awareness as a memory template. Enabling the team is a runtime-side act (create profiles, bind channels) — the dashboard just starts showing more cards. Discord channel-per-agent is a documented optional pattern for team mode; Telegram remains the default single channel.

The full content pipeline (Scholar → Scribe → Advocate, orchestrated hand-offs) maps directly onto the Phase-17 Florence-X Orchestration Preview — intent/context cards visible on the dashboard, automatic hand-offs still deferred per that phase's boundaries.

---

## 11. Bringing Mission Control under the signing chain

Everything below the key is built. What follows is the part that needs a secret
this repository does not have, written down so it is a procedure rather than a
memory.

**Why two levels instead of one.** naio-os's signature covers `manifest.yaml`,
which records a sha256 for every file it ships. Mission Control has 52 files and
re-cuts on its own cadence, so listing them individually would put 52 churning
checksums inside the signed manifest and make every dashboard change a release
event for the whole bundle. Instead the signed manifest carries **one** entry —
`mission-control/manifest.json` — and that file carries the 52. The chain reads:

```
manifest.sig  ──covers──▶  naio-os/manifest.yaml
                                 │  (one entry, one sha256)
                                 ▼
              mission-control/manifest.json
                                 │  (52 entries, one sha256 each)
                                 ▼
                   every Mission Control file
```

Re-cutting Mission Control changes exactly one checksum upstream.

**The procedure.** With the private half of `naio-os-release-key-2026-06`:

```bash
cd naio-os/mission-control
python3 tools/release.py --sign /path/to/naio-os-release-private.pem
```

That runs the self-test, rebuilds `manifest.json`, writes `manifest.sig`, and
then *verifies its own output* against `config/naio-os-release-public.pem` —
a key that produces an unverifiable signature fails there, leaving nothing
behind, rather than shipping. It then prints the entry for the next step.

```bash
cd ../..                      # repo root
# add the printed entry to naio-os/manifest.yaml under `contents:`
naio-os/scripts/compute-checksums.sh
openssl dgst -sha256 -sign /path/to/naio-os-release-private.pem \
  -out naio-os/manifest.sig naio-os/manifest.yaml
sha256sum naio-os/manifest.yaml | awk '{print $1"  manifest.yaml"}' \
  > naio-os/manifest.sha256
# update release.json's manifest.sha256 to match, then:
python3 naio-os/scripts/verify-release.py
```

`python3 tools/release.py --chain-entry` prints the entry on its own at any time.

**Why this is not done here.** Editing `manifest.yaml` invalidates `manifest.sig`,
and `verify-release.py` is fail-closed by design — it refuses a release whose
signature does not verify. A change that added Mission Control to the signed
manifest without re-signing it would take release verification from passing to
failing for everyone, and there is no way to re-sign without the key. So the
mechanism ships and the manifest is left alone. That is the correct trade, not a
shortcut: a chain you cannot verify is worse than an honest gap you can see.

**What a nurse sees in the meantime.** `naio-mc verify` reports the build as
unsigned, in those words, and still passes — the checksums are true and are
worth what they are worth. Nothing in the UI, the manifest, or the docs claims a
provenance that does not exist yet.

## 12. Build roadmap

| Phase | Deliverable | Proof it works |
|---|---|---|
| **MC-1** | Server + DB + Overview & Agents tabs; `hermes_state` + `system_health` collectors; logging skill + `mc-log`; backups | Dashboard shows live gateway status and Florence's logged actions; kill a collector → stale badge, server survives — **BUILT 11 Aug 2026** (`mission-control/`, 25/25 self-test) |
| **MC-2** | Tasks Kanban + Schedule (cron mirror) + Library (content folder convention + agent instructions) — **BUILT 11 Aug 2026** | Create task, assign to agent, dispatch via Telegram deep link; cron rituals visible with next-run times |
| **MC-3** | Memory tab: Obsidian indexer + memory_watch + Apple Notes bridge + promotion pipeline — **BUILT 11 Aug 2026** (JXA bridge written, not yet executed on a Mac) | Jot an Apple Note → promote to task and to vault Inbox → see `promoted_to` trail |
| **MC-4** | Ledger tab (gate_events, tier usage, PHI lint), role presets + role switcher, terminal launchers + SSE tail | Switch roles live; decline a gate in Telegram and see it land in the ledger; PHI lint flags a seeded test string  — **BUILT 11 Aug 2026** (Ledger, ahead of schedule) |
| **MC-5** | Hardening: retention pruning, snapshot/restore drill, `naio-mc doctor`, signed-bundle packaging, responsive/phone polish, optional Tailscale guide | `--self-test`-style smoke harness passes; restore drill from backup succeeds; phone renders over Tailscale |
| **MC-6** | Team enablement kit: multi-agent profiles, org view, router shortcuts, optional Discord channels, Florence-X adapter stub | Second agent appears on dashboard with zero dashboard-code changes |

Each phase follows the Florence-X installer contract: idempotent, preflight-checked, healthchecked, never-claim-unverified, rollback-on-failure.

---

## Appendix A — Idea provenance (what was borrowed, from where)

| Idea adopted | Source | NAIO adaptation |
|---|---|---|
| Personal dashboard tailored to real workflows beats the runtime's built-in one | ByteGrad (OpenClaw MC) | Whole premise; roles make "tailored" systematic |
| Apple Notes → task / → memory promotion | ByteGrad | Formalized into the three-layer promotion pipeline with human approval before memory |
| Memory visibility (memory.md as first-class UI) | ByteGrad | Memory tab + `memory_events` change history |
| Persist dashboard data outside app state | ByteGrad (Supabase) | Local SQLite instead — local-first, no cloud dependency, no PHI exposure |
| Per-action agent logging (agent, task, model, status, ts) | Komputer Mechanic (Hermes MC) | `agent_logs` + tier & sphere columns for EDENA auditability |
| Lightweight stack: Python + SQLite + one index.html | Komputer Mechanic | Adopted wholesale; stdlib-only constraint added |
| Tabs: Overview / Agents / Tasks / Schedule / Content | Komputer Mechanic | Adopted + Memory and Ledger tabs (NAIO-specific) |
| Log retention/cleanup so the DB stays light | Komputer Mechanic | Retention jobs; ledger tables exempt |
| Backup before any dashboard change; visible version | Komputer Mechanic | Automatic timestamped backups + footer version |
| Agents told to log via permanent memory instruction | Komputer Mechanic | Elevated to a tier-tagged NAIO skill + "silent work" detection |
| Content folder per agent; long docs saved as files, not chat dumps | Komputer Mechanic | Library tab convention |
| Roster of specialized agents with isolated souls/memory; channel-per-agent; router shortcuts; content pipeline | Komputer Mechanic | §10 team template, deferred per Phase-17 boundaries |
| Reverse-prompt the agent for personal feature ideas | ByteGrad (via Alex Finn) | Recommended step in MC-2 onboarding: ask Florence what *your* dashboard needs |
| Tailscale for same-dashboard-on-phone; SSH keys for friction removal | Komputer Mechanic | Optional Phase MC-5; localhost-only remains the default |
| Same interface on desktop and phone; grouping; notifications | Evgeny Shkuratov | Responsive single HTML; notification hooks via Telegram home channel |
| Org chart of orchestrator → managers → workers; activity feed as its own page | Steven Shoaf (Jarvis) | Org view (flagged) + activity ticker; voice explicitly out of scope for now |

## Appendix B — Explicit non-goals (v1)

Voice control · public hosting · VPS deployment · EHR/clinical-system integration of any kind · automatic memory writes · automatic cron scheduling · in-dashboard gate approval · storing note bodies or PHI · a second AI brain inside the dashboard.

---

*Agents propose. Humans judge. Nurses steward — and now they can watch the whole station from one screen.*
