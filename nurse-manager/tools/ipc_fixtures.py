#!/usr/bin/env python3
"""Drive every CLI command once and capture its IPC envelope.

Used by the contract tests (Python and Node) so that what is validated
is what the real command surface prints, not a hand-written sample.

    python3 nurse-manager/tools/ipc_fixtures.py OUTDIR   # writes OUTDIR/<name>.json
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nurse_manager import cli  # noqa: E402

OWNER = "Sample Manager"
WEEK, TODAY = "2026-09-28", "2026-09-30"


def _run(*argv) -> tuple[int, dict]:
    return cli.run([str(a) for a in argv])


def collect(workdir: Path) -> dict[str, dict]:
    """Return {fixture name: envelope}, covering every command at least once."""
    ws, empty = workdir / "ws", workdir / "empty"
    out: dict[str, dict] = {}

    def keep(name: str, *argv) -> dict:
        code, envelope = _run(*argv)
        if (code == 0) != envelope.get("ok"):
            raise RuntimeError(f"{name}: exit code {code} disagrees with envelope")
        out[name] = envelope
        return envelope.get("data", {})

    keep("sample", "sample", ws)
    keep("init", "init", empty, "--name", "Empty workspace", "--owner", "Test Manager")
    mission = keep("mission", "mission", ws, "--today", TODAY, "--week", WEEK)
    for item in mission["projects_in_motion"]["items"]:
        keep(f"project-{item['id']}", "project", ws, "--id", item["id"], "--today", TODAY)
    keep("error-project-unknown", "project", ws, "--id", "prj-000000000000", "--today", TODAY)
    keep("mission-empty", "mission", empty, "--today", TODAY, "--week", WEEK)
    keep("board", "board", ws)
    keep("table", "table", ws)
    draft = keep("brief", "brief", ws, "--week", WEEK, "--today", TODAY)
    keep("show-draft", "show", ws, "--revision", draft["id"])
    keep("accept", "accept", ws, "--revision", draft["id"], "--reviewer", OWNER,
         "--sha", draft["sha256"])
    keep("show-accepted", "show", ws, "--revision", draft["id"])
    keep("mission-after-accept", "mission", ws, "--today", TODAY, "--week", WEEK)
    keep("export-denied", "export", ws, "--revision", draft["id"], "--file", "../escape.md",
         "--by", OWNER)
    action = keep("export", "export", ws, "--revision", draft["id"], "--file", "week.md",
                  "--by", OWNER)
    keep("mission-awaiting-approval", "mission", ws, "--today", TODAY, "--week", WEEK)
    keep("approve", "approve", ws, "--action", action["id"], "--approver", OWNER,
         "--sha", action["payload_sha256"], "--destination", "week.md")
    keep("run", "run", ws, "--action", action["id"], "--actor", OWNER)
    keep("backup", "backup", ws, workdir / "backup.sqlite")
    keep("restore", "restore", ws, workdir / "backup.sqlite")
    keep("error-accept", "accept", ws, "--revision", draft["id"], "--reviewer", "Someone Else",
         "--sha", draft["sha256"])
    keep("error-restore-missing", "restore", ws, workdir / "missing.sqlite")
    return out


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    target = Path(argv[0])
    target.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for name, envelope in collect(Path(tmp)).items():
            (target / f"{name}.json").write_text(
                json.dumps(envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
