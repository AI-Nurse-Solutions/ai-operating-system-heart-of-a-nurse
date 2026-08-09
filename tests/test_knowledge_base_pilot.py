#!/usr/bin/env python3
"""Contracts for the personal Knowledge Base pilot (personal-agi/knowledge-base)."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / "personal-agi" / "knowledge-base"
VALIDATOR = KB / "validate_pack.py"
REFERENCE = KB / "packs" / "governed-ai-study-basics"

spec = importlib.util.spec_from_file_location("validate_pack", VALIDATOR)
validate_pack = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_pack)


def build_pack(root: Path, mutate=None, content: str = "# Guide\n\nBody.\n") -> Path:
    """Write a minimal valid pack under root, optionally mutated before saving."""
    pack_dir = root / "test-pack"
    (pack_dir / "content").mkdir(parents=True)
    content_path = pack_dir / "content" / "guide.md"
    content_path.write_text(content, encoding="utf-8")
    manifest = {
        "identity": {"id": "test-pack", "title": "Test Pack", "version": "0.1.0", "state": "draft"},
        "people": {"creator": "Test Author"},
        "purpose": {
            "lane": "learn",
            "intended_use": ["testing"],
            "prohibited_use": ["clinical use"],
        },
        "context": {"languages": ["en"]},
        "governance": {
            "edena_tier": "green",
            "data_class": "D0",
            "action_modes": ["observe"],
            "no_phi_attested": True,
            "accountable_human": "the tester",
            "stop_conditions": ["any real-world use"],
        },
        "evidence": {
            "sources": [{"title": "Repository README", "path": "README.md"}],
            "limitations": ["fixture only"],
            "review_due": "2027-01-01",
        },
        "review": {"status": "author_reviewed_only", "independent_review": "None."},
        "rights": {"license": "Apache-2.0", "third_party": []},
        "integrity": {
            "files": {
                "content/guide.md": hashlib.sha256(content_path.read_bytes()).hexdigest()
            }
        },
        "lifecycle": {"created": "2026-08-09"},
        "relationships": {},
        "ai_disclosure": {"assisted": False},
    }
    if mutate:
        mutate(manifest, pack_dir)
    (pack_dir / "pack.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return pack_dir


class KnowledgeBasePilotTests(unittest.TestCase):
    def refusals(self, mutate=None, content: str = "# Guide\n\nBody.\n") -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            pack_dir = build_pack(Path(tmp), mutate, content)
            return validate_pack.validate_pack(pack_dir, repo_root=ROOT)

    def test_fixture_pack_validates_cleanly(self) -> None:
        self.assertEqual(self.refusals(), [])

    def test_reference_pack_validates_cleanly(self) -> None:
        self.assertEqual(validate_pack.validate_pack(REFERENCE), [])

    def test_library_check_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), "--check"],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("a passed scan is not approval", result.stdout)

    def test_reference_pack_is_honest_about_review(self) -> None:
        manifest = json.loads((REFERENCE / "pack.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["identity"]["state"], "draft")
        self.assertEqual(manifest["review"]["status"], "author_reviewed_only")
        self.assertIn("independent review", manifest["review"]["independent_review"].lower())
        self.assertIsNone(manifest["lifecycle"]["published"])

    def test_reference_content_carries_boundary_language(self) -> None:
        content_files = sorted((REFERENCE / "content").glob("*.md"))
        self.assertTrue(content_files)
        for path in content_files:
            text = path.read_text(encoding="utf-8")
            self.assertIn("not clinical guidance", text, path.name)
            self.assertIn("## Sources", text, path.name)
            self.assertIn("## Limitations", text, path.name)
            self.assertIn(
                "Agents propose. Humans judge. Nurses steward.", text, path.name
            )

    def test_lock_records_human_acceptance(self) -> None:
        lock = json.loads((KB / "library-lock.json").read_text(encoding="utf-8"))
        self.assertEqual(lock["contract"], "personal-library-lock v0.1")
        for entry in lock["packs"]:
            self.assertTrue(entry["accepted_by"].strip())
            self.assertTrue(entry["accepted_date"].strip())

    def test_orange_tier_is_held(self) -> None:
        def mutate(manifest, _):
            manifest["governance"]["edena_tier"] = "orange"

        problems = self.refusals(mutate)
        self.assertTrue(any("held" in p for p in problems), problems)

    def test_data_class_above_d0_is_refused(self) -> None:
        def mutate(manifest, _):
            manifest["governance"]["data_class"] = "D1"

        problems = self.refusals(mutate)
        self.assertTrue(any("D0" in p for p in problems), problems)

    def test_action_mode_above_recommend_is_refused(self) -> None:
        def mutate(manifest, _):
            manifest["governance"]["action_modes"] = ["draft", "prepare_action"]

        problems = self.refusals(mutate)
        self.assertTrue(any("ceiling" in p for p in problems), problems)

    def test_missing_license_is_refused(self) -> None:
        def mutate(manifest, _):
            manifest["rights"]["license"] = ""

        problems = self.refusals(mutate)
        self.assertTrue(any("license" in p for p in problems), problems)

    def test_stale_digest_is_refused(self) -> None:
        def mutate(manifest, pack_dir):
            (pack_dir / "content" / "guide.md").write_text(
                "# Changed after digesting\n", encoding="utf-8"
            )

        problems = self.refusals(mutate)
        self.assertTrue(any("stale" in p for p in problems), problems)

    def test_unlisted_content_is_refused(self) -> None:
        def mutate(_, pack_dir):
            (pack_dir / "content" / "smuggled.md").write_text("hi\n", encoding="utf-8")

        problems = self.refusals(mutate)
        self.assertTrue(any("unlisted" in p.lower() for p in problems), problems)

    def test_non_markdown_content_is_refused(self) -> None:
        def mutate(manifest, pack_dir):
            script = pack_dir / "content" / "run.sh"
            script.write_text("#!/bin/sh\necho active\n", encoding="utf-8")
            manifest["integrity"]["files"]["content/run.sh"] = hashlib.sha256(
                script.read_bytes()
            ).hexdigest()

        problems = self.refusals(mutate)
        self.assertTrue(any("active or executable" in p for p in problems), problems)

    def test_phi_marker_is_refused(self) -> None:
        problems = self.refusals(content="# Guide\n\nPatient SSN 123-45-6789.\n")
        self.assertTrue(any("PHI" in p for p in problems), problems)

    def test_removal_state_cannot_stay_in_library(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            kb_dir = Path(tmp)
            packs_dir = kb_dir / "packs"
            packs_dir.mkdir()

            def mutate(manifest, _):
                manifest["identity"]["state"] = "recalled"

            pack_dir = build_pack(packs_dir, mutate)
            lock = {
                "contract": "personal-library-lock v0.1",
                "packs": [
                    {
                        "id": "test-pack",
                        "version": "0.1.0",
                        "path": "packs/test-pack",
                        "manifest_sha256": hashlib.sha256(
                            (pack_dir / "pack.json").read_bytes()
                        ).hexdigest(),
                        "accepted_by": "the tester",
                        "accepted_date": "2026-08-09",
                        "state_at_acceptance": "draft",
                    }
                ],
            }
            (kb_dir / "library-lock.json").write_text(
                json.dumps(lock, indent=2) + "\n", encoding="utf-8"
            )
            problems = validate_pack.validate_library(kb_dir, repo_root=ROOT)
            self.assertTrue(any("leave the library" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
