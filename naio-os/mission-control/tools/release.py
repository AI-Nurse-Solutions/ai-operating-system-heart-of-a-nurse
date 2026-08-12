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
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
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
# The epoch every published archive is stamped with, shared with
# tools/build-starter-kit.py so both reproduce the same way.
FIXED_TIME = (2026, 7, 25, 0, 0, 0)
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
        # AFTER the manifest it signs — listing either guarantees drift. Match
        # the top-level paths, not the basename: a nested tools/manifest.sig
        # would otherwise be excluded from the manifest AND from the untracked
        # report, which is the one combination nobody would notice.
        if path.suffix in SKIP_SUFFIX or str(rel) in ("manifest.json", SIG_NAME):
            continue
        out.append(rel)
    return out


def build_time() -> datetime:
    """
    When this build says it was built.

    Normally now. But `built_at` lands inside manifest.json, manifest.json lands
    inside the release archive, and that archive's checksum becomes a claim in a
    signed document — so a wall clock in there means two builds of identical
    source produce different digests, and even the key holder cannot rebuild the
    release to check the number they signed. SOURCE_DATE_EPOCH is the
    reproducible-builds convention for exactly this; scripts/sign-mission-control.py
    sets it from the commit being released, so cutting that commit twice gives
    the same bytes both times.
    """
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch:
        try:
            return datetime.fromtimestamp(int(epoch), timezone.utc)
        except (ValueError, OverflowError, OSError):
            raise SystemExit(f"release: SOURCE_DATE_EPOCH={epoch!r} is not a unix timestamp")
    return datetime.now(timezone.utc)


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
        "built_at": build_time().isoformat(timespec="seconds"),
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


def sign_manifest(key_path: Path, public_key: Path | None = None) -> None:
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

    public_key = (public_key or (HERE / PUBLIC_KEY_REL)).resolve()
    checked = subprocess.run(
        [openssl, "dgst", "-sha256", "-verify", str(public_key),
         "-signature", str(MANIFEST_SIG), str(MANIFEST)],
        text=True, capture_output=True)
    if checked.returncode != 0:
        MANIFEST_SIG.unlink(missing_ok=True)
        raise SystemExit(
            f"release: the signature this key produced does NOT verify against "
            f"{public_key}. Wrong key for {KEY_ID}? Nothing was left behind.")


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


def write_reproducible_zip(out: Path, members: list[tuple[str, Path]]) -> str:
    """
    Write `members` to `out` as a byte-for-byte reproducible archive, and return
    its sha256.

    The digest is the point. Once this archive is what `manifest.yaml` covers,
    its checksum is a claim in a signed document, and that claim should be a
    function of the source rather than of when someone happened to run a build.
    A plain `ZipFile.write()` stamps each entry with the file's mtime, so two
    builds of an identical tree minutes apart produced different archives and
    therefore different digests — the recorded number was then unreproducible
    even by the person who recorded it. Fixing the timestamp, permissions,
    order and compression level removes that noise.

    What this does and does not buy. Cutting the same commit with the same key
    twice now yields byte-identical archives, so a release can be rebuilt and
    checked rather than taken on faith. It does not let a stranger rebuild the
    archive from source alone: a signed archive contains manifest.sig, which
    only the key holder can produce. A stranger verifies the published archive
    the stronger way instead — check the enclosed signature against the pinned
    public key, then every unpacked file against manifest.json.

    Same approach, and the same FIXED_TIME, as tools/build-starter-kit.py — the
    other artifact in this repository whose checksum is published.
    """
    out.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{out.name}.", dir=out.parent)
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for arcname, src in sorted(members, key=lambda m: m[0]):
                info = zipfile.ZipInfo(arcname, FIXED_TIME)
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, src.read_bytes(),
                           compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        os.replace(tmp, out)
    finally:
        if tmp.exists():
            tmp.unlink()
    return sha256(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the manifest and stamp the claims")
    ap.add_argument("--zip", help="also write a zip of the tree to this path")
    ap.add_argument("--skip-tests", action="store_true",
                    help="only for iterating; a release without a green suite is not one")
    ap.add_argument("--sign", metavar="KEY",
                    help=f"sign manifest.json with the private half of {KEY_ID}")
    ap.add_argument("--public-key", metavar="PEM",
                    help="check the signature against this public key instead of "
                         f"{PUBLIC_KEY_REL}. For testing the signing path with a "
                         "throwaway key; `naio-mc verify` remains pinned and is "
                         "not affected by this flag.")
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
    # that was not run. The manifest has just been rewritten, so the old
    # signature is already stale — clear it BEFORE attempting to sign, not only
    # on the unsigned path. Signing can still fail (missing key, no openssl),
    # and that failure must not leave the previous signature sitting over bytes
    # it never covered.
    had_signature = MANIFEST_SIG.exists()
    if had_signature:
        MANIFEST_SIG.unlink()
        if not args.sign:
            print(f"  ! removed a {SIG_NAME} that signed the PREVIOUS manifest — "
                  f"re-run with --sign to sign this one")
    if args.sign:
        sign_manifest(Path(args.sign).expanduser(),
                      Path(args.public_key).expanduser() if args.public_key else None)
        print(f"  ✓ signed — {SIG_NAME} verifies against {PUBLIC_KEY_REL}")
        print("  → next: add this to naio-os/manifest.yaml, then re-sign it:")
        entry = chain_entry()
        print(f"      - path: {entry['path']}")
        print(f"        role: {entry['role']}")
        print(f"        sha256: {entry['sha256']}")
    else:
        print(f"  ! not signed — the private half of {KEY_ID} is not in this "
              f"repository, and `naio-mc verify` reports the build as unsigned")

    if args.zip:
        out = Path(args.zip).expanduser().resolve()
        members: list[tuple[str, Path]] = [(f"{HERE.name}/manifest.json", MANIFEST)]
        if MANIFEST_SIG.is_file():
            members.append((f"{HERE.name}/{SIG_NAME}", MANIFEST_SIG))
            # A signature is useless without the key, and this archive is
            # routinely unpacked outside a naio-os tree where `../config/`
            # does not exist. Ship the PUBLIC half at the layout the
            # verifier's standalone candidate looks for. Safe to bundle
            # only because naio-mc pins the key's fingerprint in code: an
            # attacker who swaps this file is refused, not believed.
            key = (HERE / PUBLIC_KEY_REL).resolve()
            if key.is_file():
                members.append((f"{HERE.name}/config/{key.name}", key))
                print(f"  ✓ bundled the release public key for standalone "
                      f"verification")
            else:
                print(f"  ! signed, but {PUBLIC_KEY_REL} is missing — this "
                      f"zip cannot be verified where it lands")
        members.extend((f"{HERE.name}/{rel}", HERE / rel) for rel in tracked_files())
        digest = write_reproducible_zip(out, members)
        print(f"  ✓ {out} ({out.stat().st_size // 1024} KB, sha256 {digest[:12]}…)")

    print("\n  Agents propose. Humans judge. Nurses steward.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
