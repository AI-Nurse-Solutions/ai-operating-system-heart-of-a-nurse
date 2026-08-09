#!/usr/bin/env python3
"""Fail-closed validator for the personal Knowledge Base pilot.

Implements the manual-first intake checks of knowledge-commons/PLAYBOOK.md
(§5 manifest groups, §7.2 intake scan, §12 local installation) at personal
scale. Deterministic and stdlib-only: no model, no network, no clock beyond
date-format parsing. A passed scan means only that automated checks found
no listed defect — it is not approval, and it never populates the library.

Usage:
    python3 validate_pack.py PACK_DIR            # validate one pack
    python3 validate_pack.py --check             # validate all packs + the lock (exit 2 on refusal)
    python3 validate_pack.py --relock            # refresh digests for already-accepted packs
    python3 validate_pack.py --print-digests PACK_DIR   # print content digests for a manifest
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path

KB_DIR = Path(__file__).resolve().parent
REPO_ROOT = KB_DIR.parents[1]
PACKS_DIR = KB_DIR / "packs"
LOCK_PATH = KB_DIR / "library-lock.json"
LOCK_CONTRACT = "personal-library-lock v0.1"

REQUIRED_GROUPS = (
    "identity",
    "people",
    "purpose",
    "context",
    "governance",
    "evidence",
    "review",
    "rights",
    "integrity",
    "lifecycle",
    "relationships",
    "ai_disclosure",
)
TRIAGE_STATES = {
    "draft",
    "submitted",
    "quarantined",
    "under_review",
    "changes_requested",
    "accepted_for_scope",
    "published",
    "superseded",
    "retired",
    "recalled",
    "withdrawn",
}
# States that must not be held in a personal library (PLAYBOOK.md §11.7).
REMOVAL_STATES = {"quarantined", "superseded", "retired", "recalled", "withdrawn"}
ALLOWED_TIERS = {"green", "yellow"}
HELD_TIERS = {
    "orange": "Orange content is held, never down-classified (PLAYBOOK.md §8.4)",
    "red-p": "Red-P content is prohibited",
    "red-e": "Red-E content is refused outside emergency governance",
}
ALLOWED_MODES = {"observe", "draft", "recommend"}
ALLOWED_LANES = {"learn", "practice", "lead", "build"}
CONTENT_SUFFIXES = {".md"}
# Backstop screen for obvious identifier markers; the no-PHI attestation
# remains the primary control.
PHI_MARKERS = (
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "SSN-like number"),
    (re.compile(r"\bMRN\s*[:#]", re.IGNORECASE), "medical record number marker"),
    (re.compile(r"\bDOB\s*:", re.IGNORECASE), "date-of-birth marker"),
)
SLUG_RE = re.compile(r"[a-z0-9][a-z0-9-]*")
VERSION_RE = re.compile(r"\d+\.\d+\.\d+")


def sha256_file(path: Path) -> str:
    """Return the SHA-256 hex digest of a file's bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_iso_date(value: object) -> bool:
    """Return True when value is a well-formed ISO calendar date string."""
    try:
        datetime.date.fromisoformat(str(value))
        return True
    except ValueError:
        return False


def nonempty_str(value: object) -> bool:
    """Return True when value is a non-empty, non-whitespace string."""
    return isinstance(value, str) and bool(value.strip())


def nonempty_str_list(value: object) -> bool:
    """Return True when value is a non-empty list of non-empty strings."""
    return (
        isinstance(value, list)
        and bool(value)
        and all(nonempty_str(item) for item in value)
    )


