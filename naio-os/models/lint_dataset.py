#!/usr/bin/env python3
"""
Dataset gate for NAIO fine-tuning corpora.

A rule in a plan is not a control. "No PHI in the training data" becomes a
control only when something refuses the file, so this refuses the file.

It imports PHI_PATTERNS from the Mission Control adapter rather than carrying
its own copy, for the reason that module already gives: three copies of a
detection list drifted, and a control that means something different depending
on which door you came through is not a control. The training corpus is a fourth
door.

The same caveat applies here as there: detection, not prevention. A clean run
says nothing looked like PHI. It cannot say the corpus is clean, and no reviewer
should read it that way.

Beyond PHI it enforces the parts of the plan a human reviewer reliably forgets:
governance vocabulary that the runtime can actually enforce, an approved record
having named a reviewer, sealed splits staying sealed, and preference pairs
coming from a checkpoint rather than from someone's imagination.

Usage:
    python3 naio-os/models/lint_dataset.py corpus/*.jsonl
    python3 naio-os/models/lint_dataset.py --schema-only
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = Path(__file__).resolve().parent / "schema" / "training-example.schema.json"

sys.path.insert(0, str(ROOT / "naio-os" / "mission-control"))
from adapters.phi import PHI_PATTERNS  # noqa: E402

SCANNED_FIELDS = ("input", "ideal_response", "rejected_response", "notes")


def load_schema() -> dict:
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def enums(schema: dict) -> dict[str, list[str]]:
    """The enum vocabulary, read from the schema so the lint cannot drift from it."""
    found: dict[str, list[str]] = {}

    def walk(node: object, name: str | None) -> None:
        if isinstance(node, dict):
            if "enum" in node and name:
                found.setdefault(name, list(node["enum"]))
            for key, value in node.items():
                walk(value, key if key not in {"properties", "items", "allOf"} else name)
        elif isinstance(node, list):
            for value in node:
                walk(value, name)

    walk(schema.get("properties", {}), None)
    return found


def scan_phi(record: dict) -> list[str]:
    hits = []
    for field in SCANNED_FIELDS:
        text = record.get(field)
        if not isinstance(text, str):
            continue
        for pattern, label in PHI_PATTERNS:
            if re.search(pattern, text, flags=re.IGNORECASE):
                hits.append(f"{field}: looks like a {label}")
    return hits


def check(record: dict, schema: dict, vocabulary: dict[str, list[str]]) -> list[str]:
    problems = []

    for field in schema.get("required", []):
        if not record.get(field):
            problems.append(f"missing required field '{field}'")

    for field in set(record) - set(schema.get("properties", {})):
        problems.append(f"unknown field '{field}' — the schema is closed")

    for field, allowed in vocabulary.items():
        value = record.get(field)
        if isinstance(value, str) and value not in allowed:
            problems.append(
                f"'{field}' is '{value}', which the runtime cannot enforce; "
                f"allowed: {', '.join(allowed)}"
            )
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item not in allowed:
                    problems.append(f"'{field}' contains unenforceable value '{item}'")

    if record.get("review_status") == "approved" and not record.get("reviewers"):
        problems.append("approved with no named reviewer")

    if record.get("rejected_response") and record.get("origin") != "harvested":
        problems.append(
            "rejected_response on a non-harvested record — preference pairs come "
            "from a checkpoint, not from an authored strawman"
        )

    if record.get("split") in {"eval_frozen", "injection_suite"} and record.get("origin") == "harvested":
        problems.append("a sealed split may not contain checkpoint-harvested records")

    problems.extend(scan_phi(record))
    return problems


def read_records(path: Path) -> list[tuple[int, dict]]:
    records = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            records.append((number, json.loads(line)))
        except json.JSONDecodeError as error:
            print(f"{path}:{number}: not valid JSON — {error}", file=sys.stderr)
            raise SystemExit(2)
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="JSONL corpus files")
    parser.add_argument(
        "--schema-only",
        action="store_true",
        help="check that the schema loads and its vocabulary is readable, then exit",
    )
    args = parser.parse_args()

    schema = load_schema()
    vocabulary = enums(schema)

    if args.schema_only:
        print(f"schema ok — {len(vocabulary)} enumerated fields")
        return 0

    if not args.paths:
        parser.error("give at least one corpus file, or --schema-only")

    failures = 0
    seen: dict[str, str] = {}
    for path in args.paths:
        for number, record in read_records(path):
            identifier = record.get("example_id")
            location = f"{path}:{number}"
            if identifier in seen:
                print(f"{location}: example_id '{identifier}' already used at {seen[identifier]}")
                failures += 1
            elif isinstance(identifier, str):
                seen[identifier] = location
            for problem in check(record, schema, vocabulary):
                print(f"{location}: {problem}")
                failures += 1

    if failures:
        print(f"\n{failures} problem(s). The corpus does not pass the gate.", file=sys.stderr)
        return 1

    print(f"{len(seen)} record(s) passed. Detection only — a reviewer still reads every one.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
