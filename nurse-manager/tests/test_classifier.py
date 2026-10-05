"""JEV as a classifier (ADR 0006): exit evidence for steps 4.5b and 4.9a–4.9e.

JEV advises and can only tighten. Off by default; connected only by the
manager, with their own key, which lives in the operating system's credential
store and nowhere else; every request passes the same gates as the AI model
and is bound to the preview the manager reviewed; and when JEV is off, unsure,
unreachable, or answers outside its contract, everything works as it does
without it.

JEV is exercised over real HTTP against a stand-in server on 127.0.0.1, so no
account or key is needed. The key used here is a throwaway string.
"""

import contextlib
import io
import json
import shutil
import socket
import socketserver
import sqlite3
import subprocess
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

import _bootstrap  # noqa: F401
from _bootstrap import fixed_clock

from nurse_manager import app as app_module
from nurse_manager import classifier, cli, credentials
from nurse_manager import store as store_module
from nurse_manager.actions import ActionBoundary, ActionError
from nurse_manager.assistant import AssistantService
from nurse_manager.brief import BriefService
from nurse_manager.classifier import (
    CONFIDENT,
    JEV_MODEL,
    REFUSALS,
    ROUTES,
    ClassifierError,
    ClassifierService,
    JevClient,
    JevDecisionAdapter,
    check_answers,
    check_endpoint,
)
from nurse_manager.control import AssistantControl, assistants_at_work
from nurse_manager.credentials import (
    KeyStoreUnavailable,
    MacKeychain,
    MemoryKeyStore,
    NoKeyStore,
    SecretToolStore,
)
from nurse_manager.decision_adapter import run_shadow
from nurse_manager.devhost import bind_values
from nurse_manager.sample import load_sample
from nurse_manager.services import ManagerWorkspace
from nurse_manager.store import MIGRATIONS_DIR
from nurse_manager.views import mission_control

WEEK = "2026-09-28"
TODAY = "2026-09-30"
OWNER = "me"
KEY = "ts-throwaway-test-key-0123456789"
ROUTE_REQUEST = "Draft a huddle message about the new hand hygiene audit"


def choice(options, pick, confidence=0.9):
    rest = (1 - 0.9) / (len(options) - 1)
    return {"type": "choice", "choice": pick, "confidence": confidence,
            "probabilities": {o: 0.9 if o == pick else rest for o in options}}


def default_answers(body):
    """A well-formed answer to every question: confident allow / first option,
    no refusal, and every item scored 'this week'."""
    answers = {}
    for qid, q in body["questions"].items():
        if q["type"] == "noul":
            answers[qid] = {"type": "noul", "noul": 0.02}
        elif q["type"] == "choice":
            answers[qid] = choice(list(q["criteria"]), list(q["criteria"])[0])
        else:
            answers[qid] = {"type": "score", "score": 2, "confidence": 0.8,
                            "legend": {str(i): c for i, c in enumerate(q["criteria"], start=1)},
                            "probabilities": {"1": 0.05, "2": 0.85, "3": 0.05, "4": 0.05}}
    return {"model": body["model"], "answers": answers,
            "usage": {"input_tokens": 50, "output_tokens": 0}}


class FakeJev:
    """A stand-in for TypeSafe's /v1/systemone on this computer."""

    def __init__(self, answer=default_answers, *, status=200, delay=0.0, raw=None,
                 redirect_to=None):
        self.requests: list[dict] = []
        self.answer = answer
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                sent = self.rfile.read(length)
                body = json.loads(sent)
                fake.requests.append({"path": self.path, "body": body, "raw": sent,
                                      "authorization": self.headers.get("Authorization")})
                if delay:
                    time.sleep(delay)
                if redirect_to:
                    self.send_response(307)
                    self.send_header("Location", redirect_to)
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                payload = raw if raw is not None else json.dumps(fake.answer(body)).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                try:
                    self.wfile.write(payload)
                except (BrokenPipeError, ConnectionResetError):
                    pass

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.httpd.server_port}/v1/systemone"

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


class FakeModel:
    """A stand-in local model that always says the records do not answer."""

    def __init__(self):
        self.requests: list[dict] = []
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                fake.requests.append(json.loads(self.rfile.read(length)))
                payload = json.dumps({"response": "The records do not answer this.",
                                      "done": True}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.httpd.server_port}"

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


class JevCase(unittest.TestCase):
    """A sample workspace, a stand-in JEV, and a memory key store."""

    answer = staticmethod(default_answers)

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.root = Path(self.tmp) / "ws"
        self.ws, _ = load_sample(self.root, clock=fixed_clock())
        self.addCleanup(self.ws.close)
        self.jev = FakeJev(self.answer)
        self.addCleanup(self.jev.close)
        self.keys = MemoryKeyStore()

    def service(self, ws=None, **kwargs):
        return ClassifierService(
            ws or self.ws, keystore=self.keys,
            client_factory=lambda key, model: JevClient(key, endpoint=self.jev.url, model=model),
            **kwargs)

    def connect(self, **jobs):
        svc = self.service()
        svc.connect(OWNER, KEY)
        svc.set_jobs(OWNER, {job: True for job in (jobs or dict.fromkeys(classifier.JOBS))})
        return svc

    def ledger(self):
        return self.ws.store.conn.execute(
            "SELECT * FROM classifier_requests ORDER BY created_at, id").fetchall()

    def project_id(self):
        return mission_control(self.ws, today=TODAY, week_of=WEEK)[
            "projects_in_motion"]["items"][0]["id"]

    def proposed_export(self, name="week.md"):
        briefs = BriefService(self.ws)
        revision = briefs.draft_weekly_brief(WEEK, TODAY)
        briefs.accept(revision.id, OWNER, revision.body_sha256)
        return ActionBoundary(self.ws).propose(
            "export_markdown", revision_id=revision.id, destination=name,
            purpose="Save the accepted weekly brief as a Markdown file", proposed_by=OWNER)


