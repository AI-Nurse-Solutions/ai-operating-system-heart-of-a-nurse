#!/usr/bin/env python3
"""
NAIO OS — recovery.py (Phase 8)

Local-only recovery snapshot and restore-plan tool for rendered NAIO Hermes
profile bundles. It never mutates ~/.hermes, never schedules cron, never
performs automatic restore, and refuses PHI-like content.

Modes:
- --snapshot --profile <dir> --backup-dir <dir>
- --verify <snapshot.tar.gz>
- --plan <snapshot.tar.gz> --output <dir>
- --drill --profile <dir>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

VERSION = "2.0.0-phase8"
DOCTRINE = "Agents propose. Humans judge. Nurses steward."
REQUIRED_MARKERS = ["SOUL.md", "config/edena-runtime.yaml", "config/human-gates.yaml", "logs/render-report.json"]
REFUSED_TARGETS = {Path.home().resolve(), (Path.home() / ".hermes").resolve()}
PHI_PATTERNS = [
    (re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"), "SSN-like pattern"),
    (re.compile(r"\b\d{3}[\s.-]?\d{3}[\s.-]?\d{4}\b", re.I), "phone-like pattern"),
    (re.compile(r"\b(?:MRN|medical record|patient id|DOB|date of birth|diagnosis|ICD-?10|CPT)\b[: ]", re.I), "clinical identifier"),
    (re.compile(r"\b(?:insurance|medicaid|medicare|policy)\s*(?:#|number|id)\b", re.I), "insurance identifier"),
]


def refuse(message: str) -> None:
    print(f"❌ REFUSED: {message}", file=sys.stderr)
    sys.exit(2)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_rel(root: Path, path: Path) -> str:
    rel = path.relative_to(root).as_posix()
    if rel.startswith("../") or rel == ".." or rel.startswith("/"):
        refuse(f"unsafe path escaped profile root: {path}")
    return rel


def text_files(root: Path):
    for p in sorted(root.rglob("*")):
        if p.is_file() and not p.is_symlink():
            try:
                p.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            yield p


def screen_phi(root: Path) -> None:
    hits: list[str] = []
    for p in text_files(root):
        txt = p.read_text(encoding="utf-8", errors="ignore")
        for pat, label in PHI_PATTERNS:
            m = pat.search(txt)
            if m:
                hits.append(f"{safe_rel(root, p)}: {label}: {m.group(0)[:24]!r}")
                break
    if hits:
        refuse("PHI indicators detected; recovery snapshots must be sanitized first: " + "; ".join(hits[:5]))


def validate_profile(profile: Path) -> None:
    profile = profile.resolve()
    if not profile.is_dir():
        refuse(f"profile directory not found: {profile}")
    if profile in REFUSED_TARGETS:
        refuse("refusing to snapshot home or ~/.hermes directly; use a rendered NAIO profile target")
    for rel in REQUIRED_MARKERS:
        if not (profile / rel).is_file():
            refuse(f"not a rendered NAIO profile bundle; missing {rel}")
    screen_phi(profile)


def inventory(profile: Path) -> list[dict]:
    items = []
    for p in sorted(profile.rglob("*")):
        if p.is_dir():
            continue
        if p.is_symlink():
            refuse(f"symlinks are refused in recovery snapshots: {safe_rel(profile, p)}")
        rel = safe_rel(profile, p)
        items.append({"path": rel, "sha256": sha256_file(p), "bytes": p.stat().st_size})
    return items


def write_snapshot(profile: Path, backup_dir: Path) -> Path:
    profile = profile.resolve()
    backup_dir = backup_dir.resolve()
    validate_profile(profile)
    if backup_dir in REFUSED_TARGETS:
        refuse("backup-dir cannot be home or ~/.hermes")
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snapshot = backup_dir / f"naio-profile-recovery-{ts}.tar.gz"
    manifest = {
        "schema_version": "1.0.0",
        "version": VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "profile_name": profile.name,
        "profile_root_name": "NAIO-Hermes-Profile",
        "mode": "local_only_recovery_snapshot",
        "mutation": "none_to_hermes_home",
        "no_phi_screen": True,
        "doctrine": DOCTRINE,
        "files": inventory(profile),
    }
    with tempfile.TemporaryDirectory(prefix="naio-recovery-manifest-") as td:
        mp = Path(td) / "NAIO-RECOVERY-MANIFEST.json"
        mp.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        with tarfile.open(snapshot, "w:gz") as tar:
            for p in sorted(profile.rglob("*")):
                if p.is_file():
                    tar.add(p, arcname=f"NAIO-Hermes-Profile/{safe_rel(profile, p)}", recursive=False)
            tar.add(mp, arcname="NAIO-RECOVERY-MANIFEST.json", recursive=False)
    digest = sha256_file(snapshot)
    (snapshot.with_suffix(snapshot.suffix + ".sha256")).write_text(f"{digest}  {snapshot.name}\n", encoding="utf-8")
    print(json.dumps({"status": "created", "snapshot": str(snapshot), "sha256": digest, "files": len(manifest["files"]), "no_mutation": True}, indent=2))
    return snapshot


def verify_tar_safety(snapshot: Path) -> dict:
    snapshot = snapshot.resolve()
    if not snapshot.is_file():
        refuse(f"snapshot not found: {snapshot}")
    sidecar = snapshot.with_suffix(snapshot.suffix + ".sha256")
    digest = sha256_file(snapshot)
    if sidecar.is_file():
        expected = sidecar.read_text(encoding="utf-8").split()[0]
        if expected != digest:
            refuse(f"snapshot sha256 mismatch: expected {expected[:12]}…, got {digest[:12]}…")
    with tarfile.open(snapshot, "r:gz") as tar:
        names = tar.getnames()
        for member in tar.getmembers():
            name = member.name
            p = Path(name)
            if p.is_absolute() or ".." in p.parts:
                refuse(f"unsafe archive path refused: {name}")
            if member.issym() or member.islnk() or member.isdev():
                refuse(f"unsafe archive member refused: {name}")
        if "NAIO-RECOVERY-MANIFEST.json" not in names:
            refuse("snapshot missing NAIO-RECOVERY-MANIFEST.json")
        manifest_file = tar.extractfile("NAIO-RECOVERY-MANIFEST.json")
        if manifest_file is None:
            refuse("cannot read recovery manifest")
        assert manifest_file is not None
        manifest = json.loads(manifest_file.read().decode("utf-8"))
    if manifest.get("doctrine") != DOCTRINE:
        refuse("recovery manifest doctrine mismatch")
    if manifest.get("no_phi_screen") is not True:
        refuse("recovery manifest missing no-PHI screen attestation")
    files = manifest.get("files", [])
    if not isinstance(files, list) or not files:
        refuse("recovery manifest has no files")
    print(json.dumps({"status": "verified", "snapshot": str(snapshot), "sha256": digest, "files": len(files), "no_mutation": True}, indent=2))
    return manifest


def extract_safely(snapshot: Path, dest: Path) -> Path:
    verify_tar_safety(snapshot)
    dest = dest.resolve()
    if dest in REFUSED_TARGETS:
        refuse("extract destination cannot be home or ~/.hermes")
    dest.mkdir(parents=True, exist_ok=True)
    root = dest / "extracted"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir()
    with tarfile.open(snapshot, "r:gz") as tar:
        for member in tar.getmembers():
            target = (root / member.name).resolve()
            if not str(target).startswith(str(root.resolve()) + "/") and target != root.resolve():
                refuse(f"archive extraction would escape destination: {member.name}")
            tar.extract(member, root)
    return root


def write_restore_plan(snapshot: Path, output: Path) -> Path:
    manifest = verify_tar_safety(snapshot)
    output = output.resolve()
    if output in REFUSED_TARGETS:
        refuse("restore-plan output cannot be home or ~/.hermes")
    output.mkdir(parents=True, exist_ok=True)
    plan = output / "NAIO-RESTORE-PLAN.md"
    lines = [
        "# NAIO Restore Plan — Phase 8",
        "",
        "This is a **plan**, not an automatic restore. Review before copying anything into Hermes.",
        "",
        f"- Snapshot: `{snapshot}`",
        f"- Version: `{manifest.get('version')}`",
        f"- Files: {len(manifest.get('files', []))}",
        "- Mutation: none performed by this plan",
        "- Boundary: no PHI, no clinical decisions, no direct `~/.hermes` mutation",
        "",
        "## Human restore steps",
        "1. Verify the snapshot with `scripts/recovery.py --verify <snapshot.tar.gz>`.",
        "2. Extract to a temporary review folder, not directly into `~/.hermes`.",
        "3. Review `SOUL.md`, `config/human-gates.yaml`, skills, and cron templates.",
        "4. Copy only the files you intentionally approve into your Hermes profile.",
        "5. Do not schedule cron rituals until reviewed line-by-line.",
        "",
        "## Included files",
    ]
    for item in manifest.get("files", []):
        lines.append(f"- `{item['path']}` — `{item['sha256'][:12]}…` ({item['bytes']} bytes)")
    lines += ["", DOCTRINE, ""]
    plan.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "plan-written", "plan": str(plan), "files": len(manifest.get('files', [])), "no_mutation": True}, indent=2))
    return plan


def compare_inventory(a: Path, b: Path) -> bool:
    ai = {x["path"]: x["sha256"] for x in inventory(a)}
    bi = {x["path"]: x["sha256"] for x in inventory(b)}
    return ai == bi


def drill(profile: Path) -> None:
    profile = profile.resolve()
    validate_profile(profile)
    with tempfile.TemporaryDirectory(prefix="naio-recovery-drill-") as td:
        td_p = Path(td)
        backup_dir = td_p / "backups"
        snapshot = write_snapshot(profile, backup_dir)
        verify_tar_safety(snapshot)
        extracted = extract_safely(snapshot, td_p / "restore-review")
        extracted_profile = extracted / "NAIO-Hermes-Profile"
        if not extracted_profile.is_dir():
            refuse("drill extraction missing NAIO-Hermes-Profile root")
        if not compare_inventory(profile, extracted_profile):
            refuse("drill inventory mismatch after extract")
        write_restore_plan(snapshot, td_p / "plans")
    print(json.dumps({"status": "drill-passed", "profile": str(profile), "version": VERSION, "no_mutation": True}, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="NAIO OS Phase 8 local recovery snapshots and restore drills")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--snapshot", action="store_true", help="create a local recovery snapshot")
    mode.add_argument("--verify", metavar="SNAPSHOT", help="verify a recovery snapshot")
    mode.add_argument("--plan", metavar="SNAPSHOT", help="write a human restore plan for a snapshot")
    mode.add_argument("--drill", action="store_true", help="snapshot, verify, extract, compare, and plan in temp directories")
    parser.add_argument("--profile", help="rendered NAIO profile target directory")
    parser.add_argument("--backup-dir", help="explicit local backup directory")
    parser.add_argument("--output", help="explicit directory for restore-plan output")
    args = parser.parse_args()

    if args.snapshot:
        if not args.profile or not args.backup_dir:
            refuse("--snapshot requires --profile and --backup-dir")
        write_snapshot(Path(args.profile), Path(args.backup_dir))
    elif args.verify:
        verify_tar_safety(Path(args.verify))
    elif args.plan:
        if not args.output:
            refuse("--plan requires --output")
        write_restore_plan(Path(args.plan), Path(args.output))
    elif args.drill:
        if not args.profile:
            refuse("--drill requires --profile")
        drill(Path(args.profile))
    return 0


if __name__ == "__main__":
    sys.exit(main())
