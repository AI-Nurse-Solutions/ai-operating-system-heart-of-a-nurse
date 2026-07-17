#!/usr/bin/env python3
"""Acceptance, safety, provenance, consent, and packaging tests for DISCOVER."""

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
DISCOVER = ROOT / "healthcare-research-innovation-leaders"
PACKAGE = DISCOVER / "packages" / "discover"
SOURCE_PACK = PACKAGE / "Healthcare-Research-and-Innovation-Leader-DISCOVER-SuperPowers-Pack-v1.0"
DOWNLOADS = DISCOVER / "downloads"
PROGRAM = PACKAGE / "Healthcare-Research-and-Innovation-Leader-Complete-AI-OS-with-DISCOVER-SuperPowers-Hermes-Program.md"
GUIDE = PACKAGE / "Healthcare-Research-and-Innovation-Leader-Complete-AI-OS-with-DISCOVER-SuperPowers-Setup-Guide.md"
DOCX = PACKAGE / "Healthcare-Research-and-Innovation-Leader-Complete-AI-OS-with-DISCOVER-SuperPowers-Setup-Guide.docx"
MANIFEST = PACKAGE / "ROLE-PACK.json"
ZIP = DOWNLOADS / "discover-healthcare-research-innovation-leader-complete-edition.zip"
ZIP_PREFIX = "DISCOVER-Healthcare-Research-Innovation-Leader-Complete-Edition/"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DiscoverHealthcareResearchInnovationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.program = PROGRAM.read_text(encoding="utf-8")
        cls.guide = GUIDE.read_text(encoding="utf-8")
        cls.read_first = (PACKAGE / "00-READ-FIRST.md").read_text(encoding="utf-8")
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.page = (DISCOVER / "index.html").read_text(encoding="utf-8")

    def test_required_artifacts_and_archive_provenance(self):
        for path in (PROGRAM, GUIDE, DOCX, PACKAGE / "UPSTREAM-SHA256SUMS.txt"):
            self.assertTrue(path.is_file(), path)
        archive = self.manifest["source_archive"]
        self.assertEqual(archive, {
            "bytes": 594992,
            "members": 23,
            "sha256": "79b4a3c6a974061e52348ea9c6b7e5027afc95982802397b4fe203933d2655c6",
            "supplied_name": "DISCOVER-Healthcare-Research-Innovation-Leader-Pack.zip",
        })
        records = {item["packaged_path"]: item for item in self.manifest["source_files"]}
        self.assertEqual(len(records), 23)
        self.assertEqual(records[PROGRAM.name]["upstream_sha256"], "61e900ac5c2b10ee240086ab8d24617ff9ea272bdb18b7bd181a8c60cd6102b5")
        self.assertEqual(records[PROGRAM.name]["source_sha256"], "58ba1c8746efc335060948a666b5c1ac836e2b0cc9b36fe498256b5bfd74d238")
        self.assertEqual(records[DOCX.name]["upstream_sha256"], records[DOCX.name]["source_sha256"])
        for name, record in records.items():
            path = PACKAGE / name
            self.assertEqual(path.stat().st_size, record["bytes"])
            self.assertEqual(sha256(path), record["source_sha256"])

    def test_markdown_is_renderable_whitespace_clean_and_provenanced(self):
        markdown = list(PACKAGE.rglob("*.md"))
        self.assertEqual(len(markdown), 22)
        normalized = 0
        for path in markdown:
            text = path.read_text(encoding="utf-8")
            self.assertFalse(any(line.endswith(" ") for line in text.splitlines()), path)
            self.assertNotRegex(text, r"(?m)^    (?:#|\|)")
        for record in self.manifest["source_files"]:
            if record["packaged_path"].endswith(".md") and record["source_sha256"] != record["upstream_sha256"]:
                normalized += 1
                self.assertTrue(
                    "trailing-space hard breaks" in record["transformation"]
                    or record["packaged_path"] == "README.md"
                )
        self.assertEqual(normalized, 16)
        package_readme = (PACKAGE / "README.md").read_text(encoding="utf-8")
        self.assertIn("exactly **26 files**", package_readme)
        self.assertIn("discover-healthcare-research-innovation-leader-complete-edition.zip", package_readme)
        self.assertNotIn("Four simple download aliases", package_readme)
        self.assertNotIn("DISCOVER-Hermes-Installer.md", package_readme + self.guide)

    def test_program_embeds_exact_normalized_component_inventory(self):
        markers = re.findall(
            r"^<!-- BEGIN COMPONENT: (.+?) \| SHA256: ([0-9a-f]{64}) -->$",
            self.program,
            re.MULTILINE,
        )
        self.assertEqual(len(markers), 17)
        self.assertEqual(len({relative for relative, _ in markers}), 17)
        for relative, digest in markers:
            start = f"<!-- BEGIN COMPONENT: {relative} | SHA256: {digest} -->"
            end = f"<!-- END COMPONENT: {relative} -->"
            embedded = self.program.split(start, 1)[1].split(end, 1)[0].strip("\n")
            source = (SOURCE_PACK / relative).read_text(encoding="utf-8").strip("\n")
            self.assertEqual(embedded, source, relative)
            self.assertEqual(sha256(SOURCE_PACK / relative), digest, relative)

    def test_power_workflow_template_schema_and_agent_inventories(self):
        power_text = "\n".join(path.read_text(encoding="utf-8") for path in sorted((SOURCE_PACK / "discover").glob("*.md")))
        powers = sorted(set(re.findall(r"^## PWR-(\d{2})\b", power_text, re.MULTILINE)))
        self.assertEqual(powers, [f"{index:02d}" for index in range(1, 25)])
        workflows = (SOURCE_PACK / "workflows" / "01-DISCOVER-Runnable-Workflows.md").read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"^## WF-(\d{2})\b", workflows, re.MULTILINE), [f"{index:02d}" for index in range(1, 25)])
        self.assertEqual(re.findall(r"\*\*Inventory ID:\*\* `DSC-WF-(\d{2})`", workflows), [f"{index:02d}" for index in range(1, 25)])
        templates = (SOURCE_PACK / "templates" / "01-DISCOVER-Functional-Templates.md").read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"^## TPL-(\d{2}) —", templates, re.MULTILINE), [f"{index:02d}" for index in range(1, 31)])
        schemas = (SOURCE_PACK / "workflows" / "03-DISCOVER-Schemas-and-Agents.md").read_text(encoding="utf-8")
        schema_names = re.findall(r"^### `https://nurse-ai-os\.local/schemas/research_innovation_discover/([^/]+)/1\.0\.0`$", schemas, re.MULTILINE)
        self.assertEqual(len(schema_names), 18)
        self.assertEqual(len(set(schema_names)), 18)
        self.assertEqual(re.findall(r"^\| `AGT-(\d{2})` \|", schemas, re.MULTILINE), [f"{index:02d}" for index in range(1, 11)])

    def test_schemas_are_canonical_hashed_closed_draft_2020_12(self):
        text = (SOURCE_PACK / "workflows" / "03-DISCOVER-Schemas-and-Agents.md").read_text(encoding="utf-8")
        blocks = re.findall(
            r"^### `https://nurse-ai-os\.local/schemas/research_innovation_discover/([^/]+)/1\.0\.0`\n\n"
            r"\*\*Canonical SHA-256:\*\* `([0-9a-f]{64})`\n\n```json\n([^\n]+)\n```",
            text,
            re.MULTILINE,
        )
        self.assertEqual(len(blocks), 18)
        for name, digest, payload in blocks:
            document = json.loads(payload)
            canonical = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            self.assertEqual(payload, canonical, name)
            self.assertEqual(hashlib.sha256(payload.encode()).hexdigest(), digest, name)
            self.assertEqual(document["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertEqual(document["type"], "object")
            self.assertFalse(document["additionalProperties"])
            self.assertFalse(document["unevaluatedProperties"])

    def test_fixtures_adapters_criteria_and_variants_are_exact(self):
        release = (SOURCE_PACK / "tests" / "01-DISCOVER-Release-and-Runtime-Tests.md").read_text(encoding="utf-8")
        fixture_ids = re.findall(r"^### `FX-(\d{2})@1\.0\.0`$", release, re.MULTILINE)
        self.assertEqual(fixture_ids, [f"{index:02d}" for index in range(1, 11)])
        adapter_blocks = re.findall(r"\*\*Adapter SHA-256:\*\* `([0-9a-f]{64})`\n\n```json\n([^\n]+)\n```", release)
        self.assertEqual(len(adapter_blocks), 10)
        for digest, payload in adapter_blocks:
            self.assertEqual(hashlib.sha256(payload.encode()).hexdigest(), digest)
            self.assertTrue(json.loads(payload)["no_background"])
        expected = [f"RA-{letter}{index:02d}" for letter in "ABCDEFGHIJKLMNOPQR" for index in range(1, 9)]
        expected += [f"RA-INT{index:02d}" for index in range(1, 17)]
        criteria = re.findall(r"^\| (RA-(?:[A-R]\d{2}|INT\d{2})) \|", release, re.MULTILINE)
        variants = re.findall(r"^### `(RA-(?:[A-R]\d{2}|INT\d{2})-VAR@1\.0\.0)`$", release, re.MULTILINE)
        self.assertEqual(criteria, expected)
        self.assertEqual(len(set(criteria)), 160)
        self.assertEqual(variants, [item + "-VAR@1.0.0" for item in expected])
        self.assertEqual(len(set(variants)), 160)

    def test_runtime_criteria_are_not_claimed_as_prepassed(self):
        release = (SOURCE_PACK / "tests" / "01-DISCOVER-Release-and-Runtime-Tests.md").read_text(encoding="utf-8")
        self.assertIn("Status vocabulary is `specified`, `executed`, `passed`, `failed`, `blocked`, `unsupported`", release)
        self.assertEqual(self.manifest["runtime_criteria"]["publication_status"], "specified_not_prepassed")
        self.assertIn("specified—not pre-passed", self.read_first)
        self.assertIn("160 criteria specified—not pre-passed", self.page)
        self.assertIn("does not prove they ran in a target Hermes environment", self.page)

    def test_preinstall_consent_and_installation_order(self):
        for phrase in (
            "Downloading, selecting, opening, or unzipping this package does not install or activate anything",
            "INSPECT DISCOVER INSTALLER ONLY — CREATE NO STATE.",
            "exact combined **DISCOVER Activation Card**",
            "INSTALL DISCOVER AFTER S0 — USE EXACT VERIFIED COMPONENT HASHES AND KEEP ALL POWERS AND AGENTS INACTIVE.",
            "Silence, timeout, download, file opening, title, credentials, access, earlier work",
            "create S0 and the rollback snapshot",
            "execute the 40 S1 criteria",
            "execute the 120 S2 criteria",
            "Nothing continues in the background",
        ):
            self.assertIn(phrase, self.read_first)
        self.assertTrue(self.manifest["foundation_first"])
        self.assertTrue(self.manifest["discover_overlay_second"])
        self.assertFalse(self.manifest["install_on_download"])
        self.assertIn("Wait for explicit install authority", self.program)

    def test_safe_defaults_data_action_and_authority_boundaries(self):
        false_keys = (
            "automatic_connectors", "automatic_cron", "automatic_external_actions", "automatic_memory",
            "automatic_shared_access", "clinical_decisions", "live_person_contact", "official_system_writes",
            "participant_recruitment_or_enrollment", "person_level_data_allowed", "research_or_qi_determinations",
            "role_selection_verifies_credentials_or_authority",
        )
        for key in false_keys:
            self.assertFalse(self.manifest[key], key)
        self.assertTrue(self.manifest["no_phi"])
        self.assertEqual(self.manifest["optional_superpowers_active_after_install"], 0)
        self.assertEqual(self.manifest["suggested_agents_active_after_install"], 0)
        for phrase in (
            "Removing names is not sufficient de-identification",
            "does not recruit, contact, consent, enroll, randomize, intervene, monitor, diagnose",
            "DISCOVER never assesses seriousness, relatedness, expectedness, reportability, urgency, diagnosis, or care",
        ):
            self.assertIn(phrase, self.read_first)

    def test_lane_isolation_and_institutional_nonclaim(self):
        self.assertEqual(self.manifest["population_lane"], "healthcare_research_innovation_leadership")
        self.assertEqual(self.manifest["namespace"], "research_innovation_discover.*")
        self.assertEqual(self.manifest["route"], "/healthcare-research-innovation-leaders/")
        self.assertTrue(self.manifest["standalone_interdisciplinary_lane"])
        for key in (
            "nursing_population_state_shared", "medical_resident_population_state_shared",
            "respiratory_care_population_state_shared", "hospital_administration_population_state_shared",
        ):
            self.assertFalse(self.manifest[key], key)
        self.assertTrue(self.manifest["institutional_deployment_requires_separate_authorization"])
        self.assertIn("A private DISCOVER approval does not authorize organizational or institutional deployment", self.read_first)
        nurse_manifest = (ROOT / "post-setup" / "downloads" / "manifest.json").read_text(encoding="utf-8")
        self.assertNotIn("DISCOVER", nurse_manifest)
        setup_model = (ROOT / "setup-helper" / "setup-helper-model.mjs").read_text(encoding="utf-8")
        self.assertNotIn("healthcare_research_innovation_leadership", setup_model)

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
                    relationships = archive.read(name).decode("utf-8", errors="replace")
                    self.assertNotIn('TargetMode="External"', relationships)

    def test_public_page_contract_video_and_separate_route(self):
        for phrase in (
            "Standalone interdisciplinary lane · Healthcare research and innovation leadership",
            "A leadership lane is not institutional authority",
            "24 powers inactive",
            "10 agents disabled",
            "160 criteria specified—not pre-passed",
            "Download ≠ installation",
            "AI prepares. Leaders verify and govern. Authorized humans decide",
        ):
            self.assertIn(phrase, self.page)
        self.assertIn('href="downloads/discover-healthcare-research-innovation-leader-complete-edition.zip"', self.page)
        self.assertIn("https://www.youtube-nocookie.com/embed/o6fRkTt12zU", self.page)
        self.assertNotIn("https://www.youtube.com/embed/o6fRkTt12zU", self.page)
        self.assertIn('title="Healthcare Research and Innovation Lead — Nurse AI OS"', self.page)
        self.assertIn('loading="lazy"', self.page)
        self.assertIn('referrerpolicy="strict-origin-when-cross-origin"', self.page)
        self.assertIn("allowfullscreen", self.page)

    def test_homepage_handoff_follows_breathe_and_precedes_steward_preview(self):
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        region = homepage.split("<!-- ============ HOMEPAGE SHORT", 1)[1].split("<!-- ============ ROLE CARDS", 1)[0]
        positions = [region.index(video_id) for video_id in ("InXb8EN9Hcs", "MKKx9Ie6GmY", "o6fRkTt12zU")]
        self.assertEqual(positions, sorted(positions))
        self.assertLess(region.index("o6fRkTt12zU"), region.index("steward-governance-preview"))
        self.assertEqual(region.count("o6fRkTt12zU"), 1)
        self.assertIn('class="home-discover-video"', region)
        self.assertIn("Explore the standalone DISCOVER lane", region)
        css = (ROOT / "assets" / "nurse-ai.css").read_text(encoding="utf-8")
        self.assertIn(".home-discover-video", css)

    def test_package_and_upstream_checksum_ledgers(self):
        records = {}
        for line in (PACKAGE / "PACKAGE-CHECKSUMS.sha256").read_text(encoding="utf-8").splitlines():
            digest, relative = line.split("  ", 1)
            self.assertNotIn(relative, records)
            records[relative] = digest
        expected = {item["packaged_path"] for item in self.manifest["source_files"]}
        expected.update({"00-READ-FIRST.md", "ROLE-PACK.json"})
        self.assertEqual(set(records), expected)
        for relative, digest in records.items():
            self.assertEqual(sha256(PACKAGE / relative), digest)
        upstream = {}
        for line in (PACKAGE / "UPSTREAM-SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
            digest, relative = line.split("  ", 1)
            upstream[relative] = digest
        declared = {item["upstream_path"]: item["upstream_sha256"] for item in self.manifest["source_files"] if item["upstream_path"] != "SHA256SUMS.txt"}
        self.assertEqual(upstream, declared)

    def test_zip_is_safe_complete_and_matches_package_bytes(self):
        self.assertTrue(ZIP.is_file())
        with zipfile.ZipFile(ZIP) as archive:
            self.assertIsNone(archive.testzip())
            infos = archive.infolist()
            self.assertEqual(len(infos), 26)
            self.assertTrue(all(info.filename.startswith(ZIP_PREFIX) for info in infos))
            self.assertTrue(all(not info.is_dir() for info in infos))
            self.assertTrue(all(".." not in Path(info.filename).parts and "\\" not in info.filename for info in infos))
            files = {path.relative_to(PACKAGE).as_posix(): path for path in PACKAGE.rglob("*") if path.is_file()}
            self.assertEqual({info.filename[len(ZIP_PREFIX):] for info in infos}, set(files))
            for relative, path in files.items():
                self.assertEqual(archive.read(ZIP_PREFIX + relative), path.read_bytes(), relative)
                self.assertEqual((archive.getinfo(ZIP_PREFIX + relative).external_attr >> 16) & 0o777, 0o644)

    def test_builder_is_deterministic_and_public_manifest_matches(self):
        before = sha256(ZIP)
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-healthcare-research-innovation-discover.py"))
        record = namespace["build"]()
        after = sha256(ZIP)
        self.assertEqual(before, after)
        self.assertEqual(record["sha256"], after)
        self.assertEqual(record["bytes"], ZIP.stat().st_size)
        public = json.loads((DOWNLOADS / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(public["installation_status"], "not_installed")
        self.assertEqual(public["packages"], [record])
        self.assertEqual((DOWNLOADS / "CHECKSUMS.sha256").read_text(encoding="utf-8"), f"{after}  {ZIP.name}\n")

    def test_public_scanner_reads_nested_release_artifacts(self):
        scanner = runpy.run_path(str(ROOT / "scripts" / "scan-public-healthcare-artifacts.py"))
        scanner["run_self_probes"]()
        public_files = [path for path in DISCOVER.rglob("*") if path.is_file()]
        self.assertEqual(scanner["scan_paths"](public_files), [])
        with tempfile.TemporaryDirectory() as tmp:
            unsafe = Path(tmp) / "unsafe.zip"
            with zipfile.ZipFile(unsafe, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("payload.txt", "patient name: Alex Example")
            findings = scanner["scan_paths"]([unsafe])
            self.assertTrue(any(label == "patient or mrn example" for label, _ in findings))

    def test_sitemap_and_local_public_links(self):
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn("https://nurse-ai-os.org/healthcare-research-innovation-leaders/", sitemap)
        for target in re.findall(r'href="([^"]+)"', self.page):
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            path = (DISCOVER / target.split("#", 1)[0]).resolve()
            self.assertTrue(path.exists(), target)

    def test_builder_fails_closed_on_source_drift(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-healthcare-research-innovation-discover.py"))
        with tempfile.TemporaryDirectory() as tmp:
            copied = Path(tmp) / "discover"
            shutil.copytree(PACKAGE, copied)
            target = copied / PROGRAM.name
            target.write_bytes(target.read_bytes() + b"\n")
            function_globals = namespace["validate_package"].__globals__
            original = function_globals["PACKAGE"]
            function_globals["PACKAGE"] = copied
            try:
                with self.assertRaisesRegex(ValueError, "trusted source digest or byte mismatch"):
                    namespace["validate_package"]()
            finally:
                function_globals["PACKAGE"] = original


if __name__ == "__main__":
    unittest.main()
