#!/usr/bin/env python3
"""Sign exact Harness 2.0 evidence bytes after explicit human confirmation."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path


def run(args: list[str]) -> bytes:
    return subprocess.run(args, check=True, capture_output=True).stdout


def fingerprint_private(openssl: str, private_key: Path) -> str:
    der = run([openssl, "pkey", "-in", str(private_key), "-pubout", "-outform", "DER"])
    return hashlib.sha256(der).hexdigest()


def fingerprint_public(openssl: str, public_key: Path) -> str:
    der = run([openssl, "pkey", "-pubin", "-in", str(public_key), "-outform", "DER"])
    return hashlib.sha256(der).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Human-gated Harness 2.0 detached-signature ceremony")
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--signature", type=Path, required=True)
    parser.add_argument("--private-key", type=Path, required=True)
    parser.add_argument("--public-key", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    args = parser.parse_args()

    openssl = shutil.which("openssl")
    if not openssl:
        raise SystemExit("openssl not found")

    artifact = args.artifact.resolve()
    signature = args.signature.resolve()
    private_key = args.private_key.resolve()
    public_key = args.public_key.resolve()

    if not artifact.is_file() or not private_key.is_file() or not public_key.is_file():
        raise SystemExit("artifact or key file missing")
    mode = stat.S_IMODE(private_key.stat().st_mode)
    if private_key.stat().st_uid != os.getuid() or mode & 0o077:
        raise SystemExit(f"private key ownership/permissions unsafe: mode={mode:04o}")

    actual_sha = hashlib.sha256(artifact.read_bytes()).hexdigest()
    if actual_sha != args.expected_sha256:
        raise SystemExit(f"artifact digest changed: expected={args.expected_sha256} actual={actual_sha}")

    private_fp = fingerprint_private(openssl, private_key)
    public_fp = fingerprint_public(openssl, public_key)
    if private_fp != public_fp:
        raise SystemExit("private key does not match trusted public key")

    signature.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".release-evidence.", suffix=".sig", dir=signature.parent)
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        subprocess.run(
            [openssl, "dgst", "-sha256", "-sign", str(private_key), "-out", str(tmp), str(artifact)],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [openssl, "dgst", "-sha256", "-verify", str(public_key), "-signature", str(tmp), str(artifact)],
            check=True,
            capture_output=True,
        )
        os.chmod(tmp, 0o644)
        os.replace(tmp, signature)
    finally:
        tmp.unlink(missing_ok=True)

    print(f"SIGNED artifact_sha256={actual_sha}")
    print(f"VERIFIED public_key_fingerprint_sha256={public_fp}")
    print(f"SIGNATURE {signature}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
