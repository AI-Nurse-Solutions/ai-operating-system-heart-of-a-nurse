#!/usr/bin/env python3
"""
NAIO Mission Control — MC-1 · MC-2 · MC-3
The observation plane for Nurse AI OS. Read-mostly, local-only, stdlib-only.

Doctrine carried forward:
    Agents propose. Humans judge. Nurses steward.
    No PHI. No patient-specific clinical reasoning. No gate approval here.

What this server deliberately does NOT do (architecture §4.4):
    - approve or decline a human gate (it surfaces them; the runtime owns them)
    - write Hermes memory
    - schedule cron jobs
    - hold a single secret
    - raise a tier ceiling — no endpoint exists that could

Binds 127.0.0.1 by hard default. Any other bind requires --bind and prints a warning.
"""

import argparse
import contextlib
import json
import mimetypes
import os
import re
import shutil
import sqlite3
import sys
import threading
import time
import traceback
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

VERSION = "0.4.0"
HERE = Path(__file__).resolve().parent
DB_PATH = HERE / "mission_control.db"
ROLES_DIR = HERE / "roles"
CONTENT_DIR = HERE / "content"
BACKUP_DIR = HERE / "backups"
DEFAULT_PORT = 8321
CONFIG_PATH = HERE / "config.json"

DEFAULT_CONFIG = {
    "content_root": "demo-workspace/content",
    "vault_root": "demo-vault",
    "vault_inbox": "Inbox",
    "soul_files": ["demo-workspace/SOUL.md", "demo-workspace/memory.md"],
    "apple_notes_folders": [],
    "_note": "Repoint content_root and vault_root at your real workspace and Obsidian "
             "vault. Paths are relative to this directory or absolute. This file holds "
             "paths and preferences only — never a credential.",
}


def config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    if CONFIG_PATH.is_file():
        try:
            cfg.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            pass
    return cfg


def resolve(p: str) -> Path:
    path = Path(p).expanduser()
    return path if path.is_absolute() else (HERE / path)

sys.path.insert(0, str(HERE))
from adapters.runtime import get_adapter  # noqa: E402


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_new_file(path: Path, text: str, limit: int = 500) -> Path:
    """
    Write `text` to `path`, or to `path` with a `-2`, `-3`, … suffix if that name
    is taken. Returns the path actually written.

    The promotion contract (§7.5) is that the dashboard writes *new* files into
    the vault Inbox and never edits an existing note. A plain write_text() to a
    computed `YYYY-MM-DD-title.md` breaks that quietly: promote two notes with
    the same title on one day — or one whose name collides with a note the nurse
    already wrote — and the first file is truncated with nothing to undo it.
    Exclusive creation ('x') makes the collision impossible rather than unlikely.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    for n in range(1, limit + 1):
        candidate = path if n == 1 else path.with_name(f"{path.stem}-{n}{path.suffix}")
        try:
            with open(candidate, "x", encoding="utf-8") as fh:
                fh.write(text)
            return candidate
        except FileExistsError:
            continue
    raise FileExistsError(f"{limit} files already share the name {path.name}")


# ---------------------------------------------------------------------------
# Schema — architecture §6.1, with hat_id corrected to role_id
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS agent_logs (
  id INTEGER PRIMARY KEY,
  ts TEXT NOT NULL,
  agent_id TEXT NOT NULL,
  task TEXT NOT NULL,
  detail TEXT,
  model TEXT,
  status TEXT CHECK(status IN ('completed','failed','refused','in_progress')),
  edena_tier TEXT,
  sphere TEXT
);
CREATE INDEX IF NOT EXISTS idx_agent_logs_ts ON agent_logs(ts DESC);

CREATE TABLE IF NOT EXISTS tasks (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  body TEXT,
  lane TEXT NOT NULL DEFAULT 'todo',
  assignee TEXT NOT NULL DEFAULT 'me',
  role_id TEXT,
  source TEXT,
  created_ts TEXT, updated_ts TEXT, done_ts TEXT
);

CREATE TABLE IF NOT EXISTS notes_index (
  id INTEGER PRIMARY KEY,
  source TEXT CHECK(source IN ('obsidian','apple_notes')),
  external_id TEXT,
  title TEXT, folder TEXT, tags TEXT,
  modified_ts TEXT, indexed_ts TEXT,
  promoted_to TEXT
);

CREATE TABLE IF NOT EXISTS memory_events (
  id INTEGER PRIMARY KEY,
  ts TEXT, file TEXT, change_summary TEXT, diff_lines INTEGER
);

CREATE TABLE IF NOT EXISTS gate_events (
  id INTEGER PRIMARY KEY,
  ts TEXT, agent_id TEXT, sphere TEXT, edena_tier TEXT,
  request TEXT,
  outcome TEXT CHECK(outcome IN ('pending','approved','declined','expired')),
  resolved_ts TEXT, resolved_via TEXT
);

CREATE TABLE IF NOT EXISTS cron_jobs (
  id INTEGER PRIMARY KEY,
  runtime_job_id TEXT, agent_id TEXT, label TEXT,
  schedule TEXT, next_run_ts TEXT, last_run_ts TEXT, last_status TEXT,
  is_naio_ritual INTEGER DEFAULT 0, edena_tier TEXT
);

CREATE TABLE IF NOT EXISTS content_index (
  id INTEGER PRIMARY KEY,
  agent_id TEXT, path TEXT UNIQUE, title TEXT, doc_type TEXT,
  created_ts TEXT, modified_ts TEXT, word_count INTEGER
);

CREATE TABLE IF NOT EXISTS runtime_snapshots (
  id INTEGER PRIMARY KEY, ts TEXT,
  gateway_up INTEGER, runtime_present INTEGER,
  sessions INTEGER, tokens_in INTEGER, tokens_out INTEGER,
  est_cost_usd REAL, cpu_pct REAL, ram_pct REAL, disk_pct REAL,
  hermes_db_bytes INTEGER, mc_db_bytes INTEGER
);

CREATE TABLE IF NOT EXISTS settings ( key TEXT PRIMARY KEY, value TEXT );

CREATE TABLE IF NOT EXISTS collector_state (
  name TEXT PRIMARY KEY,
  last_ok_ts TEXT,
  last_error TEXT,
  runs INTEGER DEFAULT 0,
  failures INTEGER DEFAULT 0
);
"""


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# Columns added after the first build. `CREATE TABLE IF NOT EXISTS` leaves an
# existing database alone, so a dashboard that has been running since before a
# column existed needs it added explicitly — otherwise the collector's INSERT
# fails against a table that is one column short.
ADDED_COLUMNS = [
    ("runtime_snapshots", "runtime_present", "INTEGER"),
]


