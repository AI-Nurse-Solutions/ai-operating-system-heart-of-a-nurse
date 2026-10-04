#!/usr/bin/env python3
"""Write (or check) the committed shadow report for build step 4.5.

    python3 nurse-manager/tools/shadow_report.py          # rewrite the report
    python3 nurse-manager/tools/shadow_report.py --check  # fail if it is stale
    python3 nurse-manager/tools/shadow_report.py --adapter jev   # step 4.5b: asks for the key

The report shadows the review-always baseline against the synthetic
labeled set. It is the floor any real suggester has to beat, and it proves
the harness end to end.

With ``--adapter jev`` (step 4.5b, ADR 0006) the steward runs the live JEV
adapter on the same reviewed, pinned synthetic set. The TypeSafe key is read
from standard input (at a terminal, a prompt that does not show it), never
from an argument, the environment, or a file left on disk, and the
report is printed, not committed: it is evidence for a decision, and JEV's
answers can change. Nothing JEV answers reaches a decision.
"""

from __future__ import annotations

import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nurse_manager.classifier import JevClient, JevDecisionAdapter  # noqa: E402
from nurse_manager.credentials import SECRET  # noqa: E402
from nurse_manager.decision_adapter import (  # noqa: E402
    TRUSTED_SET_DIGESTS,
    ReviewAlwaysBaseline,
    default_set_path,
    load_labeled_set,
    render_markdown,
    run_shadow,
)

REPORT = default_set_path().with_name("shadow-edena-decisions.report.md")


def main(argv: list[str]) -> int:
    digest = load_labeled_set()["sha256"]
    if digest not in TRUSTED_SET_DIGESTS:
        print(f"the labeled set changed; after review, pin its sha256 in"
              f" decision_adapter.TRUSTED_SET_DIGESTS:\n    {digest}", file=sys.stderr)
        return 1
    if argv[:2] == ["--adapter", "jev"]:
        key = (getpass.getpass("TypeSafe API key (not shown): ") if sys.stdin.isatty()
               else sys.stdin.readline()).strip()
        if not SECRET.fullmatch(key):
            print("that is not a TypeSafe key; it is not repeated here", file=sys.stderr)
            return 1
        print(render_markdown(run_shadow(JevDecisionAdapter(JevClient(key)))))
        return 0
    text = render_markdown(run_shadow(ReviewAlwaysBaseline()))
    if "--check" in argv:
        if not REPORT.is_file() or REPORT.read_text(encoding="utf-8") != text:
            print(f"{REPORT.name} is stale; run tools/shadow_report.py", file=sys.stderr)
            return 1
        print(f"{REPORT.name} is current")
        return 0
    REPORT.write_text(text, encoding="utf-8")
    print(f"wrote {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
