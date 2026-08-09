#!/usr/bin/env python3
"""Render role-tuned briefs from NAIO signal distillation records.

Deterministic by design: every word in a rendered brief comes from the
record's ``role_briefs`` field (written with judgment at distillation
time) or from this fixed template. No model, no network, no clock —
the same records always render the same briefs.

Usage:
    python3 render_briefs.py            # regenerate briefs/ next to the records
    python3 render_briefs.py --out DIR  # render into DIR instead
    python3 render_briefs.py --check    # exit 2 if briefs/ differs from records
"""

from __future__ import annotations

import argparse
import filecmp
import json
import sys
import tempfile
from pathlib import Path

SIGNALS_DIR = Path(__file__).resolve().parent
BRIEFS_DIRNAME = "briefs"

ROLE_LABELS = {
    "student": "Nursing Student & Assistant",
    "staff": "Staff Nurse",
    "np": "Nurse Practitioner (USA)",
    "leader": "Nurse Leader & Manager",
    "educator": "Nurse Educator",
    "resident": "Medical Resident",
    "resp": "Respiratory Care",
    "research": "Research & Innovation Leader",
    "admin": "Hospital / Clinic Administrator",
    "wellness": "Wellness Business",
}

FIELDS = (
    ("what_happened", "What happened"),
    ("why_it_matters_to_you", "Why it matters to you"),
    ("do_now", "Do now"),
    ("dont_do", "Don't"),
    ("watch", "Watch"),
)


def load_records(signals_dir: Path) -> list[tuple[Path, dict]]:
    records = []
    for path in sorted(signals_dir.glob("*.json")):
        with path.open(encoding="utf-8") as handle:
            records.append((path, json.load(handle)))
    return records


def brief_markdown(record_path: Path, record: dict, role: str, fields: dict) -> str:
    meta = record.get("signal_metadata", {})
    triage = record.get("triage", {})
    title = meta.get("title", record_path.stem)
    lines = [
        f"# Signal brief — {ROLE_LABELS.get(role, role)}",
        "",
        f"> **Signal:** {title}",
        f"> **Evidence tier:** {meta.get('evidence_tier', 'UNSPECIFIED')} · "
        f"**Urgency:** {triage.get('urgency', 'UNSPECIFIED')} · "
        f"**Valence:** {triage.get('valence', 'UNSPECIFIED')}",
        f"> **Source record:** `{record_path.name}` — the full distillation, "
        "including refusal-posture analysis and open questions.",
        "",
    ]
    for key, label in FIELDS:
        lines.append(f"**{label}.** {fields[key]}")
        lines.append("")
    lines.extend(
        [
            "---",
            "",
            "This brief is a hypothesis for your judgment, not an instruction, "
            "a vendor verdict, or institutional guidance. It contains no PHI and "
            "authorizes nothing. Rendered by `render_briefs.py` from the source "
            "record — edit the record, not this file.",
            "",
            "*Agents propose. Humans judge. Nurses steward.*",
            "",
        ]
    )
    return "\n".join(lines)


def index_markdown(entries: list[tuple[str, str, list[str]]]) -> str:
    lines = [
        "# Role briefs",
        "",
        "Rendered from the signal records in the parent directory by "
        "`render_briefs.py`. One folder per signal, one brief per role lane. "
        "Do not hand-edit — edit the record and re-render.",
        "",
    ]
    for slug, title, roles in entries:
        lines.append(f"## {title}")
        lines.append("")
        for role in roles:
            lines.append(f"- [{ROLE_LABELS.get(role, role)}]({slug}/{role}.md)")
        lines.append("")
    lines.append("*Agents propose. Humans judge. Nurses steward.*")
    lines.append("")
    return "\n".join(lines)


def render(signals_dir: Path, out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    count = 0
    for record_path, record in load_records(signals_dir):
        role_briefs = record.get("role_briefs")
        if not isinstance(role_briefs, dict) or not role_briefs:
            continue
        slug = record_path.stem
        slug_dir = out_dir / slug
        slug_dir.mkdir(parents=True, exist_ok=True)
        roles = []
        for role, fields in role_briefs.items():
            missing = [key for key, _ in FIELDS if not str(fields.get(key, "")).strip()]
            if missing:
                raise SystemExit(
                    f"{record_path.name}: role_briefs[{role}] missing {missing}"
                )
            (slug_dir / f"{role}.md").write_text(
                brief_markdown(record_path, record, role, fields), encoding="utf-8"
            )
            roles.append(role)
            count += 1
        entries.append(
            (slug, record.get("signal_metadata", {}).get("title", slug), roles)
        )
    (out_dir / "README.md").write_text(index_markdown(entries), encoding="utf-8")
    return count


def trees_match(left: Path, right: Path) -> bool:
    left_files = sorted(p.relative_to(left) for p in left.rglob("*.md"))
    right_files = sorted(p.relative_to(right) for p in right.rglob("*.md"))
    if left_files != right_files:
        return False
    return all(
        filecmp.cmp(left / rel, right / rel, shallow=False) for rel in left_files
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    briefs_dir = SIGNALS_DIR / BRIEFS_DIRNAME
    if args.check:
        with tempfile.TemporaryDirectory() as tmp:
            fresh = Path(tmp) / BRIEFS_DIRNAME
            render(SIGNALS_DIR, fresh)
            if not briefs_dir.is_dir() or not trees_match(fresh, briefs_dir):
                print("STALE: briefs/ does not match the records — re-run render_briefs.py")
                return 2
        print("OK: briefs/ matches the records")
        return 0

    count = render(SIGNALS_DIR, args.out or briefs_dir)
    print(f"Rendered {count} brief(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
