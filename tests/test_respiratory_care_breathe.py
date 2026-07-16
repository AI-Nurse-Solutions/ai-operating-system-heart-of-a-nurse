#!/usr/bin/env python3
"""Acceptance, safety, isolation, provenance, and packaging tests for BREATHE."""

from __future__ import annotations

import hashlib
import json
import re
import runpy
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BREATHE = ROOT / "respiratory-care"
PACKAGE = BREATHE / "packages" / "breathe"
SOURCE_PACK = PACKAGE / "Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0"
DOWNLOADS = BREATHE / "downloads"
PROGRAM = PACKAGE / "Respiratory-Care-Complete-AI-OS-with-BREATHE-SuperPowers-Hermes-Program.md"
GUIDE = PACKAGE / "Respiratory-Care-Complete-AI-OS-with-BREATHE-SuperPowers-Setup-Guide.md"
DOCX = PACKAGE / "Respiratory-Care-Complete-AI-OS-with-BREATHE-SuperPowers-Setup-Guide.docx"
MANIFEST = PACKAGE / "ROLE-PACK.json"
ZIP = DOWNLOADS / "breathe-respiratory-care-complete-edition.zip"
ZIP_PREFIX = "BREATHE-Respiratory-Care-Complete-Edition/"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class BreatheRespiratoryCareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.program = PROGRAM.read_text(encoding="utf-8")
        cls.guide = GUIDE.read_text(encoding="utf-8")
        cls.read_first = (PACKAGE / "00-READ-FIRST.md").read_text(encoding="utf-8")
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_required_artifacts_and_archive_provenance(self):
        for path in (PROGRAM, GUIDE, DOCX, PACKAGE / "UPSTREAM-SHA256SUMS.txt"):
            self.assertTrue(path.is_file(), path)
        package_readme = (PACKAGE / "README.md").read_text(encoding="utf-8")
        self.assertIn("`PACKAGE-CHECKSUMS.sha256`", package_readme)
        self.assertIn("`UPSTREAM-SHA256SUMS.txt`", package_readme)
        self.assertNotIn("`SHA256SUMS.txt`", package_readme)
        archive = self.manifest["source_archive"]
        self.assertEqual(archive["sha256"], "7fc1d4b0a8dec362bcd41e5e049b1498d70fc2cbfd9d0348f5d7b240172f2edb")
        self.assertEqual(archive["bytes"], 317428)
        self.assertEqual(archive["members"], 23)
        records = {item["packaged_path"]: item for item in self.manifest["source_files"]}
        self.assertEqual(len(records), 23)
        expected_key_sources = {
            PROGRAM.name: (
                "63821c41bd20b34edd7245d2eb640d695b7a80b33e0586893a8387e444d813bb",
                "0250340ba2b1603d84c56603f7271ac6531e20cb6979bc2a0e25d62ab896406a",
            ),
            GUIDE.name: (
                "1ff712f65a167c812b66e32cfa4d588be247617506640772da349592c2e988ff",
                "f80690b24eacbe2b2724119107be78e887b166115ea95ebdef19f84e3ec33cbd",
            ),
            DOCX.name: (
                "d2bf6752d59cffb0ca772a0387326a7fb918dc846bc14a080b86fc7ea90ae8dc",
                "d2bf6752d59cffb0ca772a0387326a7fb918dc846bc14a080b86fc7ea90ae8dc",
            ),
        }
        for name, (upstream, packaged) in expected_key_sources.items():
            self.assertEqual(records[name]["upstream_sha256"], upstream)
            self.assertEqual(records[name]["source_sha256"], packaged)
            self.assertEqual(sha256(PACKAGE / name), packaged)
            self.assertEqual((PACKAGE / name).stat().st_size, records[name]["bytes"])

    def test_markdown_normalization_and_embedded_source_parity(self):
        markdown = list(PACKAGE.rglob("*.md"))
        self.assertEqual(len(markdown), 22)
        for path in markdown:
            text = path.read_text(encoding="utf-8")
            self.assertFalse(any(line.endswith(" ") for line in text.splitlines()), path)
            self.assertNotRegex(text, r"(?m)^    (?:#|\|)")
        records = self.manifest["source_files"]
        normalized = [item for item in records if item["transformation"].startswith("replaced supplied Markdown")]
        self.assertEqual(len(normalized), 7)
        markers = re.findall(r"^<!-- BEGIN EMBEDDED COMPONENT: (.+) -->$", self.program, re.MULTILINE)
        self.assertEqual(len(markers), 17)
        self.assertEqual(len(set(markers)), 17)
        for relative in markers:
            start = f"<!-- BEGIN EMBEDDED COMPONENT: {relative} -->"
            end = f"<!-- END EMBEDDED COMPONENT: {relative} -->"
            segment = self.program.split(start, 1)[1].split(end, 1)[0].strip("\n")
            source = (SOURCE_PACK / relative).read_text(encoding="utf-8").strip("\n")
            self.assertEqual(segment, source, relative)

    def test_power_workflow_template_schema_and_agent_inventories(self):
        powers = sorted({int(x) for x in re.findall(r"^## Power (\d+)\b", self.program, re.MULTILINE)})
        self.assertEqual(powers, list(range(1, 25)))
        workflow_text = (SOURCE_PACK / "workflows" / "BREATHE-Workflows-Launch-and-Adoption-Plan.md").read_text(encoding="utf-8")
        workflows = [int(x) for x in re.findall(r"^### WF-(\d{2})\b", workflow_text, re.MULTILINE)]
        self.assertEqual(workflows, list(range(1, 25)))
        templates_text = (SOURCE_PACK / "templates" / "BREATHE-Cards-and-Templates.md").read_text(encoding="utf-8")
        templates = [int(x) for x in re.findall(r"^## Template (\d+)\b", templates_text, re.MULTILINE)]
        self.assertEqual(templates, list(range(1, 31)))
        foundation = (SOURCE_PACK / "foundation" / "Respiratory-Care-Life-Practice-and-Professional-Foundation.md").read_text(encoding="utf-8")
        schema_section = foundation.split("## Eighteen professional-owned record schemas", 1)[1].split("## Canonical Source Watch registry", 1)[0]
        schemas = re.findall(r"^\| `([^`]+)` \|", schema_section, re.MULTILINE)
        self.assertEqual(len(schemas), 18)
        self.assertEqual(len(set(schemas)), 18)
        agents = re.findall(r"^- \*\*AGT-(\d{2}):.*PERM-P0 Disabled", workflow_text, re.MULTILINE)
        self.assertEqual(agents, [f"{i:02d}" for i in range(1, 11)])

    def test_reviewed_data_approval_and_agent_contracts_are_representable(self):
        workflow = (SOURCE_PACK / "workflows" / "BREATHE-Workflows-Launch-and-Adoption-Plan.md").read_text(encoding="utf-8")
        templates = (SOURCE_PACK / "templates" / "BREATHE-Cards-and-Templates.md").read_text(encoding="utf-8")
        agent_powers = (SOURCE_PACK / "breathe" / "07-E-Engineer-Ethical-Agents.md").read_text(encoding="utf-8")
        lane = (SOURCE_PACK / "core" / "00-Standalone-Respiratory-Care-Lane-and-Human-Standard.md").read_text(encoding="utf-8")

        headers = re.findall(r"^\*\*Common header:\*\* (.+)$", templates, re.MULTILINE)
        self.assertEqual(len(headers), 30)
        for header in headers:
            for field in ("fact-versus-interpretation", "human decision owner", "status"):
                self.assertIn(field, header)

        receipts = re.findall(r"^\*\*Completion receipt:\*\* (.+)$", workflow, re.MULTILINE)
        self.assertEqual(len(receipts), 24)
        for receipt in receipts:
            for field in ("named approver", "approval scope", "approval timestamp", "receipt ID", "approved artifact/version"):
                self.assertIn(field, receipt)

        wf04 = workflow.split("### WF-04", 1)[1].split("### WF-05", 1)[0]
        self.assertIn("whole_life_private", wf04)
        self.assertIn("institution-managed BREATHE Private mode rejects", wf04)

        wf22 = workflow.split("### WF-22", 1)[1].split("### WF-23", 1)[0]
        self.assertIn("apply ORBIT once", wf22)
        self.assertIn("add CIRCLE only", wf22)
        self.assertNotIn("or ORBIT for a named agent", wf22)

        tpl28 = templates.split("## Template 28", 1)[1].split("## Template 29", 1)[0]
        for field in ("Agent sequence", "Permission intersection", "transfer contracts", "Disagreement", "Named human review order", "Failure, containment", "Termination, kill"):
            self.assertIn(field, tpl28)
        self.assertIn("completed `TPL-28` Multi-Agent Sequence Map", agent_powers)
        self.assertIn("Powers 22–24 remain `Available Inactive`", lane)
        self.assertIn("associated suggested agents remain `PERM-P0 Disabled`", lane)

    def test_declared_release_checks_are_exact_unique_and_not_claimed_as_executed(self):
        release = (SOURCE_PACK / "tests" / "BREATHE-Release-Assurance.md").read_text(encoding="utf-8")
        ids = re.findall(r"^- \[ \] \*\*(RA-(?:[A-R]\d{2}|INT\d{2}))\b", release, re.MULTILINE)
        self.assertEqual(len(ids), 160)
        self.assertEqual(len(set(ids)), 160)
        self.assertEqual(len([x for x in ids if not x.startswith("RA-INT")]), 144)
        self.assertEqual([x for x in ids if x.startswith("RA-INT")], [f"RA-INT{i:02d}" for i in range(1, 17)])
        self.assertIn("They do **not** prove the checks ran in a respiratory professional's environment", self.read_first)
        self.assertIn("not evidence that all scenarios ran in a respiratory professional's environment", (BREATHE / "index.html").read_text(encoding="utf-8"))

    def test_standalone_identity_and_no_cross_population_state(self):
        self.assertEqual(self.manifest["population_lane"], "respiratory_care")
        self.assertEqual(self.manifest["route"], "/respiratory-care/")
        self.assertEqual(self.manifest["namespace"], "resp_breathe.*")
        self.assertEqual(self.manifest["respiratory_home"], "My BREATHE")
        self.assertTrue(self.manifest["standalone_non_nurse_lane"])
        self.assertFalse(self.manifest["nursing_population_state_shared"])
        self.assertFalse(self.manifest["medical_resident_population_state_shared"])
        for phrase in (
            "adjacent, standalone respiratory-care lane",
            "not a nursing role",
            "ROUNDS extension",
            "If isolation cannot be proven, installation must stop before mutation",
        ):
            self.assertIn(phrase, self.read_first)
        nurse_manifest = json.loads((ROOT / "post-setup" / "downloads" / "manifest.json").read_text(encoding="utf-8"))
        self.assertNotIn("BREATHE", json.dumps(nurse_manifest))
        self.assertNotIn("respiratory_care", json.dumps(nurse_manifest))
        setup_model = (ROOT / "setup-helper" / "setup-helper-model.mjs").read_text(encoding="utf-8")
        self.assertNotIn("respiratory_care", setup_model)
        rounds_manifest = (ROOT / "medical-residents" / "packages" / "rounds" / "ROLE-PACK.json").read_text(encoding="utf-8")
        self.assertNotIn("resp_breathe", rounds_manifest)

    def test_preinstall_consent_and_installation_order(self):
        for phrase in (
            "Downloading, selecting, opening, or unzipping this package does not install or activate anything",
            "allows a read-only owner, target, isolation, role, credential",
            "reviews the exact combined BREATHE Activation Card",
            "Silence, timeout, download, title, credential",
            "create S0 and the rollback snapshot",
            "run 72 foundation-domain checks and issue S1",
            "issue S2",
            "72 BREATHE-domain checks plus 16 integration checks",
        ):
            self.assertIn(phrase, self.read_first)
        self.assertTrue(self.manifest["foundation_first"])
        self.assertTrue(self.manifest["breathe_overlay_second"])
        self.assertFalse(self.manifest["install_on_download"])
        self.assertIn("exact complete-program SHA-256 digest", self.program)
        self.assertIn("Any program-byte, policy, target or card change after approval invalidates that approval", self.program)

    def test_emergencies_leave_breathe_instead_of_creating_a_gate_state(self):
        templates = (SOURCE_PACK / "templates" / "BREATHE-Cards-and-Templates.md").read_text(encoding="utf-8")
        self.assertNotIn("emergency bypass", templates)
        self.assertNotIn("emergency bypass", self.program)
        self.assertIn("An emergency is never a BREATHE gate state", templates)
        self.assertIn("emergencies leave BREATHE for official procedures", templates)

    def test_safe_defaults_device_and_clinical_authority_boundaries(self):
        for key in (
            "automatic_connectors", "automatic_cron", "automatic_device_access", "automatic_external_actions",
            "automatic_memory", "automatic_shared_access", "clinical_decisions", "device_control",
            "device_data_private_use", "live_patient_specific_private_use", "role_selection_verifies_credentials_or_authority",
        ):
            self.assertFalse(self.manifest[key], key)
        self.assertTrue(self.manifest["no_phi"])
        self.assertEqual(self.manifest["optional_superpowers_active_after_install"], 0)
        self.assertEqual(self.manifest["suggested_agents_active_after_install"], 0)
        for phrase in (
            "no device, monitor, ventilator, oxygen, alarm, network, or clinical-system connection or control",
            "no autonomous diagnosis, triage, therapy selection",
            "Immediate deterioration, airway or device hazards",
            "Removing names is not sufficient de-identification",
        ):
            self.assertIn(phrase, self.read_first)

    def test_institutional_mode_and_assurance_nonclaims(self):
        self.assertTrue(self.manifest["institutional_deployment_requires_separate_authorization"])
        for phrase in (
            "This download does not create, connect, approve, certify, or validate such an environment",
            "A private BREATHE approval does not authorize hospital deployment",
            "clinical validation, HIPAA compliance, accreditation, certification, institutional approval",
            "device safety",
        ):
            self.assertIn(phrase, self.read_first)

    def test_docx_has_no_macros_embedded_objects_or_external_relationships(self):
        with zipfile.ZipFile(DOCX) as archive:
            self.assertIsNone(archive.testzip())
            names = archive.namelist()
            lowered = [name.lower() for name in names]
            self.assertFalse(any(
                "vbaproject" in name or "activex" in name or "embeddings/" in name or "oleobject" in name
                for name in lowered
            ))
            for name in names:
                if name.endswith(".rels"):
                    rels = archive.read(name).decode("utf-8", errors="replace")
                    self.assertNotIn('TargetMode="External"', rels)

    def test_public_scanner_reads_zip_docx_and_nested_text_members(self):
        scanner = runpy.run_path(str(ROOT / "scripts" / "scan-public-healthcare-artifacts.py"))
        scan_paths = scanner["scan_paths"]
        scanner["run_self_probes"]()
        with tempfile.TemporaryDirectory() as tmp:
            docx = Path(tmp) / "unsafe.docx"
            with zipfile.ZipFile(docx, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("word/document.xml", "<w:t>MRN number=A1B2C3</w:t>")
            findings = scan_paths([docx])
            self.assertTrue(any(label == "patient or mrn example" for label, _ in findings))

    def test_public_page_contract_and_separate_route(self):
        page = (BREATHE / "index.html").read_text(encoding="utf-8")
        for phrase in (
            "Standalone adjacent clinical lane · Respiratory care professionals",
            "Respiratory care means separate—not absorbed",
            "No PHI or real cases",
            "No device data or control",
            "24 powers inactive",
            "10 agents disabled",
            "160 declared checks",
            "Download ≠ installation",
            "AI prepares. Respiratory professionals verify and escalate. Authorized humans decide",
        ):
            self.assertIn(phrase, page)
        self.assertIn('href="downloads/breathe-respiratory-care-complete-edition.zip"', page)
        self.assertIn('href="packages/breathe/UPSTREAM-SHA256SUMS.txt"', page)

    def test_homepage_promotes_rt_story_to_adjacent_lane_after_rounds(self):
        page = (ROOT / "index.html").read_text(encoding="utf-8")
        video_region = page.split("<!-- ============ HOMEPAGE SHORT", 1)[1].split("<!-- ============ ROLE CARDS", 1)[0]
        ordered_ids = ["79xHeOuH_1k", "M-dIPB-pSp0", "8FvTTp-sZVk", "W1eOXb-l2EI", "ZE9pg_vnL8g", "InXb8EN9Hcs", "MKKx9Ie6GmY"]
        positions = [video_region.index(video_id) for video_id in ordered_ids]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(video_region.count("MKKx9Ie6GmY"), 1)
        rt = video_region.split('class="home-rt-video"', 1)[1]
        self.assertIn("Adjacent clinical lane · Respiratory care professionals", rt)
        self.assertIn("BREATHE — Respiratory Care Complete AI OS", rt)
        self.assertIn("https://www.youtube-nocookie.com/embed/MKKx9Ie6GmY", rt)
        self.assertIn('loading="lazy"', rt)
        self.assertIn('referrerpolicy="strict-origin-when-cross-origin"', rt)
        self.assertIn("allowfullscreen", rt)
        self.assertIn('href="respiratory-care/"', rt)

    def test_upstream_and_package_ledgers_are_exact(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-respiratory-care-breathe.py"))
        namespace["validate_upstream_ledger"]()
        expected = namespace["EXPECTED_FILES"] - {"PACKAGE-CHECKSUMS.sha256"}
        ledger = namespace["parse_ledger"]("PACKAGE-CHECKSUMS.sha256", expected)
        self.assertEqual(set(ledger), expected)
        for name, digest in ledger.items():
            self.assertEqual(sha256(PACKAGE / name), digest)

    def test_public_manifest_checksum_and_zip_bytes(self):
        public = json.loads((DOWNLOADS / "manifest.json").read_text(encoding="utf-8"))
        record = public["packages"][0]
        self.assertEqual(public["installation_status"], "not_installed")
        self.assertEqual(record["sha256"], sha256(ZIP))
        self.assertEqual(record["bytes"], ZIP.stat().st_size)
        self.assertEqual(record["acceptance_tests"]["total"], 160)
        self.assertFalse(record["nursing_population_state_shared"])
        self.assertFalse(record["medical_resident_population_state_shared"])
        self.assertFalse(record["device_control"])
        checksum = (DOWNLOADS / "CHECKSUMS.sha256").read_text(encoding="utf-8")
        self.assertEqual(checksum, f"{sha256(ZIP)}  {ZIP.name}\n")
        with zipfile.ZipFile(ZIP) as archive:
            package_files = {p.relative_to(PACKAGE).as_posix() for p in PACKAGE.rglob("*") if p.is_file()}
            expected = {ZIP_PREFIX + name for name in package_files}
            self.assertEqual(set(archive.namelist()), expected)
            self.assertEqual(len(expected), 26)
            self.assertIsNone(archive.testzip())
            for info in archive.infolist():
                self.assertEqual(info.create_system, 3)
                self.assertEqual(info.date_time, (2026, 7, 16, 0, 0, 0))
                self.assertEqual(info.external_attr >> 16, 0o100644)
            for path in PACKAGE.rglob("*"):
                if path.is_file():
                    self.assertEqual(archive.read(ZIP_PREFIX + path.relative_to(PACKAGE).as_posix()), path.read_bytes())

    def test_builder_rejects_source_wrapper_and_ledger_tampering(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-respiratory-care-breathe.py"))
        validator = namespace["validate_package"]
        targets = (PROGRAM.name, "00-READ-FIRST.md", "PACKAGE-CHECKSUMS.sha256")
        for target in targets:
            with self.subTest(target=target), tempfile.TemporaryDirectory() as temp:
                copied = Path(temp) / "breathe"
                shutil.copytree(PACKAGE, copied)
                with (copied / target).open("ab") as handle:
                    handle.write(b"\nTAMPER")
                validator.__globals__["PACKAGE"] = copied
                with self.assertRaises(ValueError):
                    validator()
        validator.__globals__["PACKAGE"] = PACKAGE

    def test_ledger_parser_rejects_parent_backslash_and_duplicate_paths(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-respiratory-care-breathe.py"))
        parser = namespace["parse_ledger"]
        with tempfile.TemporaryDirectory() as temp:
            copied = Path(temp) / "breathe"
            copied.mkdir()
            parser.__globals__["PACKAGE"] = copied
            cases = {
                "parent": "0" * 64 + "  ../escape\n",
                "backslash": "0" * 64 + "  nested\\escape\n",
                "duplicate": "0" * 64 + "  same\n" + "1" * 64 + "  same\n",
            }
            for label, content in cases.items():
                with self.subTest(label=label):
                    (copied / "ledger").write_text(content, encoding="utf-8")
                    with self.assertRaises(ValueError):
                        parser("ledger", {"same"})
        parser.__globals__["PACKAGE"] = PACKAGE

    def test_deterministic_builder_reproduces_committed_zip(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-respiratory-care-breathe.py"))
        build = namespace["build"]
        before = sha256(ZIP)
        record = build()
        self.assertEqual(record["sha256"], before)
        self.assertEqual(sha256(ZIP), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
