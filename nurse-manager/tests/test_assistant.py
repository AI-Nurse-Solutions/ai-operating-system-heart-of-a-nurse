"""Bounded assistance (G4, ADR 0004): steps 4.2–4.4 exit evidence.

No model by default; a model on this computer only when the manager
connects one; the same gates for every provider (data rules, EDENA at
``recommend``, budget before the request, draft only); and provider
failure always returns the records-only draft with the reason.

The local adapter is exercised over real HTTP against a stand-in model
server on 127.0.0.1, so no model or account is needed.
"""

import json
import os
import shutil
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

import _bootstrap
from _bootstrap import fixed_clock

from nurse_manager import cli
from nurse_manager.actions import DEFAULT_PROFILE_POLICY
from nurse_manager.assistant import (
    AssistantError,
    AssistantService,
    LocalModelProvider,
    ProviderReply,
    check_local_endpoint,
)
from nurse_manager.brief import ASSISTANT_DRAFT_BANNER, BRIEF_DRAFT_BANNER, BriefService
from nurse_manager.sample import load_sample
from nurse_manager.services import ManagerError, ManagerWorkspace
from nurse_manager.views import mission_control

WEEK = "2026-09-28"
TODAY = "2026-09-30"
OWNER = "Sample Manager"


class FakeModelServer:
    """A stand-in for an Ollama-compatible server on this computer."""

    def __init__(self, reply=None, *, status=200, delay=0.0, redirect_to=None):
        self.requests: list[dict] = []
        self.reply = reply
        server = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                server.requests.append({"path": self.path,
                                        "body": json.loads(self.rfile.read(length))})
                if delay:
                    time.sleep(delay)
                if redirect_to:
                    self.send_response(307)
                    self.send_header("Location", redirect_to)
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                text = server.reply(server.requests[-1]["body"]) if callable(server.reply) \
                    else server.reply
                payload = json.dumps({"model": "m", "response": text, "done": True}).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                try:
                    self.wfile.write(payload)
                except (BrokenPipeError, ConnectionResetError):
                    pass  # the client gave up (the timeout test)

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.endpoint = f"http://127.0.0.1:{self.httpd.server_port}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


def echo_rewrite(body):
    """A well-behaved model: keeps the headings and the cited lines, drops the rest."""
    return "\n".join(line for line in body["prompt"].splitlines()
                     if line.startswith("#") or "`" in line)


