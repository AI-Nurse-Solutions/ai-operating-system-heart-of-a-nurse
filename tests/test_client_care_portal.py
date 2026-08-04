#!/usr/bin/env python3
"""Deterministic structural and governance tests for the Client Care Portal.

The portal's runtime behavior is covered by tests/test_portal_model.mjs (node).
These tests pin the security and governance invariants that must hold in the
static repository itself: no secrets in the GitHub Pages bundle, RLS on every
table, the no-PHI notice on every entry surface, and the portal staying out of
the public marketing-shell policy scope.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORTAL = ROOT / "portal"
HTML = (PORTAL / "index.html").read_text(encoding="utf-8")
APP = (PORTAL / "portal.mjs").read_text(encoding="utf-8")
DATA = (PORTAL / "portal-data.mjs").read_text(encoding="utf-8")
MODEL = (PORTAL / "portal-model.mjs").read_text(encoding="utf-8")
CONFIG = (PORTAL / "config.mjs").read_text(encoding="utf-8")
MIGRATION = next((ROOT / "supabase" / "migrations").glob("*_client_care_portal.sql")).read_text(encoding="utf-8")
EDGE_FN = (ROOT / "supabase" / "functions" / "draft-with-ai" / "index.ts").read_text(encoding="utf-8")

TABLES = (
    "clients", "profiles", "milestones", "progress_reports",
    "action_items", "conversations", "messages", "activity_events",
)


class PortalStructureTests(unittest.TestCase):
    def test_portal_files_exist(self):
        for name in ("index.html", "portal.mjs", "portal-data.mjs", "portal-model.mjs",
                     "portal.css", "config.mjs", "README.md"):
            self.assertTrue((PORTAL / name).is_file(), name)

    def test_shell_page_basics(self):
        self.assertIn('<html lang="en">', HTML)
        self.assertIn('name="viewport"', HTML)
        self.assertIn('name="robots" content="noindex"', HTML)
        self.assertIn('type="module" src="portal.mjs"', HTML)
        self.assertIn("../assets/nurse-ai.css", HTML)

    def test_portal_opts_out_of_public_marketing_shell(self):
        # The portal is an authenticated app, deliberately outside the
        # public-entrypoint policy that governs pages using the site-header
        # shell (orientation bar, quiz CTA rules).
        self.assertNotIn('class="site-header"', HTML)
        self.assertNotIn("site-shell.js", HTML)
        self.assertIn('class="portal-topbar"', HTML)

    def test_internal_links_resolve(self):
        for href in re.findall(r'(?:href|src)="(\.\./[^"]+)"', HTML):
            target = (PORTAL / href).resolve()
            self.assertTrue(target.exists(), href)


class GovernanceTextTests(unittest.TestCase):
    def test_transparent_limits_notice_on_every_screen(self):
        # PRD §10: the boundary statement is rendered statically, outside the
        # app root, so it is visible on every screen including sign-in.
        self.assertIn("For Nurse AI OS setup, education, maintenance, and improvement support only.", HTML)
        self.assertIn("Do not enter patient information or use this portal for urgent clinical", HTML)
        self.assertIn("TRANSPARENT_LIMITS_NOTICE", MODEL)

    def test_no_phi_warning_guards_entry_forms(self):
        self.assertIn("NO_PHI_WARNING", MODEL)
        self.assertIn("NO_PHI_WARNING", APP)
        # Question entry, reply forms, and the screening speed bump all engage it.
        self.assertGreaterEqual(APP.count("noPhiCallout()"), 2)
        self.assertIn("screenSubmission", APP)
        self.assertIn("screenSubmission", MODEL)

    def test_ai_replies_stay_human_approved(self):
        self.assertIn("AI-assisted · human approved", APP)
        self.assertIn("Approve &amp; send reply", APP)
        # The edge function returns a draft and performs no writes.
        self.assertIn('return json(200, { draft })', EDGE_FN)
        self.assertNotIn(".insert(", EDGE_FN)
        self.assertNotIn(".update(", EDGE_FN)
        self.assertNotIn(".delete(", EDGE_FN)


class NoSecretsTests(unittest.TestCase):
    SECRET_PATTERNS = (
        r"sk-ant-[A-Za-z0-9-]{8}",          # Anthropic API key material
        r"eyJ[A-Za-z0-9_-]{40,}",           # JWT-shaped literals (service keys)
        r"-----BEGIN [A-Z ]*PRIVATE KEY",
        r"service_role",
    )

    def test_no_secret_material_in_portal_or_backend_sources(self):
        files = list(PORTAL.glob("*")) + [
            ROOT / "supabase" / "functions" / "draft-with-ai" / "index.ts",
            *(ROOT / "supabase" / "migrations").glob("*.sql"),
        ]
        failures = []
        for path in files:
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            for pattern in self.SECRET_PATTERNS:
                for match in re.finditer(pattern, text):
                    # The model's screening regex and tests legitimately
                    # mention the *shape* of secrets to warn users.
                    line = text[: match.start()].count("\n") + 1
                    failures.append(f"{path.relative_to(ROOT)}:{line}: {pattern}")
        self.assertEqual([], failures)

    def test_config_ships_unconfigured_with_pinned_dependency(self):
        self.assertRegex(CONFIG, r"supabaseUrl:\s*''")
        self.assertRegex(CONFIG, r"supabaseAnonKey:\s*''")
        self.assertRegex(CONFIG, r"@supabase/supabase-js@\d+\.\d+\.\d+")

    def test_edge_function_reads_key_from_environment_only(self):
        self.assertIn('Deno.env.get("ANTHROPIC_API_KEY")', EDGE_FN)
        self.assertIn('Deno.env.get("SUPABASE_ANON_KEY")', EDGE_FN)
        self.assertNotIn("SERVICE_ROLE", EDGE_FN)

    def test_supabase_js_is_version_pinned_everywhere(self):
        for text, name in ((DATA, "portal-data.mjs"), (EDGE_FN, "edge function")):
            if "@supabase/supabase-js" in text:
                self.assertNotIn("@supabase/supabase-js@latest", text, name)


class RowLevelSecurityTests(unittest.TestCase):
    def test_every_table_created_and_rls_enabled(self):
        for table in TABLES:
            self.assertIn(f"create table public.{table}", MIGRATION, table)
            self.assertIn(f"alter table public.{table} enable row level security", MIGRATION, table)

    def test_every_table_has_at_least_one_policy(self):
        for table in TABLES:
            self.assertRegex(MIGRATION, rf'create policy "[^"]+" on public\.{table}', table)

    def test_client_isolation_predicates_present(self):
        self.assertIn("portal_client_id()", MIGRATION)
        self.assertIn("portal_is_admin()", MIGRATION)
        self.assertIn("security definer", MIGRATION)
        # Clients read only *published* reports.
        self.assertRegex(MIGRATION, r"client_id = public\.portal_client_id\(\) and published")

    def test_clients_cannot_forge_ai_or_activity_records(self):
        self.assertIn("ai_assisted = false", MIGRATION)
        # activity_events: select policy only — no insert/update/delete path.
        activity_policies = re.findall(r'create policy "[^"]+" on public\.activity_events\s+for (\w+)', MIGRATION)
        self.assertEqual(["select"], activity_policies)

    def test_action_updates_are_column_guarded(self):
        self.assertIn("portal_guard_client_action_update", MIGRATION)
        self.assertIn("Clients may update only an action''s status and comment", MIGRATION)

    def test_schema_holds_no_patient_fields(self):
        # Comments may (and do) talk about the no-PHI rule; the DDL itself
        # must never define patient-shaped columns.
        ddl = "\n".join(re.sub(r"--.*$", "", line) for line in MIGRATION.splitlines())
        for forbidden in ("patient", "mrn", "date_of_birth", "medical_record", "diagnos"):
            self.assertNotIn(forbidden, ddl.lower(), forbidden)

    def test_admin_view_respects_caller_rls(self):
        self.assertIn("security_invoker = true", MIGRATION)


if __name__ == "__main__":
    unittest.main()