# -- the default posture -------------------------------------------------------


class DefaultPostureTests(JevCase):
    def test_a_new_workspace_has_jev_off_and_every_job_off(self):
        status = self.service().status()
        self.assertEqual(status["provider"], "none")
        self.assertEqual(status["model"], "")
        self.assertFalse(any(status["jobs"].values()))
        self.assertEqual(status["runs_on"], "nothing is connected")
        for preview in (self.service().preview_route(ROUTE_REQUEST),
                        self.service().preview_order(TODAY, WEEK)):
            self.assertFalse(preview["will_send"])
            self.assertEqual(preview["request"], "")
            self.assertIn("not connected", preview["reason"])

    def test_off_means_nothing_is_sent_and_nothing_is_recorded(self):
        result = self.service().route(ROUTE_REQUEST, OWNER, None)
        self.assertEqual((result["outcome"], result["suggested"]), ("not_connected", ""))
        self.assertEqual(self.jev.requests, [])
        self.assertEqual(self.ledger(), [])

    def test_connecting_turns_no_job_on(self):
        status = self.service().connect(OWNER, KEY)
        self.assertEqual((status["provider"], status["model"]), ("jev", JEV_MODEL))
        self.assertFalse(any(status["jobs"].values()))
        preview = self.service().preview_route(ROUTE_REQUEST)
        self.assertFalse(preview["will_send"])
        self.assertIn("off", preview["reason"])

    def test_no_job_can_be_turned_on_before_jev_is_connected(self):
        with self.assertRaises(ClassifierError):
            self.service().set_jobs(OWNER, {"routing": True})
        # The database refuses it too, even if the service is bypassed.
        with self.assertRaises(sqlite3.IntegrityError):
            with self.ws.store.transaction() as db:
                db.execute("INSERT INTO classifier_settings (workspace_id, provider, model,"
                           " job_routing, daily_request_limit, updated_by, updated_at)"
                           " VALUES (?, 'none', '', 1, 10, ?, ?)",
                           (self.ws.info.id, OWNER, self.ws.clock()))

    def test_only_the_manager_connects_changes_or_uses_jev(self):
        svc = self.service()
        for call in (lambda: svc.connect("Someone Else", KEY),
                     lambda: svc.disconnect("Someone Else"),
                     lambda: svc.set_jobs("Someone Else", {"routing": False}),
                     lambda: svc.route(ROUTE_REQUEST, "Someone Else", None)):
            with self.assertRaises(ClassifierError):
                call()
        self.assertEqual(self.keys.keys, {})

    def test_the_model_is_pinned_and_the_address_is_typesafes_own(self):
        self.assertNotIn("latest", JEV_MODEL)
        check_endpoint(classifier.JEV_ENDPOINT)
        for bad in ("http://api.typesafe.ai/v1/systemone", "https://example.com/v1/systemone",
                    "https://api.typesafe.ai.example.com/v1", "https://user:pw@api.typesafe.ai/v1",
                    "http://10.0.0.5/v1/systemone"):
            with self.subTest(endpoint=bad), self.assertRaises(ClassifierError):
                check_endpoint(bad)

    def test_the_default_key_store_is_never_the_test_store(self):
        self.assertNotIsInstance(credentials.default_keystore(), MemoryKeyStore)
        with self.assertRaises(KeyStoreUnavailable):
            NoKeyStore().set("jev-ws", KEY)


# -- the key -------------------------------------------------------------------


class KeyTests(JevCase):
    def test_the_key_is_kept_only_in_the_key_store(self):
        self.connect()
        self.service().route(ROUTE_REQUEST, OWNER,
                             self.service().preview_route(ROUTE_REQUEST)["request_sha256"])
        self.assertEqual(self.keys.keys, {f"jev-{self.ws.info.id}": KEY})
        self.ws.store.conn.commit()
        for path in self.root.iterdir():
            if path.is_file():
                self.assertNotIn(KEY.encode(), path.read_bytes(), path.name)
        for row in self.ws.store.events():
            self.assertNotIn(KEY, json.dumps(dict(row)))

    def test_the_key_is_sent_only_in_the_authorization_header(self):
        self.connect()
        preview = self.service().preview_route(ROUTE_REQUEST)
        self.assertNotIn(KEY, preview["request"])
        self.service().route(ROUTE_REQUEST, OWNER, preview["request_sha256"])
        sent = self.jev.requests[-1]
        self.assertEqual(sent["authorization"], f"Bearer {KEY}")
        self.assertNotIn(KEY, json.dumps(sent["body"]))
        self.assertNotIn(KEY, repr(JevClient(KEY)))

    def test_a_malformed_key_is_refused_without_repeating_it(self):
        for bad in ("short", "has spaces in the middle of it", 'quote"injection-0123456789',
                    "new\nline-0123456789abcdef"):
            with self.subTest(key=bad):
                with self.assertRaises(ClassifierError) as caught:
                    self.service().connect(OWNER, bad)
                self.assertNotIn(bad.strip(), str(caught.exception))
        self.assertEqual(self.keys.keys, {})
        self.assertEqual(self.service().status()["provider"], "none")

    def test_no_store_means_jev_stays_off(self):
        svc = ClassifierService(self.ws, keystore=NoKeyStore())
        with self.assertRaises(ClassifierError) as caught:
            svc.connect(OWNER, KEY)
        self.assertIn("credential store", str(caught.exception))
        self.assertEqual(svc.status()["provider"], "none")

    def test_disconnecting_removes_the_key_and_turns_every_job_off(self):
        self.connect()
        status = self.service().disconnect(OWNER)
        self.assertEqual(status["provider"], "none")
        self.assertFalse(any(status["jobs"].values()))
        self.assertEqual(self.keys.keys, {})

    def test_a_key_removed_from_the_store_fails_honestly(self):
        self.connect()
        self.keys.keys.clear()
        result = self.service().route(ROUTE_REQUEST, OWNER,
                                      self.service().preview_route(ROUTE_REQUEST)["request_sha256"])
        self.assertEqual(result["outcome"], "provider_failed")
        self.assertIn("Connect JEV again", result["reason"])
        self.assertEqual(self.jev.requests, [])

    def test_the_command_surface_never_takes_a_key_as_an_argument(self):
        root = str(self.root)
        printed = io.StringIO()
        with contextlib.redirect_stderr(printed):
            code, envelope = cli.run(["classifier-connect", root, "--by", OWNER,
                                      "--key-from", KEY])
        self.assertEqual(code, 2)
        self.assertNotIn(KEY, json.dumps(envelope))
        self.assertIn("never an argument", printed.getvalue())
        self.assertNotIn(KEY, printed.getvalue())
        with mock.patch.object(classifier, "default_keystore", return_value=self.keys):
            code, envelope = cli.run(["classifier-connect", root, "--by", OWNER, "--key-from",
                                      "stdin"], secret=KEY)
        self.assertTrue(envelope["ok"])
        self.assertNotIn(KEY, json.dumps(envelope))

    def test_the_app_hands_the_key_over_in_process_never_as_an_argument(self):
        argv = app_module._write_argv("classifier-connect", {"api_key": KEY}, self.root, OWNER)
        self.assertNotIn(KEY, " ".join(bind_values(argv)))
        self.assertIn("--key-from=stdin", bind_values(argv))
        self.assertIn("classifier-connect", app_module.WRITE_COMMANDS)


