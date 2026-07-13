#!/usr/bin/env python3
"""Prepare the exact Harness 2.0 evidence bytes for human-authorized signing."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def public_fingerprint(public_key: Path) -> str:
    openssl = shutil.which("openssl")
    if not openssl:
        raise RuntimeError("openssl not found")
    result = subprocess.run(
        [openssl, "pkey", "-pubin", "-in", str(public_key), "-outform", "DER"],
        check=True,
        capture_output=True,
    )
    return hashlib.sha256(result.stdout).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare final Harness 2.0 release evidence for signing")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--evidence", type=Path, default=Path("evidence/release-evidence.json"))
    parser.add_argument("--public-key", type=Path, required=True)
    parser.add_argument("--key-id", required=True)
    parser.add_argument("--signer", required=True)
    args = parser.parse_args()

    root = args.root.resolve()
    evidence_path = (root / args.evidence).resolve()
    public_key = args.public_key.resolve()
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    fingerprint = public_fingerprint(public_key)

    evidence["release_status"] = "signed_implementation_candidate"
    evidence["signing"] = {
        "algorithm": "RSA-SHA256",
        "ceremony_prepared_at": datetime.now(timezone.utc).isoformat(),
        "human_signing_authority": args.signer,
        "key_id": args.key_id,
        "public_key": "../../naio-os/config/naio-os-release-public.pem",
        "public_key_fingerprint_sha256": fingerprint,
        "signature": "release-evidence.sig",
        "signed": True,
        "trust_anchor_rotated": False,
    }
    payload = json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    fd, tmp_name = tempfile.mkstemp(prefix=".release-evidence.", suffix=".json", dir=evidence_path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, evidence_path)
    finally:
        Path(tmp_name).unlink(missing_ok=True)
    digest = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    print(json.dumps({
        "artifact": str(evidence_path),
        "artifact_sha256": digest,
        "public_key_fingerprint_sha256": fingerprint,
        "release_status": evidence["release_status"],
        "signature_pending": True,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