def validate_pack(pack_dir: Path, repo_root: Path = REPO_ROOT) -> list[str]:
    """Run every fail-closed intake check on one pack; return refusal reasons."""
    name = pack_dir.name
    problems: list[str] = []
    manifest_path = pack_dir / "pack.json"
    if not manifest_path.is_file():
        return [f"{name}: pack.json missing"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        return [f"{name}: pack.json is not valid JSON ({err})"]
    if not isinstance(manifest, dict):
        return [f"{name}: pack.json must be a JSON object"]

    for group in REQUIRED_GROUPS:
        if not isinstance(manifest.get(group), dict):
            problems.append(f"{name}: manifest group {group!r} missing or not an object")
    if problems:
        return problems

    identity = manifest["identity"]
    if identity.get("id") != name:
        problems.append(f"{name}: identity.id must equal the pack directory name")
    if not (nonempty_str(identity.get("id")) and SLUG_RE.fullmatch(identity["id"] or "")):
        problems.append(f"{name}: identity.id must be a lowercase slug")
    if not nonempty_str(identity.get("title")):
        problems.append(f"{name}: identity.title missing")
    if not (nonempty_str(identity.get("version")) and VERSION_RE.fullmatch(identity["version"])):
        problems.append(f"{name}: identity.version must be MAJOR.MINOR.PATCH")
    if identity.get("state") not in TRIAGE_STATES:
        problems.append(f"{name}: identity.state must be a PLAYBOOK.md §7.3 triage state")

    if not nonempty_str(manifest["people"].get("creator")):
        problems.append(f"{name}: people.creator missing — contributor identity is required")

    purpose = manifest["purpose"]
    if purpose.get("lane") not in ALLOWED_LANES:
        problems.append(f"{name}: purpose.lane must be one of {sorted(ALLOWED_LANES)}")
    for field in ("intended_use", "prohibited_use"):
        if not nonempty_str_list(purpose.get(field)):
            problems.append(f"{name}: purpose.{field} must be a non-empty list")

    if not nonempty_str_list(manifest["context"].get("languages")):
        problems.append(f"{name}: context.languages must be a non-empty list")

    governance = manifest["governance"]
    tier = governance.get("edena_tier")
    if tier in HELD_TIERS:
        problems.append(f"{name}: edena_tier {tier!r} refused — {HELD_TIERS[tier]}")
    elif tier not in ALLOWED_TIERS:
        problems.append(f"{name}: edena_tier must be 'green' or 'yellow'")
    if governance.get("data_class") != "D0":
        problems.append(
            f"{name}: data_class must be 'D0' — the public pack ceiling (PLAYBOOK.md §18)"
        )
    modes = governance.get("action_modes")
    if not (isinstance(modes, list) and modes and set(modes) <= ALLOWED_MODES):
        problems.append(
            f"{name}: action_modes must be a non-empty subset of {sorted(ALLOWED_MODES)} "
            "— Recommend is the kit ceiling (governance-kit/GOVERNANCE.yaml)"
        )
    if governance.get("no_phi_attested") is not True:
        problems.append(f"{name}: governance.no_phi_attested must be true")
    if not nonempty_str(governance.get("accountable_human")):
        problems.append(f"{name}: governance.accountable_human missing")
    if not nonempty_str_list(governance.get("stop_conditions")):
        problems.append(f"{name}: governance.stop_conditions must be a non-empty list")

    evidence = manifest["evidence"]
    sources = evidence.get("sources")
    if not (isinstance(sources, list) and sources):
        problems.append(f"{name}: evidence.sources must be a non-empty list")
    else:
        for idx, source in enumerate(sources):
            label = f"{name}: evidence.sources[{idx}]"
            if not (isinstance(source, dict) and nonempty_str(source.get("title"))):
                problems.append(f"{label} needs a title")
                continue
            if nonempty_str(source.get("path")):
                resolved = (repo_root / source["path"]).resolve()
                if not resolved.is_relative_to(repo_root.resolve()):
                    problems.append(f"{label} path escapes the repository")
                elif not resolved.exists():
                    problems.append(f"{label} path does not resolve: {source['path']}")
            elif not nonempty_str(source.get("url")):
                problems.append(f"{label} needs a repo-relative path or a url")
    if not nonempty_str_list(evidence.get("limitations")):
        problems.append(f"{name}: evidence.limitations must be a non-empty list")
    if not parse_iso_date(evidence.get("review_due")):
        problems.append(f"{name}: evidence.review_due must be an ISO date")

    review = manifest["review"]
    for field in ("status", "independent_review"):
        if not nonempty_str(review.get(field)):
            problems.append(
                f"{name}: review.{field} missing — record review honestly, "
                "never claim review that did not happen"
            )

    rights = manifest["rights"]
    if not nonempty_str(rights.get("license")):
        problems.append(
            f"{name}: rights.license missing — every pack declares its license "
            "explicitly; repository documentation licensing is not inherited"
        )
    if not isinstance(rights.get("third_party"), list):
        problems.append(f"{name}: rights.third_party must be a list (may be empty)")

    if not parse_iso_date(manifest["lifecycle"].get("created")):
        problems.append(f"{name}: lifecycle.created must be an ISO date")

    disclosure = manifest["ai_disclosure"]
    if not isinstance(disclosure.get("assisted"), bool):
        problems.append(f"{name}: ai_disclosure.assisted must be a boolean")
    elif disclosure["assisted"] and not nonempty_str(disclosure.get("human_verification")):
        problems.append(
            f"{name}: ai_disclosure.human_verification required when AI assisted"
        )

    problems.extend(_check_files(pack_dir, manifest))
    return problems


def _check_files(pack_dir: Path, manifest: dict) -> list[str]:
    """Verify the content inventory: exact coverage, digests, and no active content."""
    name = pack_dir.name
    problems: list[str] = []
    files = manifest["integrity"].get("files")
    if not (isinstance(files, dict) and files):
        return [f"{name}: integrity.files must be a non-empty map of path -> sha256"]

    for entry in sorted(pack_dir.iterdir()):
        if entry.name not in ("pack.json", "content"):
            problems.append(
                f"{name}: unexpected entry {entry.name!r} — a pack holds only "
                "pack.json and content/"
            )

    listed: set[Path] = set()
    for rel, digest in sorted(files.items()):
        label = f"{name}: integrity.files[{rel}]"
        rel_path = Path(rel)
        if rel_path.is_absolute() or ".." in rel_path.parts or rel_path.parts[:1] != ("content",):
            problems.append(f"{label} must be a relative path under content/")
            continue
        if rel_path.suffix not in CONTENT_SUFFIXES:
            problems.append(
                f"{label} refused — only markdown documents are pack content; "
                "active or executable content is not"
            )
            continue
        target = pack_dir / rel_path
        if not target.is_file():
            problems.append(f"{label} listed but missing from disk")
            continue
        listed.add(rel_path)
        if sha256_file(target) != digest:
            problems.append(
                f"{label} digest is stale — refusing; no review or acceptance "
                "may silently follow changing bytes"
            )
            continue
        text = target.read_text(encoding="utf-8")
        for pattern, marker in PHI_MARKERS:
            if pattern.search(text):
                problems.append(f"{label} contains a {marker} — packs carry no PHI")

    content_dir = pack_dir / "content"
    on_disk = (
        {p.relative_to(pack_dir) for p in content_dir.rglob("*") if p.is_file()}
        if content_dir.is_dir()
        else set()
    )
    if not on_disk:
        problems.append(f"{name}: content/ is missing or empty")
    for rel_path in sorted(on_disk - listed):
        problems.append(
            f"{name}: {rel_path} exists on disk but is not in integrity.files — "
            "unlisted content is refused"
        )
    return problems


def load_lock(lock_path: Path) -> tuple[dict | None, list[str]]:
    """Load and structurally validate the library lock file."""
    if not lock_path.is_file():
        return None, [f"{lock_path.name}: missing"]
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        return None, [f"{lock_path.name}: not valid JSON ({err})"]
    if not isinstance(lock, dict) or lock.get("contract") != LOCK_CONTRACT:
        return None, [f"{lock_path.name}: contract must be {LOCK_CONTRACT!r}"]
    if not isinstance(lock.get("packs"), list):
        return None, [f"{lock_path.name}: packs must be a list"]
    return lock, []


def validate_library(kb_dir: Path = KB_DIR, repo_root: Path = REPO_ROOT) -> list[str]:
    """Validate every pack on disk and every lock entry; return refusal reasons."""
    packs_dir = kb_dir / "packs"
    problems: list[str] = []
    pack_dirs = sorted(p for p in packs_dir.iterdir() if p.is_dir()) if packs_dir.is_dir() else []
    if not pack_dirs:
        problems.append("packs/: no packs found")
    for pack_dir in pack_dirs:
        problems.extend(validate_pack(pack_dir, repo_root))

    lock, lock_problems = load_lock(kb_dir / "library-lock.json")
    problems.extend(lock_problems)
    if lock is None:
        return problems

    seen: set[str] = set()
    accepted: set[str] = set()
    for idx, entry in enumerate(lock["packs"]):
        label = f"library-lock.json packs[{idx}]"
        if not isinstance(entry, dict):
            problems.append(f"{label}: must be an object")
            continue
        pack_id = entry.get("id")
        if not nonempty_str(pack_id):
            problems.append(f"{label}: id missing")
            continue
        if pack_id in seen:
            problems.append(f"{label}: duplicate entry for {pack_id!r}")
            continue
        seen.add(pack_id)
        for field in ("accepted_by", "state_at_acceptance"):
            if not nonempty_str(entry.get(field)):
                problems.append(
                    f"{label}: {field} missing — acceptance is a recorded human act"
                )
        if not parse_iso_date(entry.get("accepted_date")):
            problems.append(f"{label}: accepted_date must be an ISO date")
        if entry.get("path") != f"packs/{pack_id}":
            problems.append(f"{label}: path must be packs/{pack_id}")
        pack_dir = packs_dir / pack_id
        manifest_path = pack_dir / "pack.json"
        if not manifest_path.is_file():
            problems.append(f"{label}: accepted pack {pack_id!r} is not on disk")
            continue
        if sha256_file(manifest_path) != entry.get("manifest_sha256"):
            problems.append(
                f"{label}: manifest digest is stale — re-inspect the pack and "
                "re-accept before relocking"
            )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        state = manifest.get("identity", {}).get("state")
        if state in REMOVAL_STATES:
            problems.append(
                f"{label}: pack state {state!r} must leave the library "
                "(PLAYBOOK.md §11.7 removal and invalidation)"
            )
        if manifest.get("identity", {}).get("version") != entry.get("version"):
            problems.append(
                f"{label}: version differs from the manifest — re-inspect and re-accept"
            )
        accepted.add(pack_id)

    for pack_dir in pack_dirs:
        if pack_dir.name not in accepted:
            print(f"NOTE: {pack_dir.name} is on disk but not accepted into the library")
    return problems


def relock(kb_dir: Path = KB_DIR) -> int:
    """Refresh digests and versions for already-accepted packs; never add entries."""
    lock, lock_problems = load_lock(kb_dir / "library-lock.json")
    if lock is None:
        for problem in lock_problems:
            print(f"REFUSED: {problem}")
        return 2
    for entry in lock["packs"]:
        manifest_path = kb_dir / "packs" / entry["id"] / "pack.json"
        if not manifest_path.is_file():
            print(f"REFUSED: accepted pack {entry['id']!r} is not on disk")
            return 2
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        entry["manifest_sha256"] = sha256_file(manifest_path)
        entry["version"] = manifest.get("identity", {}).get("version")
    (kb_dir / "library-lock.json").write_text(
        json.dumps(lock, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Relocked {len(lock['packs'])} accepted pack(s); no packs were added")
    return 0


def print_digests(pack_dir: Path) -> int:
    """Print the sha256 of each content file, ready to paste into integrity.files."""
    content_dir = pack_dir / "content"
    if not content_dir.is_dir():
        print(f"REFUSED: {pack_dir.name}: content/ is missing")
        return 2
    for path in sorted(content_dir.rglob("*")):
        if path.is_file():
            rel = path.relative_to(pack_dir)
            print(f'"{rel.as_posix()}": "{sha256_file(path)}"')
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: validate a pack or the library, relock, or print digests."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pack_dir", nargs="?", type=Path, default=None)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--relock", action="store_true")
    parser.add_argument("--print-digests", action="store_true")
    args = parser.parse_args(argv)

    if args.relock:
        return relock()
    if args.print_digests:
        if args.pack_dir is None:
            print("REFUSED: --print-digests requires a pack directory")
            return 2
        return print_digests(args.pack_dir)
    if args.check or args.pack_dir is None:
        problems = validate_library()
    else:
        problems = validate_pack(args.pack_dir)
    if problems:
        for problem in problems:
            print(f"REFUSED: {problem}")
        return 2
    print("OK: no listed defect found — a passed scan is not approval")
    return 0


if __name__ == "__main__":
    sys.exit(main())
