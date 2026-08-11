#!/usr/bin/env python3
"""
tools/release.py — build the artifact and its claims in one command.

The README used to say "56/56" while the suite ran 65. Nobody lied; a number was
transcribed by hand into prose and the code moved on. This exists so that cannot
happen again: the self-test runs, the manifest records what was actually built,
and every claim about the count is written by the same command that made the zip.

    python3 tools/release.py            # verify + manifest + stamp docs
    python3 tools/release.py --zip out/mission-control.zip
    python3 tools/release.py --sign ~/keys/naio-os-release.pem   # key-holder only
    python3 tools/release.py --chain-entry     # the line naio-os's manifest needs

Signing. Mission Control now speaks the same signature contract naio-os has used
since Phase 6 — detached RSA-SHA256 over the manifest, verified with the release
public key, fail-closed. What this command cannot do is invent the private half:
`--sign` needs the key for `naio-os-release-key-2026-06`, which is not in this
repository and should never be. Without it the build is unsigned, `naio-mc
verify` says so in exactly those words, and nothing here implies a provenance it
does not have.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
MANIFEST = HERE / "manifest.json"

# The signature contract, in one place because three files have to agree on it:
# this builder, `naio-mc verify`, and whatever naio-os's release cut records.
SIG_NAME = "manifest.sig"
SIG_ALGORITHM = "RSA-SHA256"
KEY_ID = "naio-os-release-key-2026-06"
PUBLIC_KEY_REL = "../config/naio-os-release-public.pem"
MANIFEST_SIG = HERE / SIG_NAME

SKIP_DIRS = {"__pycache__", "backups", "governance", "proposals", ".git"}
SKIP_SUFFIX = {".pyc", ".db", ".db-wal", ".db-shm", ".zip"}
# Files a nurse is expected to edit or that the server writes. Recorded, but
# drift in them is normal and reported separately from drift in the code.
MUTABLE = {"config.json"}
MUTABLE_DIRS = {"content", "demo-vault", "demo-workspace"}


def tracked_files() -> list[Path]:
    out = []
    for path in sorted(HERE.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(HERE)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        # manifest.json cannot checksum itself, and manifest.sig is written
        # AFTER the manifest it signs — listing either guarantees drift.
        if path.suffix in SKIP_SUFFIX or rel.name in ("manifest.json", SIG_NAME):
            continue
        out.append(rel)
    return out


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def is_mutable(rel: Path) -> bool:
    return rel.name in MUTABLE or (rel.parts and rel.parts[0] in MUTABLE_DIRS)


def run_self_test() -> tuple[int, int]:
    """Returns (passed, failed). Raises if the suite cannot run."""
    proc = subprocess.run([sys.executable, str(HERE / "tests" / "self_test.py")],
                          capture_output=True, text=True, cwd=str(HERE))
    tail = re.sub(r"\x1b\[[0-9;]*m", "", proc.stdout)
    m = re.search(r"(\d+) passed, (\d+) failed", tail)
    if not m:
        print(tail[-2000:], file=sys.stderr)
        raise SystemExit("release: could not read the self-test result")
    return int(m.group(1)), int(m.group(2))


def version() -> str:
    src = (HERE / "mission_control.py").read_text(encoding="utf-8")
    m = re.search(r'VERSION\s*=\s*"([^"]+)"', src)
    return m.group(1) if m else "unknown"


def build_manifest(passed: int, failed: int) -> dict:
    files = {}
    for rel in tracked_files():
        files[str(rel)] = {
            "sha256": sha256(HERE / rel),
            "bytes": (HERE / rel).stat().st_size,
            "mutable": is_mutable(rel),
        }
    return {
        "_note": "Checksums of what was actually built, written by tools/release.py "
                 "at the same moment the self-test ran. On its own this proves the "
                 "tree is unchanged since packaging and nothing more. Provenance "
                 "comes from the detached signature described under 'signature' — "
                 "if manifest.sig is absent, this build is UNSIGNED and `naio-mc "
                 "verify` says so.",
        # A description of the contract, never an assertion that it was met. The
        # old 'signed: false' field was a claim living inside the very bytes a
        # signature would cover: sign the file and the field is a lie, leave it
        # and it has to be hand-edited at exactly the moment nobody is looking.
        # Whether this build is signed is now answered by checking the signature.
        "signature": {
            "algorithm": SIG_ALGORITHM,
            "detached": SIG_NAME,
            "public_key": PUBLIC_KEY_REL,
            "key_id": KEY_ID,
            "note": "Same key and same fail-closed posture as the naio-os release "
                    "chain. Verify with: openssl dgst -sha256 -verify "
                    f"{PUBLIC_KEY_REL} -signature {SIG_NAME} manifest.json",
        },
        "version": version(),
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "self_test": {"passed": passed, "failed": failed},
        "file_count": len(files),
        "files": files,
    }


def stamp_docs(passed: int) -> list[str]:
    """
    Write the count everywhere it is claimed, so prose cannot drift from the suite.

    This deliberately reaches OUTSIDE the packaged tree, into the site that
    publishes the claim. The first drift was inside this folder; the second would
    have been on the website, where a nurse actually reads it. A stamp that stops
    at the zip boundary only moves the problem somewhere with a wider audience.

    Files outside the tree are not in the manifest, so stamping them cannot make
    `verify` report drift. They are skipped silently when absent — the packaged
    zip is often unpacked far away from the site that shipped it.
    """
    touched = []
    site = HERE.parent.parent          # …/Nurse ai os Site
    targets = [
        (HERE / "README.md",
         [(r"# (\d+) checks, including the ones that matter",
           f"# {passed} checks, including the ones that matter"),
          (r"`self-test` runs \d+ checks", f"`self-test` runs {passed} checks")]),
        # The doctrine README's verification record.
        (HERE.parent / "README.md",
         [(r"passes \*\*\d+/\d+\*\* of its own self-test",
           f"passes **{passed}/{passed}** of its own self-test")]),
        # The public front door. This is the sentence a stranger reads.
        (site / "mission-control.html",
         [(r"passes its own \d+-check self-test",
           f"passes its own {passed}-check self-test")]),
    ]
    for path, subs in targets:
        if not path.is_file():
            continue
        text = original = path.read_text(encoding="utf-8")
        for pat, rep in subs:
            text = re.sub(pat, rep, text)
        if text != original:
            path.write_text(text, encoding="utf-8")
            try:
                touched.append(str(path.relative_to(HERE)))
            except ValueError:
                # Deliberately outside the packaged tree — name it in full, because
                # a stamp that reached the public site is exactly the one you want
                # to see reported by its real path.
                touched.append(str(path))
    return touched


def sign_manifest(key_path: Path) -> None:
    """
    Detached RSA-SHA256 over manifest.json, written to manifest.sig.

    Deliberately the same two openssl invocations naio-os has used since Phase 6
    rather than a second scheme with its own bugs: sign here, verify in
    `naio-mc verify`, and the signature this writes is checked immediately so a
    key that produces something unverifiable fails at the moment it is used and
    not on a nurse's laptop a week later.
    """
    openssl = shutil.which("openssl")
    if not openssl:
        raise SystemExit("release: openssl not found — cannot sign")
    if not key_path.is_file():
        raise SystemExit(f"release: no signing key at {key_path}")

    signed = subprocess.run(
        [openssl, "dgst", "-sha256", "-sign", str(key_path),
         "-out", str(MANIFEST_SIG), str(MANIFEST)],
        text=True, capture_output=True)
    if signed.returncode != 0:
        MANIFEST_SIG.unlink(missing_ok=True)
        raise SystemExit(f"release: signing failed — {(signed.stderr or '').strip()}")

    public_key = (HERE / PUBLIC_KEY_REL).resolve()
    checked = subprocess.run(
        [openssl, "dgst", "-sha256", "-verify", str(public_key),
         "-signature", str(MANIFEST_SIG), str(MANIFEST)],
        text=True, capture_output=True)
    if checked.returncode != 0:
        MANIFEST_SIG.unlink(missing_ok=True)
        raise SystemExit(
            "release: the signature this key produced does NOT verify against "
            f"{PUBLIC_KEY_REL}. Wrong key for {KEY_ID}? Nothing was left behind.")


def chain_entry() -> dict:
    """
    The one entry naio-os's signed manifest needs to cover all of Mission Control.

    Two levels, not fifty-two: naio-os's signature covers its manifest.yaml,
    which records the checksum of THIS manifest.json, which records the checksum
    of every Mission Control file. Adding one line to the signed manifest brings
    the whole directory under the chain, and re-cutting a Mission Control build
    changes exactly one checksum upstream instead of dozens.
    """
    return {
        "path": f"{HERE.name}/manifest.json",
        "role": "mission-control-manifest",
        "sha256": sha256(MANIFEST),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the manifest and stamp the claims")
    ap.add_argument("--zip", help="also write a zip of the tree to this path")
    ap.add_argument("--skip-tests", action="store_true",
                    help="only for iterating; a release without a green suite is not one")
    ap.add_argument("--sign", metavar="KEY",
                    help=f"sign manifest.json with the private half of {KEY_ID}")
    ap.add_argument("--chain-entry", action="store_true",
                    help="print the naio-os manifest.yaml entry that covers this build")
    args = ap.parse_args()

    if args.chain_entry:
        if not MANIFEST.is_file():
            raise SystemExit("release: no manifest.json yet — run this without "
                             "--chain-entry first")
        entry = chain_entry()
        print("\n# Add to naio-os/manifest.yaml under `contents:`, then re-run")
        print("# scripts/compute-checksums.sh and re-sign the manifest.\n")
        print(f"- path: {entry['path']}")
        print(f"  role: {entry['role']}")
        print(f"  sha256: {entry['sha256']}\n")
        return 0

    print("\nrelease\n")
    if args.skip_tests:
        passed, failed = 0, 0
        print("  ! tests skipped — this build must not be published")
    else:
        passed, failed = run_self_test()
        mark = "✓" if not failed else "✗"
        print(f"  {mark} self-test: {passed} passed, {failed} failed")
        if failed:
            raise SystemExit("release: refusing to build with a failing suite")

    # Stamp BEFORE hashing — otherwise the manifest records a README that the
    # very next line rewrites, and `verify` reports drift on a fresh build.
    # (It did exactly that once. Hence the comment.)
    if not args.skip_tests:
        for rel in stamp_docs(passed):
            print(f"  ✓ stamped {rel} with {passed}")

    manifest = build_manifest(passed, failed)
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"  ✓ manifest.json — {manifest['file_count']} files, version {manifest['version']}")

    # A stale signature over the previous manifest is worse than none: it would
    # fail verification and look like tampering rather than like a build step
    # that was not run. Clear it, then sign the bytes that actually exist.
    if MANIFEST_SIG.exists() and not args.sign:
        MANIFEST_SIG.unlink()
        print(f"  ! removed a {SIG_NAME} that signed the PREVIOUS manifest — "
              f"re-run with --sign to sign this one")
    if args.sign:
        sign_manifest(Path(args.sign).expanduser())
        print(f"  ✓ signed — {SIG_NAME} verifies against {PUBLIC_KEY_REL}")
        print(f"  → next: add this to naio-os/manifest.yaml, then re-sign it:")
        entry = chain_entry()
        print(f"      - path: {entry['path']}")
        print(f"        role: {entry['role']}")
        print(f"        sha256: {entry['sha256']}")
    else:
        print(f"  ! not signed — the private half of {KEY_ID} is not in this "
              f"repository, and `naio-mc verify` reports the build as unsigned")

    if args.zip:
        out = Path(args.zip).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(MANIFEST, f"{HERE.name}/manifest.json")
            if MANIFEST_SIG.is_file():
                z.write(MANIFEST_SIG, f"{HERE.name}/{SIG_NAME}")
            for rel in tracked_files():
                z.write(HERE / rel, f"{HERE.name}/{rel}")
        print(f"  ✓ {out} ({out.stat().st_size // 1024} KB)")

    print("\n  Agents propose. Humans judge. Nurses steward.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