# -- the gates -------------------------------------------------------------------


class GateTests(JevCase):
    def test_what_is_sent_is_exactly_what_was_previewed(self):
        self.connect()
        preview = self.service().preview_route(ROUTE_REQUEST)
        self.assertTrue(preview["will_send"])
        self.assertEqual([c["gate"] for c in preview["checks"]], ["data_rules", "edena", "budget"])
        self.assertTrue(all(c["passed"] for c in preview["checks"]))
        self.service().route(ROUTE_REQUEST, OWNER, preview["request_sha256"])
        # Byte for byte: the preview's text is the body, not a re-serialization of it.
        self.assertEqual(self.jev.requests[-1]["raw"], preview["request"].encode("utf-8"))
        self.assertEqual(self.jev.requests[-1]["body"]["model"], JEV_MODEL)

    def test_a_changed_or_unreviewed_preview_sends_nothing(self):
        self.connect()
        for reviewed in (None, "0" * 64,
                         self.service().preview_route(ROUTE_REQUEST + " today")["request_sha256"]):
            with self.subTest(reviewed=reviewed), self.assertRaises(ClassifierError):
                self.service().route(ROUTE_REQUEST, OWNER, reviewed)
        self.assertEqual(self.jev.requests, [])

    def test_identifiers_are_refused_before_anything_is_sent(self):
        self.connect()
        request = "Email the educator at educator@example.org about the audit"
        preview = self.service().preview_route(request)
        self.assertFalse(preview["will_send"])
        result = self.service().route(request, OWNER, preview["request_sha256"])
        self.assertEqual(result["outcome"], "refused_data_rules")
        self.assertEqual(self.jev.requests, [])
        self.assertEqual(self.ledger()[-1]["outcome"], "refused_data_rules")

    def test_the_daily_limit_is_checked_before_sending(self):
        svc = self.service()
        svc.connect(OWNER, KEY, daily_request_limit=1)
        svc.set_jobs(OWNER, {"routing": True})
        first = svc.preview_route(ROUTE_REQUEST)
        self.assertEqual(svc.route(ROUTE_REQUEST, OWNER, first["request_sha256"])["outcome"],
                         "answered")
        second = svc.preview_route(ROUTE_REQUEST)
        self.assertFalse(second["will_send"])
        self.assertEqual(svc.route(ROUTE_REQUEST, OWNER, second["request_sha256"])["outcome"],
                         "refused_budget")
        self.assertEqual(len(self.jev.requests), 1)
        self.assertEqual(svc.status()["requests_today"], 1)

    def test_nothing_is_sent_while_assistants_are_stopped(self):
        self.connect()
        preview = self.service().preview_route(ROUTE_REQUEST)
        AssistantControl(self.ws).stop(OWNER)
        result = self.service().route(ROUTE_REQUEST, OWNER, preview["request_sha256"])
        self.assertEqual(result["outcome"], "refused_stopped")
        self.assertEqual(self.jev.requests, [])

    def test_the_ledger_never_holds_the_text(self):
        self.connect()
        preview = self.service().preview_route(ROUTE_REQUEST)
        self.service().route(ROUTE_REQUEST, OWNER, preview["request_sha256"])
        for row in self.ledger():
            self.assertNotIn("hygiene", json.dumps(dict(row)))
            self.assertEqual(row["state_sha256"], preview["request_sha256"])
        self.assertEqual(self.ledger()[-1]["input_tokens"], 50)

    def test_each_job_is_evaluated_by_edena_at_recommend(self):
        self.connect()
        for preview in (self.service().preview_route(ROUTE_REQUEST),
                        self.service().preview_order(TODAY, WEEK),
                        self.service().preview_refusal("What should I do first?")):
            edena = next(c for c in preview["checks"] if c["gate"] == "edena")
            self.assertTrue(edena["passed"], preview["job"])


# -- answers outside the contract -------------------------------------------------


