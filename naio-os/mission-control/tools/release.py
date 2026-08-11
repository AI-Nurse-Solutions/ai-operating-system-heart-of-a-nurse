#!/usr/bin/env python3
"""
tools/release.py — build the artifact and its claims in one command.

The README used to say "56/56" while the suite ran 65. Nobody lied; a number was
transcribed by hand into prose and the code moved on. This exists so that cannot
happen again: the self-test runs, the manifest records what was actually built,
and every claim about the count is written by the same command that made the zip.

    python3 tools/release.py            # verify + manifest + stamp docs
    python3 tools/release.py --zip out/mission-control.zip

What it does NOT do: sign anything. There is no key, so there is no signature,
and the manifest says so on its face rather than implying a trust it does not have.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
MANIFEST = HERE / "manifest.json"

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
        if path.suffix in SKIP_SUFFIX or rel.name == "manifest.json":
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
                 "at the same moment the self-test ran. MISSION CONTROL IS NOT "
                 "SIGNED — there is no Mission Control release key yet, so this "
                 "proves this tree is unchanged since packaging, and nothing more. "
                 "Do not read it as provenance. Scope: naio-os itself has been "
                 "signed since Phase 6 (manifest.sig, release-history.json, "
                 "fail-closed verifier); Mission Control does not yet participate "
                 "in that chain.",
        "signed": False,
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


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the manifest and stamp the claims")
    ap.add_argument("--zip", help="also write a zip of the tree to this path")
    ap.add_argument("--skip-tests", action="store_true",
                    help="only for iterating; a release without a green suite is not one")
    args = ap.parse_args()

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
    print("  ! not signed — there is no release key, and the manifest says so")

    if args.zip:
        out = Path(args.zip).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(MANIFEST, f"{HERE.name}/manifest.json")
            for rel in tracked_files():
                z.write(HERE / rel, f"{HERE.name}/{rel}")
        print(f"  ✓ {out} ({out.stat().st_size // 1024} KB)")

    print("\n  Agents propose. Humans judge. Nurses steward.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
