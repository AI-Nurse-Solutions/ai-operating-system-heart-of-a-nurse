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

Two rules govern how the checks are split:

  * Structure is the schema's job. Every type, pattern, enum, required field,
    closed object, and conditional lives in training-example.schema.json and is
    enforced here by validating against it — never by a second hand-rolled copy
    of the same rule. A gate that only checked what it remembered to check would
    pass `input: 123` and a reviewer list of integers, which an earlier draft of
    this file did.
  * Everything the schema cannot express is explicit below: PHI-shaped text
    anywhere in the record, ids reused across files, and sealed splits staying
    sealed.

Validation is required, not best-effort. Missing jsonschema refuses the run the
same way the SOUL importer does, because a validator that silently degrades to
"looked fine to me" is the failure it exists to prevent.

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
from typing import Iterator, NoReturn

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = Path(__file__).resolve().parent / "schema" / "training-example.schema.json"
SEALED_SPLITS = {"eval_frozen", "injection_suite"}

sys.path.insert(0, str(ROOT / "naio-os" / "mission-control"))
from adapters.phi import PHI_PATTERNS  # noqa: E402


class DuplicateKeyError(ValueError):
    pass


def refuse(message: str) -> NoReturn:
    print(f"\n❌ REFUSED: {message}", file=sys.stderr)
    raise SystemExit(2)


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    """A record whose last duplicate key silently wins is a record nobody reviewed."""
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def build_validator():
    if not SCHEMA.is_file():
        refuse("schema file not found; validation cannot proceed")
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except Exception as error:
        refuse(
            f"required jsonschema validator unavailable: {error}. "
            "Install naio-os/requirements-import-soul.txt in an isolated environment"
        )
    try:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
        Draft202012Validator.check_schema(schema)
    except Exception as error:
        refuse(f"schema is not usable: {error}")
    return Draft202012Validator(schema, format_checker=FormatChecker())


def walk_strings(node: object, path: str = "") -> Iterator[tuple[str, str]]:
    """Every string in the record, with the path that leads to it."""
    if isinstance(node, str):
        yield path or "<record>", node
    elif isinstance(node, dict):
        for key, value in node.items():
            yield from walk_strings(value, f"{path}.{key}" if path else str(key))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from walk_strings(value, f"{path}[{index}]")


def scan_phi(record: dict) -> list[str]:
    """Scan the whole record. Naming the fields to scan is how fields get missed."""
    hits = []
    for location, text in walk_strings(record):
        for pattern, label in PHI_PATTERNS:
            if re.search(pattern, text, flags=re.IGNORECASE):
                hits.append(f"{location}: looks like a {label}")
    return hits


def schema_problems(record: dict, validator) -> list[str]:
    problems = []
    for error in sorted(validator.iter_errors(record), key=lambda item: list(item.absolute_path)):
        location = ".".join(str(part) for part in error.absolute_path) or "<record>"
        # A conditional branch explains itself through its title, so the rule is
        # written once — in the schema — and only its wording lands here.
        hint = error.schema.get("title") if isinstance(error.schema, dict) else None
        problems.append(f"{location}: {error.message}" + (f" — {hint}" if hint else ""))
    return problems


def semantic_problems(record: dict) -> list[str]:
    problems = []
    if record.get("split") in SEALED_SPLITS and record.get("origin") == "harvested":
        problems.append("a sealed split may not contain checkpoint-harvested records")
    return problems


def read_records(path: Path) -> list[tuple[int, dict]]:
    records = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line, object_pairs_hook=reject_duplicate_keys)
        except (json.JSONDecodeError, DuplicateKeyError) as error:
            refuse(f"{path}:{number}: {error}")
        if not isinstance(record, dict):
            refuse(f"{path}:{number}: a record must be a JSON object")
        records.append((number, record))
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="JSONL corpus files")
    parser.add_argument(
        "--schema-only",
        action="store_true",
        help="check that the schema loads and compiles, then exit",
    )
    args = parser.parse_args()

    validator = build_validator()

    if args.schema_only:
        print(f"schema ok — {len(validator.schema.get('properties', {}))} declared fields")
        return 0

    if not args.paths:
        parser.error("give at least one corpus file, or --schema-only")

    failures = 0
    seen: dict[str, str] = {}
    total = 0
    for path in args.paths:
        for number, record in read_records(path):
            total += 1
            location = f"{path}:{number}"
            identifier = record.get("example_id")
            if isinstance(identifier, str):
                if identifier in seen:
                    print(f"{location}: example_id '{identifier}' already used at {seen[identifier]}")
                    failures += 1
                else:
                    seen[identifier] = location
            for problem in (
                schema_problems(record, validator)
                + semantic_problems(record)
                + scan_phi(record)
            ):
                print(f"{location}: {problem}")
                failures += 1

    if failures:
        print(f"\n{failures} problem(s). The corpus does not pass the gate.", file=sys.stderr)
        return 1

    print(f"{total} record(s) passed. Detection only — a reviewer still reads every one.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
