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
from typing import NoReturn

PHI_PATTERNS = [
    (re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"), "SSN-like pattern"),
    (re.compile(r"\b\d{3}[\s.-]?\d{3}[\s.-]?\d{4}\b", re.I), "phone-like pattern"),
    (re.compile(r"\b[A-Z0-9._%+-]+@hospital|\.health|\.gov\b", re.I), "institutional email"),
    (re.compile(r"\b(?:MRN|medical record|patient id|DOB|date of birth|diagnosis|ICD-?10|CPT)\b[: ]", re.I), "clinical identifier"),
    (re.compile(r"\b(?:insurance|medicaid|medicare|policy)\s*(?:#|number|id)\b", re.I), "insurance identifier"),
    (re.compile(r"\b(?:John|Jane)\s+Doe\b|\bDOB:\s*\d", re.I), "placeholder patient ref"),
]
ALLOWED_CEILINGS = {"green", "yellow"}
SUPPORTED_SCHEMA_VERSIONS = {"1.0.0", "2.0.0"}
GOVERNANCE_LEVELS = (
    "independent-private",
    "prepare-only",
    "explicit-confirmation",
    "professional-supervision",
    "accountable-human-judgment",
    "licensed-human-judgment",
    "never-delegate",
)
DELEGATION_FLOORS = {
    "public-source-summary": "independent-private",
    "private-plan-draft": "independent-private",
    "external-send": "explicit-confirmation",
    "patient-specific-clinical-decision": "never-delegate",
    "graded-or-evaluative-work": "professional-supervision",
    "institutional-change": "accountable-human-judgment",
    "academic-learning-support": "prepare-only",
    "credential-or-competence-claim": "never-delegate",
}


class DuplicateKeyError(ValueError):
    """Raised when a JSON object repeats a key."""


def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result

def log(ok, msg):
    mark = "✅" if ok is True else ("❌" if ok is False else "ℹ️")
    print(f"  {mark} {msg}")

def refuse(msg) -> NoReturn:
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
        data = json.loads(raw, object_pairs_hook=reject_duplicate_keys)
        log(True, f"valid JSON ({len(raw)} bytes)")
    except (json.JSONDecodeError, DuplicateKeyError) as e:
        refuse(f"malformed JSON: {e}")
    if data is None:
        refuse("malformed JSON (parsed to None)")
    if not isinstance(data, dict):
        refuse("JSON root must be an object")
    soul_data: dict = data

    schema_version = soul_data.get("schema_version")
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        refuse(f"unsupported schema_version: {schema_version!r}")

    # --- 2. Mandatory schema validation ---
    print("\n[2] Schema validation...")
    schema_path = Path(args.schema) if args.schema else soul_path.parent.parent / "schema" / "naio-soul.schema.json"
    if not schema_path.is_file():
        schema_path = Path(__file__).resolve().parent.parent / "schema" / "naio-soul.schema.json"
    if not schema_path.is_file():
        refuse("schema file not found; validation cannot proceed")
    try:
        from jsonschema import Draft7Validator, FormatChecker
    except Exception as e:
        refuse(f"required jsonschema validator unavailable: {e}. Install naio-os/requirements-import-soul.txt in an isolated environment")
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
        Draft7Validator.check_schema(schema)
        validator = Draft7Validator(schema, format_checker=FormatChecker())
        errors = sorted(validator.iter_errors(soul_data), key=lambda item: list(item.absolute_path))
        if errors:
            first = errors[0]
            location = ".".join(str(item) for item in first.absolute_path) or "<root>"
            refuse(f"schema validation failed at {location}: {first.message}")
        log(True, f"schema valid ({schema_path.name}; Draft-07 + format checks)")
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
    if soul_data.get("schema_version") == "2.0.0":
        academic = b.get("no_academic_dishonesty_confirmed") is True
        authority = b.get("no_credential_inference_confirmed") is True
        log(academic, f"no_academic_dishonesty_confirmed = {b.get('no_academic_dishonesty_confirmed')}")
        log(authority, f"no_credential_inference_confirmed = {b.get('no_credential_inference_confirmed')}")
        if not (academic and authority):
            refuse("v2 academic-integrity and no-authority confirmations must both be true")

    # --- 4. Onboarding tier clamp (green|yellow only) ---
    print("\n[4] Tier clamp (onboarding allows green|yellow only)...")
    ceilings = soul_data.get("tier_ceilings", {})
    bad_tiers = {k: v for k, v in ceilings.items() if v not in ALLOWED_CEILINGS}
    for k, v in ceilings.items():
        log(v in ALLOWED_CEILINGS, f"{k}: {v}")
    if bad_tiers:
        refuse(f"tiers above yellow are not allowed at onboarding: {bad_tiers}")
    if schema_version == "2.0.0":
        spheres = soul_data.get("spheres", [])
        if len(spheres) != len(set(spheres)):
            refuse("v2 spheres must be unique")
        if set(ceilings) != set(spheres):
            refuse("v2 tier_ceilings keys must exactly match selected spheres")
        constellation = soul_data.get("role_constellation", {})
        role_buckets = ("primary", "supporting", "emerging", "contextual")
        roles = [role for status in role_buckets for role in constellation.get(status, [])]
        role_ids = [role.get("role_id") for role in roles]
        if len(role_ids) != len(set(role_ids)):
            refuse("v2 selected role IDs must be unique across the full constellation")
        for bucket in role_buckets:
            for role in constellation.get(bucket, []):
                if role.get("status") != bucket:
                    refuse(f"v2 role status must match its constellation bucket: {role.get('role_id')}")
                if bucket in {"primary", "supporting"} and role.get("authorization") == "not-current":
                    refuse(f"current primary/supporting role cannot use not-current authorization: {role.get('role_id')}")
        custom_roles = constellation.get("custom_roles", [])
        custom_ids = [item.get("role_id") for item in custom_roles]
        if len(custom_ids) != len(set(custom_ids)):
            refuse("v2 custom role declaration IDs must be unique")
        custom_by_id = {item.get("role_id"): item for item in custom_roles}
        selected_custom = {item.get("role_id"): item for item in roles if str(item.get("role_id", "")).startswith("local-role-")}
        if set(custom_by_id) != set(selected_custom):
            refuse("v2 custom role declarations must exactly match selected local roles")
        for role_id, declared in custom_by_id.items():
            selected = selected_custom[role_id]
            if declared.get("label") != selected.get("label") or declared.get("domain_id") != selected.get("domain_id"):
                refuse(f"v2 custom role label/domain mismatch: {role_id}")
        studies = soul_data.get("advanced_studies", {})
        pathways = studies.get("pathways", [])
        if studies.get("active") is not bool(pathways):
            refuse("v2 Advanced Studies active state must match pathway presence")
        pathway_ids = [item.get("id") for item in pathways]
        if len(pathway_ids) != len(set(pathway_ids)):
            refuse("v2 Advanced Studies pathway IDs must be unique")
        boundary_delegation = b.get("delegation_matrix", {})
        preference_delegation = soul_data.get("ai_operating_preferences", {}).get("delegation_matrix", {})
        if boundary_delegation != preference_delegation:
            refuse("v2 delegation matrices must be identical")
        if set(boundary_delegation) != set(DELEGATION_FLOORS):
            refuse("v2 delegation matrix must contain exactly the governed activity keys")
        level_rank = {level: index for index, level in enumerate(GOVERNANCE_LEVELS)}
        for activity, floor in DELEGATION_FLOORS.items():
            requested = boundary_delegation.get(activity)
            if requested not in level_rank or level_rank[requested] < level_rank[floor]:
                refuse(f"v2 delegation floor violated for {activity}: minimum is {floor}")

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
    if soul_data.get("schema_version") == "2.0.0":
        constellation = soul_data.get("role_constellation", {})
        counts = {key: len(constellation.get(key, [])) for key in ("primary", "supporting", "emerging", "contextual")}
        print(f"  ℹ️  Role constellation: {counts}")
        print(f"  ℹ️  Advanced Studies: {'active' if soul_data.get('advanced_studies', {}).get('active') else 'inactive'}")
        print(f"  ℹ️  Mission Controls recommended: {len(soul_data.get('mission_controls', []))} (A0 recommendation-only)")
        print("  ℹ️  Authority: self-reported, not verified; no professional or institutional authority granted")

    print(f"\n✅ VALID: naio-soul.json passed the governed dry-run checks. Nothing was written.")
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