def init_db() -> None:
    conn = db()
    with conn:
        conn.executescript(SCHEMA)
        for table, column, decl in ADDED_COLUMNS:
            have = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}
            if column not in have:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")
        conn.execute(
            "INSERT OR IGNORE INTO settings(key,value) VALUES('schema_version',?)",
            (VERSION,),
        )
    conn.close()


# ---------------------------------------------------------------------------
# Role presets — loader + validator (roles/README.md contract)
# ---------------------------------------------------------------------------

REQUIRED_KEYS = {
    "role_id", "label", "licensure", "tabs", "overview_cards",
    "starter_agents", "task_lanes", "library_filters", "ritual_pack",
    "domain_emphasis", "standing_rows", "privacy_regimes", "risk_briefing",
    "tier_note",
}
STATE_VALUES = {"flourishing", "steady", "attention", "resting"}
LICENSURE_CLASSES = {"pre_licensure", "licensed", "advanced_practice", "physician_trainee"}


class PresetError(ValueError):
    """A preset that must be rejected, with the rule it broke."""


def validate_preset(data: dict, filename: str) -> dict:
    """Rules from roles/README.md. Rule 2 is the one that matters."""
    stem = Path(filename).stem

    # Rule 2 first — a preset may never raise a tier ceiling. Reject before anything else.
    if "tier_ceilings" in data or "tier_ceiling" in data:
        raise PresetError(
            f"{filename}: contains 'tier_ceilings'. A preset may not raise a tier ceiling "
            f"(Rail 3; MISSION-CONTROL-ARCHITECTURE §5.4). Ceilings move only by a logged "
            f"decision in governance-kit/GOVERNANCE.yaml."
        )

    missing = REQUIRED_KEYS - set(data)
    if missing:
        raise PresetError(f"{filename}: missing required keys: {sorted(missing)}")

    # Rule 1 — role_id unique and matches filename
    if data["role_id"] != stem:
        raise PresetError(f"{filename}: role_id {data['role_id']!r} does not match filename")

    if data["licensure"] not in LICENSURE_CLASSES:
        raise PresetError(f"{filename}: unknown licensure class {data['licensure']!r}")

    # Rule 3 — every role carries the PHI boundary
    if "phi" not in data["privacy_regimes"]:
        raise PresetError(f"{filename}: privacy_regimes must contain 'phi'. No exceptions.")

    # Rule 4 — exactly three risks; the third is the one the system cannot catch
    if len(data["risk_briefing"]) != 3:
        raise PresetError(
            f"{filename}: risk_briefing must have exactly 3 entries, found "
            f"{len(data['risk_briefing'])}"
        )

    for key in ("tabs", "overview_cards", "starter_agents", "standing_rows"):
        if not isinstance(data[key], list) or not data[key]:
            raise PresetError(f"{filename}: {key} must be a non-empty list")

    return data


