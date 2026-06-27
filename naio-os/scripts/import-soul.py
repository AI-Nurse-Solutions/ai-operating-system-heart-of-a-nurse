#!/usr/bin/env python3
"""
NAIO OS — import-soul.py
Validates a naio-soul.json export against the schema + safety contract.
In --apply mode (Phase 3), will write SOUL files + project prompts into the
target vault. In Phase 2, --dry-run is the default and only mode.

Refuses (exit code 2) if:
  - JSON is malformed or fails JSON Schema validation
  - boundaries.no_phi_confirmed is not True
  - boundaries.no_clinical_decisions_confirmed is not True
  - Any tier_ceilings value is not green|yellow (onboarding clamp)
  - PHI indicators detected (heuristic screen)

Exit 0 = valid + safe; exit 2 = refused; exit 1 = internal error.
"""
import argparse, json, os, re, sys
from pathlib import Path

PHI_PATTERNS = [
    (re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"), "SSN-like pattern"),
    (re.compile(r"\b\d{3}[\s.-]?\d{3}[\s.-]?\d{4}\b", re.I), "phone-like pattern"),
    (re.compile(r"\b[A-Z0-9._%+-]+@hospital|\.health|\.gov\b", re.I), "institutional email"),
    (re.compile(r"\b(?:MRN|medical record|patient id|DOB|date of birth|diagnosis|ICD-?10|CPT)\b[: ]", re.I), "clinical identifier"),
    (re.compile(r"\b(?:insurance|medicaid|medicare|policy)\s*(?:#|number|id)\b", re.I), "insurance identifier"),
    (re.compile(r"\b(?:John|Jane)\s+Doe\b|\bDOB:\s*\d", re.I), "placeholder patient ref"),
]
ALLOWED_CEILINGS = {"green", "yellow"}

def log(ok, msg):
    mark = "✅" if ok is True else ("❌" if ok is False else "ℹ️")
    print(f"  {mark} {msg}")

def refuse(msg):
    print(f"\n❌ REFUSED: {msg}", file=sys.stderr)
    sys.exit(2)

def main():
    ap = argparse.ArgumentParser(description="Validate a naio-soul.json import.")
    ap.add_argument("soul", help="path to naio-soul.json")
    ap.add_argument("--schema", default=None, help="path to naio-soul.schema.json")
    ap.add_argument("--apply", action="store_true", help="(Phase 3) write files; default is dry-run")
    ap.add_argument("--target", default=None, help="target vault root for --apply")
    args = ap.parse_args()

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"\n=== import-soul [{mode}] ===")

    if args.apply:
        refuse("--apply is reserved for Phase 3 (live Hermes config). Use --dry-run (default).")

    soul_path = Path(args.soul)
    if not soul_path.is_file():
        refuse(f"file not found: {soul_path}")

    # --- 1. Load + parse JSON ---
    print("\n[1] Loading naio-soul.json...")
    data = None
    try:
        raw = soul_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        log(True, f"valid JSON ({len(raw)} bytes)")
    except json.JSONDecodeError as e:
        refuse(f"malformed JSON: {e}")
    if data is None:
        refuse("malformed JSON (parsed to None)")
    assert isinstance(data, dict)
    soul_data: dict = data

    # --- 2. Schema validation (if jsonschema available) ---
    print("\n[2] Schema validation...")
    schema_path = Path(args.schema) if args.schema else soul_path.parent.parent / "schema" / "naio-soul.schema.json"
    if not schema_path.is_file():
        schema_path = Path(__file__).resolve().parent.parent / "schema" / "naio-soul.schema.json"
    try:
        import jsonschema
        if schema_path.is_file():
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            jsonschema.validate(soul_data, schema)
            log(True, f"schema valid ({schema_path.name})")
        else:
            print("  ⚠️  schema file not found — skipping jsonschema validation")
    except ImportError:
        print("  ⚠️  jsonschema not installed — minimal structural checks only")
        required = ["schema_version", "generated_at", "identity", "spheres", "tier_ceilings", "boundaries", "doctrine"]
        missing = [k for k in required if k not in soul_data]
        if missing:
            refuse(f"missing required keys: {missing}")
        log(True, "structural keys present (jsonschema not installed)")
    except Exception as e:
        refuse(f"schema validation failed: {e}")

    # --- 3. Boundary confirmations (hard) ---
    print("\n[3] Boundary confirmations...")
    b = soul_data.get("boundaries", {})
    phi = b.get("no_phi_confirmed") is True
    clin = b.get("no_clinical_decisions_confirmed") is True
    log(phi, f"no_phi_confirmed = {b.get('no_phi_confirmed')}")
    log(clin, f"no_clinical_decisions_confirmed = {b.get('no_clinical_decisions_confirmed')}")
    if not (phi and clin):
        refuse("boundary confirmations missing — both must be true to import")

    # --- 4. Onboarding tier clamp (green|yellow only) ---
    print("\n[4] Tier clamp (onboarding allows green|yellow only)...")
    ceilings = soul_data.get("tier_ceilings", {})
    bad_tiers = {k: v for k, v in ceilings.items() if v not in ALLOWED_CEILINGS}
    for k, v in ceilings.items():
        log(v in ALLOWED_CEILINGS, f"{k}: {v}")
    if bad_tiers:
        refuse(f"tiers above yellow are not allowed at onboarding: {bad_tiers}")

    # --- 5. PHI heuristic screen ---
    print("\n[5] PHI heuristic screen...")
    screen_blob = json.dumps(soul_data)
    phi_hits = []
    for pat, label in PHI_PATTERNS:
        m = pat.search(screen_blob)
        if m:
            phi_hits.append(f"{label} (matched: '{m.group(0)[:24]}')")
            log(False, f"hit: {label}")
    if phi_hits:
        refuse(f"PHI indicators detected: {'; '.join(phi_hits)} — remove before importing")
    log(True, "no PHI indicators detected")

    # --- 6. Summary ---
    print("\n[6] Summary")
    ident = soul_data.get("identity", {})
    print(f"  ℹ️  Name: {ident.get('name','(unset)')}")
    print(f"  ℹ️  Role: {ident.get('role','(unset)')}")
    print(f"  ℹ️  Spheres: {', '.join(soul_data.get('spheres', [])) or '(none)'}")
    print(f"  ℹ️  Ceilings: {ceilings}")
    print(f"  ℹ️  Doctrine: {soul_data.get('doctrine', {}).get('edena', '?')}")
    print(f"  ℹ️  Values: {len(soul_data.get('values', []))} declared")

    print(f"\n✅ VALID: naio-soul.json is safe to import (dry-run). Nothing was written.")
    print(f"   (Phase 3 will apply this into a Hermes config with live human gates.)")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:
        print(f"\n❌ INTERNAL ERROR: {e}", file=sys.stderr)
        sys.exit(1)
