#!/usr/bin/env python3
"""
NAIO OS — check-update.py (Phase 8)

Advisory update-channel check. It verifies the local signed release metadata,
then compares release.json against release-history.json for rollback protection
and key-id trust metadata. It never downloads, installs, or mutates a Hermes
profile. Agents propose. Humans judge. Nurses steward.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASE_URL = "https://nurse-ai-os.org/naio-os"


def version_rank(version: str) -> tuple[int, int]:
    """Return sortable rank for versions shaped like 2.0.0-phase8."""
    if "-phase" not in version:
        return (0, 0)
    base, phase = version.rsplit("-phase", 1)
    try:
        major = int(base.split(".", 1)[0])
        phase_num = int("".join(ch for ch in phase if ch.isdigit()) or "0")
        return (major, phase_num)
    except Exception:
        return (0, 0)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_local_release() -> tuple[bool, str]:
    verifier = ROOT / "scripts/verify-release.py"
    r = subprocess.run([sys.executable, str(verifier), "--quiet"], cwd=ROOT, text=True, capture_output=True)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "naio-os-check-update/2.0.0-phase8", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=30) as r:
        if r.status != 200:
            raise RuntimeError(f"{url} returned HTTP {r.status}")
        return json.loads(r.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="NAIO OS Phase 8 advisory update check")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="release channel base URL")
    parser.add_argument("--local-only", action="store_true", help="verify only local release metadata and rollback history")
    parser.add_argument("--json", action="store_true", help="emit machine-readable result")
    args = parser.parse_args()

    result = {
        "status": "unknown",
        "local_version": None,
        "remote_version": None,
        "channel": None,
        "key_id": None,
        "rollback_protected": False,
        "update_available": False,
        "no_mutation": True,
        "messages": [],
    }

    release_p = ROOT / "release.json"
    history_p = ROOT / "release-history.json"
    manifest_p = ROOT / "manifest.yaml"

    try:
        release = load_json(release_p)
        history = load_json(history_p)
        manifest = yaml.safe_load(manifest_p.read_text(encoding="utf-8")) if yaml else {}
    except Exception as exc:
        result["status"] = "blocked"
        result["messages"].append(f"local metadata unreadable: {exc}")
        print(json.dumps(result, indent=2) if args.json else "❌ update check blocked: " + result["messages"][-1])
        return 2

    ok, verifier_output = verify_local_release()
    if not ok:
        result["status"] = "blocked"
        result["messages"].append("local release verification failed")
        if verifier_output:
            result["messages"].append(verifier_output.splitlines()[-1])
        print(json.dumps(result, indent=2) if args.json else "❌ update check blocked: local release verification failed")
        return 2

    local_version = manifest.get("version") or release.get("latest_version")
    result["local_version"] = local_version
    result["channel"] = release.get("channel")
    result["key_id"] = release.get("manifest", {}).get("key_id")

    versions = [item.get("version") for item in history.get("releases", []) if item.get("version")]
    latest_known = history.get("latest_version") or (versions[-1] if versions else None)
    trusted_keys = set(history.get("trusted_key_ids", []))

    if local_version not in versions:
        result["status"] = "blocked"
        result["messages"].append(f"local version {local_version} not listed in release-history.json")
    if latest_known and version_rank(str(local_version)) < version_rank(str(latest_known)):
        result["status"] = "blocked"
        result["messages"].append(f"rollback detected: local {local_version} is older than history latest {latest_known}")
    if result["key_id"] not in trusted_keys:
        result["status"] = "blocked"
        result["messages"].append(f"untrusted release key id: {result['key_id']}")

    result["rollback_protected"] = result["status"] != "blocked"

    if args.local_only or result["status"] == "blocked":
        if result["status"] != "blocked":
            result["status"] = "ok"
            result["messages"].append("local release channel verified; no mutation performed")
        print(json.dumps(result, indent=2) if args.json else format_human(result))
        return 0 if result["status"] == "ok" else 2

    try:
        remote = fetch_json(args.base_url.rstrip("/") + "/release.json")
        result["remote_version"] = remote.get("latest_version")
        if version_rank(str(result["remote_version"])) > version_rank(str(local_version)):
            result["status"] = "update_available"
            result["update_available"] = True
            result["messages"].append("newer release advertised; review and run signed bootstrap manually")
        else:
            result["status"] = "ok"
            result["messages"].append("local release is current for the advertised channel")
    except Exception as exc:
        result["status"] = "blocked"
        result["messages"].append(f"remote channel check failed: {exc}")

    print(json.dumps(result, indent=2) if args.json else format_human(result))
    return 0 if result["status"] in {"ok", "update_available"} else 2


def format_human(result: dict) -> str:
    icon = "✅" if result["status"] == "ok" else "ℹ️" if result["status"] == "update_available" else "❌"
    lines = ["", "=== NAIO OS — Phase 8 update advisory ===", "", f"{icon} status: {result['status']}"]
    for key in ["local_version", "remote_version", "channel", "key_id"]:
        if result.get(key):
            lines.append(f"  {key}: {result[key]}")
    lines.append(f"  rollback_protected: {result['rollback_protected']}")
    lines.append("  mutation: none")
    for msg in result.get("messages", []):
        lines.append(f"  - {msg}")
    lines.append("\nDoctrine: Agents propose. Humans judge. Nurses steward.")
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