def load_presets() -> tuple[dict, list]:
    presets, errors, seen = {}, [], set()
    if not ROLES_DIR.is_dir():
        return presets, [f"roles directory not found at {ROLES_DIR}"]
    for path in sorted(ROLES_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            validate_preset(data, path.name)
            if data["role_id"] in seen:
                raise PresetError(f"{path.name}: duplicate role_id {data['role_id']!r}")
            seen.add(data["role_id"])
            presets[data["role_id"]] = data
        except (PresetError, json.JSONDecodeError, KeyError) as exc:
            errors.append(str(exc))
    return presets, errors


GOV_DIR = HERE / "governance"


def load_content(role_id: str) -> dict | None:
    """
    Real content wins over sample. `content/<id>.json` is written by
    `bin/naio-soul-import` from the nurse's own soul file; `<id>.sample.json` is
    the demo fallback. The distinction is surfaced, never hidden.
    """
    real = CONTENT_DIR / f"{role_id}.json"
    if real.is_file():
        data = json.loads(real.read_text(encoding="utf-8"))
        data["sample"] = False
        return data
    sample = CONTENT_DIR / f"{role_id}.sample.json"
    if not sample.is_file():
        return None
    data = json.loads(sample.read_text(encoding="utf-8"))
    data["sample"] = True
    data["measured"] = False
    return data


def soul_state() -> dict:
    """What the dashboard knows about where its content came from."""
    record = GOV_DIR / "soul-import-record.json"
    ceilings = GOV_DIR / "tier-ceilings.json"
    real = sorted(p.stem for p in CONTENT_DIR.glob("*.json")
                  if not p.name.endswith(".sample.json") and not p.name.startswith("_"))
    out = {
        "imported": record.is_file(),
        "roles_with_real_content": real,
        "roles_on_sample": sorted(
            p.name.replace(".sample.json", "") for p in CONTENT_DIR.glob("*.sample.json")
            if p.name.replace(".sample.json", "") not in real),
        "record": None,
        "tier_ceilings": None,
        "note": "Tier ceilings live in governance/, never in a role preset. "
                "A preset carrying the key is rejected by the loader (Rail 3).",
    }
    if record.is_file():
        try:
            out["record"] = json.loads(record.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    if ceilings.is_file():
        try:
            out["tier_ceilings"] = json.loads(ceilings.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return out


# ---------------------------------------------------------------------------
# Collectors — one thread each, fault-isolated (architecture §4.2)
# A dead collector shows a stale badge. It never kills the server.
# ---------------------------------------------------------------------------

class CollectorInactive(RuntimeError):
    """Not an error: this collector has nothing to do on this machine or config."""


class Collector(threading.Thread):
    def __init__(self, name: str, interval: int, fn, stop_event: threading.Event):
        super().__init__(name=f"collector:{name}", daemon=True)
        self.collector_name = name
        self.interval = interval
        self.fn = fn
        self.stop_event = stop_event

    def run(self) -> None:
        while not self.stop_event.is_set():
            conn = None
            try:
                conn = db()
                self.fn(conn)
                with conn:
                    conn.execute(
                        "INSERT INTO collector_state(name,last_ok_ts,last_error,runs,failures) "
                        "VALUES(?,?,NULL,1,0) ON CONFLICT(name) DO UPDATE SET "
                        "last_ok_ts=excluded.last_ok_ts, last_error=NULL, runs=runs+1",
                        (self.collector_name, now_iso()),
                    )
            except CollectorInactive as inactive:
                try:
                    c2 = db()
                    with c2:
                        c2.execute(
                            "INSERT INTO collector_state(name,last_ok_ts,last_error,runs,failures) "
                            "VALUES(?,NULL,?,1,0) ON CONFLICT(name) DO UPDATE SET "
                            "last_error=excluded.last_error, runs=runs+1",
                            (self.collector_name, f"INACTIVE: {inactive}"))
                    c2.close()
                except Exception:                      # noqa: BLE001
                    pass
            except Exception:                      # noqa: BLE001 — fault isolation is the point
                err = traceback.format_exc(limit=3)
                try:
                    c2 = db()
                    with c2:
                        c2.execute(
                            "INSERT INTO collector_state(name,last_ok_ts,last_error,runs,failures) "
                            "VALUES(?,NULL,?,1,1) ON CONFLICT(name) DO UPDATE SET "
                            "last_error=excluded.last_error, runs=runs+1, failures=failures+1",
                            (self.collector_name, err[-500:]),
                        )
                    c2.close()
                except Exception:                  # noqa: BLE001
                    pass                           # never let bookkeeping kill a collector
            finally:
                if conn is not None:
                    conn.close()
            self.stop_event.wait(self.interval)


def collect_hermes_state(conn: sqlite3.Connection) -> None:
    """Runtime adapter — Hermes today, Florence-X later. §7.1"""
    adapter = get_adapter()
    state = adapter.gateway_state()
    with conn:
        conn.execute(
            "INSERT INTO runtime_snapshots(ts,gateway_up,runtime_present,sessions,tokens_in,"
            "tokens_out,est_cost_usd,cpu_pct,ram_pct,disk_pct,hermes_db_bytes,mc_db_bytes) "
            "VALUES(?,?,?,?,?,?,?,NULL,NULL,NULL,?,?)",
            (now_iso(), int(state["up"]), int(state.get("present", False)),
             state["sessions"], state["tokens_in"],
             state["tokens_out"], state["est_cost_usd"], state["hermes_db_bytes"],
             DB_PATH.stat().st_size if DB_PATH.exists() else 0),
        )
        conn.execute("DELETE FROM cron_jobs")
        for job in adapter.cron_jobs():
            conn.execute(
                "INSERT INTO cron_jobs(runtime_job_id,agent_id,label,schedule,next_run_ts,"
                "last_run_ts,last_status,is_naio_ritual,edena_tier) VALUES(?,?,?,?,?,?,?,?,?)",
                (job["id"], job["agent_id"], job["label"], job["schedule"], job["next_run_ts"],
                 job.get("last_run_ts"), job.get("last_status"), int(job.get("ritual", False)),
                 job.get("edena_tier")),
            )


def collect_system_health(conn: sqlite3.Connection) -> None:
    cpu = ram = None
    try:
        load1 = os.getloadavg()[0]
        cpu = round(min(100.0, load1 / max(1, os.cpu_count() or 1) * 100), 1)
    except (OSError, AttributeError):
        pass
    try:
        with open("/proc/meminfo", encoding="utf-8") as fh:
            info = {}
            for line in fh:
                k, _, v = line.partition(":")
                info[k] = int(v.strip().split()[0])
        total, avail = info.get("MemTotal", 0), info.get("MemAvailable", 0)
        if total:
            ram = round((total - avail) / total * 100, 1)
    except (OSError, ValueError, KeyError):
        pass
    usage = shutil.disk_usage(HERE)
    disk = round(usage.used / usage.total * 100, 1)
    with conn:
        conn.execute(
            "INSERT INTO runtime_snapshots(ts,gateway_up,sessions,tokens_in,tokens_out,"
            "est_cost_usd,cpu_pct,ram_pct,disk_pct,hermes_db_bytes,mc_db_bytes) "
            "VALUES(?,NULL,NULL,NULL,NULL,NULL,?,?,?,NULL,?)",
            (now_iso(), cpu, ram, disk, DB_PATH.stat().st_size if DB_PATH.exists() else 0),
        )
    prune_before = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
    with conn:
        conn.execute("DELETE FROM runtime_snapshots WHERE ts < ?", (prune_before,))
        conn.execute("DELETE FROM agent_logs WHERE ts < ?", (prune_before,))
        # gate_events are ledger-grade and never auto-pruned (§6)


def _walk_md(root: Path, limit: int = 2000):
    if not root.is_dir():
        return
    count = 0
    for path in sorted(root.rglob("*.md")):
        if count >= limit:
            return
        if any(part.startswith(".") for part in path.parts):
            continue
        count += 1
        yield path


def collect_content_index(conn: sqlite3.Connection) -> None:
    """Long-form artifacts in the workspace. Titles and counts — never bodies."""
    root = resolve(config()["content_root"])
    seen = []
    # One transaction for the whole run, not one per file. `with conn:` inside
    # the loop committed up to 2000 times every 60 seconds; on a real vault that
    # is thousands of fsyncs an hour for an index nobody is watching in
    # real time.
    with conn:
        for path in _walk_md(root):
            rel = str(path.relative_to(root))
            agent = rel.split(os.sep)[0] if os.sep in rel else "unassigned"
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            title = next((ln.lstrip("# ").strip() for ln in text.splitlines()
                          if ln.startswith("#")), path.stem)
            words = len(text.split())
            doc_type = path.parent.name if path.parent != root else "note"
            stat = path.stat()
            seen.append(rel)
            conn.execute(
                "INSERT INTO content_index(agent_id,path,title,doc_type,created_ts,"
                "modified_ts,word_count) VALUES(?,?,?,?,?,?,?) "
                "ON CONFLICT(path) DO UPDATE SET title=excluded.title, "
                "doc_type=excluded.doc_type, modified_ts=excluded.modified_ts, "
                "word_count=excluded.word_count",
                (agent, rel, title[:200], doc_type,
                 datetime.fromtimestamp(stat.st_ctime, timezone.utc).isoformat(timespec="seconds"),
                 datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(timespec="seconds"),
                 words))
        if seen:
            marks = ",".join("?" * len(seen))
            conn.execute(f"DELETE FROM content_index WHERE path NOT IN ({marks})", seen)
        else:
            conn.execute("DELETE FROM content_index")


TAG_RE = re.compile(r"(?:^|\s)#([A-Za-z][\w/-]{1,40})")


def collect_obsidian_index(conn: sqlite3.Connection) -> None:
    """
    Vault index: titles, tags, folders, mtimes. **Bodies are never persisted** —
    that is the PHI posture, not an optimisation. The deep link opens the real app.
    """
    root = resolve(config()["vault_root"])
    seen = []
    # One transaction per run, as in collect_content_index above — a five-minute
    # sweep of a large vault should not be thousands of separate commits.
    with conn:
        for path in _walk_md(root):
            rel = str(path.relative_to(root))
            try:
                head = path.read_text(encoding="utf-8", errors="replace")[:4000]
            except OSError:
                continue
            title = next((ln.lstrip("# ").strip() for ln in head.splitlines()
                          if ln.startswith("#")), path.stem)
            tags = sorted({m.group(1) for m in TAG_RE.finditer(head)})[:12]
            stat = path.stat()
            seen.append(rel)
            row = conn.execute(
                "SELECT id, promoted_to FROM notes_index WHERE source='obsidian' "
                "AND external_id=?", (rel,)).fetchone()
            if row:
                conn.execute(
                    "UPDATE notes_index SET title=?, folder=?, tags=?, modified_ts=?, "
                    "indexed_ts=? WHERE id=?",
                    (title[:200], str(path.parent.relative_to(root)), ",".join(tags),
                     datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(timespec="seconds"),
                     now_iso(), row["id"]))
            else:
                conn.execute(
                    "INSERT INTO notes_index(source,external_id,title,folder,tags,"
                    "modified_ts,indexed_ts,promoted_to) VALUES('obsidian',?,?,?,?,?,?,NULL)",
                    (rel, title[:200], str(path.parent.relative_to(root)), ",".join(tags),
                     datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(timespec="seconds"),
                     now_iso()))
        if seen:
            marks = ",".join("?" * len(seen))
            conn.execute(
                f"DELETE FROM notes_index WHERE source='obsidian' AND promoted_to IS NULL "
                f"AND external_id NOT IN ({marks})", seen)


def collect_memory_watch(conn: sqlite3.Connection) -> None:
    """
    SOUL.md / memory.md change history. Records that a file changed and by roughly
    how much — never the diff content, and never a write back. Mission Control does
    not touch runtime memory (§4.4).
    """
    for entry in config()["soul_files"]:
        path = resolve(entry)
        if not path.is_file():
            continue
        stat = path.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(timespec="seconds")
        key = f"memwatch:{path}"
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        prev = json.loads(row["value"]) if row else None
        lines = sum(1 for _ in path.open("r", encoding="utf-8", errors="replace"))
        state = {"mtime": mtime, "lines": lines}
        if prev != state:
            delta = lines - prev["lines"] if prev else lines
            summary = ("first seen" if prev is None else
                       f"{'+' if delta >= 0 else ''}{delta} lines")
            with conn:
                conn.execute(
                    "INSERT INTO memory_events(ts,file,change_summary,diff_lines) "
                    "VALUES(?,?,?,?)", (now_iso(), str(path.name), summary, abs(delta)))
                conn.execute(
                    "INSERT INTO settings(key,value) VALUES(?,?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (key, json.dumps(state)))


def collect_apple_notes(conn: sqlite3.Connection) -> None:
    """
    macOS only, configured folders only, metadata only. Runs the JXA bridge if it
    is present and we are on a Mac; otherwise does nothing and says so honestly.
    """
    folders = config().get("apple_notes_folders") or []
    bridge = HERE / "bridges" / "apple_notes.jxa"
    if sys.platform != "darwin" or not folders or not bridge.is_file():
        raise CollectorInactive(
            "apple_notes bridge inactive: "
            + ("not macOS" if sys.platform != "darwin"
               else "no folders configured" if not folders else "bridge script missing"))
    import subprocess
    out = subprocess.run(["osascript", "-l", "JavaScript", str(bridge), *folders],
                         capture_output=True, text=True, timeout=30)
    if out.returncode != 0:
        raise RuntimeError(f"JXA bridge failed: {out.stderr[:200]}")
    for note in json.loads(out.stdout or "[]"):
        row = conn.execute(
            "SELECT id FROM notes_index WHERE source='apple_notes' AND external_id=?",
            (note["id"],)).fetchone()
        with conn:
            if row:
                conn.execute("UPDATE notes_index SET title=?, folder=?, modified_ts=?, "
                             "indexed_ts=? WHERE id=?",
                             (note["title"][:200], note.get("folder"), note.get("modified"),
                              now_iso(), row["id"]))
            else:
                conn.execute(
                    "INSERT INTO notes_index(source,external_id,title,folder,tags,"
                    "modified_ts,indexed_ts,promoted_to) "
                    "VALUES('apple_notes',?,?,?,NULL,?,?,NULL)",
                    (note["id"], note["title"][:200], note.get("folder"),
                     note.get("modified"), now_iso()))


# ---------------------------------------------------------------------------
# PHI lint — a detection control backstopping the policy control (§8)
# ---------------------------------------------------------------------------

# The shapes live in adapters/phi.py — one list, three callers. (§7.3)
from adapters.phi import PHI_PATTERNS  # noqa: E402


def phi_lint() -> list[dict]:
    """Scan dashboard-owned text for PHI shapes. Detection, not prevention."""
    hits = []
    targets = [
        ("tasks", "title", "id"), ("tasks", "body", "id"),
        ("agent_logs", "task", "id"), ("agent_logs", "detail", "id"),
        ("content_index", "title", "id"),
    ]
    # closing(), because this runs on every /api/ledger and /api/phi-lint call:
    # one raised exception on a bare close() leaks the handle for the life of
    # the process, and this is the endpoint most likely to be hit in a loop.
    with contextlib.closing(db()) as conn:
        for table, col, key in targets:
            try:
                rows = conn.execute(
                    f"SELECT {key} AS k, {col} AS v FROM {table} WHERE {col} IS NOT NULL")
            except sqlite3.Error:
                continue
            for row in rows:
                for pattern, label in PHI_PATTERNS:
                    if re.search(pattern, row["v"] or "", re.IGNORECASE):
                        hits.append({"table": table, "column": col,
                                     "row_id": row["k"], "pattern": label})
    return hits


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    server_version = f"NAIO-MissionControl/{VERSION}"
    presets: dict = {}
    preset_errors: list = []

    def log_message(self, fmt, *args):  # quieter default logging
        if os.environ.get("MC_VERBOSE"):
            super().log_message(fmt, *args)

    # -- helpers ----------------------------------------------------------
    def _json(self, payload, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _static(self, rel: str) -> None:
        candidate = (HERE / rel.lstrip("/")).resolve()
        # is_relative_to, not startswith: HERE carries no trailing separator, so
        # a string prefix also matches a SIBLING directory whose name starts the
        # same way — `/n/mission-control-backup/secrets.env` passed that check.
        if not candidate.is_relative_to(HERE) or not candidate.is_file():
            self._json({"error": "not found"}, 404)
            return
        ctype = mimetypes.guess_type(str(candidate))[0] or "application/octet-stream"
        data = candidate.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    # -- the loopback control, actually enforced ---------------------------
    # Binding to 127.0.0.1 does not stop a web page the nurse has open from
    # POSTing to http://127.0.0.1:8321, and it does not stop DNS rebinding: a
    # hostile page resolves its own name to 127.0.0.1 and reaches these
    # endpoints with no preflight, because a form or a text/plain fetch needs
    # none. There is no auth here by design, so the Host and Origin headers are
    # the control — a same-origin request from the dashboard carries a loopback
    # Host and no Origin.
    # allowed_hosts starts as loopback only. Passing --bind explicitly adds that
    # address, so the documented "reach it from a phone over Tailscale" path
    # stays possible for someone who has read the warning — it is not silently
    # closed, and it is not silently open either.
    allowed_hosts: set = {"127.0.0.1", "localhost", "::1"}

    def _local_only(self) -> bool:
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]").lower()
        if host not in self.allowed_hosts:
            self._json({"error": f"refused: unexpected Host {host!r}. This dashboard "
                                 f"answers to the address it was bound to, and nothing "
                                 f"else — that is what stands in for a login here."}, 403)
            return False
        if self.headers.get("Origin"):
            self._json({"error": "refused: cross-origin request. Nothing here is "
                                 "reachable from another page."}, 403)
            return False
        return True

    # -- routes -----------------------------------------------------------
    def do_GET(self):  # noqa: N802
        if not self._local_only():
            return None
        route = urlparse(self.path)
        path, query = route.path, parse_qs(route.query)
        try:
            if path == "/" or path == "/index.html":
                return self._static("index.html")
            if not path.startswith("/api/"):
                return self._static(path)

            if path == "/api/health":
                return self._json(self._health())
            if path == "/api/roles":
                return self._json({
                    "roles": [
                        {"role_id": r["role_id"], "label": r["label"], "licensure": r["licensure"]}
                        for r in self.presets.values()
                    ],
                    "errors": self.preset_errors,
                })
            if path.startswith("/api/role/"):
                role_id = path.rsplit("/", 1)[-1]
                preset = self.presets.get(role_id)
                if not preset:
                    return self._json({"error": f"unknown role {role_id!r}"}, 404)
                content = load_content(role_id)
                if content is None:
                    return self._json({
                        "error": f"no content for role {role_id!r}",
                        "preset": preset,
                    }, 404)
                return self._json({"preset": preset, "content": content,
                                   "sample": content.get("sample", False)})
            if path == "/api/agents":
                return self._json({"agents": self._agents()})
            if path == "/api/activity":
                limit = int(query.get("limit", ["50"])[0])
                conn = db()
                rows = conn.execute(
                    "SELECT ts,agent_id,task,detail,model,status,edena_tier,sphere "
                    "FROM agent_logs ORDER BY ts DESC LIMIT ?", (min(limit, 500),)
                ).fetchall()
                conn.close()
                return self._json({"activity": [dict(r) for r in rows]})
            if path == "/api/gates":
                conn = db()
                rows = conn.execute(
                    "SELECT id,ts,agent_id,sphere,edena_tier,request,outcome "
                    "FROM gate_events WHERE outcome='pending' ORDER BY ts DESC"
                ).fetchall()
                conn.close()
                return self._json({
                    "gates": [dict(r) for r in rows],
                    "note": "Mission Control surfaces gates. It never approves them — "
                            "resolve in the runtime channel where the gate lives.",
                })
            if path == "/api/collectors":
                return self._json({"collectors": self._collectors()})
            if path == "/api/soul":
                return self._json(soul_state())

            if path == "/api/tasks":
                conn = db()
                rows = conn.execute(
                    "SELECT id,title,body,lane,assignee,role_id,source,created_ts,"
                    "updated_ts,done_ts FROM tasks ORDER BY updated_ts DESC, id DESC"
                ).fetchall()
                conn.close()
                return self._json({"tasks": [dict(r) for r in rows]})

            if path == "/api/schedule":
                conn = db()
                rows = conn.execute(
                    "SELECT runtime_job_id,agent_id,label,schedule,next_run_ts,last_run_ts,"
                    "last_status,is_naio_ritual,edena_tier FROM cron_jobs "
                    "ORDER BY is_naio_ritual DESC, next_run_ts"
                ).fetchall()
                conn.close()
                return self._json({
                    "jobs": [dict(r) for r in rows],
                    "read_only": True,
                    "note": "A mirror of the runtime's schedule. Mission Control displays "
                            "rituals; it does not schedule them, and no endpoint here can.",
                })

            if path == "/api/library":
                conn = db()
                rows = conn.execute(
                    "SELECT agent_id,path,title,doc_type,created_ts,modified_ts,word_count "
                    "FROM content_index ORDER BY modified_ts DESC"
                ).fetchall()
                conn.close()
                return self._json({
                    "items": [dict(r) for r in rows],
                    "root": str(resolve(config()["content_root"])),
                })

            if path == "/api/memory":
                conn = db()
                events = conn.execute(
                    "SELECT ts,file,change_summary,diff_lines FROM memory_events "
                    "ORDER BY ts DESC LIMIT 50").fetchall()
                notes = conn.execute(
                    "SELECT id,source,external_id,title,folder,tags,modified_ts,promoted_to "
                    "FROM notes_index ORDER BY modified_ts DESC LIMIT 300").fetchall()
                conn.close()
                cfg = config()
                vault = resolve(cfg["vault_root"])
                return self._json({
                    "memory_events": [dict(r) for r in events],
                    "notes": [dict(r) for r in notes],
                    "vault_root": str(vault),
                    "vault_name": vault.name,
                    "soul_files": [str(resolve(f)) for f in cfg["soul_files"]],
                    "note": "Metadata only. Note bodies are never persisted here — they stay "
                            "at the source, which is the PHI posture rather than an optimisation.",
                })

            if path == "/api/ledger":
                conn = db()
                gates = conn.execute(
                    "SELECT id,ts,agent_id,sphere,edena_tier,request,outcome,resolved_ts,"
                    "resolved_via FROM gate_events ORDER BY ts DESC LIMIT 200").fetchall()
                tiers = conn.execute(
                    "SELECT edena_tier AS tier, COUNT(*) AS n FROM agent_logs "
                    "WHERE edena_tier IS NOT NULL GROUP BY edena_tier ORDER BY n DESC"
                ).fetchall()
                refusals = conn.execute(
                    "SELECT ts,agent_id,task,detail,sphere,edena_tier FROM agent_logs "
                    "WHERE status='refused' ORDER BY ts DESC LIMIT 50").fetchall()
                counts = conn.execute(
                    "SELECT status, COUNT(*) AS n FROM agent_logs GROUP BY status").fetchall()
                conn.close()
                lint = phi_lint()
                return self._json({
                    "gates": [dict(r) for r in gates],
                    "tier_usage": [dict(r) for r in tiers],
                    "refusals": [dict(r) for r in refusals],
                    "status_counts": {r["status"]: r["n"] for r in counts},
                    "phi_lint": {"hits": lint, "clean": not lint},
                    "note": "Gate events are ledger-grade and never auto-pruned. This is the "
                            "tab you would show an educator, a manager, or a skeptic.",
                })

            if path == "/api/phi-lint":
                hits = phi_lint()
                return self._json({"hits": hits, "clean": not hits, "checked_ts": now_iso()})
            return self._json({"error": "not found"}, 404)
        except Exception as exc:                    # noqa: BLE001
            return self._json({"error": str(exc)}, 500)

    def do_POST(self):  # noqa: N802
        if not self._local_only():
            return None
        route = urlparse(self.path)
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            return self._json({"error": "invalid JSON"}, 400)

        # The dashboard writes only to dashboard-owned tables (§4.1).
        if route.path == "/api/activity":
            required = {"agent_id", "task", "status"}
            if not required <= set(payload):
                return self._json({"error": f"required: {sorted(required)}"}, 400)
            if payload["status"] not in {"completed", "failed", "refused", "in_progress"}:
                return self._json({"error": "invalid status"}, 400)
            conn = db()
            with conn:
                conn.execute(
                    "INSERT INTO agent_logs(ts,agent_id,task,detail,model,status,edena_tier,sphere) "
                    "VALUES(?,?,?,?,?,?,?,?)",
                    (payload.get("ts") or now_iso(), payload["agent_id"], payload["task"],
                     payload.get("detail"), payload.get("model"), payload["status"],
                     payload.get("edena_tier"), payload.get("sphere")),
                )
            conn.close()
            return self._json({"ok": True}, 201)

        if route.path == "/api/gates":
            # Surfacing only. There is deliberately no endpoint that resolves a gate.
            required = {"agent_id", "request"}
            if not required <= set(payload):
                return self._json({"error": f"required: {sorted(required)}"}, 400)
            conn = db()
            with conn:
                conn.execute(
                    "INSERT INTO gate_events(ts,agent_id,sphere,edena_tier,request,outcome) "
                    "VALUES(?,?,?,?,?,'pending')",
                    (now_iso(), payload["agent_id"], payload.get("sphere"),
                     payload.get("edena_tier"), payload["request"]),
                )
            conn.close()
            return self._json({"ok": True}, 201)

        if route.path == "/api/tasks":
            if not payload.get("title"):
                return self._json({"error": "title required"}, 400)
            conn = db()
            with conn:
                cur = conn.execute(
                    "INSERT INTO tasks(title,body,lane,assignee,role_id,source,created_ts,"
                    "updated_ts) VALUES(?,?,?,?,?,?,?,?)",
                    (payload["title"][:300], payload.get("body"),
                     payload.get("lane", "todo"), payload.get("assignee", "me"),
                     payload.get("role_id"), payload.get("source", "manual"),
                     now_iso(), now_iso()))
            conn.close()
            return self._json({"ok": True, "id": cur.lastrowid}, 201)

        if route.path.startswith("/api/content/"):
            return self._patch_content(route.path.rsplit("/", 1)[-1], payload)

        if route.path == "/api/promote":
            return self._promote(payload)

        return self._json({"error": "not found"}, 404)

    def do_PATCH(self):  # noqa: N802
        if not self._local_only():
            return None
        route = urlparse(self.path)
        length = int(self.headers.get("Content-Length") or 0)
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self._json({"error": "invalid JSON"}, 400)

        if route.path.startswith("/api/tasks/"):
            try:
                task_id = int(route.path.rsplit("/", 1)[-1])
            except ValueError:
                return self._json({"error": "bad task id"}, 400)
            fields, values = [], []
            for key in ("title", "body", "lane", "assignee"):
                if key in payload:
                    fields.append(f"{key}=?")
                    values.append(payload[key])
            if not fields:
                return self._json({"error": "nothing to update"}, 400)
            fields.append("updated_ts=?"); values.append(now_iso())
            if payload.get("lane") == "done":
                fields.append("done_ts=?"); values.append(now_iso())
            values.append(task_id)
            conn = db()
            with conn:
                conn.execute(f"UPDATE tasks SET {','.join(fields)} WHERE id=?", values)
            conn.close()
            return self._json({"ok": True})

        return self._json({"error": "not found"}, 404)

    # -- editing your own content -----------------------------------------
    EDITABLE = {"season", "seasonBody", "seasonMeta", "mission", "values"}

    def _patch_content(self, role_id: str, payload: dict):
        """
        Write through to `content/<role>.json` — the nurse's own file.

        Two rules worth stating:
          * Sample content is never edited in place. If a role is still on sample,
            a fresh EMPTY real file is created rather than promoting demo data to
            look like yours.
          * Nothing here can create a number. Only the fields a person actually
            knows about themselves are writable.
        """
        if role_id not in self.presets:
            return self._json({"error": f"unknown role {role_id!r}"}, 404)

        real = CONTENT_DIR / f"{role_id}.json"
        if real.is_file():
            data = json.loads(real.read_text(encoding="utf-8"))
        else:
            data = {
                "role_id": role_id, "sample": False, "measured": False,
                "source": {"generator": "manual",
                           "imported_at": now_iso()},
                "label": self.presets[role_id]["label"],
                "mission": "", "sub": "", "values": [],
                "season": "", "seasonBody": "", "seasonMeta": "",
                "actions": [], "domains": {}, "signals": [], "opps": [], "agents": [],
                "momentum": {"hero": None, "unit": "hours",
                             "label": "Nothing measured yet.", "note": "",
                             "kpis": [], "weekly": [], "caption": "", "evidence": []},
                "license": {"days": None, "gates": None, "currency": [],
                            "reputation": [], "risks": [], "scopeNote": ""},
                "needs": ["import your SOUL file, or keep filling this in by hand"],
            }

        changed = []
        for key in self.EDITABLE:
            if key in payload:
                data[key] = payload[key]
                changed.append(key)

        # standing rows: the credentials that could lapse
        if "currency" in payload:
            rows = payload["currency"]
            if not isinstance(rows, list):
                return self._json({"error": "currency must be a list"}, 400)
            clean = []
            for row in rows[:40]:
                name = str(row.get("name", "")).strip()[:80]
                meta = str(row.get("meta", "")).strip()[:160]
                state = row.get("state", "steady")
                if state not in STATE_VALUES:
                    state = "steady"
                if name:
                    clean.append({"name": name, "meta": meta, "state": state})
            data.setdefault("license", {})["currency"] = clean
            changed.append("currency")

        if not changed:
            return self._json({"error": f"nothing writable in payload; "
                                        f"allowed: {sorted(self.EDITABLE | {'currency'})}"}, 400)

        # PHI lint the incoming text before it lands
        blob = json.dumps(payload, ensure_ascii=False)
        for pattern, label in PHI_PATTERNS:
            if re.search(pattern, blob, re.IGNORECASE):
                return self._json({
                    "error": f"refused: that looks like {label}. Nothing was written. "
                             f"This field is not a place for patient information.",
                }, 400)

        needs = [n for n in data.get("needs", [])
                 if not (data.get("season") and n.startswith("season"))
                 and not (data.get("license", {}).get("currency") and n.startswith("credentials"))]
        data["needs"] = needs

        CONTENT_DIR.mkdir(exist_ok=True)
        created = not real.is_file()          # asked BEFORE the write, or it is always False
        real.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return self._json({"ok": True, "changed": sorted(changed),
                           "created": created, "needs": needs})

    # -- the promotion pipeline (architecture §7.6) ------------------------
    def _promote(self, payload: dict):
        """
        capture → keep → act.

        Three destinations, and one of them is deliberately not a write:
          task   → a row in the dashboard's own Kanban
          vault  → a markdown file in the vault's Inbox
          memory → a PROPOSAL file. Mission Control never writes runtime memory.
                   The nurse approves it in the runtime, where the gate lives.
        """
        note_id, dest = payload.get("note_id"), payload.get("to")
        if dest not in ("task", "vault", "memory"):
            return self._json({"error": "to must be one of: task, vault, memory"}, 400)

        conn = db()
        note = conn.execute("SELECT * FROM notes_index WHERE id=?", (note_id,)).fetchone()
        if not note:
            conn.close()
            return self._json({"error": f"no note {note_id!r}"}, 404)

        cfg = config()
        title = note["title"] or "(untitled)"
        stamp = None

        if dest == "task":
            with conn:
                cur = conn.execute(
                    "INSERT INTO tasks(title,body,lane,assignee,source,created_ts,updated_ts) "
                    "VALUES(?,?,'todo','me',?,?,?)",
                    (title[:300], None, f"{note['source']}:{note['external_id']}",
                     now_iso(), now_iso()))
            stamp = f"task:{cur.lastrowid}"

        elif dest == "vault":
            inbox = resolve(cfg["vault_root"]) / cfg.get("vault_inbox", "Inbox")
            inbox.mkdir(parents=True, exist_ok=True)
            safe = re.sub(r"[^\w\- ]+", "", title)[:60].strip() or "note"
            target = write_new_file(
                inbox / f"{datetime.now(timezone.utc):%Y-%m-%d}-{safe}.md",
                f"# {title}\n\n"
                f"> Promoted from {note['source']} on {now_iso()}.\n"
                f"> Source: `{note['external_id']}`\n\n"
                f"<!-- The body stayed at the source. Paste what you want to keep. -->\n")
            stamp = f"obsidian:{target.relative_to(resolve(cfg['vault_root']))}"

        else:  # memory
            proposals = HERE / "proposals"
            proposals.mkdir(exist_ok=True)
            safe = re.sub(r"[^\w\- ]+", "", title)[:60].strip() or "note"
            target = write_new_file(
                proposals / f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{safe}.md",
                f"# Proposed memory entry\n\n"
                f"**Source:** {note['source']} · `{note['external_id']}`\n"
                f"**Proposed:** {now_iso()}\n\n"
                f"## Candidate\n\n{title}\n\n"
                f"---\n\n"
                f"This is a **proposal**, not a memory write. Mission Control does not and "
                f"cannot write runtime memory. Review this in your runtime and approve it "
                f"there, where the gate lives.\n")
            stamp = f"memory-proposal:{target.name}"

        with conn:
            conn.execute("UPDATE notes_index SET promoted_to=? WHERE id=?", (stamp, note_id))
        conn.close()
        return self._json({
            "ok": True, "promoted_to": stamp,
            "wrote_runtime_memory": False,
            "note": ("A proposal was written for you to approve in the runtime. "
                     "Nothing was written to memory." if dest == "memory" else None),
        }, 201)

    # -- data shaping -----------------------------------------------------
    def _health(self) -> dict:
        conn = db()
        snap = conn.execute(
            "SELECT * FROM runtime_snapshots WHERE gateway_up IS NOT NULL ORDER BY ts DESC LIMIT 1"
        ).fetchone()
        sys_snap = conn.execute(
            "SELECT * FROM runtime_snapshots WHERE cpu_pct IS NOT NULL OR disk_pct IS NOT NULL "
            "ORDER BY ts DESC LIMIT 1"
        ).fetchone()
        logs = conn.execute("SELECT COUNT(*) AS n FROM agent_logs").fetchone()["n"]
        gates = conn.execute(
            "SELECT COUNT(*) AS n FROM gate_events WHERE outcome='pending'"
        ).fetchone()["n"]
        conn.close()
        return {
            "version": VERSION,
            "ts": now_iso(),
            "runtime": dict(snap) if snap else None,
            "system": dict(sys_snap) if sys_snap else None,
            "activity_rows": logs,
            "pending_gates": gates,
            "collectors": self._collectors(),
            "preset_errors": self.preset_errors,
            "roles_loaded": len(self.presets),
            "soul": soul_state(),
        }

    def _collectors(self) -> list:
        conn = db()
        rows = conn.execute("SELECT * FROM collector_state").fetchall()
        conn.close()
        out = []
        for row in rows:
            err = row["last_error"] or ""
            if err.startswith("INACTIVE:"):
                out.append({
                    "name": row["name"], "last_ok_ts": row["last_ok_ts"],
                    "runs": row["runs"], "failures": row["failures"],
                    "stale": False, "inactive": True,
                    "last_error": err[len("INACTIVE: "):][:200],
                })
                continue
            stale = True
            if row["last_ok_ts"]:
                try:
                    age = (datetime.now(timezone.utc)
                           - datetime.fromisoformat(row["last_ok_ts"])).total_seconds()
                    stale = age > 180
                except ValueError:
                    stale = True
            out.append({
                "name": row["name"], "last_ok_ts": row["last_ok_ts"],
                "runs": row["runs"], "failures": row["failures"],
                "stale": stale, "inactive": False,
                "last_error": (row["last_error"] or "")[:200] or None,
            })
        return out

    def _agents(self) -> list:
        conn = db()
        rows = conn.execute(
            "SELECT agent_id, COUNT(*) AS actions, MAX(ts) AS last_ts, "
            "SUM(status='refused') AS refusals, SUM(status='failed') AS failures "
            "FROM agent_logs GROUP BY agent_id ORDER BY last_ts DESC"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Backups — always keep a restore point before touching index.html or the DB (§4.1)
# ---------------------------------------------------------------------------

def backup(reason: str = "manual") -> Path:
    BACKUP_DIR.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = BACKUP_DIR / f"{stamp}-{reason}"
    target.mkdir(parents=True, exist_ok=True)
    for name in ("index.html", "mission_control.db"):
        src = HERE / name
        if src.exists():
            shutil.copy2(src, target / name)
    return target


# ---------------------------------------------------------------------------
# Serve
# ---------------------------------------------------------------------------

def serve(bind: str, port: int, with_collectors: bool = True):
    init_db()
    presets, errors = load_presets()
    Handler.presets, Handler.preset_errors = presets, errors
    if errors:
        print("Preset errors (these roles will not load):", file=sys.stderr)
        for err in errors:
            print(f"  ✗ {err}", file=sys.stderr)

    stop_event = threading.Event()
    collectors = []
    if with_collectors:
        collectors = [
            Collector("hermes_state", 30, collect_hermes_state, stop_event),
            Collector("system_health", 30, collect_system_health, stop_event),
            Collector("content_index", 60, collect_content_index, stop_event),
            Collector("memory_watch", 60, collect_memory_watch, stop_event),
            Collector("obsidian_index", 300, collect_obsidian_index, stop_event),
            Collector("apple_notes", 900, collect_apple_notes, stop_event),
        ]
        for c in collectors:
            c.start()

    if bind != "127.0.0.1":
        # An explicit --bind is also an explicit consent: accept that Host, and
        # keep refusing every other one.
        Handler.allowed_hosts = set(Handler.allowed_hosts) | {bind.lower()}
        print(f"\n  ⚠  WARNING: binding to {bind}, not 127.0.0.1.\n"
              f"     Mission Control has no authentication because it is not supposed to be\n"
              f"     reachable. You are removing the only control that made that safe.\n",
              file=sys.stderr)

    httpd = ThreadingHTTPServer((bind, port), Handler)
    print(f"NAIO Mission Control {VERSION}")
    print(f"  → http://{bind}:{port}")
    print(f"  roles loaded: {len(presets)}   collectors: {len(collectors)}")
    print("  Agents propose. Humans judge. Nurses steward.\n")
    return httpd, stop_event, collectors


def main() -> int:
    parser = argparse.ArgumentParser(description="NAIO Mission Control (MC-1)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--bind", default="127.0.0.1",
                        help="hard default 127.0.0.1; anything else prints a warning")
    parser.add_argument("--no-collectors", action="store_true")
    parser.add_argument("--backup", action="store_true", help="take a backup and exit")
    parser.add_argument("--check-presets", action="store_true",
                        help="validate roles/*.json and exit non-zero on any failure")
    parser.add_argument("--phi-lint", action="store_true", help="run the PHI lint and exit")
    args = parser.parse_args()

    if args.backup:
        print(f"backup written to {backup('manual')}")
        return 0

    if args.check_presets:
        presets, errors = load_presets()
        for rid in sorted(presets):
            print(f"  ✓ {rid}")
        for err in errors:
            print(f"  ✗ {err}")
        print(f"\n{len(presets)} valid, {len(errors)} rejected")
        return 1 if errors else 0

    if args.phi_lint:
        init_db()
        hits = phi_lint()
        for hit in hits:
            print(f"  ⚠ {hit['table']}.{hit['column']} row {hit['row_id']}: {hit['pattern']}")
        print("PHI lint clean." if not hits else f"\n{len(hits)} hit(s) — review the ledger.")
        return 1 if hits else 0

    httpd, stop_event, _ = serve(args.bind, args.port, not args.no_collectors)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping…")
    finally:
        stop_event.set()
        httpd.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
