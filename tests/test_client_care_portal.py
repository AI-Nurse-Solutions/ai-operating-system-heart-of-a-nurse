#!/usr/bin/env python3
"""Deterministic structural and governance tests for the Client Care Portal.

The portal's runtime behavior is covered by tests/test_portal_model.mjs (node).
These tests pin the security and governance invariants that must hold in the
static repository itself: no secrets in the GitHub Pages bundle, RLS on every
table, the no-PHI notice on every entry surface, and the portal staying out of
the public marketing-shell policy scope.

Files are loaded lazily inside the tests, so a missing file surfaces as a
clear test failure instead of a collection error.
"""

from __future__ import annotations

import re
import unittest
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORTAL = ROOT / "portal"

TABLES = (
    "clients", "profiles", "milestones", "progress_reports",
    "action_items", "conversations", "messages", "activity_events",
)


@lru_cache(maxsize=None)
def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def html() -> str:
    return read("portal/index.html")


def app() -> str:
    return read("portal/portal.mjs")


def data() -> str:
    return read("portal/portal-data.mjs")


def model() -> str:
    return read("portal/portal-model.mjs")


def config() -> str:
    return read("portal/config.mjs")


def edge_fn() -> str:
    return read("supabase/functions/draft-with-ai/index.ts")


@lru_cache(maxsize=None)
def migration() -> str:
    candidates = sorted((ROOT / "supabase" / "migrations").glob("*_client_care_portal.sql"))
    if not candidates:
        raise AssertionError("client_care_portal migration is missing")
    return candidates[0].read_text(encoding="utf-8")


class PortalStructureTests(unittest.TestCase):
    def test_portal_files_exist(self):
        for name in ("index.html", "portal.mjs", "portal-data.mjs", "portal-model.mjs",
                     "portal.css", "config.mjs", "README.md"):
            self.assertTrue((PORTAL / name).is_file(), name)
        self.assertTrue(migration(), "migration must exist and be non-empty")
        self.assertTrue(edge_fn(), "edge function must exist and be non-empty")

    def test_shell_page_basics(self):
        self.assertIn('<html lang="en">', html())
        self.assertIn('name="viewport"', html())
        self.assertIn('name="robots" content="noindex"', html())
        self.assertIn('type="module" src="portal.mjs"', html())
        self.assertIn("../assets/nurse-ai.css", html())

    def test_portal_opts_out_of_public_marketing_shell(self):
        # The portal is an authenticated app, deliberately outside the
        # public-entrypoint policy that governs pages using the site-header
        # shell (orientation bar, quiz CTA rules).
        self.assertNotIn('class="site-header"', html())
        self.assertNotIn("site-shell.js", html())
        self.assertIn('class="portal-topbar"', html())

    def test_internal_links_resolve(self):
        for href in re.findall(r'(?:href|src)="(\.\./[^"]+)"', html()):
            target = (PORTAL / href).resolve()
            self.assertTrue(target.exists(), href)


class GovernanceTextTests(unittest.TestCase):
    def test_transparent_limits_notice_on_every_screen(self):
        # PRD §10: the boundary statement is rendered statically, outside the
        # app root, so it is visible on every screen including sign-in.
        self.assertIn("For Nurse AI OS setup, education, maintenance, and improvement support only.", html())
        self.assertIn("Do not enter patient information or use this portal for urgent clinical", html())
        self.assertIn("TRANSPARENT_LIMITS_NOTICE", model())

    def test_no_phi_warning_guards_entry_forms(self):
        self.assertIn("NO_PHI_WARNING", model())
        self.assertIn("NO_PHI_WARNING", app())
        # Question entry, reply forms, and the screening speed bump all engage it.
        self.assertGreaterEqual(app().count("noPhiCallout()"), 2)
        self.assertIn("screenGate", app())
        self.assertIn("screenSubmission", model())

    def test_ai_replies_stay_human_approved(self):
        self.assertIn("AI-assisted · human approved", app())
        self.assertIn("Approve &amp; send reply", app())
        # The edge function returns a draft and performs no writes.
        self.assertIn('return json(200, { draft })', edge_fn())
        self.assertNotIn(".insert(", edge_fn())
        self.assertNotIn(".update(", edge_fn())
        self.assertNotIn(".delete(", edge_fn())


