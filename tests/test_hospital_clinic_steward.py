#!/usr/bin/env python3
"""Acceptance, nonclaim, provenance, isolation, and packaging tests for STEWARD preview."""

from __future__ import annotations

import hashlib
import json
import runpy
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEWARD = ROOT / "hospital-clinic-administrators"
PREVIEW = STEWARD / "preview"
DOWNLOADS = STEWARD / "downloads"
SPEC = PREVIEW / "STEWARD-Governance-Specification.md"
PDF = PREVIEW / "STEWARD-Governance-Specification.pdf"
GAPS = PREVIEW / "STEWARD-Enforcement-Gap-Register.md"
PROVENANCE = PREVIEW / "SOURCE-PROVENANCE.json"
ZIP = DOWNLOADS / "steward-governance-preview.zip"
ZIP_PREFIX = "STEWARD-Governance-Preview/"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class StewardGovernancePreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = SPEC.read_text(encoding="utf-8")
        cls.gaps = GAPS.read_text(encoding="utf-8")
        cls.readme = (PREVIEW / "README.md").read_text(encoding="utf-8")
        cls.provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
        cls.page = (STEWARD / "index.html").read_text(encoding="utf-8")
        cls.home = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.css = (ROOT / "assets" / "nurse-ai.css").read_text(encoding="utf-8")
        cls.workflow = (ROOT / ".github" / "workflows" / "hospital-clinic-steward.yml").read_text(encoding="utf-8")

    def test_public_artifact_inventory_excludes_installer_payload(self):
        expected = {
            "PACKAGE-CHECKSUMS.sha256",
            "README.md",
            "SOURCE-PROVENANCE.json",
            "STEWARD-Enforcement-Gap-Register.md",
            "STEWARD-Governance-Specification.md",
            "STEWARD-Governance-Specification.pdf",
        }
        self.assertEqual({p.name for p in PREVIEW.iterdir() if p.is_file()}, expected)
        self.assertFalse((STEWARD / "packages").exists())
        all_paths = "\n".join(p.relative_to(STEWARD).as_posix() for p in STEWARD.rglob("*") if p.is_file())
        for forbidden in ("Hermes-Program", "Setup-Guide", "SuperPowers-Pack", "ROLE-PACK"):
            self.assertNotIn(forbidden, all_paths)

    def test_specification_status_and_complete_ai_os_claim(self):
        for phrase in (
            "Public governance preview · non-executable · not institution-approved",
            "This document is a governance specification, not software",
            "Complete AI OS claim | **Paused**",
            "Runtime adapter | **Not implemented**",
            "Institutional authorization | **Not granted**",
        ):
            self.assertIn(phrase, self.spec)
        self.assertIn("installable **Complete AI OS** claim remains paused", self.readme)

    def test_one_lane_context_variant_architecture_is_preserved(self):
        for phrase in (
            "population: `hospital_clinic_administration`",
            "namespace: `hcadmin_steward.*`",
            "Why one lane",
            "Why context variants are mandatory",
            "clinic, ambulatory, or practice manager",
            "dual-hat clinician-administrator",
            "unknown or unverified authority",
        ):
            self.assertIn(phrase, self.spec)

    def test_human_authority_and_consequential_action_boundaries(self):
        for phrase in (
            "AI may prepare. Authorized humans judge, approve, act, record, and remain accountable",
            "A title is context, not permission",
            "Human approval must not convert a prohibited function into an allowed one",
            "official-system writes or official records",
        ):
            self.assertIn(phrase, self.spec)
        self.assertIn("will not perform, stage, execute, or transmit", self.gaps)
        self.assertIn("Human review or approval does not convert", self.gaps)
        self.assertNotIn("will not autonomously perform", self.gaps)

    def test_no_operational_data_or_prompt_level_privacy_claim(self):
        for phrase in (
            "This preview accepts **no operational data**",
            "A prompt-level refusal is not a privacy control",
            "validated **pre-model** controls",
            "Aggregate data is not automatically anonymous",
            "Hiding a field or panel is not technical separation",
        ):
            self.assertIn(phrase, self.spec)
        self.assertFalse(self.provenance["public_distribution"]["operational_data_authorized"])

    def test_no_surveillance_or_hidden_workforce_scoring(self):
        for phrase in (
            "must not rank, risk-score, profile, monitor, or predict",
            "sentiment",
            "burnout or impairment",
            "productivity or individual performance",
            "Psychological-safety and listening work is especially sensitive",
        ):
            self.assertIn(phrase, self.spec)

    def test_zero_agents_and_no_runtime_artifacts(self):
        self.assertIn("This preview ships **zero agents**", self.spec)
        self.assertIn("No capability above is implemented, active, installable, or available for operational use", self.spec)
        self.assertEqual(self.provenance["source_inventory"]["agent_runtime_artifacts"], 0)
        self.assertEqual(self.provenance["source_inventory"]["executable_schema_artifacts"], 0)
        self.assertFalse(self.provenance["public_distribution"]["executable_or_installer_included"])
        self.assertFalse(self.provenance["public_distribution"]["activation_instructions_included"])

    def test_gap_register_has_sixteen_open_enforcement_gates(self):
        ids = [f"STW-G{i:02d}" for i in range(1, 17)]
        for gap_id in ids:
            self.assertEqual(self.gaps.count(gap_id), 1, gap_id)
        self.assertEqual(self.gaps.count("| Open |"), 16)
        for phrase in ("pre-model PHI/sensitive-data control", "segregation-of-duties", "Smallest next step"):
            self.assertIn(phrase, self.gaps)

    def test_source_provenance_records_static_audit_not_runtime_proof(self):
        archive = self.provenance["source_archive"]
        self.assertEqual(archive["sha256"], "30d44b5372390318ce324d973d854a73a6aa840e889b2f960df4340d58ee2752")
        self.assertEqual(archive["bytes"], 363602)
        self.assertEqual(archive["members"], 23)
        self.assertTrue(archive["crc_passed"])
        self.assertEqual(archive["internal_checksum_matches"], 22)
        self.assertEqual(self.provenance["source_parity"]["embedded_components_matched"], 17)
        self.assertEqual(self.provenance["audit_disposition"], "source_integrity_verified_runtime_enforcement_not_established")
        self.assertFalse(self.provenance["public_distribution"]["original_source_payload_included"])
        review = self.provenance["review_context"]
        self.assertFalse(review["publicly_reproducible_from_preview_alone"])
        self.assertIn("not third-party certification", review["review_type"])
        self.assertIn("not third-party certification", self.spec)

    def test_pdf_is_pinned_publication_artifact(self):
        pdf = PDF.read_bytes()
        self.assertTrue(pdf.startswith(b"%PDF-"))
        self.assertEqual(PDF.stat().st_size, 563521)
        self.assertEqual(sha256(PDF), "ce56db69ce02ed1ff2968b57d2ea53eba1e7f22b9095b9c3acb7835d2af25e45")
        self.assertEqual(sha256(SPEC), "3be24aeb2405ec1020261888166696ab8758ca510df8b563214199deac0a0925")
        for marker in (b"/StructTreeRoot", b"/MarkInfo", b"/Marked true", b"/Lang (en)"):
            self.assertIn(marker, pdf)

    def test_accessibility_landmarks_motion_and_maturity_labels(self):
        for page in (self.page, self.home):
            self.assertIn('class="skip-link" href="#main-content"', page)
            self.assertIn('<main id="main-content" tabindex="-1">', page)
        self.assertIn("@media (prefers-reduced-motion: reduce)", self.css)
        self.assertIn("color: #116b69", self.css)
        self.assertIn("Documentation review only — no runtime tier assigned", self.spec)
        for ambiguous in ("EDENA Yellow", "Phase A — Green", "Phase B — Yellow", "Phase C — Orange", "Phase D — Red"):
            self.assertNotIn(ambiguous, self.spec + self.gaps)

    def test_ci_tracks_generated_artifacts_and_runs_hash_pinned_pdf_gate(self):
        for phrase in (
            "actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5 # v4",
            "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 # v5",
            '"LICENSE"',
            '"scripts/check-steward-pdf.py"',
            '"scripts/requirements-steward-pdf.txt"',
            "--require-hashes",
            "git ls-files --error-unmatch",
            "git status --porcelain --untracked-files=all",
            "target.relative_to(root)",
            "python3 scripts/check-steward-pdf.py --self-test",
        ):
            self.assertIn(phrase, self.workflow)
        requirement = (ROOT / "scripts" / "requirements-steward-pdf.txt").read_text(encoding="utf-8")
        self.assertEqual(
            requirement,
            "pypdf==6.14.2 --hash=sha256:3f07891af76dc002657e04993ab9b4de81de29f9013b9761d0b7968bff12e946\n",
        )

    def test_public_page_is_preview_not_product_or_installer(self):
        for phrase in (
            "Public governance preview · Hospital and clinic administration",
            "This is a specification, not software",
            "Complete AI OS claim paused",
            "Runtime not implemented",
            "Not institution-approved",
            "This preview ships zero agents",
            "Smallest next step",
        ):
            self.assertIn(phrase, self.page)
        self.assertNotIn("Install safely", self.page)
        self.assertNotIn("Activation Card", self.page)
        self.assertNotIn("Complete Edition", self.page)
        self.assertNotIn("Hermes-Program", self.page)
        self.assertIn("youtube-nocookie.com/embed/xdlnYkMJQl4", self.page)
        self.assertIn("vision narrative, not evidence", self.page)

    def test_public_page_links_only_preview_artifacts(self):
        for link in (
            'href="preview/STEWARD-Governance-Specification.md"',
            'href="preview/STEWARD-Governance-Specification.pdf"',
            'href="preview/STEWARD-Enforcement-Gap-Register.md"',
            'href="preview/SOURCE-PROVENANCE.json"',
            'href="downloads/steward-governance-preview.zip"',
        ):
            self.assertIn(link, self.page)
        self.assertNotIn("steward-hospital-clinic-administrator-complete-edition", self.page)

    def test_homepage_handoff_is_preview_and_outside_nurse_role_grid(self):
        page = (ROOT / "index.html").read_text(encoding="utf-8")
        admin = page.index('class="home-admin-lane"')
        self.assertLess(page.index('class="home-resident-video"'), page.index('class="home-rt-video"'))
        self.assertLess(page.index('class="home-rt-video"'), admin)
        self.assertLess(page.index('class="home-discover-video"'), page.index('class="home-thrive-video"'))
        self.assertLess(page.index('class="home-thrive-video"'), admin)
        self.assertLess(admin, page.index("<!-- ============ ROLE CARDS"))
        region = page[admin:page.index("<!-- ============ ROLE CARDS")]
        for phrase in ("Public governance preview", "STEWARD Governance Specification", "Non-executable", "Complete AI OS claim remains paused"):
            self.assertIn(phrase, region)
        self.assertIn("youtube-nocookie.com/embed/xdlnYkMJQl4", region)

    def test_no_cross_population_registration_or_state(self):
        nurse_manifest = json.loads((ROOT / "post-setup" / "downloads" / "manifest.json").read_text(encoding="utf-8"))
        self.assertNotIn("STEWARD", json.dumps(nurse_manifest))
        setup_model = (ROOT / "setup-helper" / "setup-helper-model.mjs").read_text(encoding="utf-8")
        self.assertNotIn("hospital_clinic_administration", setup_model)
        rounds = (ROOT / "medical-residents" / "packages" / "rounds" / "ROLE-PACK.json").read_text(encoding="utf-8")
        breathe = (ROOT / "respiratory-care" / "packages" / "breathe" / "ROLE-PACK.json").read_text(encoding="utf-8")
        self.assertNotIn("hcadmin_steward", rounds + breathe)

    def test_package_checksum_ledger_is_exact(self):
        ledger = {}
        for line in (PREVIEW / "PACKAGE-CHECKSUMS.sha256").read_text(encoding="utf-8").splitlines():
            digest, name = line.split("  ", 1)
            self.assertNotIn(name, ledger)
            ledger[name] = digest
        self.assertEqual(set(ledger), {"LICENSE", "README.md", "SOURCE-PROVENANCE.json", "STEWARD-Enforcement-Gap-Register.md", "STEWARD-Governance-Specification.md", "STEWARD-Governance-Specification.pdf"})
        for name, digest in ledger.items():
            path = ROOT / "LICENSE" if name == "LICENSE" else PREVIEW / name
            self.assertEqual(sha256(path), digest)

    def test_public_manifest_and_zip_contract(self):
        public = json.loads((DOWNLOADS / "manifest.json").read_text(encoding="utf-8"))
        record = public["packages"][0]
        self.assertEqual(record["artifact_class"], "non_executable_governance_preview")
        self.assertEqual(record["runtime_status"], "not_implemented")
        self.assertEqual(record["complete_ai_os_claim"], "paused")
        self.assertFalse(record["activation_available"])
        self.assertFalse(record["institutional_authorization"])
        self.assertFalse(record["operational_data_authorized"])
        self.assertEqual(record["sha256"], sha256(ZIP))
        self.assertEqual(record["bytes"], ZIP.stat().st_size)
        self.assertEqual((DOWNLOADS / "CHECKSUMS.sha256").read_text(encoding="utf-8"), f"{sha256(ZIP)}  {ZIP.name}\n")

    def test_deterministic_zip_has_only_preview_artifacts(self):
        with zipfile.ZipFile(ZIP) as archive:
            self.assertIsNone(archive.testzip())
            expected_names = {
                ZIP_PREFIX + name for name in (
                    "LICENSE", "PACKAGE-CHECKSUMS.sha256", "README.md", "SOURCE-PROVENANCE.json",
                    "STEWARD-Enforcement-Gap-Register.md", "STEWARD-Governance-Specification.md",
                    "STEWARD-Governance-Specification.pdf",
                )
            }
            self.assertEqual(set(archive.namelist()), expected_names)
            for info in archive.infolist():
                self.assertEqual(info.date_time, (2026, 7, 16, 0, 0, 0))
                self.assertEqual(info.create_system, 3)
                self.assertEqual(info.external_attr >> 16, 0o100644)
            names = "\n".join(archive.namelist())
            for forbidden in ("Hermes-Program", "Setup-Guide", "SuperPowers-Pack", "ROLE-PACK"):
                self.assertNotIn(forbidden, names)

    def test_builder_rejects_document_tampering(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-hospital-clinic-steward.py"))
        validator = namespace["validate_sources"]
        with tempfile.TemporaryDirectory() as temp:
            copied = Path(temp) / "preview"
            shutil.copytree(PREVIEW, copied)
            with (copied / "STEWARD-Governance-Specification.md").open("ab") as handle:
                handle.write(b"\nTAMPER")
            validator.__globals__["PREVIEW"] = copied
            with self.assertRaises(ValueError):
                validator()
        validator.__globals__["PREVIEW"] = PREVIEW

    def test_deterministic_builder_reproduces_committed_zip(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-hospital-clinic-steward.py"))
        before = sha256(ZIP)
        record = namespace["build"]()
        self.assertEqual(record["sha256"], before)
        self.assertEqual(sha256(ZIP), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
