#!/usr/bin/env python3
"""
MC-1 self-test — proves the acceptance criteria, not just that imports resolve.

  1. server starts and serves the UI
  2. presets load; a preset carrying tier_ceilings is REJECTED (Rail 3)
  3. every API endpoint answers
  4. mc-log writes a row and it comes back
  5. a gate can be surfaced — and there is no endpoint that resolves one
  6. killing a collector produces a stale badge and the server survives
  7. the PHI lint catches a seeded string
  8. MC-2: tasks create and move; the schedule mirror cannot schedule
  9. MC-3: the promotion pipeline routes three ways and NEVER writes runtime memory
 10. note bodies are never persisted; gate events are never pruned
 11. the SOUL bridge: refusals, a real import, and no invented numbers
"""
from __future__ import annotations

import json
import os
import re
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

PASS, FAIL, SKIP = [], [], []


def check(name: str, cond: bool, detail: str = "") -> None:
    (PASS if cond else FAIL).append(name)
    mark = "\033[32m✓\033[0m" if cond else "\033[31m✗\033[0m"
    print(f"  {mark} {name}" + (f" — {detail}" if detail and not cond else ""))


def free_port() -> int:
    """An unused loopback port, so two runs never collide on a fixed one."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def skip(name: str, why: str) -> None:
    """A check that could not run. Counted as neither pass nor fail, and said
    out loud — a silently skipped test is a false pass wearing a green shirt."""
    SKIP.append(name)
    print(f"  \033[33m–\033[0m {name} — SKIPPED: {why}")


def get(path: str, port: int):
    """Returns (status, payload). A 4xx is data here, not an exception."""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=5) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read() or b"{}")
        except json.JSONDecodeError:
            return exc.code, {}


def main() -> int:
    workdir = Path(tempfile.mkdtemp(prefix="mc-selftest-"))
    stage = workdir / "mission-control"
    shutil.copytree(HERE, stage, ignore=shutil.ignore_patterns(
        "backups", "*.db", "*.db-wal", "*.db-shm", "__pycache__"))
    # An ephemeral port, not a fixed one. On 8399 a crashed earlier run leaves a
    # server the health probe happily connects to, and the suite then asserts
    # against someone else's tree and passes.
    port = free_port()

    print("\nNAIO Mission Control — MC-1 self-test\n")

    # -- 2. the rule that matters: a preset may not raise a tier ceiling -----
    bad = stage / "roles" / "_evil.json"
    good = json.loads((stage / "roles" / "bedside.json").read_text())
    good.update({"role_id": "_evil", "label": "Evil", "tier_ceilings": {"clinical": "red"}})
    bad.write_text(json.dumps(good))

    sys.path.insert(0, str(stage))
    for mod in [m for m in list(sys.modules) if m.startswith(("mission_control", "adapters"))]:
        del sys.modules[mod]
    import mission_control as mc  # noqa: E402
    mc.HERE = stage
    mc.ROLES_DIR = stage / "roles"
    mc.CONTENT_DIR = stage / "content"
    mc.DB_PATH = stage / "mission_control.db"

    presets, errors = mc.load_presets()
    check("tier_ceilings preset is rejected", "_evil" not in presets)
    check("rejection names the rule", any("tier ceiling" in e for e in errors),
          f"errors={errors}")
    bad.unlink()

    presets, errors = mc.load_presets()
    check("8 presets valid once the bad file is gone", len(presets) == 8 and not errors,
          f"{len(presets)} valid, {len(errors)} errors")
    check("every preset carries the PHI boundary",
          all("phi" in p["privacy_regimes"] for p in presets.values()))
    check("every preset has exactly three risks",
          all(len(p["risk_briefing"]) == 3 for p in presets.values()))
    check("every role has content",
          all((mc.CONTENT_DIR / f"{r}.sample.json").is_file() for r in presets))

    # -- 1. start the server ------------------------------------------------
    env = {**os.environ, "HERMES_HOME": str(workdir / "no-hermes")}
    proc = subprocess.Popen(
        [sys.executable, str(stage / "mission_control.py"), "--port", str(port)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, cwd=str(stage))
    up = False
    for _ in range(50):
        time.sleep(0.2)
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=2)
            up = True
            break
        except (urllib.error.URLError, OSError):
            continue
    check("server starts and answers on 127.0.0.1", up)
    if not up:
        out, err = proc.communicate(timeout=5)
        print(err.decode()[-2000:])
        proc.kill()
        return 1

    try:
        # -- 3. endpoints ---------------------------------------------------
        status, health = get("/api/health", port)
        check("GET /api/health", status == 200 and health["roles_loaded"] == 8)

        status, roles = get("/api/roles", port)
        check("GET /api/roles lists 8", status == 200 and len(roles["roles"]) == 8)

        ok = True
        for rid in [r["role_id"] for r in roles["roles"]]:
            st, payload = get(f"/api/role/{rid}", port)
            ok &= (st == 200 and "preset" in payload and "content" in payload
                   and payload["sample"] is True)
        check("GET /api/role/<id> returns preset + content for all 8, flagged sample", ok)

        st, payload = get("/api/role/nope", port)
        check("unknown role 404s cleanly", st == 404 and "error" in payload)

        for path in ("/api/agents", "/api/activity", "/api/gates", "/api/collectors"):
            st, _ = get(path, port)
            check(f"GET {path}", st == 200)

        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=5) as r:
            body = r.read().decode()
        check("UI is served and has no hardcoded role data",
              "const ROLES" not in body and "/api/role/" in body)

        # -- 4. mc-log ------------------------------------------------------
        rc = subprocess.call([sys.executable, str(stage / "bin" / "mc-log"),
                              "--agent", "florence", "--task", "Drafted the weekly ledger",
                              "--status", "completed", "--model", "anthropic/claude-sonnet",
                              "--tier", "green", "--sphere", "career",
                              "--url", f"http://127.0.0.1:{port}/api/activity"])
        st, act = get("/api/activity", port)
        check("mc-log writes a row that comes back",
              rc == 0 and any(a["task"].startswith("Drafted") for a in act["activity"]))

        rc_bad = subprocess.call([sys.executable, str(stage / "bin" / "mc-log"),
                                  "--agent", "florence", "--task", "x", "--status", "completed",
                                  "--model", "unknown",
                                  "--url", f"http://127.0.0.1:{port}/api/activity"],
                                 stderr=subprocess.DEVNULL)
        check("mc-log refuses model='unknown'", rc_bad == 2)

        st, agents = get("/api/agents", port)
        check("agents roll up from the log",
              st == 200 and any(a["agent_id"] == "florence" for a in agents["agents"]))

        # -- 5. gates: surfaced, never resolved -----------------------------
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/gates",
            data=json.dumps({"agent_id": "scribe", "request": "Send a LinkedIn post",
                             "sphere": "creative", "edena_tier": "yellow"}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=5) as r:
            gate_ok = r.status in (200, 201)
        st, gates = get("/api/gates", port)
        check("a gate can be surfaced", gate_ok and len(gates["gates"]) == 1)

        resolved = False
        for path, method in (("/api/gates/1/approve", "POST"), ("/api/gate/1", "POST")):
            try:
                rq = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=b"{}",
                                            headers={"Content-Type": "application/json"},
                                            method=method)
                with urllib.request.urlopen(rq, timeout=3) as r:
                    body_j = json.loads(r.read() or b"{}")
                    if r.status < 400 and not body_j.get("error"):
                        resolved = True
            except urllib.error.HTTPError:
                pass
        check("no endpoint approves a gate (Rail 4)", not resolved)

        # -- 7. PHI lint ----------------------------------------------------
        conn = sqlite3.connect(stage / "mission_control.db", timeout=10)
        with conn:
            conn.execute("INSERT INTO tasks(title,lane,assignee,created_ts) "
                         "VALUES('follow up MRN 4471902','todo','me','2026-08-11')")
        conn.close()
        st, lint = get("/api/phi-lint", port)
        check("PHI lint catches a seeded MRN",
              st == 200 and not lint["clean"] and
              any(h["pattern"] == "medical record number" for h in lint["hits"]))

        # -- 8. MC-2: tasks ---------------------------------------------------
        rq = urllib.request.Request(f"http://127.0.0.1:{port}/api/tasks",
            data=json.dumps({"title": "File the certification reimbursement",
                             "lane": "to-do", "assignee": "me"}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(rq, timeout=5) as r:
            created = json.loads(r.read())
        st, tl = get("/api/tasks", port)
        made = [t for t in tl["tasks"] if t["id"] == created.get("id")]
        check("a task can be created",
              created.get("ok") and len(made) == 1
              and made[0]["title"].startswith("File the certification"))

        rq = urllib.request.Request(f"http://127.0.0.1:{port}/api/tasks/{created['id']}",
            data=json.dumps({"lane": "done"}).encode(),
            headers={"Content-Type": "application/json"}, method="PATCH")
        with urllib.request.urlopen(rq, timeout=5) as r:
            moved = r.status == 200
        st, tl = get("/api/tasks", port)
        moved_row = next(t for t in tl["tasks"] if t["id"] == created["id"])
        check("a task can be moved between lanes and stamps done_ts",
              moved and moved_row["lane"] == "done" and moved_row["done_ts"])

        # -- 8b. MC-2: the schedule mirror is read-only -----------------------
        st, sched = get("/api/schedule", port)
        check("schedule mirror declares itself read-only",
              st == 200 and sched.get("read_only") is True)
        can_schedule = False
        for path, method in (("/api/schedule", "POST"), ("/api/cron", "POST")):
            try:
                rq = urllib.request.Request(f"http://127.0.0.1:{port}{path}",
                    data=json.dumps({"label": "evil", "schedule": "* * * * *"}).encode(),
                    headers={"Content-Type": "application/json"}, method=method)
                with urllib.request.urlopen(rq, timeout=3) as r:
                    if r.status < 400 and not json.loads(r.read() or b"{}").get("error"):
                        can_schedule = True
            except urllib.error.HTTPError:
                pass
        check("no endpoint schedules a cron job", not can_schedule)

        # -- 8a. the loopback control, actually tested ------------------------
        # Binding to 127.0.0.1 does not stop a page the nurse has open from
        # POSTing here, so Host and Origin are the control that stands in for
        # the login this dashboard deliberately does not have.
        def raw(method, path, headers):
            rq = urllib.request.Request(f"http://127.0.0.1:{port}{path}",
                                        data=b"{}" if method != "GET" else None,
                                        headers=headers, method=method)
            try:
                with urllib.request.urlopen(rq, timeout=5) as r:
                    return r.status
            except urllib.error.HTTPError as e:
                return e.code

        check("a request with a foreign Host is refused",
              raw("POST", "/api/tasks", {"Host": "evil.example",
                                         "Content-Type": "application/json"}) == 403)
        check("a cross-origin request is refused even from loopback",
              raw("POST", "/api/tasks", {"Host": f"127.0.0.1:{port}",
                                         "Origin": "https://evil.example",
                                         "Content-Type": "application/json"}) == 403)
        check("a GET with a foreign Host is refused too",
              raw("GET", "/api/health", {"Host": "evil.example"}) == 403)
        check("the dashboard's own requests still work",
              raw("GET", "/api/health", {"Host": f"127.0.0.1:{port}"}) == 200)

        # -- 8b. installed is not running -------------------------------------
        # The health strip must never say 'runtime up' for a Hermes that is only
        # on disk. Presence and liveness are two different questions.
        from adapters.runtime import HermesAdapter          # noqa: PLC0415
        absent = HermesAdapter(workdir / "no-hermes").gateway_state()
        installed_dir = workdir / "hermes-installed"
        installed_dir.mkdir(exist_ok=True)
        installed = HermesAdapter(installed_dir).gateway_state()
        stale_pid = workdir / "hermes-stale"
        stale_pid.mkdir(exist_ok=True)
        (stale_pid / "hermes.pid").write_text("2147480000\n")
        stale = HermesAdapter(stale_pid).gateway_state()
        live_dir = workdir / "hermes-live"
        live_dir.mkdir(exist_ok=True)
        (live_dir / "hermes.pid").write_text(f"{os.getpid()}\n")
        alive = HermesAdapter(live_dir).gateway_state()
        check("an absent runtime is neither present nor up",
              absent["present"] is False and absent["up"] is False)
        check("an installed but stopped runtime is present and NOT up",
              installed["present"] is True and installed["up"] is False,
              installed["liveness"])
        check("a pid file pointing at nothing does not count as up",
              stale["present"] is True and stale["up"] is False, stale["liveness"])
        check("a live pid file is what makes the runtime up",
              alive["present"] is True and alive["up"] is True, alive["liveness"])

        # -- 9. MC-3: the promotion pipeline ----------------------------------
        st, mem = get("/api/memory", port)
        notes = mem["notes"]
        check("vault index populated from the demo vault", st == 200 and len(notes) >= 4)
        check("indexed notes carry metadata only, never a body",
              all("body" not in n and "content" not in n for n in notes))

        def promote(nid, to):
            rq = urllib.request.Request(f"http://127.0.0.1:{port}/api/promote",
                data=json.dumps({"note_id": nid, "to": to}).encode(),
                headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(rq, timeout=5) as r:
                return json.loads(r.read())

        # Every baseline below is read BEFORE the action it is a baseline for.
        # Read afterwards, `any(Inbox.glob('*.md'))` was already true from the two
        # notes the demo vault ships, and the SOUL/memory comparison compared a
        # file to itself: two green checks that could not go red.
        inbox_before = {p.name for p in (stage / "demo-vault" / "Inbox").glob("*.md")}
        soul_before = (stage / "demo-workspace" / "SOUL.md").read_text()
        mem_before = (stage / "demo-workspace" / "memory.md").read_text()

        p_task = promote(notes[0]["id"], "task")
        p_vault = promote(notes[1]["id"], "vault")
        p_mem = promote(notes[2]["id"], "memory")
        inbox_after = {p.name for p in (stage / "demo-vault" / "Inbox").glob("*.md")}
        check("promote → task", p_task["promoted_to"].startswith("task:"))
        check("promote → vault Inbox writes a file that was not there before",
              p_vault["promoted_to"].startswith("obsidian:")
              and len(inbox_after - inbox_before) == 1,
              f"new files: {sorted(inbox_after - inbox_before)}")
        check("promote → memory writes a PROPOSAL, not memory",
              p_mem["promoted_to"].startswith("memory-proposal:")
              and p_mem["wrote_runtime_memory"] is False
              and (stage / "proposals").is_dir())

        # A promotion writes a NEW note. It never truncates one. Two notes with
        # the same title promoted on the same day used to compute the same
        # `YYYY-MM-DD-title.md` and the second write silently replaced the first
        # — the vault is the nurse's own writing, and losing a paragraph of it to
        # a name collision is not a rounding error.
        inbox = stage / "demo-vault" / "Inbox"
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        keeper = inbox / f"{today}-collision probe.md"
        keeper.write_text("# Mine\n\nWords the nurse wrote herself.\n", encoding="utf-8")
        conn_probe = sqlite3.connect(str(stage / "mission_control.db"))
        with conn_probe:
            for i in range(2):
                conn_probe.execute(
                    "INSERT INTO notes_index(source,external_id,title,folder,modified_ts) "
                    "VALUES('apple_notes',?,'collision probe','Inbox',?)",
                    (f"probe-{i}", today))
        rows = conn_probe.execute(
            "SELECT id FROM notes_index WHERE external_id LIKE 'probe-%' ORDER BY id"
        ).fetchall()
        conn_probe.close()
        p_a = promote(rows[0][0], "vault")
        p_b = promote(rows[1][0], "vault")
        check("two same-title promotions on one day write two files",
              p_a["promoted_to"] != p_b["promoted_to"],
              f"{p_a['promoted_to']} vs {p_b['promoted_to']}")
        check("promotion never overwrites a note the nurse already wrote",
              keeper.read_text() == "# Mine\n\nWords the nurse wrote herself.\n")

        check("promoting to memory did not touch SOUL.md or memory.md",
              soul_before == (stage / "demo-workspace" / "SOUL.md").read_text()
              and mem_before == (stage / "demo-workspace" / "memory.md").read_text())

        st, mem2 = get("/api/memory", port)
        promoted = [n for n in mem2["notes"] if n["promoted_to"]]
        check("promotion stamps the trail on the note", len(promoted) == 5,
              f"{len(promoted)} stamped")

        # -- 9b. library ------------------------------------------------------
        st, lib = get("/api/library", port)
        check("library indexes the workspace", st == 200 and len(lib["items"]) >= 5)
        check("library rows carry counts, not bodies",
              all("body" not in i and i.get("word_count", 0) > 0 for i in lib["items"]))

        # -- 10. ledger: gates survive pruning --------------------------------
        conn = sqlite3.connect(stage / "mission_control.db", timeout=10)
        with conn:
            conn.execute("UPDATE gate_events SET ts='2019-01-01T00:00:00+00:00'")
            conn.execute("INSERT INTO agent_logs(ts,agent_id,task,model,status) "
                         "VALUES('2019-01-01T00:00:00+00:00','florence','ancient','m','completed')")
        conn.close()
        sys.path.insert(0, str(stage))
        conn = sqlite3.connect(stage / "mission_control.db", timeout=10)
        conn.row_factory = sqlite3.Row
        mc.DB_PATH = stage / "mission_control.db"
        mc.collect_system_health(conn)          # this is what prunes
        old_logs = conn.execute(
            "SELECT COUNT(*) c FROM agent_logs WHERE ts < '2020-01-01'").fetchone()["c"]
        old_gates = conn.execute(
            "SELECT COUNT(*) c FROM gate_events WHERE ts < '2020-01-01'").fetchone()["c"]
        conn.close()
        check("retention prunes ancient agent logs", old_logs == 0)
        check("retention NEVER prunes a gate event (ledger-grade)", old_gates >= 1)

        subprocess.call([sys.executable, str(stage / "bin" / "mc-log"),
                         "--agent", "florence",
                         "--task", "Refused: patient-specific dosing question",
                         "--status", "refused", "--model", "anthropic/claude-sonnet",
                         "--tier", "green", "--sphere", "career",
                         "--detail", "Rail 2 — the tool has no clearance.",
                         "--url", f"http://127.0.0.1:{port}/api/activity"])
        st, ledger = get("/api/ledger", port)
        check("ledger surfaces a boundary refusal with its reason",
              st == 200 and ledger["status_counts"].get("refused", 0) >= 1
              and any("Rail 2" in (r.get("detail") or "") for r in ledger["refusals"]))
        check("ledger reports tier usage",
              any(t["tier"] == "green" for t in ledger["tier_usage"]))

        # -- 11. the SOUL bridge ----------------------------------------------
        importer = stage / "bin" / "naio-soul-import"
        fixture = stage / "fixtures" / "naio-soul.example.json"
        check("a soul fixture ships for testing", fixture.is_file())

        def run_import(src, *extra):
            return subprocess.run([sys.executable, str(importer), str(src), *extra],
                                  capture_output=True, text=True, cwd=str(stage))

        # refusal 1 — a boundary that is not confirmed
        bad1 = workdir / "unconfirmed.json"
        soul = json.loads(fixture.read_text())
        soul["boundaries"]["no_phi_confirmed"] = False
        bad1.write_text(json.dumps(soul))
        r1 = run_import(bad1)
        check("importer REFUSES an unconfirmed boundary",
              r1.returncode != 0 and "REFUSED" in r1.stderr)

        # refusal 2 — PHI anywhere in the file
        bad2 = workdir / "phi.json"
        soul = json.loads(fixture.read_text())
        soul["identity"]["always_remember"] = "remember MRN 4471902, room 12B"
        bad2.write_text(json.dumps(soul))
        r2 = run_import(bad2)
        check("importer REFUSES PHI-shaped content, writing nothing",
              r2.returncode != 0 and "PHI-shaped" in r2.stderr
              and not (stage / "content" / "bedside.json").exists())

        # dry run writes nothing
        r3 = run_import(fixture)
        check("dry run is the default and writes nothing",
              r3.returncode == 0 and "Dry run" in r3.stdout
              and not (stage / "content" / "bedside.json").exists())

        # the real thing
        r4 = run_import(fixture, "--apply")
        content_file = stage / "content" / "bedside.json"
        check("--apply writes real content", r4.returncode == 0 and content_file.is_file())
        check("--apply writes tier ceilings to GOVERNANCE, not a preset",
              (stage / "governance" / "tier-ceilings.json").is_file()
              and (stage / "governance" / "soul-import-record.json").is_file())

        for pf in (stage / "roles").glob("*.json"):
            raw = json.loads(pf.read_text())
            if "tier_ceilings" in raw:
                check("no preset gained tier_ceilings from the import", False, pf.name)
                break
        else:
            check("no preset gained tier_ceilings from the import", True)

        presets2, errors2 = mc.load_presets()
        check("all 8 presets still validate after an import",
              len(presets2) == 8 and not errors2)

        real = json.loads(content_file.read_text())
        check("imported content carries the nurse's own mission and values",
              real["mission"].startswith("Become the nurse")
              and len(real["values"]) == 4)
        check("imported content invents NO numbers",
              all(d["share"] is None for d in real["domains"].values())
              and real["actions"] == []
              and real["momentum"]["hero"] is None
              and real["license"]["days"] is None)
        check("imported content lists what is still needed", len(real["needs"]) >= 3)

        # the server must prefer real over sample, and say which
        st, role = get("/api/role/bedside", port)
        check("server serves real content and flags it sample:false",
              st == 200 and role["sample"] is False
              and role["content"]["mission"].startswith("Become the nurse"))
        st, other = get("/api/role/student", port)
        check("a role without an import still serves sample, flagged", other["sample"] is True)
        st, soul_state = get("/api/soul", port)
        check("/api/soul reports which roles are real and which are sample",
              st == 200 and soul_state["imported"] is True
              and "bedside" in soul_state["roles_with_real_content"]
              and "student" in soul_state["roles_on_sample"])

        # -- 11b. every one of the eight roles round-trips quiz → file → preset
        role_ids = sorted(p.stem for p in (stage / "roles").glob("*.json"))
        round_tripped = []
        for rid in role_ids:
            probe = workdir / f"soul-{rid}.json"
            soul = json.loads(fixture.read_text())
            soul["identity"]["role"] = rid
            probe.write_text(json.dumps(soul))
            r = run_import(probe)
            if r.returncode == 0 and f"→ preset {rid!r}" in r.stdout:
                round_tripped.append(rid)
        check("all 8 roles map 1:1 with no guessing",
              len(round_tripped) == 8, f"mapped: {round_tripped}")

        legacy_fixture = stage / "fixtures" / "naio-soul.legacy-1.0.0.json"
        r_leg = run_import(legacy_fixture)
        check("a schema 1.0.0 soul file still imports, and says what it mapped",
              r_leg.returncode == 0 and "retired 1.0.0 spelling" in r_leg.stdout)

        # -- 11b. the export the live quiz actually emits -----------------------
        # Every soul test above used a fixture written by hand. The schema pinned
        # schema_version to ^1. while soul-quiz.html moved to 2.0.0, so a nurse
        # who took the quiz and imported the download was refused — and the suite
        # stayed green, because no fixture had ever been 2.0.0. The producer is
        # the quiz; the contract has to be checked against what it produces.
        v2_fixture = stage / "fixtures" / "naio-soul.v2-role-constellation.json"
        r_v2 = run_import(v2_fixture)
        check("the 2.0.0 role-constellation export the live quiz emits imports",
              r_v2.returncode == 0 and "REFUSED" not in r_v2.stdout,
              r_v2.stdout.strip().replace("\n", " | ")[:300])

        # A 2.x export's identity.role is the LEGACY value — the quiz collapses
        # 36 constellation roles into four of them, so an NP, a resident and an
        # entrepreneur all arrive as 'staff' or 'other' and land on the bedside
        # preset. Five of the eight presets were unreachable from a live export.
        # The primary constellation role is the authoritative one.
        v2_cases = [
            ("nurse-practitioner", "staff", "np"),
            ("nurse-educator", "leader", "educator"),
            ("charge-nurse-team-lead", "leader", "charge"),
            ("medical-resident-fellow", "other", "resident"),
            ("nurse-entrepreneur", "other", "entrepreneur"),
            ("bedside-nurse", "staff", "bedside"),
            ("prelicensure-nursing-student", "student", "student"),
        ]
        v2_mapped = []
        for role_id, legacy, expected in v2_cases:
            probe = workdir / f"v2-{role_id}.json"
            soul = json.loads(v2_fixture.read_text())
            soul["identity"]["role"] = legacy
            soul["role_constellation"]["primary"][0]["role_id"] = role_id
            probe.write_text(json.dumps(soul))
            r = run_import(probe)
            if r.returncode == 0 and f"→ preset {expected!r}" in r.stdout:
                v2_mapped.append(role_id)
        check("a 2.x export maps from its PRIMARY constellation role, not the "
              "legacy identity.role", len(v2_mapped) == len(v2_cases),
              f"mapped {v2_mapped}")

        # A role id the map has not caught up with must fall back and say so,
        # never guess silently.
        unknown = workdir / "v2-unknown-role.json"
        soul = json.loads(v2_fixture.read_text())
        soul["role_constellation"]["primary"][0]["role_id"] = "role-invented-tomorrow"
        unknown.write_text(json.dumps(soul))
        r_unknown = run_import(unknown)
        check("an unmapped constellation role falls back to identity.role and warns",
              r_unknown.returncode == 0
              and "has no preset mapping yet" in r_unknown.stdout,
              r_unknown.stdout.strip().replace("\n", " | ")[:200])

        # A 1.x file has no constellation, so identity.role stays authoritative.
        r_v1_role = run_import(fixture)
        check("a 1.x file still maps from identity.role",
              r_v1_role.returncode == 0 and "from identity.role" in r_v1_role.stdout)

        # A committed fixture is a photograph of the producer, and photographs
        # age. When this runs inside the site repo, regenerate from soul-quiz's
        # own model and fail if the fixture no longer matches what it emits —
        # so the next version bump breaks a test here instead of breaking a
        # nurse's first import.
        quiz_model = HERE.parent.parent / "soul-quiz" / "soul-quiz-model.mjs"
        quiz_test = HERE.parent.parent / "tests" / "test_soul_quiz_constellation.py"
        node = shutil.which("node")
        if not (quiz_model.is_file() and quiz_test.is_file()):
            skip("the committed v2 fixture still matches what soul-quiz emits",
                 "soul-quiz not present — running outside the site repo")
        elif not node:
            skip("the committed v2 fixture still matches what soul-quiz emits",
                 "node not available")
        else:
            state_js = re.search(
                r"def representative_state_js\(\).*?return\s+(?:f?\"\"\"|r?\"\"\")(.*?)\"\"\"",
                quiz_test.read_text(encoding="utf-8"), re.DOTALL)
            if not state_js:
                skip("the committed v2 fixture still matches what soul-quiz emits",
                     "could not read the quiz's representative state from its own tests")
            else:
                # The probe goes in a temp dir and imports the model by file://
                # URL. An earlier version wrote it into the repo root and deleted
                # it afterwards, which dirtied the working tree for the length of
                # the run and left the file behind whenever the delete failed or
                # the process died first — precisely what CI's
                # `test -z "$(git status --porcelain)"` gate exists to catch. A
                # test that can fail the build by running is not a test.
                probe_dir = Path(tempfile.mkdtemp(prefix="mc-quiz-probe-"))
                try:
                    gen = probe_dir / "probe.mjs"
                    gen.write_text(
                        "import {createInitialState,buildOsConfig} from "
                        f"'{quiz_model.resolve().as_uri()}';\n" + state_js.group(1) +
                        "\nconsole.log(JSON.stringify(buildOsConfig(s,"
                        "'2026-07-20T00:00:00.000Z')));\n", encoding="utf-8")
                    live = subprocess.run([node, str(gen)], capture_output=True,
                                          text=True, cwd=str(probe_dir), timeout=60)
                except subprocess.TimeoutExpired:
                    live = None
                finally:
                    shutil.rmtree(probe_dir, ignore_errors=True)
                if live is None:
                    skip("the committed v2 fixture still matches what soul-quiz emits",
                         "the node probe did not finish inside 60s")
                    skip("every quiz role maps to a preset", "the node probe timed out")
                else:
                    emitted = json.loads(live.stdout) if live.returncode == 0 else {}
                    committed = json.loads(v2_fixture.read_text(encoding="utf-8"))
                    check("the committed v2 fixture still matches what soul-quiz emits",
                          live.returncode == 0
                          and emitted.get("schema_version") == committed.get("schema_version")
                          and emitted.get("generator") == committed.get("generator"),
                          f"live={emitted.get('schema_version')}/{emitted.get('generator')} "
                          f"fixture={committed.get('schema_version')}/{committed.get('generator')}"
                          + (f" node_stderr={live.stderr.strip()[:200]}"
                             if live.returncode != 0 else ""))

                    # The importer's constellation map is a copy of the quiz's
                    # role list, and copies drift. Read the ids the model
                    # actually declares and fail here when one has no preset —
                    # a new quiz role should break a test, not quietly land a
                    # nurse on the fallback.
                    declared = set(re.findall(r"role\('([a-z0-9-]+)',",
                                              quiz_model.read_text(encoding="utf-8")))
                    importer_src = (stage / "bin" / "naio-soul-import").read_text(
                        encoding="utf-8")
                    mapped_block = re.search(
                        r"CONSTELLATION_ROLE_MAP.*?\n\}", importer_src, re.DOTALL)
                    mapped_ids = set(re.findall(r'"([a-z0-9-]+)":\s*\(',
                                                mapped_block.group(0) if mapped_block else ""))
                    check("every role the quiz can emit has a preset mapping",
                          declared and not (declared - mapped_ids),
                          f"unmapped: {sorted(declared - mapped_ids)}")

        # -- 12. editing your own season and standing rows ---------------------
        def patch(role, body):
            rq = urllib.request.Request(f"http://127.0.0.1:{port}/api/content/{role}",
                data=json.dumps(body).encode(),
                headers={"Content-Type": "application/json"}, method="POST")
            try:
                with urllib.request.urlopen(rq, timeout=5) as r:
                    return r.status, json.loads(r.read() or b"{}")
            except urllib.error.HTTPError as e:
                return e.code, json.loads(e.read() or b"{}")

        st, out = patch("bedside", {"season": "Certification & consolidation",
                                    "seasonBody": "Depth this season.",
                                    "seasonMeta": "Week 9 of 16"})
        st2, role = get("/api/role/bedside", port)
        check("a season can be set and survives a reload",
              st == 200 and role["content"]["season"] == "Certification & consolidation")
        check("setting a season removes it from the still-needed list",
              not any(n.startswith("season") for n in role["content"].get("needs", [])))

        st, out = patch("bedside", {"currency": [
            {"name": "ACLS", "meta": "Renews 24 October 2026 · no class booked",
             "state": "attention"},
            {"name": "RN license", "meta": "Renews 30 September 2027", "state": "flourishing"}]})
        st2, role = get("/api/role/bedside", port)
        rows = role["content"]["license"]["currency"]
        check("credentials can be added and come back in order",
              st == 200 and len(rows) == 2 and rows[0]["name"] == "ACLS"
              and rows[0]["state"] == "attention")

        st, out = patch("bedside", {"season": "Follow up on MRN 4471902"})
        st2, role = get("/api/role/bedside", port)
        check("editing REFUSES PHI before it is written",
              st == 400 and "MRN" not in json.dumps(role["content"]))

        st, out = patch("bedside", {"license": {"days": 999}})
        check("editing cannot invent a number — only writable fields are accepted",
              st == 400 and "allowed" in out.get("error", ""))

        # a role still on sample gets its OWN empty file, never a promoted demo
        st, out = patch("resident", {"season": "PGY-2 — the long middle"})
        st2, role = get("/api/role/resident", port)
        check("editing a sample role creates an empty real file, not a copy of the demo",
              st == 200 and role["sample"] is False
              and role["content"]["season"] == "PGY-2 — the long middle"
              and role["content"]["actions"] == []
              and role["content"]["momentum"]["hero"] is None)

        st, out = patch("nope", {"season": "x"})
        check("editing an unknown role 404s", st == 404)

        # -- 13. the record verifies itself -----------------------------------
        rel = subprocess.run([sys.executable, str(stage / "tools" / "release.py"),
                              "--skip-tests"], capture_output=True, text=True, cwd=str(stage))
        man_path = stage / "manifest.json"
        check("release.py writes a manifest", rel.returncode == 0 and man_path.is_file())
        man = json.loads(man_path.read_text())
        check("the manifest declares itself unsigned", man.get("signed") is False)
        check("the manifest checksums the whole tree", man.get("file_count", 0) >= 40)

        def naio(*a):
            return subprocess.run([sys.executable, str(stage / "naio-mc"), *a],
                                  capture_output=True, text=True, cwd=str(stage))

        v = naio("verify")
        check("verify passes on an untouched tree",
              v.returncode == 0 and "matches the manifest" in v.stdout)

        code_file = stage / "adapters" / "runtime.py"
        code_file.write_text(code_file.read_text() + "\n# tamper\n")
        v = naio("verify")
        check("verify FAILS and names the file when code changes",
              v.returncode == 1 and "CODE CHANGED" in v.stdout
              and "runtime.py" in v.stdout)
        code_file.write_text(code_file.read_text().replace("\n# tamper\n", ""))

        cfg = stage / "config.json"
        cfg.write_text(json.dumps({**json.loads(cfg.read_text()), "vault_inbox": "Elsewhere"}))
        v = naio("verify")
        check("verify tolerates a file the nurse is meant to edit",
              v.returncode == 0 and "yours to edit" in v.stdout)

        # -- 14. configure guards the paths ------------------------------------
        badvault = workdir / "badvault"
        badvault.mkdir(exist_ok=True)
        (badvault / "handoff MRN 4471902.md").write_text("x")
        (badvault / "ok.md").write_text("x")
        c = naio("configure", "--vault", str(badvault), "--apply")
        check("configure REFUSES a folder whose filenames look like PHI",
              c.returncode == 1 and "look like patient information" in c.stdout
              and "Nothing written" in c.stdout)

        c = naio("configure", "--vault", str(stage / "demo-vault"))
        check("configure dry-runs by default and counts what it would index",
              c.returncode == 0 and "Dry run" in c.stdout
              and "markdown files would be indexed" in c.stdout)

        c = naio("configure", "--vault", "/no/such/place", "--apply")
        check("configure REFUSES a path that does not exist",
              c.returncode == 1 and "not a directory" in c.stdout)

        # -- 16. the Starter Kit seam -------------------------------------------
        # The kit and Mission Control shipped as two artifacts in one folder.
        # These tests are about the join: that it wires the right things, that it
        # refuses a folder that is not a kit, and that the PHI refusal still
        # applies when the path arrives by a friendlier route.
        kit = workdir / "My-Nurse-AI-OS"
        for d in ("00-Start-Here", "01-SOUL", "02-Skills", "03-Memory/inbox",
                  "04-Projects", "05-Learning", "08-Integrations"):
            (kit / d).mkdir(parents=True, exist_ok=True)
        (kit / "01-SOUL" / "SOUL.md").write_text("# SOUL\n")
        (kit / "01-SOUL" / "boundaries.md").write_text("# boundaries\n")
        (kit / "01-SOUL" / "SOUL.template.md").write_text("# template\n")
        # The kit ships a README in 01-SOUL/. It is documentation, not a soul.
        # Counting it caught a real false pass against the actual kit: a folder
        # where nothing had been written yet reported "watching 1 SOUL file".
        (kit / "01-SOUL" / "README.md").write_text("# what this folder is for\n")
        (kit / "04-Projects" / "ccrn.md").write_text("# ccrn\n")

        c = naio("configure", "--kit", str(kit))
        check("configure --kit dry-runs and wires the kit in one flag",
              c.returncode == 0 and "Dry run" in c.stdout
              and "the Library tab" in c.stdout
              and "03-Memory/inbox" in c.stdout)

        cfg_path = stage / "config.json"
        before = cfg_path.read_bytes()
        c = naio("configure", "--kit", str(kit), "--apply")
        wired = json.loads(cfg_path.read_text())
        check("--kit --apply sets vault, library, inbox and soul files together",
              c.returncode == 0
              and wired.get("vault_root") == str(kit)
              and wired.get("content_root") == str(kit / "04-Projects")
              and wired.get("vault_inbox") == "03-Memory/inbox"
              and len(wired.get("soul_files", [])) == 2,
              json.dumps({k: wired.get(k) for k in
                          ("vault_root", "content_root", "vault_inbox", "soul_files")}))

        check("neither a template nor a README is mistaken for a soul file",
              all(not s.endswith(".template.md") and not s.endswith("README.md")
                  for s in wired.get("soul_files", [])),
              str(wired.get("soul_files")))
        cfg_path.write_bytes(before)   # leave the tree as we found it

        # A folder that is not a kit must be refused, not half-configured.
        notkit = workdir / "just-a-folder"
        (notkit / "stuff").mkdir(parents=True, exist_ok=True)
        c = naio("configure", "--kit", str(notkit), "--apply")
        check("configure --kit REFUSES a folder that is not a Starter Kit",
              c.returncode == 1 and "does not look like a Starter Kit" in c.stdout
              and cfg_path.read_bytes() == before)

        # The friendlier route must not be the softer one.
        phikit = workdir / "phi-kit"
        for d in ("00-Start-Here", "01-SOUL", "03-Memory", "04-Projects"):
            (phikit / d).mkdir(parents=True, exist_ok=True)
        (phikit / "03-Memory" / "handoff MRN 4471902.md").write_text("x")
        c = naio("configure", "--kit", str(phikit), "--apply")
        check("configure --kit still REFUSES a kit with PHI-shaped filenames",
              c.returncode == 1 and "look like patient information" in c.stdout
              and cfg_path.read_bytes() == before)

        # A kit with no SOUL file yet is the normal first-run state, not an error.
        newkit = workdir / "fresh-kit"
        for d in ("00-Start-Here", "01-SOUL", "03-Memory/inbox", "04-Projects"):
            (newkit / d).mkdir(parents=True, exist_ok=True)
        (newkit / "01-SOUL" / "SOUL.template.md").write_text("# template\n")
        (newkit / "01-SOUL" / "README.md").write_text("# what this folder is for\n")
        c = naio("configure", "--kit", str(newkit))
        check("a kit with no SOUL.md is wired anyway, and says to take the quiz",
              c.returncode == 0 and "no 01-SOUL/SOUL.md yet" in c.stdout
              and "soul-quiz" in c.stdout)

        # The nudge must survive a kit that ships other soul files — otherwise a
        # non-empty file list reads as "done" on a folder nobody has filled in.
        (newkit / "01-SOUL" / "boundaries.md").write_text("# boundaries\n")
        c = naio("configure", "--kit", str(newkit))
        check("shipped soul files do not silence the missing-SOUL.md warning",
              c.returncode == 0 and "watching 1 SOUL file" in c.stdout
              and "no 01-SOUL/SOUL.md yet" in c.stdout)
        cfg_path.write_bytes(before)

        # -- 16b. the kit that actually ships -----------------------------------
        # Every test above builds its own kit, so they only ever proved that
        # --kit works against the layout the fixture invented. It did not: the
        # published Starter Kit uses Projects/, Memory/ and 00-Start-Here/SOUL.md,
        # and this command refused it outright while telling the nurse to go
        # download the very kit it had just rejected. A green suite said nothing,
        # because nothing pointed at the real thing.
        #
        # So point at the real thing. This reads the kit as it exists in the
        # repo, not a copy of it, and is the check that would have caught it.
        real_kit = HERE.parent.parent / "starter-kit" / "My-Nurse-AI-OS"
        if not real_kit.is_dir():
            skip("configure --kit accepts the published Starter Kit",
                 f"no kit at {real_kit} — running outside the site repo")
            skip("the published kit resolves a real SOUL.md", "same")
        else:
            c = naio("configure", "--kit", str(real_kit))
            check("configure --kit accepts the published Starter Kit",
                  c.returncode == 0
                  and "does not look like a Starter Kit" not in c.stdout
                  and "published Starter Kit layout" in c.stdout,
                  c.stdout.strip().replace("\n", " | ")[:400])

            # Accepting it is not enough; it has to wire the right folders. The
            # nurse's own SOUL.md is the file that decides whether the dashboard
            # knows who it is working for, so that is what gets asserted.
            check("the published kit resolves a real SOUL.md",
                  "watching" in c.stdout and "SOUL.md" in c.stdout
                  and "no 00-Start-Here/SOUL.md yet" not in c.stdout,
                  c.stdout.strip().replace("\n", " | ")[:400])

        # Both layouts must keep working. A fix that swapped one hard-coded
        # guess for another would pass the test above and still be a guess.
        bothkit = workdir / "component-kit"
        for d in ("00-Start-Here", "01-SOUL", "03-Memory/inbox", "04-Projects"):
            (bothkit / d).mkdir(parents=True, exist_ok=True)
        (bothkit / "01-SOUL" / "SOUL.md").write_text("# SOUL\n")
        c = naio("configure", "--kit", str(bothkit))
        check("the component layout still works after the published fix",
              c.returncode == 0 and "component Starter Kit layout" in c.stdout
              and "03-Memory/inbox" in c.stdout)
        cfg_path.write_bytes(before)

        # -- 15. the Apple Notes bridge: never run on a Mac, so guard it statically
        # This is the one component shipped without ever having been executed. We
        # cannot run it here, so we assert the two things that must hold whether or
        # not it has ever run: it never asks Notes for a body, and checking it
        # writes nothing.
        jxa = (stage / "bridges" / "apple_notes.jxa").read_text(encoding="utf-8")
        # Strip comments first — the file documents the rule in a trailing comment
        # ("never note.body()"), and a checker that cannot tell a promise from a
        # call would fail on the very line that keeps the promise.
        jxa_code = [ln.split("//")[0] for ln in jxa.splitlines()]
        body_calls = [ln.strip() for ln in jxa_code
                      if ".body()" in ln or ".plaintext()" in ln]
        check("the Apple Notes bridge never reads a note body", not body_calls,
              "; ".join(body_calls[:2]))

        cfg_before = (stage / "config.json").read_bytes()
        n = naio("notes-check")
        check("notes-check writes nothing",
              (stage / "config.json").read_bytes() == cfg_before)

        if sys.platform != "darwin":
            check("notes-check calls a bridge it cannot run 'inactive', not 'failed'",
                  n.returncode == 0 and "not macOS" in n.stdout
                  and "has not failed at anything" in n.stdout)
        else:
            check("notes-check runs on macOS and reports honestly",
                  n.returncode in (0, 1)
                  and ("no folders to check" in n.stdout or "bridge ran" in n.stdout
                       or "Automation" in n.stdout))

        # -- 6. collector failure: stale badge, server survives --------------
        os.chmod(stage / "adapters" / "runtime.py", 0o000)
        time.sleep(0.2)
        conn = sqlite3.connect(stage / "mission_control.db", timeout=10)
        with conn:
            conn.execute("UPDATE collector_state SET last_ok_ts='2020-01-01T00:00:00+00:00' "
                         "WHERE name='hermes_state'")
        conn.close()
        os.chmod(stage / "adapters" / "runtime.py", 0o644)
        st, cols = get("/api/collectors", port)
        stale = [c for c in cols["collectors"] if c["stale"]]
        check("a stalled collector shows a stale badge", st == 200 and len(stale) >= 1)
        st, _ = get("/api/health", port)
        check("server survives a stalled collector", st == 200)

        # -- backups --------------------------------------------------------
        rc = subprocess.call([sys.executable, str(stage / "mission_control.py"), "--backup"],
                             cwd=str(stage), stdout=subprocess.DEVNULL)
        backups = list((stage / "backups").glob("*"))
        check("backup writes a restore point", rc == 0 and len(backups) == 1)

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        shutil.rmtree(workdir, ignore_errors=True)

    print(f"\n  {len(PASS)} passed, {len(FAIL)} failed"
          + (f", {len(SKIP)} skipped" if SKIP else ""))
    if FAIL:
        print("  failed: " + ", ".join(FAIL))
    print("\n  Agents propose. Humans judge. Nurses steward.\n")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