class ContractTests(unittest.TestCase):
    QUESTIONS = {
        "decision": {"type": "choice", "criteria": {"allow": "", "require_human": "",
                                                    "deny": ""}},
        "yes": {"type": "noul"},
        "level": {"type": "score", "criteria": ["a", "b", "c", "d"]},
    }

    def good(self):
        return {"model": JEV_MODEL, "answers": {
            "decision": choice(["allow", "require_human", "deny"], "deny"),
            "yes": {"type": "noul", "noul": 0.3},
            "level": {"type": "score", "score": 3.2, "confidence": 0.7,
                      "probabilities": {"1": 0.1, "2": 0.1, "3": 0.5, "4": 0.3}},
        }, "usage": {"input_tokens": 12}}

    def test_a_well_formed_answer_is_used(self):
        answers, tokens = check_answers(self.QUESTIONS, self.good(), JEV_MODEL)
        self.assertEqual(answers["decision"]["choice"], "deny")
        self.assertAlmostEqual(answers["level"]["position"], (3.2 - 1) / 3)
        self.assertEqual(tokens, 12)

    def test_every_answer_outside_the_contract_is_refused(self):
        def changed(edit):
            reply = self.good()
            edit(reply)
            return reply

        cases = {
            "another model": lambda r: r.update(model="jev-latest"),
            "missing answer": lambda r: r["answers"].pop("yes"),
            "extra answer": lambda r: r["answers"].update(more={"type": "noul", "noul": 1}),
            "wrong type": lambda r: r["answers"]["yes"].update(type="choice"),
            "option not offered": lambda r: r["answers"]["decision"].update(choice="maybe"),
            "probabilities do not add up": lambda r: r["answers"]["decision"][
                "probabilities"].update(deny=0.2),
            "noul out of range": lambda r: r["answers"]["yes"].update(noul=1.5),
            "noul not a number": lambda r: r["answers"]["yes"].update(noul=True),
            "confidence missing": lambda r: r["answers"]["decision"].pop("confidence"),
            "score out of range": lambda r: r["answers"]["level"].update(score=9),
            "score levels missing": lambda r: r["answers"]["level"]["probabilities"].pop("4"),
            "not a number": lambda r: r["answers"]["decision"]["probabilities"].update(
                allow=float("nan")),
            "a number too large for a float": lambda r: r["answers"]["decision"].update(
                confidence=10 ** 400),
            "a choice that is not its most probable option": lambda r: r["answers"][
                "decision"].update(probabilities={"allow": 0.7, "require_human": 0.2,
                                                  "deny": 0.1}),
            "score levels not the ones asked": lambda r: r["answers"]["level"].update(
                probabilities={"-inf": 0.1, "0": 0.1, "1": 0.5, "inf": 0.3}),
            "score levels renumbered": lambda r: r["answers"]["level"].update(
                probabilities={"0": 0.1, "1": 0.1, "2": 0.5, "3": 0.3}),
        }
        for name, edit in cases.items():
            with self.subTest(case=name):
                self.assertIsInstance(check_answers(self.QUESTIONS, changed(edit), JEV_MODEL), str)

    def test_an_impossible_token_count_is_not_recorded(self):
        for tokens in (10 ** 400, 2 ** 63, -1, True, "12"):
            with self.subTest(tokens=tokens):
                reply = self.good()
                reply["usage"]["input_tokens"] = tokens
                self.assertIsNone(check_answers(self.QUESTIONS, reply, JEV_MODEL)[1])


