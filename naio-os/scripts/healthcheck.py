#!/usr/bin/env python3
"""
NAIO OS — healthcheck.py
Verify-before-claim harness. The installer never reports success until this
passes. Checks the Phase 18 bundle is internally consistent.
"""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parent.parent
PASS, FAIL = 0, 0


def ok(msg):
    global PASS
    PASS += 1
    print(f"  ✅ {msg}")


def fail(msg):
    global FAIL
    FAIL += 1
    print(f"  ❌ {msg}")


def info(msg):
    print(f"  ℹ️  {msg}")


def load_manifest():
    manifest_path = ROOT / "manifest.yaml"
    if not manifest_path.is_file():
        fail("manifest.yaml missing")
        return None
    if yaml is None:
        fail("pyyaml not installed — cannot parse manifest/checksums")
        return None
    try:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        ok(f"manifest.yaml parses (version {manifest.get('version','?')})")
        return manifest
    except Exception as e:
        fail(f"manifest.yaml malformed: {e}")
        return None


def verify_checksums(manifest):
    print("\n[6] Checksum verification")
    contents = manifest.get("contents", []) if manifest else []
    if not contents:
        fail("manifest has no contents list")
        return
    for item in contents:
        rel = item.get("path", "")
        if item.get("self_checksum_excluded"):
            info(f"{rel} self-checksum excluded by policy")
            continue
        expected = item.get("sha256")
        if not expected:
            fail(f"{rel} missing sha256 (run scripts/compute-checksums.sh)")
            continue
        p = ROOT / rel
        if not p.is_file():
            fail(f"{rel} missing; cannot verify sha256")
            continue
        actual = hashlib.sha256(p.read_bytes()).hexdigest()
        if actual == expected:
            ok(f"{rel} sha256 verified")
        else:
            fail(f"{rel} CHECKSUM MISMATCH (expected {expected[:12]}…, got {actual[:12]}…)")


def verify_release_metadata():
    print("\n[2] Release metadata + signature")
    verifier = ROOT / "scripts/verify-release.py"
    if not verifier.is_file():
        fail("scripts/verify-release.py missing")
        return
    r = subprocess.run([sys.executable, str(verifier), "--quiet"], cwd=ROOT, text=True, capture_output=True)
    output = (r.stdout + r.stderr).strip()
    if r.returncode == 0:
        ok("release metadata and manifest signature verified")
    else:
        fail("release metadata/signature verification failed")
        if output:
            for line in output.splitlines()[-8:]:
                info(line)


def main():
    parser = argparse.ArgumentParser(description="NAIO OS Phase 18 healthcheck")
    parser.add_argument("--checksums-only", action="store_true", help="only verify manifest + checksums")
    args = parser.parse_args()

    print("\n=== NAIO OS — healthcheck ===\n")

    print("[1] Manifest")
    manifest = load_manifest()
    if manifest is None:
        print_summary()
        return 1

    contents = manifest.get("contents", [])

    if not args.checksums_only:
        print("\n[2] Bundle contents")
        if not contents:
            fail("no contents declared in manifest")
        for item in contents:
            rel = item.get("path", "")
            p = ROOT / rel
            if p.is_file():
                ok(f"{rel} exists")
            else:
                fail(f"{rel} MISSING")

        print("\n[3] Policy doctrine")
        for name in ["config/edena-policy.yaml", "config/florence-x.yaml"]:
            p = ROOT / name
            if not p.is_file():
                fail(f"{name} missing")
                continue
            txt = p.read_text(encoding="utf-8")
            if "Agents propose. Humans judge. Nurses steward." in txt:
                ok(f"{name} carries doctrine line")
            else:
                fail(f"{name} missing doctrine line")
            if yaml is not None:
                try:
                    yaml.safe_load(txt)
                    ok(f"{name} parses as YAML")
                except Exception as e:
                    fail(f"{name} malformed YAML: {e}")

        print("\n[4] Schemas")
        for schema_name in ["schema/naio-soul.schema.json", "schema/naio-projects.schema.json"]:
            p = ROOT / schema_name
            if p.is_file():
                try:
                    schema = json.loads(p.read_text(encoding="utf-8"))
                    ok(f"{schema_name} parses (draft {schema.get('$schema','?').split('/')[-1]})")
                except Exception as e:
                    fail(f"{schema_name} malformed: {e}")
            else:
                fail(f"{schema_name} missing")

        print("\n[5] Scripts")
        for s in ["scripts/preflight.sh", "scripts/import-soul.py", "scripts/import-projects.py", "scripts/render-profile.py", "scripts/self-test.py", "scripts/verify-release.py", "scripts/check-update.py", "scripts/recovery.py", "scripts/activation.py", "scripts/launch.py", "scripts/cohort.py", "scripts/evidence.py", "scripts/contribute.py", "scripts/pilot.py", "scripts/readiness.py", "scripts/registry.py", "scripts/orchestration.py", "scripts/governance.py", "scripts/healthcheck.py", "scripts/compute-checksums.sh", "install.sh", "bootstrap.sh"]:
            p = ROOT / s
            if p.is_file():
                ok(f"{s} present")
            else:
                fail(f"{s} missing")

    verify_release_metadata()
    verify_checksums(manifest)
    print_summary()
    return 1 if FAIL else 0


def print_summary():
    print(f"\n--- summary ---")
    print(f"  ok:   {PASS}")
    print(f"  fail: {FAIL}")
    if FAIL > 0:
        print("\n❌ HEALTHCHECK FAILED — bundle is inconsistent. Do not ship.")
    else:
        print("\n✅ HEALTHCHECK PASSED — bundle is internally consistent (Phase 18 target-only apply + activation + launch + cohort + evidence + contribution + pilot + readiness + registry + orchestration + governance scope).")


if __name__ == "__main__":
    sys.exit(main())
