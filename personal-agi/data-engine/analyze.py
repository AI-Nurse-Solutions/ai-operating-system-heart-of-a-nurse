#!/usr/bin/env python3
"""Closed-vocabulary analysis engine for the personal Data Analysis Engine pilot.

Judgment happens at spec time: the human declares columns, operations, and
boundaries in spec.json, and this engine executes only that closed vocabulary
over data.csv — no model, no network, no clock, no improvised analysis.
Deterministic by design: the same spec and data always render byte-identical
reports. Boundary doctrine is inherited from the Phase 22 Adoption & Outcomes
Ledger (naio-os/scripts/outcomes.py): results are adoption signals and
learning evidence for the nurse's own judgment, never efficacy claims.

Usage:
    python3 analyze.py ANALYSIS_DIR   # render one analysis's report.md
    python3 analyze.py                # render every analysis under analyses/
    python3 analyze.py --check        # exit 2 if any report is stale
"""

from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parent
ANALYSES_DIR = ENGINE_DIR / "analyses"
SPEC_NAME = "spec.json"
DATA_NAME = "data.csv"
REPORT_NAME = "report.md"

ALLOWED_TIERS = {"green", "yellow"}
ALLOWED_DATA_CLASSES = {"D0", "D1"}
COLUMN_TYPES = {"string", "number", "date"}
CLOSED_OPS = {"count", "count_by", "sum", "mean", "min", "max"}
NUMBER_OPS = {"sum", "mean", "min", "max"}
MAX_ROWS = 10_000