class FailureTests(JevCase):
    def route_with(self, jev):
        self.jev.close()
        self.jev = jev
        self.addCleanup(jev.close)
        svc = self.connect()
        return svc.route(ROUTE_REQUEST, OWNER, svc.preview_route(ROUTE_REQUEST)["request_sha256"])

    def test_failures_change_nothing_and_say_why(self):
        cases = {
            "rejected key": (FakeJev(status=401), "provider_failed", "did not accept the key"),
            "rate limited": (FakeJev(status=429), "provider_failed", "rate limit"),
            "overloaded": (FakeJev(status=529), "provider_failed", "overloaded"),
            "redirected": (FakeJev(redirect_to="http://example.com/"), "provider_failed",
                           "answered 307"),
            "not JSON": (FakeJev(raw=b"<html>"), "provider_failed", "not understood"),
            "wrong model": (FakeJev(lambda b: {**default_answers(b), "model": "jev-latest"}),
                            "output_refused", "different model"),
        }
        for name, (jev, outcome, words) in cases.items():
            with self.subTest(case=name):
                result = self.route_with(jev)
                self.assertEqual(result["outcome"], outcome)
                self.assertEqual(result["suggested"], "")
                self.assertIn(words, result["reason"])
                self.assertIn("Choose where to go yourself", result["reason"])

    def test_a_reply_that_never_finishes_is_given_up_on_time(self):
        # Each byte comes within the read timeout, so only an overall deadline ends it.
        class Drip(socketserver.BaseRequestHandler):
            def handle(self):
                self.request.recv(65536)
                try:
                    for byte in b"HTTP/1.1 200 OK\r\n" * 100:
                        self.request.sendall(bytes([byte]))
                        time.sleep(0.05)
                except OSError:
                    pass

        server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), Drip)
        server.daemon_threads = True
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        self.connect()
        url = f"http://127.0.0.1:{server.server_address[1]}/v1/systemone"
        svc = ClassifierService(
            self.ws, keystore=self.keys, timeout=0.5, stop_poll=0.05,
            client_factory=lambda key, model: JevClient(key, endpoint=url, model=model))
        started = time.monotonic()
        result = svc.route(ROUTE_REQUEST, OWNER, svc.preview_route(ROUTE_REQUEST)["request_sha256"])
        self.assertLess(time.monotonic() - started, 3)
        self.assertEqual((result["outcome"], result["suggested"]), ("provider_failed", ""))
        self.assertIn("did not reply in time", result["reason"])
        self.assertIsNotNone(self.ledger()[-1]["finished_at"])

    def test_the_last_request_of_the_day_is_taken_once(self):
        # Two requests passed the preview's limit check at once; the one that
        # comes second to the write is refused there, and nothing is sent.
        svc = self.connect()
        svc.connect(OWNER, KEY, daily_request_limit=1)
        svc.set_jobs(OWNER, dict.fromkeys(classifier.JOBS, True))
        sha = svc.preview_route(ROUTE_REQUEST)["request_sha256"]
        counts = iter([0, 1])  # the gate saw none sent; by the write, another had been
        with mock.patch.object(ClassifierService, "_sent_since",
                               side_effect=lambda _day: next(counts)):
            result = svc.route(ROUTE_REQUEST, OWNER, sha)
        self.assertEqual(result["outcome"], "refused_budget")
        self.assertEqual(self.jev.requests, [])

    def test_a_dead_first_address_falls_through_to_the_next(self):
        # As when an IPv6 address has no route: the next address is tried.
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            dead = probe.getsockname()[1]  # closed again before it is tried
        port = int(self.jev.url.split(":")[2].split("/")[0])
        real = socket.getaddrinfo

        def both(host, _port, *args, **kwargs):
            return ([(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", dead))]
                    + real(host, port, *args, **kwargs))
        svc = self.connect()
        with mock.patch.object(classifier.socket, "getaddrinfo", side_effect=both):
            result = svc.route(ROUTE_REQUEST, OWNER,
                               svc.preview_route(ROUTE_REQUEST)["request_sha256"])
        self.assertEqual(result["outcome"], "answered")
        self.assertEqual(len(self.jev.requests), 1)

    def test_an_unreachable_jev_changes_nothing(self):
        self.jev.close()
        svc = self.connect()
        result = svc.route(ROUTE_REQUEST, OWNER, svc.preview_route(ROUTE_REQUEST)["request_sha256"])
        self.assertEqual((result["outcome"], result["suggested"]), ("provider_failed", ""))
        self.assertEqual(self.ledger()[-1]["outcome"], "provider_failed")


# -- 1. action review --------------------------------------------------------------


def suggests(pick, confidence):
    def answer(body):
        reply = default_answers(body)
        reply["answers"]["decision"] = choice(list(body["questions"]["decision"]["criteria"]),
                                              pick, confidence)
        return reply
    return answer


class ActionReviewTests(JevCase):
    def review(self, answer):
        self.jev.answer = answer
        svc = self.connect()
        action = self.proposed_export()
        preview = svc.preview_action(action.id)
        self.assertTrue(preview["will_send"])
        return svc, action, svc.review_action(action.id, OWNER, preview["request_sha256"])

    def approve(self, action):
        return ActionBoundary(self.ws).approve(action.id, OWNER, seen_sha256=action.payload_sha256,
                                               seen_destination=action.destination)

    def test_a_confident_stricter_suggestion_holds_the_approval_until_acknowledged(self):
        svc, action, result = self.review(suggests("deny", 0.9))
        self.assertEqual((result["suggestion"], result["core_decision"], result["hold"]),
                         ("deny", "require_human", True))
        with self.assertRaises(ActionError) as caught:
            self.approve(action)
        self.assertIn("acknowledge", str(caught.exception))
        self.assertEqual(ActionBoundary(self.ws).get(action.id).status, "awaiting_approval")
        acknowledged = svc.acknowledge(action.id, OWNER)
        self.assertTrue(acknowledged["acknowledged"])
        self.assertEqual(self.approve(action).status, "approved")

    def test_jev_never_changes_the_policy_decision(self):
        _svc, action, _result = self.review(suggests("deny", 0.99))
        after = ActionBoundary(self.ws).get(action.id)
        self.assertEqual((after.policy_decision, after.policy_reasons, after.tier),
                         (action.policy_decision, action.policy_reasons, action.tier))

    def test_an_unsure_or_less_strict_suggestion_changes_nothing(self):
        for name, answer in (("stricter but unsure", suggests("deny", CONFIDENT - 0.01)),
                             ("less strict", suggests("allow", 0.99)),
                             ("the same", suggests("require_human", 0.99))):
            with self.subTest(case=name):
                self.setUp()
                _svc, action, result = self.review(answer)
                self.assertFalse(result["hold"])
                self.assertEqual(self.approve(action).status, "approved")

    def test_turning_jev_off_while_it_works_means_its_answer_is_not_used(self):
        svc = self.connect()
        action = self.proposed_export()
        preview = svc.preview_action(action.id)

        def answer(body):
            other = ManagerWorkspace(self.root, clock=fixed_clock())
            try:
                self.service(other).disconnect(OWNER)
            finally:
                other.close()
            return suggests("deny", 0.95)(body)
        self.jev.answer = answer
        result = svc.review_action(action.id, OWNER, preview["request_sha256"])
        self.assertEqual((result["outcome"], result["hold"]), ("stopped", False))
        self.assertIn("turned off while JEV worked", result["reason"])
        self.assertIsNone(svc.action_classification(action.id))
        self.assertEqual(self.ledger()[-1]["outcome"], "stopped")

    def test_jev_never_approves_anything(self):
        _svc, action, _result = self.review(suggests("allow", 1.0))
        self.assertEqual(ActionBoundary(self.ws).get(action.id).status, "awaiting_approval")
        self.assertEqual(self.ws.store.conn.execute(
            "SELECT count(*) FROM approvals WHERE action_id = ?", (action.id,)).fetchone()[0], 0)

    def test_an_action_is_reviewed_once_and_only_while_it_waits(self):
        svc, action, _result = self.review(suggests("require_human", 0.9))
        with self.assertRaises(ClassifierError):
            svc.review_action(action.id, OWNER, "0" * 64)
        self.approve(action)
        later = self.proposed_export("later.md")
        self.approve(later)
        self.assertFalse(svc.preview_action(later.id)["will_send"])

    def test_only_a_hold_can_be_acknowledged_and_only_once_by_the_manager(self):
        svc, action, _result = self.review(suggests("deny", 0.9))
        with self.assertRaises(ClassifierError):
            svc.acknowledge(action.id, "Someone Else")
        svc.acknowledge(action.id, OWNER)
        with self.assertRaises(ClassifierError):
            svc.acknowledge(action.id, OWNER)
        self.setUp()
        svc, action, _result = self.review(suggests("allow", 0.9))
        with self.assertRaises(ClassifierError):
            svc.acknowledge(action.id, OWNER)


# -- 2. refusal check -----------------------------------------------------------------


def refuses(category, yes=0.95):
    def answer(body):
        reply = default_answers(body)
        if category in reply["answers"]:
            reply["answers"][category] = {"type": "noul", "noul": yes}
        return reply
    return answer


class RefusalCheckTests(JevCase):
    def setUp(self):
        super().setUp()
        self.model = FakeModel()
        self.addCleanup(self.model.close)

    def assistant(self, *, refusal_check=True):
        svc = self.service()
        svc.connect(OWNER, KEY)
        svc.set_jobs(OWNER, {"refusal_check": refusal_check})
        assistant = AssistantService(self.ws, classifier=self.service())
        assistant.connect_local(OWNER, "llama3.2", endpoint=self.model.url)
        return assistant

    def ask(self, assistant, question, *, classifier_sha="from-preview"):
        project = self.project_id()
        preview = assistant.preview_project_question(project, question, TODAY)
        if classifier_sha == "from-preview":
            classifier_sha = preview["classifier"]["request_sha256"] or None
        return preview, assistant.answer_project_question(
            project, question, TODAY, OWNER, reviewed_prompt_sha256=preview["prompt_sha256"],
            reviewed_classifier_sha256=classifier_sha)

    def test_a_confident_refusal_stops_the_question_before_the_model(self):
        for category in REFUSALS:
            with self.subTest(category=category):
                self.setUp()
                self.jev.answer = refuses(category)
                preview, result = self.ask(self.assistant(), "Which of my nurses should I rank last?")
                self.assertTrue(preview["classifier"]["will_send"])
                self.assertEqual(result["outcome"], "refused_intake")
                self.assertEqual(result["refusal"]["category"], category)
                self.assertTrue(result["refusal"]["nearest_path"])
                self.assertEqual(self.model.requests, [])
                self.assertEqual(self.ledger()[-1]["result"], f"refused:{category}")

    def test_a_clear_question_goes_on_to_the_model(self):
        _preview, result = self.ask(self.assistant(), "What should I do first?")
        self.assertEqual((result["outcome"], result["refusal"]), ("answered", None))
        self.assertEqual(len(self.model.requests), 1)
        self.assertEqual(self.ledger()[-1]["result"], "clear")
        self.assertIn("found nothing to refuse", result["classifier_note"])

    def test_an_unsure_check_refuses_nothing_and_says_so(self):
        self.jev.answer = refuses("staff_performance", CONFIDENT - 0.01)
        _preview, result = self.ask(self.assistant(), "What should I do first?")
        self.assertEqual(result["outcome"], "answered")
        self.assertIn("not sure", result["classifier_note"])
        self.assertIn("an individual's performance or conduct", result["classifier_note"])

    def test_an_unavailable_jev_lets_the_question_go_on_and_says_so(self):
        self.jev.close()
        _preview, result = self.ask(self.assistant(), "What should I do first?")
        self.assertEqual(result["outcome"], "answered")
        self.assertEqual(len(self.model.requests), 1)
        self.assertIn("went on without JEV's check", result["classifier_note"])

    def test_with_the_check_off_jev_is_not_asked(self):
        preview, result = self.ask(self.assistant(refusal_check=False), "What should I do first?")
        self.assertFalse(preview["classifier"]["will_send"])
        self.assertEqual((result["outcome"], result["classifier_note"]), ("answered", ""))
        self.assertEqual(self.jev.requests, [])

    def test_a_stop_while_jev_checks_says_jev_had_the_question(self):
        self.jev.close()
        self.jev = FakeJev(delay=2.0)
        self.addCleanup(self.jev.close)
        assistant = self.assistant()
        project, question = self.project_id(), "What should I do first?"
        preview = assistant.preview_project_question(project, question, TODAY)
        result: dict = {}

        def work():
            ws = ManagerWorkspace(self.root, clock=fixed_clock())
            try:
                mine = AssistantService(ws, classifier=self.service(ws, stop_poll=0.05))
                result.update(mine.answer_project_question(
                    project, question, TODAY, OWNER,
                    reviewed_prompt_sha256=preview["prompt_sha256"],
                    reviewed_classifier_sha256=preview["classifier"]["request_sha256"]))
            finally:
                ws.close()
        worker = threading.Thread(target=work, daemon=True)
        worker.start()
        deadline = time.monotonic() + 2
        while not self.jev.requests and time.monotonic() < deadline:
            time.sleep(0.02)
        other = ManagerWorkspace(self.root, clock=fixed_clock())
        self.addCleanup(other.close)
        AssistantControl(other).stop(OWNER)
        worker.join(5)
        self.assertEqual((len(self.jev.requests), len(self.model.requests)), (1, 0))
        self.assertEqual(result["outcome"], "stopped")
        self.assertIn("while JEV was working", result["reason"])
        self.assertIn("Nothing went to the AI model", result["reason"])
        self.assertNotIn("Nothing was sent", result["reason"])

    def test_the_check_must_be_reviewed_too(self):
        with self.assertRaises(ClassifierError):
            self.ask(self.assistant(), "What should I do first?", classifier_sha=None)
        self.assertEqual((self.jev.requests, self.model.requests), ([], []))

    def test_jev_is_asked_only_when_the_question_would_reach_a_model(self):
        svc = self.service()
        svc.connect(OWNER, KEY)
        svc.set_jobs(OWNER, {"refusal_check": True})
        assistant = AssistantService(self.ws, classifier=self.service())  # no model connected
        preview = assistant.preview_project_question(self.project_id(), "What first?", TODAY)
        self.assertFalse(preview["classifier"]["will_send"])
        result = assistant.answer_project_question(self.project_id(), "What first?", TODAY, OWNER)
        self.assertEqual(result["outcome"], "no_model")
        self.assertEqual(self.jev.requests, [])


# -- 3. routing -------------------------------------------------------------------------


class RoutingTests(JevCase):
    def route(self, answer):
        self.jev.answer = answer
        svc = self.connect()
        return svc.route(ROUTE_REQUEST, OWNER, svc.preview_route(ROUTE_REQUEST)["request_sha256"])

    def test_a_confident_suggestion_names_a_place_and_starts_nothing(self):
        def pick(body):
            reply = default_answers(body)
            reply["answers"]["route"] = choice(list(ROUTES), "pack_communication", 0.9)
            return reply
        before = self.ws.store.conn.execute("SELECT count(*) FROM artifacts").fetchone()[0]
        result = self.route(pick)
        self.assertEqual((result["suggested"], result["label"]),
                         ("pack_communication", "Communication pack"))
        self.assertEqual([a["route"] for a in result["alternatives"]], list(ROUTES))
        self.assertEqual(self.ws.store.conn.execute(
            "SELECT count(*) FROM artifacts").fetchone()[0], before)

    def test_an_unsure_answer_suggests_nothing(self):
        def unsure(body):
            reply = default_answers(body)
            reply["answers"]["route"] = choice(list(ROUTES), "library", 0.3)
            return reply
        result = self.route(unsure)
        self.assertEqual((result["outcome"], result["suggested"]), ("answered", ""))
        self.assertIn("not sure", result["reason"])
        self.assertEqual(self.ledger()[-1]["result"], "unsure:library")

    def test_the_request_text_is_never_stored(self):
        self.route(default_answers)
        self.ws.store.conn.commit()
        self.assertNotIn(b"hand hygiene", (self.root / "workspace.sqlite").read_bytes())


# -- 4. attention order -------------------------------------------------------------------


class AttentionTests(JevCase):
    def setUp(self):
        super().setUp()
        self.proposed_export()  # one approval waiting, besides the sample's decisions

    def items(self):
        return [i["id"] for i in mission_control(self.ws, today=TODAY, week_of=WEEK)[
            "needs_my_judgment"]["items"]]

    def order(self, answer):
        self.jev.answer = answer
        svc = self.connect()
        return svc.order(TODAY, WEEK, OWNER, svc.preview_order(TODAY, WEEK)["request_sha256"])

    def test_a_suggested_order_keeps_every_item_and_shows_no_score(self):
        def last_first(body):
            reply = default_answers(body)
            n = len(body["questions"])
            for i in range(1, n + 1):
                reply["answers"][f"item_{i}"]["score"] = 4 if i == n else 1
            return reply
        items = self.items()
        result = self.order(last_first)
        self.assertEqual(sorted(result["order"]), sorted(items))
        self.assertEqual(result["order"][0], items[-1])
        self.assertTrue(result["reordered"])
        self.assertFalse({"score", "scores", "position", "confidence"} & set(result))

    def test_an_unsure_answer_keeps_the_usual_order(self):
        def unsure(body):
            reply = default_answers(body)
            for answer in reply["answers"].values():
                answer["confidence"] = 0.2
            return reply
        result = self.order(unsure)
        self.assertEqual((result["order"], result["reordered"]), (self.items(), False))
        self.assertIn("not sure", result["reason"])

    def test_no_owner_names_are_sent(self):
        self.order(default_answers)
        sent = json.dumps(self.jev.requests[-1]["body"])
        for row in self.ws.store.conn.execute("SELECT DISTINCT owner FROM tasks"):
            self.assertNotIn(f'"{row["owner"]}"', sent)


# -- the stop control -----------------------------------------------------------------------


class StopTests(JevCase):
    def test_a_stop_during_a_slow_lookup_returns_at_once_and_sends_nothing(self):
        real = socket.getaddrinfo

        def slow(*args, **kwargs):
            time.sleep(3)
            return real(*args, **kwargs)

        def stop_soon():
            time.sleep(0.3)
            other = ManagerWorkspace(self.root, clock=fixed_clock())
            try:
                AssistantControl(other).stop(OWNER)
            finally:
                other.close()
        svc = self.service(stop_poll=0.05)
        self.connect()
        sha = svc.preview_route(ROUTE_REQUEST)["request_sha256"]
        threading.Thread(target=stop_soon, daemon=True).start()
        started = time.monotonic()
        with mock.patch.object(classifier.socket, "getaddrinfo", side_effect=slow):
            result = svc.route(ROUTE_REQUEST, OWNER, sha)
        self.assertLess(time.monotonic() - started, 1.5)
        self.assertEqual(result["outcome"], "refused_stopped")
        self.assertEqual(self.jev.requests, [])

    def test_a_stop_abandons_a_request_and_discards_its_answer(self):
        self.jev.close()
        self.jev = FakeJev(delay=3.0)
        self.addCleanup(self.jev.close)
        svc = self.connect()
        preview = svc.preview_route(ROUTE_REQUEST)
        result: dict = {}

        def work():
            # Its own connection, as each request to the app has.
            ws = ManagerWorkspace(self.root, clock=fixed_clock())
            try:
                result.update(self.service(ws, stop_poll=0.05).route(
                    ROUTE_REQUEST, OWNER, preview["request_sha256"]))
            finally:
                ws.close()
        worker = threading.Thread(target=work, daemon=True)
        worker.start()
        other = ManagerWorkspace(self.root, clock=fixed_clock())
        self.addCleanup(other.close)
        deadline = time.monotonic() + 2
        while not assistants_at_work(other)["items"] and time.monotonic() < deadline:
            time.sleep(0.02)
        working = assistants_at_work(other)["items"]
        self.assertTrue(any(item["id"].startswith("clr-") for item in working))
        started = time.monotonic()
        AssistantControl(other).stop(OWNER)
        worker.join(5)
        self.assertLess(time.monotonic() - started, 1.5)
        self.assertEqual((result["outcome"], result["suggested"]), ("stopped", ""))


# -- the credential stores -------------------------------------------------------------------


class CredentialStoreTests(unittest.TestCase):
    def run_recorder(self, returncodes=None):
        calls = []
        codes = iter(returncodes or [])

        def fake_run(argv, *, input=None, **_kwargs):  # noqa: A002
            calls.append((argv, input))
            code = next(codes, 0)
            stdout = KEY if "find-generic-password" in argv or "lookup" in argv else ""
            return subprocess.CompletedProcess(argv, code, stdout, "")
        return calls, fake_run

    def test_the_keychain_gets_the_key_on_standard_input_only(self):
        calls, fake_run = self.run_recorder()
        with mock.patch.object(credentials.subprocess, "run", side_effect=fake_run):
            MacKeychain().set("jev-ws-0123", KEY)
        (argv, stdin), *_rest = calls
        self.assertEqual(argv, ["/usr/bin/security", "-i"])
        self.assertIn(KEY, stdin)
        self.assertTrue(all(KEY not in " ".join(a) for a, _ in calls))

    def test_the_system_keyring_gets_the_key_on_standard_input_only(self):
        calls, fake_run = self.run_recorder()
        with mock.patch.object(SecretToolStore, "_find", return_value="/usr/bin/secret-tool"), \
                mock.patch.object(credentials.subprocess, "run", side_effect=fake_run):
            SecretToolStore().set("jev-ws-0123", KEY)
        store_argv, stdin = calls[0]
        self.assertEqual(store_argv[1], "store")
        self.assertEqual(stdin, KEY)
        self.assertTrue(all(KEY not in " ".join(a) for a, _ in calls))

    def test_the_keyring_program_is_never_found_through_path(self):
        with tempfile.TemporaryDirectory() as planted:
            fake = Path(planted) / "secret-tool"
            fake.write_text("#!/bin/sh\ncat > /dev/null\n")
            fake.chmod(0o755)
            with mock.patch.dict(credentials.os.environ, {"PATH": planted}):
                found = SecretToolStore()._find()
        self.assertIn(found, (None, *SecretToolStore.TOOLS))
        self.assertTrue(all(Path(t).is_absolute() for t in SecretToolStore.TOOLS))

    def test_a_key_typed_at_a_terminal_is_not_shown(self):
        with mock.patch.object(cli.sys.stdin, "isatty", return_value=True), \
                mock.patch.object(cli.getpass, "getpass", return_value=KEY) as hidden:
            self.assertEqual(cli._read_key(), KEY)
        hidden.assert_called_once()

    def test_a_store_that_did_not_keep_the_key_is_an_error(self):
        _calls, fake_run = self.run_recorder([1])
        with mock.patch.object(credentials.subprocess, "run", side_effect=fake_run), \
                self.assertRaises(KeyStoreUnavailable):
            MacKeychain().set("jev-ws-0123", KEY)

    def test_accounts_and_keys_cannot_carry_quotes_or_newlines(self):
        for account, secret in (('ws"; rm', KEY), ("jev-ws", 'abc"def-0123456789'),
                                ("jev-ws", "abc\ndef-0123456789"), ("jev ws", KEY)):
            with self.subTest(account=account, secret=secret), self.assertRaises(ValueError):
                MemoryKeyStore().set(account, secret)


# -- the migration --------------------------------------------------------------------------


class MigrationTests(unittest.TestCase):
    def test_upgrading_keeps_every_record_and_starts_with_jev_off(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            old_dir = tmp / "migrations-before-classifier"
            old_dir.mkdir()
            for path in MIGRATIONS_DIR.glob("*.sql"):
                # The sample's current writer needs task transitions. This
                # fixture is genuinely pre-classifier, with task history;
                # separate integration tests cover upstream without history.
                if path.stem < "0014" or path.stem == "0014_task_transitions":
                    shutil.copy(path, old_dir / path.name)
            with mock.patch.object(store_module, "MIGRATIONS_DIR", old_dir):
                old, _ = load_sample(tmp / "ws", clock=fixed_clock())
                self.assertIsNone(old.store.conn.execute(
                    "SELECT 1 FROM sqlite_master WHERE name = 'classifier_settings'").fetchone())
                counts = {t: old.store.conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
                          for t in ("tasks", "projects", "event_log", "assistant_requests")}
                old.close()
            new = ManagerWorkspace(tmp / "ws", clock=fixed_clock())
            try:
                self.assertEqual(new.store.schema_version,
                                 max(f.stem for f in MIGRATIONS_DIR.glob("*.sql")))
                for table, n in counts.items():
                    self.assertGreaterEqual(
                        new.store.conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0], n)
                self.assertEqual(ClassifierService(new, keystore=MemoryKeyStore()).status()[
                    "provider"], "none")
                self.assertTrue(any(tmp.joinpath("ws", "backups").iterdir()))
            finally:
                new.close()


# -- the shadow harness (step 4.5b) -----------------------------------------------------------


class ShadowAdapterTests(unittest.TestCase):
    def test_the_live_adapter_runs_on_the_pinned_synthetic_set_and_decides_nothing(self):
        jev = FakeJev(suggests("allow", 0.95))
        self.addCleanup(jev.close)
        report = run_shadow(JevDecisionAdapter(JevClient(KEY, endpoint=jev.url)))
        self.assertTrue(jev.requests)
        for sent in jev.requests:
            self.assertEqual(set(sent["body"]["questions"]["decision"]["criteria"]),
                             {"allow", "require_human", "deny"})
        # Always "allow" is less strict than every hold and denial, and the
        # report names those cases rather than trusting the adapter.
        self.assertTrue(report["less_strict"])


if __name__ == "__main__":
    unittest.main()
