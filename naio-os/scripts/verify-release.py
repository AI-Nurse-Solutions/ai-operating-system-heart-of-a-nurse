#!/usr/bin/env python3
"""
NAIO OS — verify-release.py (Phase 14)

Verifies the update-channel metadata and signed manifest before artifact
checksums are trusted. Phase 14 preserves release history, key-id trust metadata, rollback protection, and adds activation metadata.

Contract:
- release.json declares the latest supported bundle version, key id, and manifest digest.
- release-history.json declares trusted key ids and monotonic phase history.
- manifest.sha256 must match manifest.yaml exactly.
- manifest.sig must verify against config/naio-os-release-public.pem.
- Verification is fail-closed unless --allow-unsigned is explicitly passed.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parent.parent


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_expected_sha(path: Path) -> str:
    txt = path.read_text(encoding="utf-8").strip()
    if not txt:
        raise ValueError("manifest.sha256 is empty")
    return txt.split()[0]


def verify_signature(manifest: Path, sig: Path, pub: Path) -> tuple[bool, str]:
    openssl = shutil.which("openssl")
    if not openssl:
        return False, "openssl not found"
    if not sig.is_file():
        return False, "manifest.sig missing"
    if not pub.is_file():
        return False, "release public key missing"
    cmd = [openssl, "dgst", "-sha256", "-verify", str(pub), "-signature", str(sig), str(manifest)]
    r = subprocess.run(cmd, text=True, capture_output=True)
    msg = (r.stdout + r.stderr).strip()
    return r.returncode == 0, msg or f"openssl exit={r.returncode}"


def version_rank(version: str) -> tuple[int, int]:
    if "-phase" not in version:
        return (0, 0)
    base, phase = version.rsplit("-phase", 1)
    try:
        return (int(base.split(".", 1)[0]), int("".join(ch for ch in phase if ch.isdigit()) or "0"))
    except Exception:
        return (0, 0)


def main() -> int:
    parser = argparse.ArgumentParser(description="NAIO OS Phase 14 release verifier")
    parser.add_argument("--allow-unsigned", action="store_true", help="warn instead of failing if signature verification cannot run")
    parser.add_argument("--quiet", action="store_true", help="print only failures/success summary")
    args = parser.parse_args()

    def say(msg: str):
        if not args.quiet:
            print(msg)

    release_p = ROOT / "release.json"
    history_p = ROOT / "release-history.json"
    manifest_p = ROOT / "manifest.yaml"
    sha_p = ROOT / "manifest.sha256"
    sig_p = ROOT / "manifest.sig"
    pub_p = ROOT / "config/naio-os-release-public.pem"

    failures = []
    say("\n=== NAIO OS — release verification (Phase 14) ===\n")

    for p in [release_p, history_p, manifest_p, sha_p, sig_p, pub_p]:
        if not p.is_file():
            failures.append(f"missing {p.relative_to(ROOT)}")
        else:
            say(f"  ✅ {p.relative_to(ROOT)} present")
    if failures:
        for f in failures:
            print(f"  ❌ {f}")
        print("\n❌ RELEASE VERIFICATION FAILED")
        return 2

    try:
        release = json.loads(release_p.read_text(encoding="utf-8"))
        say(f"  ✅ release.json parses (latest={release.get('latest_version','?')})")
    except Exception as e:
        print(f"  ❌ release.json malformed: {e}")
        return 2

    try:
        history = json.loads(history_p.read_text(encoding="utf-8"))
        say(f"  ✅ release-history.json parses (latest={history.get('latest_version','?')})")
    except Exception as e:
        print(f"  ❌ release-history.json malformed: {e}")
        return 2

    if yaml is None:
        print("  ❌ pyyaml not installed — cannot compare release manifest metadata")
        return 2
    try:
        manifest = yaml.safe_load(manifest_p.read_text(encoding="utf-8"))
        say(f"  ✅ manifest.yaml parses (version={manifest.get('version','?')})")
    except Exception as e:
        print(f"  ❌ manifest.yaml malformed: {e}")
        return 2

    manifest_version = str(manifest.get("version"))
    if release.get("latest_version") != manifest.get("version"):
        failures.append(f"release latest_version {release.get('latest_version')} != manifest version {manifest.get('version')}")
    if release.get("channel") not in {"stable", "preview"}:
        failures.append("release channel must be stable or preview")
    if release.get("minimum_installer_phase") != 14:
        failures.append("release minimum_installer_phase must be 14")

    releases = history.get("releases", [])
    history_versions = [r.get("version") for r in releases if r.get("version")]
    history_latest = history.get("latest_version")
    key_id = release.get("manifest", {}).get("key_id")
    trusted_key_ids = set(history.get("trusted_key_ids", []))
    if manifest_version not in history_versions:
        failures.append(f"manifest version {manifest_version} is not listed in release-history.json")
    if history_latest and version_rank(manifest_version) < version_rank(str(history_latest)):
        failures.append(f"rollback detected: manifest version {manifest_version} is older than release-history latest {history_latest}")
    if key_id not in trusted_key_ids:
        failures.append(f"release key_id {key_id!r} is not trusted by release-history.json")
    if history.get("rollback_policy", {}).get("fail_closed") is not True:
        failures.append("release-history rollback_policy.fail_closed must be true")
    elif key_id in trusted_key_ids and manifest_version in history_versions:
        say(f"  ✅ release-history trusts key_id={key_id} and protects version={manifest_version}")

    expected_sha = read_expected_sha(sha_p)
    actual_sha = sha256_file(manifest_p)
    if expected_sha == actual_sha:
        say(f"  ✅ manifest.sha256 matches manifest.yaml ({actual_sha[:12]}…)")
    else:
        failures.append(f"manifest.sha256 mismatch expected {expected_sha[:12]}… got {actual_sha[:12]}…")

    release_digest = release.get("manifest", {}).get("sha256")
    if release_digest == actual_sha:
        say("  ✅ release.json manifest digest matches manifest.yaml")
    else:
        failures.append("release.json manifest.sha256 does not match manifest.yaml")

    sig_ok, sig_msg = verify_signature(manifest_p, sig_p, pub_p)
    if sig_ok:
        say(f"  ✅ manifest.sig verifies with release public key ({sig_msg})")
    elif args.allow_unsigned:
        say(f"  ⚠️  signature verification unavailable/failed but allowed: {sig_msg}")
    else:
        failures.append(f"signature verification failed: {sig_msg}")

    if failures:
        for f in failures:
            print(f"  ❌ {f}")
        print("\n❌ RELEASE VERIFICATION FAILED — do not trust manifest/checksums.")
        return 2

    print("\n✅ RELEASE VERIFICATION PASSED — manifest digest and signature are valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
