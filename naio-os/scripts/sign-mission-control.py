#!/usr/bin/env python3
"""
NAIO OS — sign-mission-control.py

Bring Mission Control under the naio-os signing chain in one command, or
rehearse the whole thing without a key.

    scripts/sign-mission-control.py --rehearse
    scripts/sign-mission-control.py --key /path/to/naio-os-release-private.pem

WHY THIS EXISTS. The procedure it replaces was seven manual steps across two
directories, with a hand-edited JSON digest in the middle and a fail-closed
verifier at the end. Every step is individually easy and the sequence is not:
`compute-checksums.sh` rewrites manifest.yaml, so hashing or signing before it
runs produces a signature for a file that no longer exists, and the failure
surfaces as a verifier refusing the release rather than as a mistake anyone can
see. A key-holder gets one attempt at this on a release day. It should be one
command, and it should be rehearsable by people who do not hold the key.

WHAT IT DOES, in order:

  1. Pins SOURCE_DATE_EPOCH to the commit being released, so the archive built
     in step 2 is byte-identical for anyone who rebuilds it from that commit.
  2. Runs Mission Control's own release build: self-test, manifest.json,
     manifest.sig, and a reproducible assets/mission-control.zip.
  3. Writes BOTH entries into manifest.yaml's `contents` — the nested manifest
     and the archive. The nested manifest is what makes the checksums signed;
     the archive is what makes them fetched. Neither is sufficient alone, and
     §11 of mission-control/ARCHITECTURE.md explains why at length.
  4. compute-checksums.sh, manifest.sha256, release.json's digest, manifest.sig.
  5. verify-release.py.

ALL OR NOTHING. Everything happens in a staging copy of the tree. The real
tree is touched only after verify-release.py passes there — so a run that fails
anywhere leaves a repository that still verifies, which is the property that
matters when the alternative is a half-signed release nobody can roll back
without the key.

  Agents propose. Humans judge. Nurses steward.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import suppress
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parent.parent
MC = ROOT / "mission-control"
ZIP_REL = "assets/mission-control.zip"

# Written back into the real tree, and only after the staged copy verifies.
OUTPUTS = [
    "manifest.yaml",
    "manifest.sha256",
    "manifest.sig",
    "release.json",
    ZIP_REL,
    "mission-control/manifest.json",
    "mission-control/manifest.sig",
    "mission-control/README.md",       # release.py stamps the self-test count
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(cmd: list[str], cwd: Path, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True,
                          env={**os.environ, **(env or {})})


def source_date_epoch() -> str:
    """
    The commit timestamp, so the archive is a function of the source.

    Falls back to a fixed epoch outside a git checkout rather than to the wall
    clock: an unreproducible release artifact is the thing this exists to
    prevent, so the fallback has to be reproducible too.
    """
    r = run(["git", "log", "-1", "--format=%ct"], ROOT)
    stamp = r.stdout.strip()
    return stamp if r.returncode == 0 and stamp.isdigit() else "1785024000"


def upsert_entry(contents: list, path: str, role: str, digest: str) -> str:
    """Add or update one `contents` entry, returning what happened for the log."""
    for item in contents:
        if item.get("path") == path:
            was = item.get("sha256")
            item["role"], item["sha256"] = role, digest
            return "unchanged" if was == digest else "updated"
    contents.append({"path": path, "role": role, "sha256": digest})
    return "added"


def stage(work: Path) -> Path:
    """
    A copy of the bundle to work in, so a failure never lands in the repo.

    The bundle is copied; its siblings are symlinked. Mission Control's
    self-test reaches out of the bundle to check the committed SOUL fixture
    against what soul-quiz emits and to wire the published Starter Kit, and it
    SKIPS those when it cannot find them — so staging the bundle alone quietly
    ran a smaller suite, and `release.py` would then stamp that smaller number
    into manifest.json and README.md as the release's test count. Symlinks are
    enough because the self-test only reads them, and they keep the staging
    cost at the bundle rather than the whole repository.
    """
    staged = work / ROOT.name
    shutil.copytree(ROOT, staged, symlinks=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc",
                                                  "mission_control.db", "backups"))
    for sibling in ROOT.parent.iterdir():
        if sibling.name in {ROOT.name, ".git"}:
            continue
        with suppress(OSError):
            (work / sibling.name).symlink_to(sibling, target_is_directory=sibling.is_dir())
    return staged


def throwaway_key(work: Path) -> tuple[Path, Path]:
    priv, pub = work / "rehearsal-private.pem", work / "rehearsal-public.pem"
    subprocess.run(["openssl", "genpkey", "-algorithm", "RSA",
                    "-pkeyopt", "rsa_keygen_bits:2048", "-out", str(priv)],
                   check=True, capture_output=True)
    subprocess.run(["openssl", "rsa", "-in", str(priv), "-pubout", "-out", str(pub)],
                   check=True, capture_output=True)
    return priv, pub


def sign_bundle(staged: Path, key: Path, public_key: Path, epoch: str,
                say) -> list[str]:
    """The whole operation, inside `staged`. Raises RuntimeError on any failure."""
    notes = []
    env = {"SOURCE_DATE_EPOCH": epoch}
    mc = staged / "mission-control"

    # 1. Mission Control's own build: self-test, manifest.json, manifest.sig.
    r = run([sys.executable, "tools/release.py", "--sign", str(key),
             "--public-key", str(public_key), "--zip", str(staged / ZIP_REL)], mc, env)
    if r.returncode != 0:
        raise RuntimeError(f"mission-control release build failed:\n{r.stdout}{r.stderr}")
    for line in r.stdout.splitlines():
        if "self-test:" in line or "manifest.json —" in line or "signed —" in line:
            notes.append(line.strip().lstrip("✓ ").strip())
    say(f"  ✓ mission-control built and signed (SOURCE_DATE_EPOCH={epoch})")

    zip_path = staged / ZIP_REL
    if not zip_path.is_file():
        raise RuntimeError(f"{ZIP_REL} was not produced")
    say(f"  ✓ {ZIP_REL} — {zip_path.stat().st_size // 1024} KB, "
        f"sha256 {sha256_file(zip_path)[:12]}…")

    # 2. Both entries into the signed manifest. One without the other is the
    #    half-measure §11 warns about, so they go in together or not at all.
    manifest_p = staged / "manifest.yaml"
    manifest = yaml.safe_load(manifest_p.read_text(encoding="utf-8"))
    contents = manifest.setdefault("contents", [])
    what = [
        upsert_entry(contents, "mission-control/manifest.json",
                     "mission-control-manifest", sha256_file(mc / "manifest.json")),
        upsert_entry(contents, ZIP_REL, "mission-control-archive", sha256_file(zip_path)),
        # The tool that cuts the release belongs in the release it cuts, next to
        # verify-release.py and self-test.py, which are already covered. A
        # signing script nobody can check the integrity of is a gap in the same
        # chain it maintains.
        upsert_entry(contents, "scripts/sign-mission-control.py", "release-signer",
                     sha256_file(staged / "scripts/sign-mission-control.py")),
    ]
    manifest_p.write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True, width=1000),
        encoding="utf-8")
    say(f"  ✓ manifest.yaml — nested manifest {what[0]}, archive {what[1]}, "
        f"signer {what[2]}")

    # 3. compute-checksums.sh REWRITES manifest.yaml, so it has to run before
    #    anything hashes or signs that file. This ordering is the whole reason
    #    the manual procedure was worth replacing.
    r = run(["bash", "scripts/compute-checksums.sh"], staged)
    if r.returncode != 0:
        raise RuntimeError(f"compute-checksums.sh failed:\n{r.stdout}{r.stderr}")
    say("  ✓ content checksums recomputed")

    digest = sha256_file(manifest_p)
    (staged / "manifest.sha256").write_text(f"{digest}  manifest.yaml\n", encoding="utf-8")

    release_p = staged / "release.json"
    release = json.loads(release_p.read_text(encoding="utf-8"))
    release.setdefault("manifest", {})["sha256"] = digest
    release_p.write_text(json.dumps(release, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8")
    say(f"  ✓ manifest.sha256 and release.json digest — {digest[:12]}…")

    r = run(["openssl", "dgst", "-sha256", "-sign", str(key),
             "-out", str(staged / "manifest.sig"), "manifest.yaml"], staged)
    if r.returncode != 0:
        raise RuntimeError(f"signing manifest.yaml failed:\n{r.stdout}{r.stderr}")
    say("  ✓ manifest.sig written")

    # 4. The gate. Nothing reaches the real tree unless this passes here.
    r = run([sys.executable, "scripts/verify-release.py"], staged)
    if r.returncode != 0:
        raise RuntimeError(f"verify-release.py refused the result:\n{r.stdout}{r.stderr}")
    say("  ✓ verify-release.py passed against the staged bundle")
    return notes


def publish(staged: Path, dest_root: Path, backup: Path) -> list[str]:
    """
    Copy the staged artifacts across, or put everything back.

    Publication is the one step that touches the repository, and it is eight
    separate copies. A failure partway through — a full disk, an unwritable
    destination, a Ctrl-C — would leave a new manifest.yaml beside the old
    nested artifacts it no longer describes: a tree that verifies neither as the
    old release nor as the new one, with no key on hand to re-cut it. Staging
    makes the *computation* all-or-nothing; this makes the write all-or-nothing
    too, which is the half that a reviewer of the first version rightly pointed
    out was still missing.

    Takes dest_root rather than reading the module global so the rollback can be
    tested against a scratch tree. An untested rollback is a comment.
    """
    done: list[tuple[str, bool]] = []       # (path, did it exist before this run)
    try:
        for rel in OUTPUTS:
            src, dst = staged / rel, dest_root / rel
            if not src.is_file():
                continue
            existed = dst.is_file()
            if existed:
                keep = backup / rel
                keep.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dst, keep)
            # Recorded BEFORE the write, not after: copy2 truncates its
            # destination first, so the file being written when a disk fills is
            # the one most in need of restoring.
            done.append((rel, existed))
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    except (OSError, KeyboardInterrupt):
        for rel, existed in reversed(done):
            with suppress(OSError):
                if existed:
                    shutil.copy2(backup / rel, dest_root / rel)
                else:
                    (dest_root / rel).unlink()
        raise
    return [rel for rel, _ in done]


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Bring Mission Control under the naio-os signing chain")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--key", metavar="PEM",
                      help="private half of naio-os-release-key-2026-06")
    mode.add_argument("--rehearse", action="store_true",
                      help="run the whole procedure against a throwaway keypair in a "
                           "scratch copy, verify it, and change nothing")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    def say(msg: str):
        if not args.quiet:
            print(msg)

    if yaml is None:
        print("  ✗ pyyaml is required — pip install -r requirements-import-soul.txt")
        return 2
    if not shutil.which("openssl"):
        print("  ✗ openssl not found")
        return 2

    say("\n=== NAIO OS — Mission Control signing chain ===\n")
    epoch = source_date_epoch()

    with tempfile.TemporaryDirectory(prefix="naio-sign-") as tmp:
        work = Path(tmp)
        staged = stage(work)

        if args.rehearse:
            key, public_key = throwaway_key(work)
            # The rehearsal has to verify against the key it actually used, so
            # the staged copy's pinned public half is swapped for the throwaway.
            # This is why a rehearsal cannot accidentally produce something
            # shippable: the artifacts it makes verify only against a key that
            # is deleted when this function returns.
            (staged / "config/naio-os-release-public.pem").write_bytes(public_key.read_bytes())
            say("  ✓ throwaway keypair generated (the real key is not needed to rehearse)")
        else:
            key = Path(args.key).expanduser().resolve()
            if not key.is_file():
                print(f"  ✗ no signing key at {key}")
                return 2
            public_key = (ROOT / "config/naio-os-release-public.pem").resolve()

        try:
            notes = sign_bundle(staged, key, public_key, epoch, say)
        except RuntimeError as exc:
            print(f"\n  ✗ {exc}")
            print("\n❌ NOTHING WAS CHANGED — the repository still verifies as it did.")
            return 1

        if args.rehearse:
            print("\n✅ REHEARSAL PASSED — the procedure is sound end to end.")
            print("   Nothing was written. Re-run with --key to do it for real.")
            for note in notes:
                print(f"     · {note}")
            return 0

        try:
            written = publish(staged, ROOT, work / "rollback")
        except (OSError, KeyboardInterrupt) as exc:
            print(f"\n  ✗ publishing failed: {exc}")
            print("\n❌ ROLLED BACK — the repository is as it was before this run.")
            return 1
        say(f"  ✓ wrote {len(written)} artifacts into the working tree")

    print("\n✅ MISSION CONTROL IS SIGNED AND IN THE CHAIN.")
    print("   Commit the artifacts, publish the archive at the release base_url,")
    print("   and `naio-mc verify` will report a signed build.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
