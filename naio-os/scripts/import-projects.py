#!/usr/bin/env python3
"""
NAIO OS — import-projects.py
Validates a naio-projects.json export from the Life & Projects Quiz against
schema + safety contract. Phase 2 is DRY-RUN only: no files are written.

Refuses (exit code 2) if:
  - JSON is malformed or fails JSON Schema validation
  - Project count does not match projects length
  - Any EDENA tier exceeds onboarding clamp (green|yellow)
  - Any file_path escapes 04-Projects/
  - PHI indicators are detected in project text
"""
import argparse, json, re, sys
from pathlib import Path

PHI_PATTERNS = [
    (re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"), "SSN-like pattern"),
    (re.compile(r"\b\d{3}[\s.-]?\d{3}[\s.-]?\d{4}\b", re.I), "phone-like pattern"),
    (re.compile(r"\b[A-Z0-9._%+-]+@(?:hospital|clinic|health|gov)\.[A-Z]{2,}\b", re.I), "institutional email"),
    (re.compile(r"\b(?:MRN|medical record|patient id|DOB|date of birth|diagnosis|ICD-?10|CPT)\b[: ]", re.I), "clinical identifier"),
    (re.compile(r"\b(?:insurance|medicaid|medicare|policy)\s*(?:#|number|id)\b", re.I), "insurance identifier"),
]
ALLOWED_TIERS = {"green", "yellow"}
ALLOWED_GATES = {"every-output", "before-external-use", "forced-irreversible"}


def log(ok, msg):
    mark = "✅" if ok is True else ("❌" if ok is False else "ℹ️")
    print(f"  {mark} {msg}")


def refuse(msg):
    print(f"\n❌ REFUSED: {msg}", file=sys.stderr)
    sys.exit(2)


def safe_project_path(path_text: str) -> bool:
    p = Path(path_text)
    if p.is_absolute():
        return False
    parts = p.parts
    return bool(parts) and parts[0] == "04-Projects" and ".." not in parts and path_text.endswith(".md")


def main():
    ap = argparse.ArgumentParser(description="Validate a naio-projects.json import.")
    ap.add_argument("projects", help="path to naio-projects.json")
    ap.add_argument("--schema", default=None, help="path to naio-projects.schema.json")
    ap.add_argument("--apply", action="store_true", help="(Phase 3+) write files; default is dry-run")
    args = ap.parse_args()

    print(f"\n=== import-projects [{'APPLY' if args.apply else 'DRY-RUN'}] ===")
    if args.apply:
        refuse("--apply is reserved for Phase 3+ (live Hermes/vault writes). Use dry-run now.")

    path = Path(args.projects)
    if not path.is_file():
        refuse(f"file not found: {path}")

    print("\n[1] Loading naio-projects.json...")
    data: dict | None = None
    try:
        raw = path.read_text(encoding="utf-8")
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            data = parsed
        log(True, f"valid JSON ({len(raw)} bytes)")
    except Exception as e:
        refuse(f"malformed JSON: {e}")
    if data is None:
        refuse("root must be a JSON object")
    assert data is not None

    print("\n[2] Schema validation...")
    schema_path = Path(args.schema) if args.schema else Path(__file__).resolve().parent.parent / "schema" / "naio-projects.schema.json"
    try:
        import jsonschema
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        jsonschema.validate(data, schema)
        log(True, f"schema valid ({schema_path.name})")
    except ImportError:
        print("  ⚠️  jsonschema not installed — minimal structural checks only")
        for key in ["schema_version", "generated_at", "identity", "spheres_active", "project_count", "projects"]:
            if key not in data:
                refuse(f"missing required key: {key}")
        log(True, "structural keys present (jsonschema not installed)")
    except Exception as e:
        refuse(f"schema validation failed: {e}")

    projects = data.get("projects", [])
    print("\n[3] Count + tiers + gates...")
    if data.get("project_count") != len(projects):
        refuse(f"project_count mismatch: {data.get('project_count')} vs {len(projects)}")
    log(True, f"project_count matches ({len(projects)})")

    for i, pr in enumerate(projects, start=1):
        name = pr.get("name", f"project-{i}")
        tier = pr.get("edena_tier")
        gate = pr.get("human_gate")
        fpath = pr.get("file_path", "")
        if tier not in ALLOWED_TIERS:
            log(False, f"{name}: tier {tier}")
            refuse("onboarding project tiers must be green|yellow")
        if gate not in ALLOWED_GATES:
            log(False, f"{name}: gate {gate}")
            refuse("unknown human gate")
        if not safe_project_path(fpath):
            log(False, f"{name}: unsafe path {fpath}")
            refuse("project file paths must stay under 04-Projects/*.md")
    log(True, "all project tiers, gates, and file paths are safe")

    print("\n[4] PHI heuristic screen...")
    blob = json.dumps(data)
    hits = []
    for pat, label in PHI_PATTERNS:
        m = pat.search(blob)
        if m:
            hits.append(f"{label} (matched: {m.group(0)[:24]!r})")
            log(False, f"hit: {label}")
    if hits:
        refuse("PHI indicators detected: " + "; ".join(hits))
    log(True, "no PHI indicators detected")

    print("\n[5] Summary")
    print(f"  ℹ️  Name: {data.get('identity', {}).get('name','(unset)')}")
    print(f"  ℹ️  Spheres: {', '.join(data.get('spheres_active', [])) or '(none)'}")
    print(f"  ℹ️  Projects: {len(projects)}")
    print("\n✅ VALID: naio-projects.json is safe to import (dry-run). Nothing was written.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:
        print(f"\n❌ INTERNAL ERROR: {e}", file=sys.stderr)
        sys.exit(1)