class NoSecretsTests(unittest.TestCase):
    SECRET_PATTERNS = (
        r"sk-ant-[A-Za-z0-9-]{8}",          # Anthropic API key material
        r"eyJ[A-Za-z0-9_-]{40,}",           # JWT-shaped literals (service keys)
        r"-----BEGIN [A-Z ]*PRIVATE KEY",
        r"service_role",
    )

    # Deliberate references to the *shape* of a secret — the client-side
    # screening samples in the model — are allow-listed by (file, pattern)
    # so a future sample tweak fails here only if it appears somewhere new.
    ALLOWED_MATCHES = {
        ("portal/portal-model.mjs", r"sk-ant-[A-Za-z0-9-]{8}"),
    }

    def test_no_secret_material_in_portal_or_backend_sources(self):
        files = list(PORTAL.glob("*")) + [
            ROOT / "supabase" / "functions" / "draft-with-ai" / "index.ts",
            *(ROOT / "supabase" / "migrations").glob("*.sql"),
        ]
        failures = []
        for path in files:
            if not path.is_file():
                continue
            relative = str(path.relative_to(ROOT))
            text = path.read_text(encoding="utf-8")
            for pattern in self.SECRET_PATTERNS:
                if (relative, pattern) in self.ALLOWED_MATCHES:
                    continue
                for match in re.finditer(pattern, text):
                    line = text[: match.start()].count("\n") + 1
                    failures.append(f"{relative}:{line}: {pattern}")
        self.assertEqual([], failures)

    def test_config_ships_unconfigured_with_pinned_dependency(self):
        self.assertRegex(config(), r"supabaseUrl:\s*''")
        self.assertRegex(config(), r"supabaseAnonKey:\s*''")
        self.assertRegex(config(), r"@supabase/supabase-js@\d+\.\d+\.\d+")

    def test_edge_function_reads_key_from_environment_only(self):
        self.assertIn('Deno.env.get("ANTHROPIC_API_KEY")', edge_fn())
        self.assertIn('Deno.env.get("SUPABASE_ANON_KEY")', edge_fn())
        self.assertNotIn("SERVICE_ROLE", edge_fn())

    def test_supabase_js_is_version_pinned_everywhere(self):
        for text, name in ((data(), "portal-data.mjs"), (edge_fn(), "edge function")):
            if "@supabase/supabase-js" in text:
                self.assertNotIn("@supabase/supabase-js@latest", text, name)


class RowLevelSecurityTests(unittest.TestCase):
    def test_every_table_created_and_rls_enabled(self):
        for table in TABLES:
            self.assertIn(f"create table public.{table}", migration(), table)
            self.assertIn(f"alter table public.{table} enable row level security", migration(), table)

    def test_every_table_has_at_least_one_policy(self):
        for table in TABLES:
            self.assertRegex(migration(), rf'create policy "[^"]+" on public\.{table}', table)

    def test_client_isolation_predicates_present(self):
        self.assertIn("portal_client_id()", migration())
        self.assertIn("portal_is_admin()", migration())
        self.assertIn("security definer", migration())
        # Clients read only *published* reports.
        self.assertRegex(migration(), r"client_id = public\.portal_client_id\(\) and published")

    def test_clients_cannot_forge_ai_or_activity_records(self):
        self.assertIn("ai_assisted = false", migration())
        # activity_events: select policy only — no insert/update/delete path.
        activity_policies = re.findall(r'create policy "[^"]+" on public\.activity_events\s+for (\w+)', migration())
        self.assertEqual(["select"], activity_policies)

    def test_action_updates_are_column_guarded(self):
        self.assertIn("portal_guard_client_action_update", migration())
        self.assertIn("Clients may update only an action''s status and comment", migration())
        # The row identity is pinned too, so related_id/audit references
        # cannot be orphaned by a client rewriting an action's id.
        self.assertRegex(migration(), r"new\.id\s+is distinct from old\.id")

    def test_helper_surfaces_are_scoped_to_authenticated_users(self):
        self.assertIn("portal_open_conversation", migration())
        self.assertRegex(migration(), r"revoke all on function public\.portal_open_conversation[^;]+from anon")
        self.assertIn("portal_directory", migration())
        self.assertIn("revoke all on public.portal_directory from anon", migration())
        self.assertIn("grant select on public.portal_directory to authenticated", migration())
        # The directory exposes names only — never emails or roles.
        directory = migration().split("create or replace view public.portal_directory", 1)[1].split(";", 1)[0]
        self.assertIn("select p.id, p.name", directory)
        self.assertNotIn("email", directory)

    def test_schema_holds_no_patient_fields(self):
        # Comments may (and do) talk about the no-PHI rule; the DDL itself
        # must never define patient-shaped columns.
        ddl = "\n".join(re.sub(r"--.*$", "", line) for line in migration().splitlines())
        for forbidden in ("patient", "mrn", "date_of_birth", "medical_record", "diagnos"):
            self.assertNotIn(forbidden, ddl.lower(), forbidden)

    def test_admin_view_respects_caller_rls(self):
        self.assertIn("security_invoker = true", migration())


if __name__ == "__main__":
    unittest.main()
