#!/usr/bin/env python3
"""Build the committed healthcare sandbox artifacts (Phase 3).

Expands the reviewed case catalog into FHIR-shaped bundles and case
summaries under mission-control/healthcare-sandbox/. Deterministic:
running twice produces byte-identical output; CI rebuilds twice and
diffs. The README.md in the target tree is authored, not generated,
and is left untouched.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "naio-integrations" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from naio_integrations.sandbox import SyntheticPatientSandbox  # noqa: E402

OUTPUT_ROOT = ROOT / "mission-control" / "healthcare-sandbox"


def main() -> int:
    sandbox = SyntheticPatientSandbox()
    for case_id in sandbox.case_ids():
        case_dir = OUTPUT_ROOT / "cases" / case_id
        case_dir.mkdir(parents=True, exist_ok=True)
        bundle_path = case_dir / "bundle.json"
        bundle_path.write_text(
            json.dumps(sandbox.build_case(case_id), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"built {bundle_path.relative_to(ROOT)}")
        summary_path = case_dir / "case-summary.md"
        summary_path.write_text(sandbox.case_summary(case_id), encoding="utf-8")
        print(f"built {summary_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
