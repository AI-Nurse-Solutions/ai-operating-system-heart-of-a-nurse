"""Education, committee, and communication packs (5.4): the manifest checks,
review dates, and documents started from a pack.

The exit check: every pack ships a manifest naming its maintainer and its
review dates, and pins the exact templates it was reviewed with. A pack past
its review date, or failing its checks, starts nothing.
"""

from __future__ import annotations

import copy
import json
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

import _bootstrap  # noqa: F401
from _bootstrap import fixed_clock

from nurse_manager import packs as packs_module
from nurse_manager import store as store_module
from nurse_manager.brief import BriefService, StaleRevision
from nurse_manager.packs import (
    PACK_DRAFT_BANNER,
    PackError,
    PackService,
    available_packs,
    load_pack,
    template_sha256,
)
from nurse_manager.sample import load_sample
from nurse_manager.services import CaptureRefused, ManagerError, ManagerWorkspace
from nurse_manager.store import _connect, _split_sql
from nurse_manager.views import mission_control, packs as packs_view

TODAY = "2026-09-30"
OWNER = "me"
SHIPPED = ("committee", "communication", "education")


def catalog() -> dict:
    return packs_module._catalog()


class ManifestTests(unittest.TestCase):
    """What every shipped manifest must say, and what the loader refuses."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.good = json.loads((packs_module.packs_dir() / "committee.json").read_text("utf-8"))

    def write(self, manifest: dict, name: str | None = None) -> Path:
        path = self.dir / f"{name or manifest.get('id', 'pack')}.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return path

    def test_every_shipped_pack_names_its_maintainer_and_review_dates(self):
        files = sorted(p.stem for p in packs_module.packs_dir().glob("*.json"))
        self.assertEqual(tuple(files), SHIPPED)
        for path in sorted(packs_module.packs_dir().glob("*.json")):
            with self.subTest(pack=path.stem):
                manifest = load_pack(path, catalog())
                self.assertTrue(manifest["maintainer"].strip())
                self.assertLess(manifest["reviewed_on"], manifest["review_by"])
                self.assertTrue(manifest["rules"])
                for template_id, pinned in manifest["templates"].items():
                    self.assertEqual(template_sha256(catalog()["templates"][template_id]), pinned)

    def test_the_packs_cover_education_committees_and_communication(self):
        by_id = {p["id"]: p for p in available_packs(TODAY)}
        self.assertEqual(set(by_id["education"]["templates"]),
                         {"education-plan", "competency-checklist", "case-study"})
        self.assertIn("meeting-pack", by_id["committee"]["templates"])
        self.assertIn("message-draft", by_id["communication"]["templates"])
        self.assertTrue(all(p["status"] == "current" for p in by_id.values()))

    def test_a_manifest_missing_what_the_exit_check_requires_is_refused(self):
        cases = {
            "no maintainer": ("maintainer", None, "maintainer is required"),
            "blank maintainer": ("maintainer", "  ", "maintainer is required"),
            "no review date": ("review_by", None, "must be dates"),
            "not a date": ("reviewed_on", "last spring", "must be dates"),
            "review before it was reviewed": ("review_by", "2026-01-01", "must come after"),
            "no version": ("version", "latest", "version must look like"),
            "no rules": ("rules", [], "at least one rule"),
            "wrong schema": ("schema", "something-else@1", "not a nurse-manager-pack@1"),
            "another catalog": ("catalog", {"schema_version": "2.0.0"}, "different template catalog"),
        }
        for label, (key, value, message) in cases.items():
            with self.subTest(case=label):
                manifest = copy.deepcopy(self.good)
                if value is None:
                    manifest.pop(key)
                else:
                    manifest[key] = value
                with self.assertRaisesRegex(PackError, message):
                    load_pack(self.write(manifest), catalog())

    def test_a_changed_or_missing_template_needs_the_pack_reviewed_again(self):
        manifest = copy.deepcopy(self.good)
        manifest["templates"]["meeting-pack"] = "0" * 64
        with self.assertRaisesRegex(PackError, "changed since the pack was reviewed"):
            load_pack(self.write(manifest), catalog())
        edited = copy.deepcopy(catalog())
        edited["templates"]["meeting-pack"]["sections"][0]["guidance"] += " Edited."
        with self.assertRaisesRegex(PackError, "meeting-pack changed since"):
            load_pack(self.write(self.good), edited)
        manifest = copy.deepcopy(self.good)
        manifest["templates"]["no-such-template"] = "0" * 64
        with self.assertRaisesRegex(PackError, "not in the catalog"):
            load_pack(self.write(manifest), catalog())

    def test_the_id_must_match_the_file(self):
        with self.assertRaisesRegex(PackError, "match its file name"):
            load_pack(self.write(self.good, name="renamed"), catalog())

    def test_a_broken_pack_is_listed_as_unavailable_never_dropped_or_used(self):
        manifest = copy.deepcopy(self.good)
        manifest.pop("maintainer")
        self.write(manifest)
        self.write(json.loads((packs_module.packs_dir() / "education.json").read_text("utf-8")))
        with mock.patch.object(packs_module, "packs_dir", lambda: self.dir):
            listed = {p["id"]: p for p in available_packs(TODAY)}
        self.assertEqual(listed["committee"]["status"], "unavailable")
        self.assertIn("maintainer is required", listed["committee"]["reason"])
        self.assertEqual(listed["education"]["status"], "current")


class _WorkspaceCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name) / "ws"
        self.ws, _ = load_sample(self.root, clock=fixed_clock())
        self.addCleanup(self.ws.close)
        self.service = PackService(self.ws)
        self.project = self.ws.store.conn.execute(
            "SELECT * FROM projects WHERE title LIKE 'Unit Based%'").fetchone()

    def start(self, **kwargs):
        kwargs.setdefault("today", TODAY)
        return self.service.start("committee", "meeting-pack", **kwargs)


class ReviewDateTests(_WorkspaceCase):
    def test_a_pack_past_its_review_date_starts_nothing_and_says_who_to_ask(self):
        listed = {p["id"]: p for p in available_packs("2027-03-30")}
        self.assertEqual(listed["committee"]["status"], "due_for_review")
        self.assertIn("Project steward (GOVERNANCE.md)", listed["committee"]["reason"])
        before = len(self.service.documents())
        with self.assertRaisesRegex(PackError, "Past its review date \\(2027-03-29\\)"):
            self.start(today="2027-03-30")
        self.assertEqual(len(self.service.documents()), before)
        # On its review date it is still current.
        self.assertTrue(self.start(today="2027-03-29"))

    def test_the_screen_shows_the_status_for_the_requested_day(self):
        view = packs_view(self.ws, today="2027-04-01")
        self.assertEqual({p["status"] for p in view["packs"]}, {"due_for_review"})
        self.assertTrue(all(p["maintainer"] and p["review_by"] for p in view["packs"]))


class DocumentTests(_WorkspaceCase):
    def test_a_draft_holds_the_template_the_rules_and_where_it_came_from(self):
        document_id = self.start(project_id=self.project["id"])
        view = self.service.view(document_id)
        body = view["current"]["body_markdown"]
        spec = catalog()["templates"]["meeting-pack"]
        headings = [line[3:] for line in body.splitlines() if line.startswith("## ")]
        self.assertEqual(headings, ["Before you use this"] + [s["heading"] for s in spec["sections"]])
        self.assertIn("never effective until it is approved", body)
        self.assertIn(f"`{self.project['id']}`", body)
        self.assertIn("Committee pack 1.0.0", body)
        self.assertEqual(body.count("_Write this section._"), len(spec["sections"]))
        revision = view["current"]["revision"]
        self.assertEqual((revision["status"], revision["created_by"]), ("draft", OWNER))
        self.assertEqual(revision["source_refs"], [self.project["id"]])
        self.assertIn(PACK_DRAFT_BANNER, view["current"]["markdown"])
        row = self.ws.store.conn.execute(
            "SELECT * FROM pack_documents WHERE artifact_id = ?", (document_id,)).fetchone()
        self.assertEqual((row["pack_id"], row["pack_version"], row["template_id"]),
                         ("committee", "1.0.0", "meeting-pack"))
        self.assertEqual(row["template_sha256"], template_sha256(spec))

    def test_only_a_pack_template_and_a_workspace_project_are_accepted(self):
        with self.assertRaisesRegex(PackError, "no pack called"):
            self.service.start("finance", "meeting-pack", today=TODAY)
        with self.assertRaisesRegex(PackError, "has no template education-plan"):
            self.service.start("committee", "education-plan", today=TODAY)
        with self.assertRaises(ManagerError):
            self.start(project_id="prj-000000000000")

    def test_edits_are_new_drafts_and_acceptance_binds_to_the_text_reviewed(self):
        document_id = self.start()
        first = self.service.view(document_id)["current"]
        body = first["body_markdown"].replace("_Write this section._", "Dates first (synthetic).", 1)
        saved = self.service.save(document_id, body, first["revision"]["sha256"])
        self.assertEqual((saved.revision_no, saved.status), (2, "draft"))
        briefs = BriefService(self.ws)
        with self.assertRaises(StaleRevision):
            briefs.accept(saved.id, OWNER, first["revision"]["sha256"])
        accepted = briefs.accept(saved.id, OWNER, saved.body_sha256)
        self.assertEqual(accepted.status, "accepted")
        # A later edit is a new draft; the accepted version stays accepted until replaced.
        later = self.service.save(document_id, body + "\nOne more line.\n", saved.body_sha256)
        view = self.service.view(document_id)
        self.assertEqual(view["current"]["revision"]["id"], later.id)
        self.assertEqual(view["accepted"]["id"], saved.id)
        listed = next(d for d in self.service.documents() if d["id"] == document_id)
        self.assertEqual((listed["status"], listed["has_accepted"]), ("draft", True))
        titles = [i["title"] for i in mission_control(self.ws, today=TODAY,
                                                      week_of="2026-09-28")["recent_accepted_outputs"]["items"]]
        self.assertIn("Meeting Brief, Agenda, Minutes, and Action List", titles)

    def test_a_save_cannot_land_between_the_acceptance_checks_and_the_acceptance(self):
        # Two tabs: one accepts version 2 while the other saves version 3. The
        # save must not commit between the "is this the latest?" check and the
        # acceptance, or an older version ends up accepted.
        document_id = self.start()
        first = self.service.view(document_id)["current"]
        v2 = self.service.save(document_id, first["body_markdown"] + "\nv2\n",
                               first["revision"]["sha256"])
        root, clock = self.root, self.ws.clock
        attempt: dict = {}

        def other_tab_saves():
            ws = ManagerWorkspace(root, clock=clock)
            try:
                PackService(ws).save(document_id, v2.body_markdown + "v3\n", v2.body_sha256)
                attempt["saved"] = True
            except Exception as exc:  # noqa: BLE001 - reported below
                attempt["saved"] = exc
            finally:
                ws.close()

        latest = BriefService.latest

        def latest_then_other_tab(self_, artifact_id):
            found = latest(self_, artifact_id)
            if "thread" not in attempt:
                attempt["thread"] = threading.Thread(target=other_tab_saves, daemon=True)
                attempt["thread"].start()
                attempt["thread"].join(0.3)
                attempt["saved_before_accept"] = not attempt["thread"].is_alive()
            return found

        with mock.patch.object(BriefService, "latest", latest_then_other_tab):
            BriefService(self.ws).accept(v2.id, OWNER, v2.body_sha256)
        attempt["thread"].join(5)
        self.assertFalse(attempt["saved_before_accept"],
                         "a save committed between the acceptance checks and the acceptance")
        self.assertIs(attempt["saved"], True)
        # The acceptance came first: version 2 accepted, version 3 the newer draft.
        view = self.service.view(document_id)
        self.assertEqual((view["accepted"]["revision_no"], view["current"]["revision"]["revision_no"]),
                         (2, 3))

    def test_a_stale_empty_unchanged_or_identifying_edit_is_refused_and_nothing_is_stored(self):
        document_id = self.start()
        current = self.service.view(document_id)["current"]
        base, text = current["revision"]["sha256"], current["body_markdown"]
        cases = {
            "stale": (text + "x", "0" * 64, StaleRevision, "changed since you opened it"),
            "empty": ("   \n", base, PackError, "needs content"),
            "unchanged": (text, base, PackError, "nothing changed"),
            "too long": ("x" * 50_001, base, PackError, "under 50000"),
            "identifier": (text + "\nCall 555-123-4567.\n", base, CaptureRefused, "PHONE_NUMBER"),
        }
        for label, (body, sha, error, message) in cases.items():
            with self.subTest(case=label), self.assertRaisesRegex(error, message):
                self.service.save(document_id, body, sha)
        self.assertEqual(len(BriefService(self.ws).history(document_id)), 1)

    def test_arguments_the_cli_cannot_parse_get_an_answer_not_an_exit(self):
        from nurse_manager import cli

        code, envelope = cli.run(["document-save", str(self.root), "--id", "art-000000000000",
                                  "--body"])
        self.assertEqual((code, envelope["ok"], envelope["error"]["type"]),
                         (2, False, "UsageError"))
        self.assertEqual(envelope["command"], "document-save")

    def test_a_document_is_found_only_in_its_own_workspace(self):
        with self.assertRaisesRegex(PackError, "not in this workspace"):
            self.service.view("art-000000000000")
        brief = BriefService(self.ws).draft_weekly_brief("2026-09-28", TODAY)
        with self.assertRaisesRegex(PackError, "not in this workspace"):
            self.service.view(brief.artifact_id)  # a weekly brief is not a pack document


class MigrationTests(unittest.TestCase):
    def test_artifacts_are_rebuilt_with_every_brief_and_revision_kept(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "workspace.sqlite"
        conn = _connect(path)
        conn.execute("CREATE TABLE schema_migrations (version TEXT PRIMARY KEY,"
                     " applied_at TEXT NOT NULL)")
        for version, sql in (m for m in store_module._migrations() if m[0] < "0011"):
            conn.execute("BEGIN IMMEDIATE")
            for statement in _split_sql(sql):
                conn.execute(statement)
            conn.execute("INSERT INTO schema_migrations VALUES (?, 'then')", (version,))
            conn.execute("COMMIT")
        at = "2026-09-01T09:00:00+00:00"
        conn.executescript(f"""
            INSERT INTO workspaces (id, name, profile, owner, sample, created_at)
                VALUES ('ws-000000000001', 'W', 'personal_manager', 'M', 0, '{at}');
            INSERT INTO artifacts (id, workspace_id, kind, title, week_of, created_at)
                VALUES ('art-000000000001', 'ws-000000000001', 'weekly_brief', 'Brief',
                        '2026-08-31', '{at}');
            INSERT INTO artifact_revisions (id, artifact_id, revision_no, body_markdown,
                body_sha256, status, created_by, created_at)
                VALUES ('rev-000000000001', 'art-000000000001', 1, '# Brief', 'h', 'accepted',
                        'M', '{at}');
        """)
        conn.close()
        migrated = store_module.Store(path)
        self.addCleanup(migrated.close)
        (row,) = migrated.conn.execute("SELECT * FROM artifacts")
        self.assertEqual((row["id"], row["kind"], row["week_of"]),
                         ("art-000000000001", "weekly_brief", "2026-08-31"))
        self.assertEqual(migrated.conn.execute(
            "SELECT artifact_id FROM artifact_revisions").fetchone()[0], "art-000000000001")
        self.assertEqual(migrated.conn.execute("PRAGMA foreign_key_check").fetchall(), [])
        with self.assertRaises(sqlite3.IntegrityError):
            migrated.conn.execute("UPDATE artifacts SET kind = 'memo'")


if __name__ == "__main__":
    unittest.main()