class _Case(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.ws, _ = load_sample(self.tmp / "ws", clock=fixed_clock())
        self.servers: list[FakeModelServer] = []

    def tearDown(self):
        for server in self.servers:
            server.close()
        self.ws.close()
        self._tmp.cleanup()

    def server(self, reply=echo_rewrite, **kwargs) -> FakeModelServer:
        server = FakeModelServer(reply, **kwargs)
        self.servers.append(server)
        return server

    def service(self, **kwargs) -> AssistantService:
        kwargs.setdefault("timeout", 5.0)
        return AssistantService(self.ws, **kwargs)

    def connect(self, server: FakeModelServer, **kwargs) -> AssistantService:
        assistant = self.service()
        assistant.connect_local(OWNER, "llama3.2", endpoint=server.endpoint, **kwargs)
        return assistant

    def draft(self, assistant: AssistantService) -> dict:
        return assistant.draft_weekly_brief(WEEK, TODAY, OWNER)

    def ledger(self) -> list:
        return list(self.ws.store.conn.execute(
            "SELECT * FROM assistant_requests ORDER BY created_at"))


class DefaultPostureTests(_Case):
    def test_a_new_workspace_has_no_model(self):
        status = self.service().status()
        self.assertEqual(status["provider"], "none")
        self.assertEqual(status["runs_on"], "nothing is connected")
        self.assertFalse(status["cloud"]["available"])
        self.assertIn("No cloud AI service has been chosen", status["cloud"]["reason"])

    def test_no_model_still_drafts_the_brief_from_records_and_says_so(self):
        result = self.draft(self.service())
        self.assertEqual(result["outcome"], "no_model")
        self.assertFalse(result["drafted_by_model"])
        self.assertIn("No AI model is connected", result["reason"])
        revision = BriefService(self.ws).revision(result["revision"]["id"])
        self.assertEqual(revision.created_by, OWNER)
        self.assertIn("no AI model was used", revision.body_markdown)

    def test_an_environment_variable_never_connects_a_model(self):
        with mock.patch.dict(os.environ, {"OLLAMA_HOST": "127.0.0.1:11434",
                                          "OPENAI_API_KEY": "x", "ANTHROPIC_API_KEY": "x"}):
            self.assertEqual(self.service().status()["provider"], "none")
            self.assertEqual(self.draft(self.service())["outcome"], "no_model")

    def test_mission_control_is_honest_about_assistants(self):
        mc = mission_control(self.ws, today=TODAY, week_of=WEEK)
        self.assertEqual(mc["assistants_at_work"]["state"], "unavailable")
        self.assertIn("No assistant is connected", mc["assistants_at_work"]["empty_message"])
        self.connect(self.server())
        mc = mission_control(self.ws, today=TODAY, week_of=WEEK)
        self.assertEqual(mc["assistants_at_work"]["state"], "unavailable")
        self.assertIn("No assistant is running", mc["assistants_at_work"]["empty_message"])


class SettingsTests(_Case):
    def test_only_the_accountable_manager_changes_ai_settings(self):
        with self.assertRaises(AssistantError):
            self.service().connect_local("Someone Else", "llama3.2")
        with self.assertRaises(AssistantError):
            self.service().connect_local("assistant:local", "llama3.2")
        self.connect(self.server())
        with self.assertRaises(AssistantError):
            self.service().disconnect("Someone Else")
        with self.assertRaises(AssistantError):
            self.service().draft_weekly_brief(WEEK, TODAY, "Someone Else")

    def test_a_local_model_must_run_on_this_computer(self):
        for endpoint in ("http://example.com:11434", "https://127.0.0.1:11434",
                         "http://10.0.0.5:11434", "http://user:pw@127.0.0.1:11434",
                         "http://127.0.0.1:11434/proxy", "http://127.0.0.1.example.com",
                         "http://localhost:99999", "file:///etc/passwd"):
            with self.subTest(endpoint=endpoint), self.assertRaises(AssistantError):
                check_local_endpoint(endpoint)
        self.assertEqual(check_local_endpoint("http://localhost:11434/"), "http://localhost:11434")
        self.assertEqual(check_local_endpoint("http://[::1]:8080"), "http://[::1]:8080")

    def test_model_names_are_checked(self):
        for name in ("", " ", "a b", "x" * 101, "../../etc", "-rm"):
            with self.subTest(name=name), self.assertRaises(AssistantError):
                self.service().connect_local(OWNER, name)

    def test_disconnect_returns_to_no_model_and_is_audited(self):
        assistant = self.connect(self.server())
        self.assertEqual(assistant.status()["provider"], "local")
        self.assertEqual(assistant.status()["runs_on"], "this computer")
        self.assertEqual(assistant.disconnect(OWNER)["provider"], "none")
        kinds = [(e["kind"], e["record_type"]) for e in self.ws.store.events()]
        self.assertEqual(kinds.count(("configure", "assistant_settings")), 2)

    def test_settings_survive_close_and_reopen(self):
        self.connect(self.server())
        self.ws.close()
        self.ws = ManagerWorkspace(self.tmp / "ws", clock=fixed_clock())
        self.assertEqual(self.service().status()["model"], "llama3.2")


class LocalDraftTests(_Case):
    def test_a_local_model_drafts_and_the_draft_waits_for_the_manager(self):
        server = self.server()
        result = self.draft(self.connect(server))
        self.assertEqual(result["outcome"], "drafted", result["reason"])
        self.assertTrue(result["drafted_by_model"])
        self.assertEqual((result["provider"], result["model"]), ("local", "llama3.2"))

        briefs = BriefService(self.ws)
        revision = briefs.revision(result["revision"]["id"])
        self.assertEqual(revision.status, "draft")
        self.assertEqual(revision.created_by, "assistant:local")
        self.assertEqual(result["revision"]["created_by"], "assistant:local")
        self.assertIn("by the AI model `llama3.2` on this computer", revision.body_markdown)
        self.assertNotIn("no AI model was used", revision.body_markdown)
        rendered = briefs.render(revision)
        self.assertIn(ASSISTANT_DRAFT_BANNER, rendered)
        self.assertNotIn(BRIEF_DRAFT_BANNER, rendered)
        self.assertTrue(revision.source_refs)
        self.assertTrue(set(revision.source_refs) <= set(
            briefs.draft_weekly_brief(WEEK, TODAY).source_refs))

        # Only the manager can accept it; the assistant cannot.
        latest = self.draft(self.service())["revision"]
        with self.assertRaises(ManagerError):
            briefs.accept(latest["id"], "assistant:local", latest["sha256"])
        accepted = briefs.accept(latest["id"], OWNER, latest["sha256"])
        self.assertEqual(accepted.accepted_by, OWNER)

    def test_what_is_sent_is_the_record_sections_only(self):
        server = self.server()
        self.draft(self.connect(server))
        (request,) = server.requests
        self.assertEqual(request["path"], "/api/generate")
        body = request["body"]
        self.assertEqual(body["model"], "llama3.2")
        self.assertIs(body["stream"], False)
        self.assertTrue(body["prompt"].startswith("## "))
        self.assertNotIn("no AI model was used", body["prompt"])
        self.assertNotIn(self.ws.info.name, body["prompt"])
        self.assertIn("never add names", body["system"])

    def test_the_ledger_keeps_metadata_never_text(self):
        server = self.server()
        self.draft(self.connect(server))
        (row,) = self.ledger()
        self.assertEqual(row["outcome"], "drafted")
        self.assertRegex(row["prompt_sha256"], r"^[0-9a-f]{64}$")
        prompt = server.requests[0]["body"]["prompt"]
        stored = " ".join(str(v) for v in tuple(row))
        for line in prompt.splitlines():
            if len(line) > 20:
                self.assertNotIn(line, stored)

    def test_proxy_settings_cannot_carry_the_text_off_this_computer(self):
        server = self.server()
        with mock.patch.dict(os.environ, {"HTTP_PROXY": "http://203.0.113.1:9",
                                          "http_proxy": "http://203.0.113.1:9",
                                          "NO_PROXY": "", "no_proxy": ""}):
            result = self.draft(self.connect(server))
        self.assertEqual(result["outcome"], "drafted", result["reason"])
        self.assertEqual(len(server.requests), 1)

    def test_a_redirect_is_never_followed(self):
        elsewhere = self.server()
        server = self.server(redirect_to=f"{elsewhere.endpoint}/api/generate")
        result = self.draft(self.connect(server))
        self.assertEqual(result["outcome"], "provider_failed")
        self.assertEqual(elsewhere.requests, [])


class FallbackTests(_Case):
    def assert_records_only(self, result, outcome, reason_fragment):
        self.assertEqual(result["outcome"], outcome)
        self.assertFalse(result["drafted_by_model"])
        self.assertIn(reason_fragment, result["reason"])
        revision = BriefService(self.ws).revision(result["revision"]["id"])
        self.assertEqual(revision.created_by, OWNER)
        self.assertEqual(revision.status, "draft")
        self.assertIn("no AI model was used", revision.body_markdown)
        self.assertEqual(self.ledger()[-1]["outcome"], outcome)
        self.assertEqual(self.ledger()[-1]["revision_id"], revision.id)

    def test_server_not_running(self):
        assistant = self.service()
        server = self.server()
        endpoint = server.endpoint
        server.close()
        self.servers.remove(server)
        assistant.connect_local(OWNER, "llama3.2", endpoint=endpoint)
        self.assert_records_only(self.draft(assistant), "provider_failed", "not reachable")

    def test_server_error(self):
        self.assert_records_only(self.draft(self.connect(self.server(status=404))),
                                 "provider_failed", "answered 404")

    def test_timeout(self):
        server = self.server(delay=1.5)
        assistant = self.connect(server)
        assistant.timeout = 0.3
        self.assert_records_only(self.draft(assistant), "provider_failed", "not reachable")

    def test_an_adapter_bug_still_falls_back(self):
        class Broken:
            kind, model, runs_on = "local", "broken", "this computer"

            def estimate_cents(self, *args):
                return 0

            def complete(self, *args, **kwargs):
                raise RuntimeError("bug")

        self.connect(self.server())
        assistant = self.service(provider_factory=lambda s: Broken())
        self.assert_records_only(self.draft(assistant), "provider_failed", "unexpectedly")

    def test_output_with_identifiers_is_not_saved(self):
        server = self.server(lambda body: body["prompt"] + "\nEmail jane.doe@example.org")
        self.assert_records_only(self.draft(self.connect(server)),
                                 "output_refused", "EMAIL_ADDRESS")

    def test_output_citing_records_that_were_not_sent_is_not_saved(self):
        server = self.server(lambda body: body["prompt"] + "\nSee `tsk-0123456789ab`.")
        self.assert_records_only(self.draft(self.connect(server)),
                                 "output_refused", "tsk-0123456789ab")

    def test_output_that_drops_every_citation_is_not_saved(self):
        server = self.server(lambda body: "A tidy summary with nothing to check it against.")
        self.assert_records_only(self.draft(self.connect(server)),
                                 "output_refused", "had no citation")

    def test_one_valid_citation_does_not_vouch_for_other_lines(self):
        def one_good_line_then_claims(body):
            cited = next(line for line in body["prompt"].splitlines() if "`" in line)
            return cited + "\nMorale on the unit is the lowest it has been in a year."
        server = self.server(one_good_line_then_claims)
        result = self.draft(self.connect(server))
        self.assert_records_only(result, "output_refused", "1 line(s) had no citation")
        self.assertIn("Morale on the unit", result["reason"])

    def test_empty_output_is_not_saved(self):
        self.assert_records_only(self.draft(self.connect(self.server("  "))),
                                 "output_refused", "returned nothing")

    def test_the_data_rules_stop_the_request_before_anything_is_sent(self):
        # Capture refuses identifiers, so plant one the way an older or
        # hand-edited database might hold it.
        self.ws.store.conn.execute(
            "UPDATE priorities SET text = 'Call 555-867-5309 about staffing'"
            " WHERE workspace_id = ? AND rank = 1", (self.ws.info.id,))
        server = self.server()
        self.assert_records_only(self.draft(self.connect(server)),
                                 "refused_data_rules", "Nothing was sent")
        self.assertEqual(server.requests, [])

    def test_edena_decides_before_anything_is_sent(self):
        policy = json.loads(DEFAULT_PROFILE_POLICY.read_text(encoding="utf-8"))
        policy["assistant_evaluation"]["action_mode"] = "act_with_approval"
        path = self.tmp / "policy.json"
        path.write_text(json.dumps(policy), encoding="utf-8")
        server = self.server()
        self.connect(server)
        result = self.draft(self.service(profile_policy=path))
        self.assert_records_only(result, "refused_policy", "EDENA-")
        self.assertEqual(server.requests, [])


class BudgetTests(_Case):
    def test_the_daily_limit_is_checked_before_the_request(self):
        server = self.server()
        assistant = self.connect(server, daily_request_limit=1)
        self.assertEqual(self.draft(assistant)["outcome"], "drafted")
        result = self.draft(assistant)
        self.assertEqual(result["outcome"], "refused_budget")
        self.assertIn("today's limit of 1", result["reason"])
        self.assertEqual(len(server.requests), 1)
        self.assertEqual(assistant.status()["requests_today"], 1)

    def test_a_zero_limit_sends_nothing(self):
        server = self.server()
        self.assertEqual(self.draft(self.connect(server, daily_request_limit=0))["outcome"],
                         "refused_budget")
        self.assertEqual(server.requests, [])

    def test_failed_requests_count_against_the_limit(self):
        server = self.server(status=500)
        assistant = self.connect(server, daily_request_limit=2)
        self.draft(assistant)
        self.draft(assistant)
        self.assertEqual(self.draft(assistant)["outcome"], "refused_budget")
        self.assertEqual(len(server.requests), 2)

    def test_a_paid_provider_is_stopped_by_the_monthly_budget_before_it_is_called(self):
        calls = []

        class Paid:
            kind, model, runs_on = "local", "priced", "a stand-in paid service"

            def estimate_cents(self, system, prompt, max_output_tokens):
                return 5

            def complete(self, *args, **kwargs):
                calls.append(1)
                return ProviderReply("x", cost_cents=5)

        self.connect(self.server())  # budget stays at its default: 0 cents
        result = self.draft(self.service(provider_factory=lambda s: Paid()))
        self.assertEqual(result["outcome"], "refused_budget")
        self.assertIn("this month's AI budget", result["reason"])
        self.assertEqual(calls, [])

    def test_an_interrupted_request_still_counts(self):
        class Crash(BaseException):
            pass

        class Dies:
            kind, model, runs_on = "local", "dies", "this computer"

            def estimate_cents(self, *args):
                return 3

            def complete(self, *args, **kwargs):
                raise Crash()

        self.connect(self.server(), daily_request_limit=1)
        # No settings path sets a budget yet (no paid service exists).
        self.ws.store.conn.execute("UPDATE assistant_settings SET monthly_budget_cents = 10")
        with self.assertRaises(Crash):
            self.draft(self.service(provider_factory=lambda s: Dies()))
        (row,) = self.ledger()
        self.assertEqual(row["outcome"], "provider_failed")
        self.assertIsNone(row["cost_cents"])
        status = self.service().status()
        self.assertEqual(status["requests_today"], 1)
        self.assertEqual(status["spent_this_month_cents"], 3)
        self.assertEqual(self.draft(self.service())["outcome"], "refused_budget")


class PreviewTests(_Case):
    def test_the_preview_is_exactly_what_is_sent_and_writes_nothing(self):
        server = self.server()
        assistant = self.connect(server)
        events = len(self.ws.store.events())
        preview = assistant.preview_weekly_brief(WEEK, TODAY)
        self.assertTrue(preview["will_send"])
        self.assertEqual(len(self.ws.store.events()), events, "a preview records nothing")
        self.assertEqual(self.ledger(), [])
        self.assertEqual(server.requests, [])
        result = assistant.draft_weekly_brief(WEEK, TODAY, OWNER,
                                              reviewed_prompt_sha256=preview["prompt_sha256"])
        self.assertEqual(result["outcome"], "drafted")
        sent = server.requests[0]["body"]
        self.assertEqual((sent["system"], sent["prompt"]), (preview["system"], preview["prompt"]))
        self.assertEqual(self.ledger()[0]["prompt_sha256"], preview["prompt_sha256"])

    def test_a_request_is_refused_if_the_records_changed_after_the_preview(self):
        server = self.server()
        assistant = self.connect(server)
        preview = assistant.preview_weekly_brief(WEEK, TODAY)
        self.ws.store.conn.execute(
            "UPDATE priorities SET text = 'A different first priority' WHERE rank = 1")
        with self.assertRaises(AssistantError):
            assistant.draft_weekly_brief(WEEK, TODAY, OWNER,
                                         reviewed_prompt_sha256=preview["prompt_sha256"])
        self.assertEqual(server.requests, [])
        self.assertEqual(self.ledger(), [])

    def test_the_preview_says_why_nothing_would_be_sent(self):
        self.assertEqual(self.service().preview_weekly_brief(WEEK, TODAY)["reason"],
                         "No AI model is connected. This draft was composed from your records.")
        preview = self.connect(self.server(), daily_request_limit=0).preview_weekly_brief(WEEK, TODAY)
        self.assertFalse(preview["will_send"])
        self.assertEqual([c["passed"] for c in preview["checks"]], [True, True, False])
        self.assertIn("today's limit of 0", preview["reason"])
        self.assertTrue(preview["prompt"], "the manager still sees what would have been sent")


class ProjectQuestionTests(_Case):
    QUESTION = "What should I do first?"

    def setUp(self):
        super().setUp()
        self.project_id = mission_control(self.ws, today=TODAY, week_of=WEEK)[
            "projects_in_motion"]["items"][0]["id"]

    def revisions(self) -> int:
        return self.ws.store.conn.execute("SELECT count(*) FROM artifact_revisions").fetchone()[0]

    def ask(self, assistant, question=QUESTION, **kwargs):
        return assistant.answer_project_question(self.project_id, question, TODAY, OWNER, **kwargs)

    def test_with_no_model_nothing_is_sent_and_the_dashboard_is_the_answer(self):
        result = self.ask(self.service())
        self.assertEqual((result["outcome"], result["answer"]), ("no_model", ""))
        self.assertIn("project dashboard", result["reason"])
        self.assertEqual(self.ledger()[-1]["task"], "project_question")

    def test_the_preview_is_what_is_sent_and_the_answer_is_never_saved(self):
        server = self.server(lambda body: "Start with `" + body["prompt"].split("`")[1] + "`.")
        assistant = self.connect(server)
        preview = assistant.preview_project_question(self.project_id, self.QUESTION, TODAY)
        self.assertTrue(preview["will_send"])
        self.assertTrue(preview["prompt"].startswith("## Question\n\nWhat should I do first?"))
        self.assertIn(self.project_id, preview["prompt"])
        before = self.revisions()
        result = self.ask(assistant, reviewed_prompt_sha256=preview["prompt_sha256"])
        self.assertEqual(result["outcome"], "answered", result["reason"])
        self.assertTrue(result["answered_by_model"])
        self.assertEqual(result["source_refs"], [self.project_id])
        sent = server.requests[0]["body"]
        self.assertEqual((sent["system"], sent["prompt"]), (preview["system"], preview["prompt"]))
        self.assertEqual(self.revisions(), before, "an answer is never saved as a record")
        (row,) = [r for r in self.ledger() if r["task"] == "project_question"]
        self.assertEqual((row["outcome"], row["revision_id"]), ("answered", None))
        self.assertNotIn("Start with", " ".join(str(v) for v in tuple(row)))

    def test_the_context_holds_only_this_projects_records(self):
        from nurse_manager.assistant import compose_project_context

        text, refs = compose_project_context(self.ws, self.project_id, TODAY)
        self.assertEqual(refs[0], self.project_id)
        db = self.ws.store.conn
        for ref in refs[1:]:
            table = {"tsk": "tasks", "dec": "decisions", "src": "sources"}[ref.split("-")[0]]
            (project,) = db.execute(f"SELECT project_id FROM {table} WHERE id = ?", (ref,)).fetchone()
            self.assertEqual(project, self.project_id)
        other = [r for r in db.execute("SELECT id FROM tasks WHERE project_id != ?", (self.project_id,))]
        for (task_id,) in other:
            self.assertNotIn(task_id, text)

    def test_a_changed_question_or_record_needs_a_new_preview(self):
        server = self.server()
        assistant = self.connect(server)
        preview = assistant.preview_project_question(self.project_id, self.QUESTION, TODAY)
        with self.assertRaises(AssistantError):
            self.ask(assistant, "What is blocking this?",
                     reviewed_prompt_sha256=preview["prompt_sha256"])
        self.assertEqual(server.requests, [])

    def test_identifiers_in_the_question_are_never_sent(self):
        server = self.server()
        result = self.ask(self.connect(server), "Should I email jane.doe@example.org first?")
        self.assertEqual(result["outcome"], "refused_data_rules")
        self.assertIn("EMAIL_ADDRESS", result["reason"])
        self.assertEqual(server.requests, [])

    def test_questions_are_checked(self):
        for question in ("", "   ", "x" * 501):
            with self.subTest(length=len(question)), self.assertRaises(AssistantError):
                self.ask(self.service(), question)
        with self.assertRaises(ManagerError):
            self.service().answer_project_question("prj-000000000000", self.QUESTION, TODAY, OWNER)
        with self.assertRaises(AssistantError):
            self.service().answer_project_question(self.project_id, self.QUESTION, TODAY,
                                                   "Someone Else")

    def test_the_model_may_say_the_records_do_not_answer(self):
        from nurse_manager.assistant import NO_ANSWER

        result = self.ask(self.connect(self.server(NO_ANSWER)))
        self.assertEqual((result["outcome"], result["answer"]), ("answered", NO_ANSWER))

    def test_a_preview_is_bound_to_the_model_it_named(self):
        first, second = self.server(), self.server()
        assistant = self.connect(first)
        preview = assistant.preview_project_question(self.project_id, self.QUESTION, TODAY)
        # Another tab switches the model's address after the manager reviewed the preview.
        assistant.connect_local(OWNER, "llama3.2", endpoint=second.endpoint)
        with self.assertRaises(AssistantError):
            self.ask(assistant, reviewed_prompt_sha256=preview["prompt_sha256"])
        brief_preview = self.connect(first).preview_weekly_brief(WEEK, TODAY)
        assistant.connect_local(OWNER, "mistral", endpoint=first.endpoint)
        with self.assertRaises(AssistantError):
            assistant.draft_weekly_brief(WEEK, TODAY, OWNER,
                                         reviewed_prompt_sha256=brief_preview["prompt_sha256"])
        self.assertEqual((first.requests, second.requests), ([], []))

    def test_an_answer_citing_other_records_is_not_shown(self):
        server = self.server(lambda body: "See `tsk-0123456789ab`.")
        result = self.ask(self.connect(server))
        self.assertEqual((result["outcome"], result["answer"]), ("output_refused", ""))
        self.assertIn("not sent to it", result["reason"])

    def test_project_questions_share_the_daily_limit(self):
        server = self.server()
        assistant = self.connect(server, daily_request_limit=1)
        self.assertEqual(self.draft(assistant)["outcome"], "drafted")
        self.assertEqual(self.ask(assistant)["outcome"], "refused_budget")
        self.assertEqual(len(server.requests), 1)


class LocalAdapterTests(unittest.TestCase):
    def test_the_local_adapter_costs_nothing(self):
        self.assertEqual(LocalModelProvider("m").estimate_cents("s", "p" * 10_000, 1200), 0)

    def test_a_reply_it_does_not_understand_is_a_failure(self):
        from nurse_manager.assistant import ProviderUnavailable

        server = FakeModelServer(reply=None)
        try:
            with self.assertRaises(ProviderUnavailable):
                LocalModelProvider("m", server.endpoint).complete(
                    "s", "p", max_output_tokens=10, timeout=5)
        finally:
            server.close()


class CliTests(unittest.TestCase):
    def test_the_headless_surface(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        ws = str(tmp / "ws")
        server = FakeModelServer(echo_rewrite)
        self.addCleanup(server.close)
        self.assertEqual(cli.run(["sample", ws])[0], 0)
        code, env = cli.run(["assistant", ws])
        self.assertEqual((code, env["data"]["provider"]), (0, "none"))
        code, env = cli.run(["assistant-local", ws, "--model", "llama3.2", "--by", OWNER,
                             "--endpoint", server.endpoint])
        self.assertEqual((code, env["data"]["provider"]), (0, "local"))
        code, env = cli.run(["assistant-brief", ws, "--week", WEEK, "--today", TODAY,
                             "--by", OWNER])
        self.assertEqual((code, env["data"]["outcome"]), (0, "drafted"))
        code, env = cli.run(["assistant-local", ws, "--model", "x", "--by", OWNER,
                             "--endpoint", "http://example.com"])
        self.assertEqual((code, env["error"]["type"]), (2, "AssistantError"))
        code, env = cli.run(["assistant-off", ws, "--by", OWNER])
        self.assertEqual((code, env["data"]["provider"]), (0, "none"))


if __name__ == "__main__":
    unittest.main()
