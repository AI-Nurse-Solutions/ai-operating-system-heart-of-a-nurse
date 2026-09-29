#!/usr/bin/env python3
"""Sign an update feed, for the steward (build step 6.2).

    python3 nurse-manager/tools/sign_update_feed.py FEED.json --key PRIVATE.pem
    python3 nurse-manager/tools/sign_update_feed.py --key-entry PUBLIC.pem

The first form checks FEED.json against the feed format, then writes
FEED.json.sig: an RSA-SHA256 signature of the file's exact bytes, made by
OpenSSL on the steward's own machine. The private key never enters this
repository. The second form prints the entry to pin in
config/update-feed.json (``trusted_keys``) for a public key.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nurse_manager.update import (  # noqa: E402
    UpdateError,
    _parse_feed,
    load_public_key,
    verify_signature,
)


def key_entry(public_pem: Path) -> dict:
    pem = public_pem.read_text(encoding="utf-8")
    _, _, key_id = load_public_key(pem)
    return {"key_id": key_id, "pem": pem.strip() + "\n"}


def sign(feed: Path, private_key: Path, channel: str) -> Path:
    openssl = shutil.which("openssl")
    if not openssl:
        raise UpdateError("signing needs OpenSSL on the steward's machine")
    data = feed.read_bytes()
    parsed = _parse_feed(json.loads(data.decode("utf-8")), channel)
    if parsed["expires"] <= date.today():
        raise UpdateError("this feed has already expired; set a later expiry date")
    sig = feed.with_name(feed.name + ".sig")
    # Signed into memory and written only once it verifies, so a failed run
    # never truncates or replaces a signature that was already good.
    signature = subprocess.run([openssl, "dgst", "-sha256", "-sign", str(private_key)],
                               input=data, check=True, capture_output=True).stdout
    public = subprocess.run([openssl, "pkey", "-in", str(private_key), "-pubout"], check=True,
                            capture_output=True, text=True).stdout
    n, e, key_id = load_public_key(public)
    if not verify_signature(n, e, data, signature):
        raise UpdateError("the new signature does not verify; nothing was written")
    fd, tmp = tempfile.mkstemp(dir=sig.parent, prefix=f".{sig.name}.")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(signature)
        os.replace(tmp, sig)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
    print(f"signed {feed.name} (sequence {parsed['sequence']}) with key {key_id}")
    return sig


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("feed", nargs="?", type=Path)
    parser.add_argument("--key", type=Path, help="the steward's private key (PEM)")
    parser.add_argument("--channel", default="pilot")
    parser.add_argument("--key-entry", type=Path, help="print the trusted_keys entry for a public key")
    args = parser.parse_args(argv)
    try:
        if args.key_entry:
            print(json.dumps(key_entry(args.key_entry), indent=2))
            return 0
        if not (args.feed and args.key):
            parser.error("give a feed and --key, or --key-entry")
        sign(args.feed, args.key, args.channel)
        return 0
    except (UpdateError, OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"not signed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
