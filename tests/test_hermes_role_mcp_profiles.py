from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import stat
import tempfile
import types
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ROOT / "hermes-role-profiles"
SOURCE = PROFILES / "source"
DOWNLOADS = PROFILES / "downloads"
MANIFEST = PROFILES / "manifest.json"
CHECKSUMS = PROFILES / "CHECKSUMS.sha256"
ROLES = {
    "study-coach": "future",
    "curator": "discover",
    "builder-operator": "discover",
    "manager-lead": "lead",
    "admin-pilot-ops": "steward",
    "clinician-np": "wings",
    "clinician-resident": "rounds",
}
MAPPING_CLASSIFICATIONS = {
    "study-coach": "direct_pathway_only",
    "curator": "adjacent_conditional_not_exact_lane",
    "builder-operator": "adjacent_conditional_not_exact_lane",
    "manager-lead": "direct_role_conditional",
    "admin-pilot-ops": "conditional_candidate",
    "clinician-np": "direct_country_restricted",
    "clinician-resident": "direct_fit",
}
PINNED_SPECS = {
    "@modelcontextprotocol/server-filesystem@2026.7.10",
    "@cyanheads/pubmed-mcp-server@2.10.1",
    "reddit-mcp-server@1.5.1",
    "workspace-mcp==1.22.1",
    "c8a4fed36da2ec03284bdd13f540b65e0af27bb1",
    "1d22ed4fc4f725df8af90ef75a4a7bd1e3bc9882",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_builder_module(name: str) -> types.ModuleType:
    builder_path = ROOT / "scripts/build-hermes-role-profiles.py"
    spec = importlib.util.spec_from_file_location(name, builder_path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load builder: {builder_path}")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    return builder


class HermesRoleMcpProfilesTests(unittest.TestCase):
    def test_seven_installable_profile_sources_exist(self) -> None:
        self.assertEqual({path.name for path in SOURCE.iterdir() if path.is_dir()}, set(ROLES))
        for role in ROLES:
            profile = SOURCE / role
            for required in (
                "distribution.yaml",
                "profile.yaml",
                "config.yaml",
                "mcp.json",
                "MCP-SUPPLY-CHAIN-LOCK.json",
                "SOUL.md",
                "README.md",
                "MCP-ACTIVATION-CARD.md",
                ".env.template",
                "skills/review-mcp-activation/SKILL.md",
            ):
                self.assertTrue((profile / required).is_file(), f"{role} missing {required}")
            distribution = json.loads((profile / "distribution.yaml").read_text())
            self.assertEqual(distribution["schema_version"], 1)
            self.assertEqual(distribution["version"], "1.0.0")
            self.assertEqual(distribution["hermes_requires"], ">=0.19.0")
            self.assertEqual(distribution["mapping"]["classification"], MAPPING_CLASSIFICATIONS[role])
            self.assertTrue(distribution["mapping"]["condition"])
            readme = (profile / "README.md").read_text()
            self.assertIn("does not display or enforce the bundled card", readme)
            self.assertIn("Do not use `--yes`", readme)
            self.assertIn("`config.yaml:mcp_servers` at runtime", readme)
            self.assertIn(f"--name {role} --alias", readme)
            self.assertNotIn(f"--alias {role}", readme)
            self.assertIn(f"hermes -p {role} mcp configure <exact-server-name>", readme)
            card = (profile / "MCP-ACTIVATION-CARD.md").read_text()
            self.assertIn(f"Mapping classification: `{MAPPING_CLASSIFICATIONS[role]}`", card)
            self.assertIn("Mapping eligibility condition:", card)
            skill = (profile / "skills/review-mcp-activation/SKILL.md").read_text()
            self.assertNotIn("configure, update, or remove", skill)

    def test_all_mcp_servers_are_inactive_and_zero_tool_by_default(self) -> None:
        found_specs: set[str] = set()
        for role in ROLES:
            config = json.loads((SOURCE / role / "config.yaml").read_text())
            self.assertEqual(config["terminal"]["home_mode"], "profile")
            self.assertEqual(config["approvals"]["mode"], "manual")
            self.assertEqual(config["approvals"]["cron_mode"], "deny")
            self.assertFalse(config["security"]["allow_lazy_installs"])
            self.assertFalse(config["security"]["tirith_fail_open"])
            servers = config.get("mcp_servers", {})
            self.assertTrue(servers, role)
            for server_name, server in servers.items():
                self.assertIs(server.get("enabled"), False, f"{role}/{server_name}")
                self.assertEqual(server.get("command"), "__NAIO_MCP_ACTIVATION_BLOCKED__")
                self.assertEqual(server.get("args"), [server_name])
                self.assertNotIn("url", server)
                self.assertTrue(server.get("candidate"), f"{role}/{server_name} candidate metadata missing")
                self.assertEqual(server.get("sampling"), {"enabled": False})
                self.assertEqual(server.get("elicitation"), {"enabled": False})
                self.assertEqual(server.get("connect_timeout"), 30)
                self.assertEqual(server.get("timeout"), 60)
                self.assertNotIn("startup_timeout", server)
                self.assertNotIn("tool_timeout", server)
                self.assertEqual(
                    server.get("tools"),
                    {
                        "include": ["__NAIO_NO_MCP_TOOLS_APPROVED__"],
                        "resources": False,
                        "prompts": False,
                    },
                    f"{role}/{server_name}",
                )
                serialized = json.dumps(server, sort_keys=True)
                for spec in PINNED_SPECS:
                    if spec in serialized:
                        found_specs.add(spec)
                self.assertNotRegex(serialized, r"modelcontextprotocol/server-filesystem(?:\"|$)")
                self.assertNotRegex(serialized, r"pubmed-mcp-server(?:\"|$)")
                self.assertNotRegex(serialized, r"reddit-mcp-server(?:\"|$)")
                self.assertNotIn("workspace-mcp\"", serialized)
                self.assertNotIn("/main", serialized)
        self.assertEqual(found_specs, PINNED_SPECS)

    def test_source_rejects_sensitive_content_before_processing(self) -> None:
        corpus = "\n".join(path.read_text(errors="replace") for path in SOURCE.rglob("*.md"))
        for required in (
            "reject it before processing, transforming, summarizing, or storing it",
            "No PHI",
            "No patient cases or narratives",
            "No credentials or secrets",
            "Downloading or unzipping does not install, connect, or activate anything",
        ):
            self.assertIn(required, corpus)
        for prohibited in (
            "de-identified case",
            "deidentified case",
            "de-identify the case",
            "real patient case",
            "log-clinical-case",
            "hermes mcp list-tools",
            "run /deidentify-check",
            "Tirith fail-open",
        ):
            self.assertNotIn(prohibited.lower(), corpus.lower())
        public_text = "\n".join(
            path.read_text(errors="replace")
            for path in PROFILES.rglob("*")
            if path.is_file() and path.suffix != ".zip"
        )
        public_text += (ROOT / "scripts/build-hermes-role-profiles.py").read_text()
        self.assertNotIn("/Users/", public_text)

    def test_supply_chain_and_mapping_are_complete(self) -> None:
        lock = json.loads((PROFILES / "MCP-SUPPLY-CHAIN-LOCK.json").read_text())
        self.assertEqual(lock["schema_version"], "1.0")
        self.assertEqual(set(lock["dependencies"]), {
            "filesystem", "obsidian", "google_workspace", "pubmed", "reddit", "x", "github_remote"
        })
        self.assertEqual(lock["dependencies"]["github_remote"]["pinning_status"], "remote_service_not_code_pinnable")
        mapping = json.loads((PROFILES / "ROLE-DOWNLOAD-MAP.json").read_text())
        self.assertEqual({entry["profile"]: entry["lane"] for entry in mapping["mappings"]}, ROLES)
        self.assertEqual(
            {entry["profile"]: entry["mapping_classification"] for entry in mapping["mappings"]},
            MAPPING_CLASSIFICATIONS,
        )
        self.assertTrue(all(entry["mapping_condition"] for entry in mapping["mappings"]))
        self.assertTrue(all(entry["activation"] == "separate_explicit_post_card_approval" for entry in mapping["mappings"]))
        self.assertTrue(all(
            entry["activation_readiness"] == "blocked_pending_complete_transitive_lock_and_lock_consuming_runtime"
            for entry in mapping["mappings"]
        ))
        for role in ROLES:
            role_lock = json.loads((SOURCE / role / "MCP-SUPPLY-CHAIN-LOCK.json").read_text())
            has_github_remote = "github" in role_lock["dependencies"]
            self.assertEqual("remote GitHub service" in role_lock["policy"], has_github_remote)
        provenance = json.loads((PROFILES / "SOURCE-PROVENANCE.json").read_text())
        self.assertIn(
            "tirith_fail_closed_requested_with_v019_circuit_breaker_caveat",
            provenance["critical_corrections"],
        )
        self.assertNotIn("tirith_fail_closed", provenance["critical_corrections"])

    def test_deterministic_downloads_match_sources_and_ledgers(self) -> None:
        manifest = json.loads(MANIFEST.read_text())
        self.assertEqual(len(manifest["profiles"]), 7)
        expected_checksum_lines = []
        for record in manifest["profiles"]:
            self.assertEqual(
                record["activation_readiness"],
                "blocked_pending_complete_transitive_lock_and_lock_consuming_runtime",
            )
            role = record["profile"]
            archive_path = DOWNLOADS / record["filename"]
            self.assertEqual(record["sha256"], sha256(archive_path))
            self.assertEqual(record["bytes"], archive_path.stat().st_size)
            expected_checksum_lines.append(f"{record['sha256']}  downloads/{record['filename']}")
            with zipfile.ZipFile(archive_path) as archive:
                self.assertIsNone(archive.testzip())
                infos = archive.infolist()
                self.assertEqual(len(infos), record["members"])
                expected_names = {
                    f"naio-{role}-hermes-profile-v1.0.0/{path.relative_to(SOURCE / role).as_posix()}"
                    for path in (SOURCE / role).rglob("*") if path.is_file()
                }
                self.assertEqual({info.filename for info in infos}, expected_names)
                for info in infos:
                    self.assertFalse(info.is_dir())
                    self.assertEqual((info.external_attr >> 16) & 0o177777, stat.S_IFREG | 0o644)
                    source_path = SOURCE / role / info.filename.split("/", 1)[1]
                    self.assertEqual(archive.read(info), source_path.read_bytes())
        self.assertEqual(CHECKSUMS.read_text(), "\n".join(expected_checksum_lines) + "\n")

    def test_archive_validation_failure_preserves_published_bytes(self) -> None:
        builder = load_builder_module("build_hermes_role_profiles")

        slug = "study-coach"
        published = DOWNLOADS / f"naio-{slug}-hermes-profile-v1.0.0.zip"
        staged = published.with_name(f".{published.name}.staged")
        before = published.read_bytes()
        with mock.patch.object(builder, "validate_archive", side_effect=ValueError("forced validation failure")):
            with self.assertRaisesRegex(ValueError, "forced validation failure"):
                builder.build_zip(slug)
        self.assertEqual(published.read_bytes(), before)
        self.assertFalse(staged.exists())

    def test_archive_builder_rejects_source_symlinks_and_special_files(self) -> None:
        builder = load_builder_module("build_hermes_role_profiles_source_entries")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            downloads = root / "downloads"
            profile = source / "study-coach"
            profile.mkdir(parents=True)
            downloads.mkdir()
            outside = root / "outside-secret.txt"
            outside.write_text("must never be packaged")
            link = profile / "linked-secret.txt"
            link.symlink_to(outside)
            with mock.patch.object(builder, "SOURCE", source), mock.patch.object(builder, "DOWNLOADS", downloads):
                with self.assertRaisesRegex(ValueError, "Source symlink prohibited"):
                    builder.build_zip("study-coach")
            self.assertFalse(any(downloads.iterdir()))

            link.unlink()
            regular = profile / "README.md"
            regular.write_text("safe")
            fifo = profile / "special.fifo"
            os.mkfifo(fifo)
            try:
                with mock.patch.object(builder, "SOURCE", source), mock.patch.object(builder, "DOWNLOADS", downloads):
                    with self.assertRaisesRegex(ValueError, "Non-regular source entry prohibited"):
                        builder.build_zip("study-coach")
                self.assertFalse(any(downloads.iterdir()))
            finally:
                fifo.unlink(missing_ok=True)

    def test_provenance_rejects_symlinks_and_special_files(self) -> None:
        builder = load_builder_module("build_hermes_role_profiles_provenance_entries")
        with tempfile.TemporaryDirectory() as directory:
            upstream = Path(directory) / "upstream"
            role = upstream / "study-coach"
            role.mkdir(parents=True)
            outside = Path(directory) / "outside.txt"
            outside.write_text("must never be hashed")
            link = role / "linked.txt"
            link.symlink_to(outside)
            with self.assertRaisesRegex(ValueError, "Provenance source symlink prohibited"):
                builder.source_provenance(upstream)
            link.unlink()
            role.rmdir()
            role.symlink_to(Path(directory) / "missing-role", target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "Provenance role root must be a real directory"):
                builder.source_provenance(upstream)
            role.unlink()
            role.mkdir()
            fifo = role / "special.fifo"
            os.mkfifo(fifo)
            try:
                with self.assertRaisesRegex(ValueError, "Provenance source special entry prohibited"):
                    builder.source_provenance(upstream)
            finally:
                fifo.unlink(missing_ok=True)

            nested = role / "nested"
            nested.mkdir()
            (nested / "file.txt").write_text("safe provenance bytes")
            outside_directory = Path(directory) / "outside-directory"
            outside_directory.mkdir()
            (outside_directory / "file.txt").write_text("outside provenance bytes")
            held = role / "held-nested"
            original_open = builder.os.open
            swapped = False

            def swap_parent_before_final_open(path, flags, *args, **kwargs):
                nonlocal swapped
                if path == "file.txt" and kwargs.get("dir_fd") is not None and not swapped:
                    nested.rename(held)
                    nested.symlink_to(outside_directory, target_is_directory=True)
                    swapped = True
                return original_open(path, flags, *args, **kwargs)

            try:
                with mock.patch.object(builder.os, "open", side_effect=swap_parent_before_final_open):
                    provenance = builder.source_provenance(upstream)
                record = provenance["upstream_roles"]["study-coach"]["study-coach/nested/file.txt"]
                self.assertEqual(record["sha256"], hashlib.sha256(b"safe provenance bytes").hexdigest())
            finally:
                if nested.is_symlink():
                    nested.unlink()
                if held.exists():
                    held.rename(nested)

    def test_companion_record_rejects_symlink_artifact(self) -> None:
        module_path = ROOT / "scripts/hermes_role_profile_records.py"
        spec = importlib.util.spec_from_file_location("hermes_role_profile_records_symlink", module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            root = repo / "hermes-role-profiles"
            downloads = root / "downloads"
            downloads.mkdir(parents=True)
            outside = repo / "outside.zip"
            outside.write_bytes(b"outside")
            artifact = downloads / "profile.zip"
            artifact.symlink_to(outside)
            manifest = {
                "profiles": [{
                    "profile": "study-coach",
                    "download": "downloads/profile.zip",
                    "bytes": len(outside.read_bytes()),
                    "sha256": hashlib.sha256(outside.read_bytes()).hexdigest(),
                    "mcp_enabled_by_default": False,
                    "mcp_tools_exposed_by_default": 0,
                }]
            }
            (root / "manifest.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "beneath its root"):
                module.companion_record(repo, "study-coach")

            artifact.unlink()
            safe_bytes = b"safe archive bytes"
            artifact.write_bytes(safe_bytes)
            outside_directory = repo / "outside-downloads"
            outside_directory.mkdir()
            (outside_directory / "profile.zip").write_bytes(b"outside archive bytes")
            held = root / "held-downloads"
            original_open = module.os.open
            swapped = False

            def swap_parent_before_final_open(path, flags, *args, **kwargs):
                nonlocal swapped
                if path == "profile.zip" and kwargs.get("dir_fd") is not None and not swapped:
                    downloads.rename(held)
                    downloads.symlink_to(outside_directory, target_is_directory=True)
                    swapped = True
                return original_open(path, flags, *args, **kwargs)

            try:
                with mock.patch.object(module.os, "open", side_effect=swap_parent_before_final_open):
                    self.assertEqual(module._read_regular_within(root, Path("downloads/profile.zip")), safe_bytes)
            finally:
                if downloads.is_symlink():
                    downloads.unlink()
                if held.exists():
                    held.rename(downloads)

    def test_archive_validator_rejects_noncanonical_metadata_before_payload_read(self) -> None:
        builder = load_builder_module("build_hermes_role_profiles_metadata")
        root_name = "naio-study-coach-hermes-profile-v1.0.0"

        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "unsafe.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                info = zipfile.ZipInfo(f"{root_name}/../escape.txt", builder.FIXED_ZIP_TIME)
                info.create_system = 3
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                archive.writestr(info, b"unsafe")
            with self.assertRaisesRegex(ValueError, "Unsafe or noncanonical ZIP member"):
                builder.validate_archive(archive_path, "study-coach", 1)

            raw_name_archive = Path(directory) / "raw-nul.zip"
            expected_name = f"{root_name}/README.md"
            padded_name = expected_name + "XXXXX"
            with zipfile.ZipFile(raw_name_archive, "w") as archive:
                info = zipfile.ZipInfo(padded_name, builder.FIXED_ZIP_TIME)
                info.create_system = 3
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                archive.writestr(info, b"unsafe")
            raw_bytes = raw_name_archive.read_bytes()
            replacement = expected_name.encode() + b"\x00XXXX"
            self.assertEqual(len(replacement), len(padded_name.encode()))
            self.assertEqual(raw_bytes.count(padded_name.encode()), 2)
            raw_name_archive.write_bytes(raw_bytes.replace(padded_name.encode(), replacement))
            with self.assertRaisesRegex(ValueError, "Unsafe or noncanonical ZIP member"):
                builder.validate_archive(raw_name_archive, "study-coach", 1)

    def test_role_manifests_reference_correct_companions(self) -> None:
        central = {
            record["profile"]: record
            for record in json.loads(MANIFEST.read_text())["profiles"]
        }

        def assert_exact_companion(companion: dict, profile: str) -> None:
            source = central[profile]
            self.assertEqual(companion["profile"], profile)
            self.assertEqual(companion["version"], source["version"])
            self.assertEqual(companion["bytes"], source["bytes"])
            self.assertEqual(companion["sha256"], source["sha256"])
            self.assertEqual(companion["download"], f"/hermes-role-profiles/{source['download']}")
            self.assertEqual(companion["mapping_classification"], MAPPING_CLASSIFICATIONS[profile])
            self.assertEqual(companion["mapping_condition"], source["mapping_condition"])
            self.assertEqual(
                companion["activation_readiness"],
                "blocked_pending_complete_transitive_lock_and_lock_consuming_runtime",
            )
            self.assertFalse(companion["mcp_enabled_by_default"])
            self.assertEqual(companion["mcp_tools_exposed_by_default"], 0)
            self.assertEqual(companion["activation"], "separate_explicit_post_card_approval")

        post_setup = json.loads((ROOT / "post-setup/downloads/manifest.json").read_text())
        by_role = {record["role"]: record for record in post_setup["packages"]}
        expected = {
            "Nursing Student and Nursing Assistant": "study-coach",
            "Nurse Leader and Manager": "manager-lead",
            "Nurse Practitioner (USA)": "clinician-np",
        }
        for role, profile in expected.items():
            companion = by_role[role]["hermes_mcp_profile_companion"]
            assert_exact_companion(companion, profile)

        lane_manifests = {
            ROOT / "medical-residents/downloads/manifest.json": ["clinician-resident"],
            ROOT / "hospital-clinic-administrators/downloads/manifest.json": ["admin-pilot-ops"],
            ROOT / "healthcare-research-innovation-leaders/downloads/manifest.json": ["curator", "builder-operator"],
        }
        for path, profiles in lane_manifests.items():
            manifest = json.loads(path.read_text())
            self.assertEqual([item["profile"] for item in manifest["hermes_mcp_profile_companions"]], profiles)
            for companion, profile in zip(manifest["hermes_mcp_profile_companions"], profiles, strict=True):
                assert_exact_companion(companion, profile)

    def test_public_handoff_copy_preserves_separate_activation_gate(self) -> None:
        pages = {
            ROOT / "medical-residents/index.html": "clinician-resident",
            ROOT / "hospital-clinic-administrators/index.html": "admin-pilot-ops",
            ROOT / "healthcare-research-innovation-leaders/index.html": "curator",
        }
        for path, profile in pages.items():
            text = path.read_text()
            self.assertIn(f"../hermes-role-profiles/downloads/naio-{profile}-hermes-profile-v1.0.0.zip", text)
            self.assertIn("../hermes-role-profiles/CHECKSUMS.sha256", text)
            self.assertIn("MCP connectors remain disabled", text)
            self.assertIn("separate activation card", text.lower())
        discover = (ROOT / "healthcare-research-innovation-leaders/index.html").read_text()
        self.assertIn("naio-builder-operator-hermes-profile-v1.0.0.zip", discover)
        post_setup = (ROOT / "post-setup/index.html").read_text()
        for role in ("study-coach", "manager-lead", "clinician-np"):
            self.assertIn(f"../hermes-role-profiles/downloads/naio-{role}-hermes-profile-v1.0.0.zip", post_setup)
        self.assertGreaterEqual(post_setup.count("MCP connectors remain disabled with zero tools"), 3)
        self.assertGreaterEqual(post_setup.lower().count("separate activation card"), 3)
        helper = (ROOT / "setup-helper/setup-helper-model.mjs").read_text()
        for role in ("study-coach", "manager-lead", "clinician-np"):
            self.assertIn(f"naio-{role}-hermes-profile-v1.0.0.zip", helper)
        self.assertIn("separate MCP activation card", helper)
        self.assertNotIn("and the separately downloaded naio-study-coach", helper)
        self.assertNotIn("and the separately downloaded naio-manager-lead", helper)
        self.assertNotIn("and the separately downloaded naio-clinician-np", helper)
        self.assertGreaterEqual(helper.count("optional MCP companion"), 3)
        self.assertIn("Only if I select the Nursing Student pathway", helper)
        self.assertIn("not automatically offered for Nursing Assistant or Bridge", helper)
        self.assertIn("Only if I am actually operating as a nurse leader or manager", helper)
        self.assertIn("USA-only WINGS Nurse Practitioner", helper)
        self.assertEqual(helper.count("verify the selected companion ZIP against hermes-role-profiles/CHECKSUMS.sha256"), 3)
        self.assertEqual(helper.count("confirm central-manifest and archive config parity"), 3)
        workflow = (ROOT / ".github/workflows/hermes-role-mcp-profiles.yml").read_text()
        self.assertIn("actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020", workflow)
        self.assertIn("npm ci --ignore-scripts --no-audit --no-fund", workflow)
        self.assertIn("npm run test:switchboard-browser", workflow)
        publication_readme = (PROFILES / "README.md").read_text()
        self.assertIn("scanner-crash circuit breaker", publication_readme)
        self.assertIn("Tirith is defense in depth, not the activation gate", publication_readme)

    def test_every_profile_explains_soul_mission_control_and_conditional_mcp_value(self) -> None:
        central = (PROFILES / "README.md").read_text()
        for phrase in (
            "SOUL tells Hermes who it serves",
            "Mission Control turns intention into governed work",
            "MCP defines what Hermes may eventually reach",
            "starts read-only inspection only",
        ):
            self.assertIn(phrase, central)
        for profile in ROLES:
            readme = (PROFILES / "source" / profile / "README.md").read_text()
            soul = (PROFILES / "source" / profile / "SOUL.md").read_text()
            for phrase in (
                "Why this matters",
                "SOUL — who Hermes serves",
                "Mission Control — how intention becomes work",
                "MCP — what Hermes may eventually reach",
                "Giving Hermes this ZIP starts only read-only inspection",
            ):
                self.assertIn(phrase, readme, f"{profile}: {phrase}")
            for phrase in (
                "Why Nurse AI OS matters in this role",
                "What the three layers bring to Hermes",
                "Handing this folder to Hermes means **inspect first**",
                "all published servers remain blocked, disabled, and tool-denied",
            ):
                self.assertIn(phrase, soul, f"{profile}: {phrase}")


if __name__ == "__main__":
    unittest.main()