# Screens inherited from the Phase 22 checker: the attestation is the primary
# control, these are backstops that fail closed.
PHI_PATTERNS = (
    (re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"), "SSN-like pattern"),
    (re.compile(r"\b\d{3}[\s.-]\d{3}[\s.-]\d{4}\b"), "phone-like pattern"),
    (
        re.compile(
            r"\b(?:MRN|medical record|patient id|DOB|date of birth|diagnosis|"
            r"ICD-?10|CPT|room number|patient name)\b[: ]",
            re.IGNORECASE,
        ),
        "clinical identifier",
    ),
)
SECRET_PATTERNS = (
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key"),
    (
        re.compile(r"\b(?:sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})\b"),
        "token-like secret",
    ),
    (
        re.compile(r"\b(?:api[_-]?key|password|secret|token)\s*[:=]\s*[^\s`]+", re.IGNORECASE),
        "credential assignment",
    ),
)
# Phrase-based, no negation parsing: keep claims language out of specs.
OVERCLAIM_PHRASES = (
    "clinically validated",
    "clinical efficacy",
    "improves patient outcomes",
    "patient outcome improvement",
    "reduces errors",
    "mortality reduction",
    "safety validated",
    "roi guaranteed",
    "proves roi",
    "staffing reduction",
    "compliance validated",
    "certifies competency",
    "competency certified",
    "performance evaluation",
)

OP_LABELS = {
    "count": "Row count",
    "count_by": "Count by",
    "sum": "Sum of",
    "mean": "Mean of",
    "min": "Minimum of",
    "max": "Maximum of",
}


def sha256_file(path: Path) -> str:
    """Return the SHA-256 hex digest of a file's bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def nonempty_str(value: object) -> bool:
    """Return True when value is a non-empty, non-whitespace string."""
    return isinstance(value, str) and bool(value.strip())


def nonempty_str_list(value: object) -> bool:
    """Return True when value is a non-empty list of non-empty strings."""
    return (
        isinstance(value, list)
        and bool(value)
        and all(nonempty_str(item) for item in value)
    )


def screen(text: str, name: str) -> list[str]:
    """Run the PHI and secret backstop screens over text; return refusals."""
    problems = []
    for pattern, label in PHI_PATTERNS:
        if pattern.search(text):
            problems.append(f"{name}: contains a {label} — analyses carry no PHI")
    for pattern, label in SECRET_PATTERNS:
        if pattern.search(text):
            problems.append(f"{name}: contains a {label} — analyses carry no secrets")
    return problems


def validate_spec(spec: object, name: str) -> list[str]:
    """Run every fail-closed check on a parsed spec; return refusal reasons."""
    if not isinstance(spec, dict):
        return [f"{name}: spec.json must be a JSON object"]
    problems = []
    for field in ("title", "question"):
        if not nonempty_str(spec.get(field)):
            problems.append(f"{name}: {field} missing")
    if spec.get("edena_tier") not in ALLOWED_TIERS:
        problems.append(f"{name}: edena_tier must be 'green' or 'yellow'")
    if spec.get("data_class") not in ALLOWED_DATA_CLASSES:
        problems.append(
            f"{name}: data_class must be 'D0' or 'D1' — the personal data boundary"
        )

    columns = spec.get("columns")
    declared: dict[str, str] = {}
    if not (isinstance(columns, list) and columns):
        problems.append(f"{name}: columns must be a non-empty list")
    else:
        for idx, column in enumerate(columns):
            label = f"{name}: columns[{idx}]"
            if not (isinstance(column, dict) and nonempty_str(column.get("name"))):
                problems.append(f"{label} needs a name")
                continue
            if column.get("type") not in COLUMN_TYPES:
                problems.append(f"{label} type must be one of {sorted(COLUMN_TYPES)}")
                continue
            if column["name"] in declared:
                problems.append(f"{label} duplicates column {column['name']!r}")
                continue
            declared[column["name"]] = column["type"]

    analyses = spec.get("analyses")
    if not (isinstance(analyses, list) and analyses):
        problems.append(f"{name}: analyses must be a non-empty list")
    else:
        for idx, analysis in enumerate(analyses):
            label = f"{name}: analyses[{idx}]"
            if not isinstance(analysis, dict):
                problems.append(f"{label} must be an object")
                continue
            op = analysis.get("op")
            if op not in CLOSED_OPS:
                problems.append(
                    f"{label} op {op!r} is outside the closed vocabulary "
                    f"{sorted(CLOSED_OPS)} — the engine never improvises an analysis"
                )
                continue
            if op == "count":
                continue
            column = analysis.get("column")
            if column not in declared:
                problems.append(f"{label} column {column!r} is not declared")
                continue
            if op in NUMBER_OPS and declared[column] != "number":
                problems.append(f"{label} op {op!r} requires a number column")

    provenance = spec.get("provenance")
    if not isinstance(provenance, dict):
        problems.append(f"{name}: provenance missing")
    else:
        if not nonempty_str(provenance.get("source")):
            problems.append(f"{name}: provenance.source missing")
        if provenance.get("no_phi_attested") is not True:
            problems.append(f"{name}: provenance.no_phi_attested must be true")

    boundaries = spec.get("boundaries")
    if not isinstance(boundaries, dict):
        problems.append(f"{name}: boundaries missing")
    else:
        for field in ("intended_use", "not_claims"):
            if not nonempty_str_list(boundaries.get(field)):
                problems.append(f"{name}: boundaries.{field} must be a non-empty list")

    spec_text = json.dumps(spec).lower()
    for phrase in OVERCLAIM_PHRASES:
        if phrase in spec_text:
            problems.append(
                f"{name}: spec contains the overclaim phrase {phrase!r} — results "
                "here are adoption signals and learning evidence only (Phase 22 "
                "boundary); keep claims language out of specs"
            )
    return problems


def validate_data(spec: dict, data_path: Path, name: str) -> tuple[list[dict], list[str]]:
    """Parse data.csv against the declared columns fail-closed; return rows + refusals."""
    raw = data_path.read_text(encoding="utf-8")
    problems = screen(raw, f"{name}: data.csv")
    declared = [column["name"] for column in spec["columns"]]
    types = {column["name"]: column["type"] for column in spec["columns"]}
    reader = csv.reader(raw.splitlines())
    try:
        header = next(reader)
    except StopIteration:
        return [], problems + [f"{name}: data.csv is empty"]
    if header != declared:
        return [], problems + [
            f"{name}: data.csv header {header!r} must exactly match the "
            f"declared columns {declared!r} — the schema is closed"
        ]
    rows: list[dict] = []
    for line, values in enumerate(reader, start=2):
        if len(values) != len(declared):
            problems.append(f"{name}: data.csv line {line} has {len(values)} cells")
            continue
        row = {}
        for column, value in zip(declared, values):
            if not value.strip():
                problems.append(
                    f"{name}: data.csv line {line} column {column!r} is empty — "
                    "empty cells are refused, not guessed at"
                )
                continue
            if types[column] == "number":
                try:
                    row[column] = float(value)
                except ValueError:
                    problems.append(
                        f"{name}: data.csv line {line} column {column!r} is not a number"
                    )
                    continue
            elif types[column] == "date":
                try:
                    datetime.date.fromisoformat(value.strip())
                except ValueError:
                    problems.append(
                        f"{name}: data.csv line {line} column {column!r} is not an ISO date"
                    )
                    continue
                row[column] = value.strip()
            else:
                row[column] = value.strip()
        if len(row) == len(declared):
            rows.append(row)
    if len(rows) > MAX_ROWS:
        problems.append(
            f"{name}: data.csv has {len(rows)} rows — the personal engine caps at "
            f"{MAX_ROWS}; this is not a warehouse"
        )
    return rows, problems


def format_number(value: float) -> str:
    """Format a number without a trailing .0 for whole values."""
    return f"{int(value)}" if value == int(value) else f"{value:.2f}"


def run_analysis(analysis: dict, rows: list[dict]) -> list[str]:
    """Execute one closed-vocabulary operation; return its markdown lines."""
    op = analysis["op"]
    if op == "count":
        return [f"### {OP_LABELS['count']}", "", f"**{len(rows)}** row(s).", ""]
    column = analysis["column"]
    heading = f"### {OP_LABELS[op]} `{column}`"
    if op == "count_by":
        counts: dict[str, int] = {}
        for row in rows:
            key = str(row[column])
            counts[key] = counts.get(key, 0) + 1
        lines = [heading, "", "| Value | Count |", "|---|---|"]
        for key, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"| {key} | {count} |")
        lines.append("")
        return lines
    values = [row[column] for row in rows]
    if not values:
        return [heading, "", "No rows — nothing to compute.", ""]
    if op == "sum":
        result = format_number(sum(values))
    elif op == "mean":
        result = f"{sum(values) / len(values):.2f}"
    elif op == "min":
        result = format_number(min(values))
    else:
        result = format_number(max(values))
    return [heading, "", f"**{result}**", ""]


def render_report(analysis_dir: Path, spec: dict, rows: list[dict]) -> str:
    """Render the deterministic report — provenance, results, and the boundary."""
    lines = [
        f"# Analysis report — {spec['title']}",
        "",
        f"> **Question:** {spec['question']}",
        f"> **EDENA tier:** {spec['edena_tier']} · **Data class:** {spec['data_class']} · "
        f"**Rows:** {len(rows)}",
        f"> **Provenance:** `{DATA_NAME}` sha256 `{sha256_file(analysis_dir / DATA_NAME)}` · "
        f"`{SPEC_NAME}` sha256 `{sha256_file(analysis_dir / SPEC_NAME)}` · "
        f"source: {spec['provenance']['source']}",
        "",
        "## Results",
        "",
    ]
    for analysis in spec["analyses"]:
        lines.extend(run_analysis(analysis, rows))
    lines.extend(
        [
            "---",
            "",
            "These results are observations of your own recorded data — adoption "
            "signals and learning evidence for your judgment, per the Phase 22 "
            "boundary. They are not clinical-efficacy, patient-outcome, safety, "
            "ROI, staffing, compliance, certification, or performance-evaluation "
            "claims, and they feed no employer analytics. This is an Observe/Draft "
            "artifact rendered deterministically by `analyze.py` from `data.csv` "
            "and `spec.json` — edit those, not this file.",
            "",
            "*Agents propose. Humans judge. Nurses steward.*",
            "",
        ]
    )
    return "\n".join(lines)


def render(analysis_dir: Path, out_path: Path | None = None) -> list[str]:
    """Validate one analysis fail-closed and write its report; return refusals."""
    name = analysis_dir.name
    spec_path = analysis_dir / SPEC_NAME
    data_path = analysis_dir / DATA_NAME
    if not spec_path.is_file():
        return [f"{name}: {SPEC_NAME} missing"]
    if not data_path.is_file():
        return [f"{name}: {DATA_NAME} missing"]
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        return [f"{name}: {SPEC_NAME} is not valid JSON ({err})"]
    problems = validate_spec(spec, name)
    problems.extend(screen(json.dumps(spec), f"{name}: {SPEC_NAME}"))
    if problems:
        return problems
    rows, data_problems = validate_data(spec, data_path, name)
    if data_problems:
        return data_problems
    report = render_report(analysis_dir, spec, rows)
    (out_path or analysis_dir / REPORT_NAME).write_text(report, encoding="utf-8")
    return []


def analysis_dirs() -> list[Path]:
    """Return every analysis directory, sorted by name."""
    if not ANALYSES_DIR.is_dir():
        return []
    return sorted(path for path in ANALYSES_DIR.iterdir() if path.is_dir())


def check() -> list[str]:
    """Re-render every analysis to a temp file and report stale or refused reports."""
    problems = []
    dirs = analysis_dirs()
    if not dirs:
        problems.append("analyses/: no analyses found")
    for analysis_dir in dirs:
        report_path = analysis_dir / REPORT_NAME
        with tempfile.TemporaryDirectory() as tmp:
            fresh_path = Path(tmp) / REPORT_NAME
            refusals = render(analysis_dir, out_path=fresh_path)
            if refusals:
                problems.extend(refusals)
                continue
            if not report_path.is_file():
                problems.append(f"{analysis_dir.name}: {REPORT_NAME} is missing — render it")
            elif report_path.read_bytes() != fresh_path.read_bytes():
                problems.append(
                    f"{analysis_dir.name}: {REPORT_NAME} is stale — re-run analyze.py"
                )
    return problems


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: render one or all analyses, or verify freshness with --check."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("analysis_dir", nargs="?", type=Path, default=None)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    if args.check:
        problems = check()
        if problems:
            for problem in problems:
                print(f"REFUSED: {problem}")
            return 2
        print("OK: every report matches its spec and data")
        return 0

    dirs = [args.analysis_dir] if args.analysis_dir else analysis_dirs()
    if not dirs:
        print("REFUSED: no analyses found")
        return 2
    problems = []
    for analysis_dir in dirs:
        refusals = render(analysis_dir)
        if refusals:
            problems.extend(refusals)
        else:
            print(f"Rendered {analysis_dir.name}/{REPORT_NAME}")
    if problems:
        for problem in problems:
            print(f"REFUSED: {problem}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
