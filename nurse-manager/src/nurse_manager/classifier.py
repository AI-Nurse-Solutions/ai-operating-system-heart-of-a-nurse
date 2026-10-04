"""JEV as a classifier (ADR 0006): it advises, and it can only tighten.

JEV is TypeSafe AI's "System One" model. It does not write text. It answers
typed questions about a piece of text: yes or no (a *noul*, the probability
of yes), a *choice* among named options, or a *score* on described levels,
each with probabilities and a confidence. It is fast and costs very little,
so it suits small decisions. In the Manager Edition it has four jobs. Each
is off until the manager turns it on:

1. **Action review.** Beside the policy's decision on a proposed action,
   JEV suggests allow, hold for review, or deny. If it is confident its
   suggestion is stricter than the policy's, the approval is held until
   the manager acknowledges the suggestion. It never changes the policy's
   decision, never approves anything, and never lowers a tier.
2. **Refusal check.** Before a question about a project goes to the AI
   model, JEV checks it against the refusal categories. A confident "yes"
   refuses the question, and nothing goes to the model.
3. **Routing.** JEV suggests which part of the workspace a typed request
   belongs to. The manager follows the link or chooses another; nothing
   starts by itself.
4. **Attention order.** JEV suggests an order for "Needs my judgment". No
   score is ever shown, nothing is hidden, and the usual order is kept
   whenever JEV is not sure.

Every request passes the same gates as the AI model (ADR 0004):

* The manager connects JEV explicitly, with their own key. It is never
  preselected and never read from an environment variable. The key lives
  in the operating system's credential store, never in the workspace.
* Only text the workspace's data rules admit is sent. It is screened again
  first, and the privacy screen does not detect names.
* The EDENA engine decides, at ``recommend``, whether an assistant may do
  this at all.
* A daily request limit is checked before anything is sent.
* The manager sees exactly what will be sent, and the request is bound to
  that preview by its hash.
* While assistants are stopped, nothing is sent; a request on its way is
  abandoned and its answer discarded.
* When JEV is off, unsure, unreachable, or answers outside its contract,
  everything works as it does without JEV, and the manager is told why.
  Nothing switches to another service.

The ledger keeps metadata only: hashes, outcomes, the result as a fixed key
(an option, a category, a route), and a confidence. Never the text.
"""

from __future__ import annotations

import http.client
import json
import math
import socket
import ssl
import threading
import time
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol

from ._naio import (
    ActionMode,
    Actor,
    DataClass,
    DataZone,
    Decision,
    EdenaPolicyEngine,
    GatewayRequest,
    RiskTier,
    edena_engine,
)
from .actions import DEFAULT_PROFILE_POLICY, ActionBoundary
from .brief import BriefService, sha256_text
from .control import AssistantControl
from .credentials import SECRET, KeyStore, KeyStoreUnavailable, default_keystore
from .decision_adapter import OPTIONS, STRICTNESS, Choice
from .services import ManagerError, ManagerWorkspace
from .store import new_id

# The one address and the one model. Neither is a setting: changing either is
# a reviewed code change (ADR 0006). The model is pinned, never "jev-latest",
# so a model change at TypeSafe cannot silently change what JEV does here.
JEV_ENDPOINT = "https://api.typesafe.ai/v1/systemone"
JEV_HOST = "api.typesafe.ai"
JEV_MODEL = "jev-1.13.0"
PROVIDER = "jev"
RUNS_ON = "TypeSafe AI's servers in the United States"

JOBS = ("action_review", "refusal_check", "routing", "attention")
JOB_TITLES = {
    "action_review": "Reviewing a proposed action with JEV",
    "refusal_check": "Checking a question with JEV before the AI model sees it",
    "routing": "Suggesting where a request belongs, with JEV",
    "attention": "Suggesting an order for what needs your judgment, with JEV",
}
JOB_NAMES = {
    "action_review": "action review",
    "refusal_check": "refusal check",
    "routing": "routing",
    "attention": "attention order",
}
# The EDENA intent each job is evaluated under, at recommend.
INTENTS = {
    "action_review": "classify_proposed_action",
    "refusal_check": "check_request_scope",
    "routing": "route_request",
    "attention": "order_attention",
}

DEFAULT_DAILY_LIMIT = 200
MAX_DAILY_LIMIT = 2000
# How sure JEV must be before its answer changes anything. Holds and
# refusals need CONFIDENT; a suggested route or order needs SUGGEST, because
# the manager always confirms those. Below them, nothing changes.
CONFIDENT = 0.8
SUGGEST = 0.5
REQUEST_TIMEOUT_SECONDS = 15.0
CONNECT_TIMEOUT_SECONDS = 5.0
STOP_POLL_SECONDS = 0.5
MAX_RESPONSE_BYTES = 64 * 1024
MAX_REQUEST_CHARS = 500
MAX_ORDER_ITEMS = 30
_TOLERANCE = 0.02

# Requests that reached JEV count against the daily limit.
_SENT = ("answered", "provider_failed", "output_refused", "stopped")

STOPPED_BEFORE = ("refused_stopped", "Nothing was sent: assistants are stopped. Let them work"
                  " again from Mission Control first.")
STOPPED_DURING = ("stopped", "You stopped assistants while JEV was working, so its answer"
                  " was discarded.")

WHAT_IT_DOES = (
    "Suggests whether a proposed action should be allowed, held for your review, or denied."
    " A confident stricter suggestion holds the approval until you acknowledge it.",
    "Checks a question for patient, staff-performance, confidential, clinical, or"
    " named-person content before the AI model sees it, and refuses it if JEV is confident.",
    "Suggests where in this workspace a request you type belongs. You choose.",
    "Suggests an order for what needs your judgment. You keep your own order a click away.",
)
NEVER_DOES = (
    "It never writes text, drafts, or answers.",
    "It never approves, sends, or exports anything, and never lowers a tier.",
    "It never changes the policy's decision, and never removes a review step.",
    "It never sees anything you have not previewed, and never sees patient or employee"
    " information: the data rules refuse it first.",
)
GATES = (
    "Only material your workspace's data rules admit is sent, and it is checked again first."
    " The check cannot detect names.",
    "The EDENA policy decides whether an assistant may do this; assistants only recommend.",
    "A daily request limit is checked before anything is sent.",
    "You see exactly what will be sent, and the request is bound to that preview.",
    "If JEV is off, unsure, or unavailable, everything works as it does without it, and you"
    " are told why. Nothing goes to any other service.",
)
# TypeSafe's terms as read on 2026-10-04 (docs.typesafe.ai/legal; the privacy
# policy dated 19 Nov 2025; the Master Customer Agreement). Facts, not claims.
TERMS = (
    "TypeSafe says it does not train or fine-tune models on what you send.",
    "It keeps what you send for as long as it says is reasonably necessary to provide the"
    " service; no fixed period is stated. Zero retention is offered to enterprise customers"
    " only.",
    "It is hosted in the United States.",
    "It offers no business associate agreement (BAA). That is one more reason only your own"
    " planning material is ever sent.",
    "Its terms say its output may be wrong and that you are responsible for evaluating it.",
    "JEV is in early access: you need your own key from TypeSafe.",
)

# -- the questions JEV is asked ---------------------------------------------

ACTION_OPTIONS = {
    "allow": "The action is routine and within the policy: it can go ahead.",
    "require_human": "The action needs the manager's own review before it happens.",
    "deny": "The action should not happen in a Personal Manager workspace.",
}
OPTION_LABELS = {"allow": "allowed", "require_human": "held for your review", "deny": "denied"}
_CORE_TO_OPTION = {"allow": "allow", "require_approval": "require_human", "deny": "deny"}

# Refusal categories: (the yes/no question, the label, the nearest permitted path).
REFUSALS = {
    "patient_information": (
        "Does the request mention or describe an identifiable patient, or tell a patient's"
        " story in enough detail that someone could recognize them?",
        "patient information",
        "Ask about the process, the unit's pattern, or the policy instead, without describing"
        " any patient.",
    ),
    "staff_performance": (
        "Does the request concern an identifiable staff member's performance, conduct,"
        " discipline, or attendance?",
        "an individual's performance or conduct",
        "Use your organization's own process for an individual. Here, ask about team-level"
        " supports, expectations, or the process.",
    ),
    "employer_confidential": (
        "Does the request include employer- or vendor-confidential material, such as"
        " contract terms, unreleased plans, or internal financial figures?",
        "confidential employer material",
        "Confidential material needs an organization workspace. Ask without it.",
    ),
    "clinical_decision": (
        "Does the request ask for a diagnosis, a treatment, a dose, or another decision about"
        " a patient's care?",
        "a clinical decision",
        "Clinical decisions belong to the licensed clinician and your organization's clinical"
        " resources. Nurse AI OS is not a clinical tool.",
    ),
    "named_person_judgment": (
        "Does the request ask to decide about, score, rank, or judge a named person?",
        "a judgment about a named person",
        "Ask about roles, criteria, or the process instead of a named person.",
    ),
}

# Where a request can go: (what JEV is told, the label the manager sees).
ROUTES = {
    "weekly_brief": ("Prepare, review, or accept this week's manager brief.",
                     "Weekly brief"),
    "project_question": ("Think through one project using its own records.",
                         "A project's dashboard: Think with this project"),
    "pack_education": ("Start a document for staff education: an education plan, a"
                       " competency checklist, or a case study.", "Education pack"),
    "pack_committee": ("Prepare for a committee: an agenda pack, minutes, a brief, or a"
                       " policy or procedure draft.", "Committee pack"),
    "pack_communication": ("Draft a message, an announcement, or a huddle script for a team.",
                           "Communication pack"),
    "library": ("Add a source, or check that a source is still current.", "Library"),
    "learning": ("Plan or record the manager's own professional learning.",
                 "Learning and Growth"),
    "contributions": ("Record something the manager did, and who shares the credit.",
                      "Contributions"),
    "memory": ("Ask the assistant to remember something for later questions.", "Memory"),
    "outside": ("None of these: it involves patients, an individual's performance, or"
                " confidential employer material, so it needs the organization's own"
                " process.", "None of these: use your organization's own process"),
}

ORDER_LEVELS = (
    "It can wait until next week.",
    "It should be handled this week.",
    "It should be handled today.",
    "It needs attention now.",
)
_ITEM_KINDS = {"task": "a decision on a task", "draft": "a draft to review",
               "action": "an action to approve"}


class ClassifierError(ManagerError):
    pass


class ClassifierUnavailable(Exception):
    """JEV could not produce an answer. The message is shown to the manager."""


# -- the client -------------------------------------------------------------


def check_endpoint(endpoint: str) -> urllib.parse.SplitResult:
    """TypeSafe's own address over HTTPS, or a stand-in on this computer (tests)."""
    parsed = urllib.parse.urlsplit(endpoint)
    try:
        port = parsed.port
    except ValueError as exc:
        raise ClassifierError("the JEV address has an invalid port") from exc
    secure = parsed.scheme == "https" and parsed.hostname == JEV_HOST and port in (None, 443)
    # A stand-in on this computer is accepted so the gates can be tested end to
    # end; nothing sent to it leaves the device. It is never a setting.
    local = parsed.scheme == "http" and parsed.hostname in ("127.0.0.1", "localhost", "::1")
    if (not (secure or local) or parsed.username or parsed.password or parsed.query
            or parsed.fragment):
        raise ClassifierError("JEV must be reached at TypeSafe's own address, over HTTPS")
    return parsed


_STATUS = {
    401: "JEV did not accept the key; check it on TypeSafe's site and connect again",
    403: "JEV refused the request; check the key's access on TypeSafe's site",
    422: "JEV could not read the request",
    429: "JEV's rate limit was reached; try again in a minute",
    529: "JEV is overloaded; try again shortly",
}


class JevClient:
    """One POST to TypeSafe's ``/v1/systemone``.

    HTTPS with certificate checks, no redirects (anything but 200 is a
    failure), short timeouts, a size limit on the reply. The key is sent only
    in the Authorization header and is never part of any message or repr.
    """

    kind = PROVIDER
    runs_on = RUNS_ON

    def __init__(self, api_key: str, *, endpoint: str = JEV_ENDPOINT, model: str = JEV_MODEL):
        self._address = check_endpoint(endpoint)
        self.endpoint = endpoint
        self.model = model
        self._key = api_key

    def __repr__(self) -> str:
        return f"JevClient(model={self.model!r}, endpoint={self.endpoint!r})"

    def _port(self) -> int:
        return self._address.port or (443 if self._address.scheme == "https" else 80)

    def resolve(self, timeout: float) -> None:
        """Look up JEV's address now, within ``timeout``.

        A name lookup has no timeout of its own. Doing it before the request
        is sent means nothing waits on it while the workspace is locked for
        the last stop check (see ``ClassifierService._ask``).
        """
        self._resolved = _lookup(self._address.hostname or "", self._port(), timeout)

    def ask(self, text: str, *, timeout: float,
            on_sent: Callable[[], None]) -> dict[str, Any]:
        """Send one request body, exactly as given; return the reply as parsed JSON.

        ``text`` is the JSON the manager previewed: its bytes are what is
        sent, not a re-serialization of it. Call ``on_sent`` once, when the
        request has been handed to the network.
        """
        data = text.encode("utf-8")
        address = self._address
        host, port = address.hostname or "", self._port()
        connect_timeout = min(timeout, CONNECT_TIMEOUT_SECONDS)
        if address.scheme == "https":
            conn: http.client.HTTPConnection = http.client.HTTPSConnection(
                host, port, timeout=connect_timeout)
        else:
            conn = http.client.HTTPConnection(host, port, timeout=connect_timeout)
        try:
            try:
                # Connect to the address looked up beforehand; TLS still checks
                # the certificate against JEV's own host name.
                resolved = getattr(self, "_resolved", None) or _lookup(host, port, connect_timeout)
                sock = _connect(resolved, connect_timeout)
                if address.scheme == "https":
                    sock = ssl.create_default_context().wrap_socket(sock, server_hostname=host)
                sock.settimeout(timeout)
                conn.sock = sock
                conn.request("POST", address.path or "/", body=data, headers={
                    "Authorization": f"Bearer {self._key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                })
            except (OSError, http.client.HTTPException) as exc:
                raise ClassifierUnavailable(
                    "JEV could not be reached; check this computer's internet connection"
                ) from exc
            on_sent()
            try:
                response = conn.getresponse()
                status = response.status
                raw = response.read(MAX_RESPONSE_BYTES + 1)
            except (OSError, http.client.HTTPException) as exc:
                raise ClassifierUnavailable("JEV did not reply in time") from exc
        finally:
            conn.close()
        if status != 200:
            raise ClassifierUnavailable(_STATUS.get(status, f"JEV answered {status}"))
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ClassifierUnavailable("JEV's reply was too large")
        try:
            reply = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise ClassifierUnavailable("JEV's reply was not understood") from exc
        if not isinstance(reply, dict):
            raise ClassifierUnavailable("JEV's reply was not understood")
        return reply


class Client(Protocol):
    kind: str
    model: str
    endpoint: str
    runs_on: str

    def ask(self, text: str, *, timeout: float,
            on_sent: Callable[[], None]) -> dict[str, Any]: ...

    def resolve(self, timeout: float) -> None: ...


Addresses = list[tuple[int, Any]]


def _lookup(host: str, port: int, timeout: float) -> Addresses:
    """Every address for ``host``, in the order given, or ClassifierUnavailable
    if none comes within ``timeout``."""
    found: dict[str, Any] = {}

    def look() -> None:
        try:
            found["addresses"] = [(family, address) for family, _type, _proto, _name, address
                                  in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)]
        except OSError as exc:
            found["error"] = exc

    worker = threading.Thread(target=look, name="classifier-lookup", daemon=True)
    worker.start()
    worker.join(timeout)
    if not found.get("addresses"):
        raise ClassifierUnavailable(
            "JEV could not be reached; check this computer's internet connection")
    return found["addresses"]


def _connect(addresses: Addresses, timeout: float) -> socket.socket:
    """Connect to the first address that answers, trying each in turn (an IPv6
    address with no route falls through to IPv4), all within ``timeout``."""
    deadline = time.monotonic() + timeout
    failure: OSError | None = None
    for family, address in addresses:
        left = deadline - time.monotonic()
        if left <= 0:
            break
        sock = socket.socket(family, socket.SOCK_STREAM)
        sock.settimeout(left)
        try:
            sock.connect(address)
            return sock
        except OSError as exc:
            failure = exc
            sock.close()
    raise failure or OSError("JEV could not be reached in time")


def action_questions() -> dict[str, dict[str, Any]]:
    """The one question about a proposed action, asked by the live review and the
    shadow harness alike, so the harness measures what the live review asks."""
    return {"decision": {
        "type": "choice",
        "instructions": "Under this workspace's policy, should this proposed action be"
                        " allowed, held for the manager's review, or denied?",
        "criteria": dict(ACTION_OPTIONS),
    }}


def request_text(body: dict[str, Any]) -> str:
    """The one way a request body is written: shown in the preview, hashed, and sent."""
    return json.dumps(body, indent=2, sort_keys=True, ensure_ascii=False)


def default_client_factory(api_key: str, model: str) -> Client:
    # JEV_ENDPOINT is read when the client is made, never from settings.
    return JevClient(api_key, endpoint=JEV_ENDPOINT, model=model)


# -- checking JEV's answers --------------------------------------------------


def _number(value: Any, low: float = 0.0, high: float = 1.0) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        value = float(value)
    except OverflowError:  # an integer too large for a float is outside the contract
        return None
    if not math.isfinite(value) or value < low - 1e-9 or value > high + 1e-9:
        return None
    return min(max(value, low), high)


def _distribution(probs: Any, keys: list[str]) -> dict[str, float] | None:
    if not isinstance(probs, dict) or set(probs) != set(keys):
        return None
    out = {}
    for key in keys:
        p = _number(probs[key])
        if p is None:
            return None
        out[key] = p
    return out if abs(sum(out.values()) - 1.0) <= _TOLERANCE else None


def check_answers(questions: dict[str, dict[str, Any]], reply: dict[str, Any],
                  model: str) -> tuple[dict[str, dict[str, Any]], int | None] | str:
    """The answers, checked against what was asked, and the input tokens used.

    Returns a string saying why the reply cannot be used when it is outside
    the contract: a different model, a missing or extra answer, a wrong type,
    an option that was not offered, or probabilities that are not a
    distribution. Such a reply changes nothing.
    """
    if reply.get("model") != model:
        return "JEV answered with a different model than the one this app pins"
    answers = reply.get("answers")
    if not isinstance(answers, dict) or set(answers) != set(questions):
        return "JEV did not answer exactly the questions it was asked"
    checked: dict[str, dict[str, Any]] = {}
    for qid, question in questions.items():
        answer = answers[qid]
        kind = question["type"]
        if not isinstance(answer, dict) or answer.get("type") != kind:
            return "JEV answered a question with the wrong kind of answer"
        if kind == "noul":
            yes = _number(answer.get("noul"))
            if yes is None:
                return "JEV's yes/no answer was out of range"
            checked[qid] = {"noul": yes}
        elif kind == "choice":
            options = list(question["criteria"])
            probs = _distribution(answer.get("probabilities"), options)
            confidence = _number(answer.get("confidence"))
            if answer.get("choice") not in options or probs is None or confidence is None:
                return "JEV's choice was not one of the options, or its probabilities did not add up"
            if probs[answer["choice"]] < max(probs.values()) - _TOLERANCE:
                return "JEV's choice was not the option it gave the highest probability"
            checked[qid] = {"choice": answer["choice"], "probabilities": probs,
                            "confidence": confidence}
        else:  # score
            # The levels are the ones asked, numbered 1 to N, and nothing else.
            levels = len(question["criteria"])
            keys = [str(n) for n in range(1, levels + 1)]
            dist = _distribution(answer.get("probabilities"), keys) if levels >= 2 else None
            confidence = _number(answer.get("confidence"))
            score = _number(answer.get("score"), 1, levels)
            if dist is None or confidence is None or score is None:
                return "JEV's score was out of range, or its probabilities did not add up"
            # Where the score falls between the lowest and highest level, 0 to 1.
            checked[qid] = {"position": (score - 1) / (levels - 1), "confidence": confidence}
    usage = reply.get("usage")
    tokens = usage.get("input_tokens") if isinstance(usage, dict) else None
    if isinstance(tokens, bool) or not isinstance(tokens, int) or not 0 <= tokens < 2**53:
        tokens = None
    return checked, tokens


def _strings(value: Any) -> list[str]:
    """Every piece of text in a state, for the data-rules check."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for v in value.values() for s in _strings(v)]
    if isinstance(value, list):
        return [s for v in value for s in _strings(v)]
    return []


def _clean_request(text: str) -> str:
    text = " ".join(text.split())
    if not text:
        raise ClassifierError("type what you need to do")
    if len(text) > MAX_REQUEST_CHARS:
        raise ClassifierError(f"keep it under {MAX_REQUEST_CHARS} characters")
    return text


# -- the service ---------------------------------------------------------------


@dataclass
class _Prepared:
    job: str
    body: dict[str, Any]
    text: str
    sha: str
    checks: list[dict[str, Any]] = field(default_factory=list)
    blocked: tuple[str, str] | None = None
    model: str = ""


class ClassifierService:
    """JEV settings, gates, and the four jobs, for one workspace."""

    def __init__(
        self,
        ws: ManagerWorkspace,
        *,
        keystore: KeyStore | None = None,
        client_factory: Callable[[str, str], Client] | None = None,
        edena: EdenaPolicyEngine | None = None,
        profile_policy: Path = DEFAULT_PROFILE_POLICY,
        timeout: float = REQUEST_TIMEOUT_SECONDS,
        stop_poll: float = STOP_POLL_SECONDS,
    ):
        self.ws = ws
        # Looked up when the service is made, so tests can stand in for both.
        self.keystore = keystore or default_keystore()
        self.client_factory = client_factory or default_client_factory
        self.edena = edena or edena_engine()
        self.profile = json.loads(Path(profile_policy).read_text(encoding="utf-8"))
        self.control = AssistantControl(ws)
        self.timeout = timeout
        self.stop_poll = stop_poll

    @property
    def account(self) -> str:
        return f"jev-{self.ws.info.id}"

    # -- settings -------------------------------------------------------------

    def settings(self) -> dict[str, Any]:
        row = self.ws.store.conn.execute(
            "SELECT * FROM classifier_settings WHERE workspace_id = ?", (self.ws.info.id,)
        ).fetchone()
        if row is None:  # the default: not connected, every job off
            return {"provider": "none", "model": "", "jobs": dict.fromkeys(JOBS, False),
                    "daily_request_limit": DEFAULT_DAILY_LIMIT}
        # The model shown is the one sent: always the pinned one while connected.
        return {"provider": row["provider"],
                "model": JEV_MODEL if row["provider"] == PROVIDER else "",
                "jobs": {job: bool(row[f"job_{job}"]) for job in JOBS},
                "daily_request_limit": row["daily_request_limit"]}

    def status(self) -> dict[str, Any]:
        settings = self.settings()
        connected = settings["provider"] == PROVIDER
        return {
            **settings,
            "runs_on": RUNS_ON if connected else "nothing is connected",
            "keystore": self.keystore.name,
            "keystore_available": self.keystore.available(),
            "requests_today": self._sent_since(self.ws.clock()[:10]),
            "input_tokens_this_month": self._tokens_since(self.ws.clock()[:7]),
            "what_it_does": list(WHAT_IT_DOES),
            "never_does": list(NEVER_DOES),
            "gates": list(GATES),
            "terms": list(TERMS),
        }

    def connect(self, by: str, api_key: str, *,
                daily_request_limit: int | None = None) -> dict[str, Any]:
        """The manager connects JEV with their own key. Every job stays off."""
        by = self._owner(by)
        key = (api_key or "").strip()
        if not SECRET.fullmatch(key):
            # Never repeat the key, or any part of it, in a message.
            raise ClassifierError("that does not look like a TypeSafe API key; paste the key"
                                  " exactly as TypeSafe shows it")
        limit = (self.settings()["daily_request_limit"] if daily_request_limit is None
                 else daily_request_limit)
        if not 0 <= limit <= MAX_DAILY_LIMIT:
            raise ClassifierError(f"the daily request limit must be between 0 and"
                                  f" {MAX_DAILY_LIMIT}")
        try:
            self.keystore.set(self.account, key)
        except KeyStoreUnavailable as exc:
            raise ClassifierError(f"JEV was not connected: {exc}") from None
        self._save(by, provider=PROVIDER, model=JEV_MODEL, jobs=dict.fromkeys(JOBS, False),
                   limit=limit)
        return self.status()

    def disconnect(self, by: str) -> dict[str, Any]:
        """Back to the default: not connected, every job off, the key removed."""
        by = self._owner(by)
        self._save(by, provider="none", model="", jobs=dict.fromkeys(JOBS, False),
                   limit=self.settings()["daily_request_limit"])
        try:
            self.keystore.delete(self.account)
        except KeyStoreUnavailable as exc:
            raise ClassifierError(f"JEV is off, but its key could not be removed from"
                                  f" {self.keystore.name}: {exc}. Remove it there.") from None
        return self.status()

    def set_jobs(self, by: str, jobs: dict[str, bool]) -> dict[str, Any]:
        """Turn each job on or off. Only while JEV is connected."""
        by = self._owner(by)
        settings = self.settings()
        if set(jobs) - set(JOBS):
            raise ClassifierError("unknown JEV job")
        merged = {**settings["jobs"], **{k: bool(v) for k, v in jobs.items()}}
        if any(merged.values()) and settings["provider"] != PROVIDER:
            raise ClassifierError("connect JEV before turning on any of its jobs")
        self._save(by, provider=settings["provider"], model=settings["model"], jobs=merged,
                   limit=settings["daily_request_limit"])
        return self.status()

    def _owner(self, by: str) -> str:
        by = (by or "").strip()
        if by != self.ws.info.owner:
            raise ClassifierError(
                "only the accountable manager for this workspace can change or use JEV"
            )
        return by

    def _save(self, by: str, *, provider: str, model: str, jobs: dict[str, bool],
              limit: int) -> None:
        values = {"ws": self.ws.info.id, "provider": provider, "model": model, "limit": limit,
                  "by": by, "at": self.ws.clock(), **{job: int(jobs[job]) for job in JOBS}}
        with self.ws.store.transaction() as db:
            db.execute(
                "INSERT INTO classifier_settings (workspace_id, provider, model,"
                " job_action_review, job_refusal_check, job_routing, job_attention,"
                " daily_request_limit, updated_by, updated_at)"
                " VALUES (:ws, :provider, :model, :action_review, :refusal_check, :routing,"
                " :attention, :limit, :by, :at)"
                " ON CONFLICT (workspace_id) DO UPDATE SET provider = :provider,"
                " model = :model, job_action_review = :action_review,"
                " job_refusal_check = :refusal_check, job_routing = :routing,"
                " job_attention = :attention, daily_request_limit = :limit,"
                " updated_by = :by, updated_at = :at",
                values,
            )
            self.ws.store.log(by, "configure", "classifier_settings", self.ws.info.id)

    # -- usage ----------------------------------------------------------------

    def _sent_since(self, prefix: str) -> int:
        marks = ",".join("?" * len(_SENT))
        return self.ws.store.conn.execute(
            f"SELECT count(*) AS n FROM classifier_requests WHERE workspace_id = ?"  # noqa: S608
            f" AND outcome IN ({marks}) AND created_at >= ?",
            (self.ws.info.id, *_SENT, prefix),
        ).fetchone()["n"]

    def _tokens_since(self, prefix: str) -> int:
        return self.ws.store.conn.execute(
            "SELECT coalesce(sum(input_tokens), 0) AS t FROM classifier_requests"
            " WHERE workspace_id = ? AND created_at >= ?",
            (self.ws.info.id, prefix),
        ).fetchone()["t"]

    # -- the gates --------------------------------------------------------------

    def _prepare(self, job: str, state: Any, questions: dict[str, dict[str, Any]]) -> _Prepared:
        """Build exactly what would be sent, and run every gate before sending.

        Writes and sends nothing. Previews and real requests both use it, so
        what the manager sees is what is sent.
        """
        settings = self.settings()
        # Always the pinned model: a reviewed change to JEV_MODEL reaches every
        # connected workspace, whatever was stored when JEV was connected.
        model = JEV_MODEL
        body = {"model": model, "state": state, "questions": questions}
        text = request_text(body)
        sha = sha256_text(f"{PROVIDER}\n{JEV_ENDPOINT}\n\n{text}")
        prep = _Prepared(job, body, text, sha, model=model)
        if settings["provider"] != PROVIDER:
            prep.blocked = ("not_connected", "JEV is not connected. Everything works without"
                                             " it.")
            return prep
        if not settings["jobs"][job]:
            prep.blocked = ("job_off", f"JEV's {JOB_NAMES[job]} is off. Everything works"
                                       " without it.")
            return prep

        content = "\n".join(_strings(state))
        findings = self.ws.privacy.analyze(content)
        kinds = ", ".join(sorted({f.entity_type for f in findings}))
        prep.checks.append({
            "gate": "data_rules", "passed": not findings,
            "detail": "No identifying details were found. The check cannot detect names,"
                      " so read the text yourself." if not findings else
                      f"The text includes details the data rules keep on this computer ({kinds}).",
        })
        if findings:
            prep.blocked = ("refused_data_rules", "Nothing was sent: the text includes details"
                            f" the data rules keep on this computer ({kinds}).")

        decision = self._edena_decide(job, content)
        allowed = decision.decision is Decision.ALLOW
        codes = ", ".join(decision.reason_codes)
        prep.checks.append({
            "gate": "edena", "passed": allowed,
            "detail": "The EDENA policy allows an assistant to recommend." if allowed
                      else f"The EDENA policy did not allow this ({codes}).",
        })
        if not allowed and prep.blocked is None:
            prep.blocked = ("refused_policy", f"Nothing was sent: the EDENA policy did not"
                                              f" allow this ({codes}).")

        used, limit = self._sent_since(self.ws.clock()[:10]), settings["daily_request_limit"]
        over = used >= limit
        prep.checks.append({
            "gate": "budget", "passed": not over,
            "detail": f"Within today's limit ({used} of {limit} JEV requests used)." if not over
                      else f"Today's limit of {limit} JEV requests has been reached.",
        })
        if over and prep.blocked is None:
            prep.blocked = ("refused_budget", f"Nothing was sent: today's limit of {limit} JEV"
                                              " requests has been reached.")
        if self.control.state()["stopped"]:
            prep.blocked = STOPPED_BEFORE  # the manager's stop comes before every other reason
        return prep

    def _preview(self, prep: _Prepared) -> dict[str, Any]:
        connected = prep.blocked is None or prep.blocked[0] not in ("not_connected", "job_off")
        return {
            "job": prep.job,
            "provider": PROVIDER if connected else "none",
            "model": prep.model if connected else "",
            "runs_on": RUNS_ON if connected else "nothing is connected",
            "request": prep.text if connected else "",
            "request_sha256": prep.sha if connected else "",
            "checks": prep.checks,
            "will_send": prep.blocked is None,
            "reason": prep.blocked[1] if prep.blocked else "",
        }

    def _edena_decide(self, job: str, content: str):
        spec = self.profile["assistant_evaluation"]
        tenant = f"personal:{self.ws.info.id}"
        return self.edena.decide(GatewayRequest(
            request_id=new_id("req"),
            actor=Actor(actor_id=f"assistant:{PROVIDER}", role=spec["role"], tenant=tenant),
            intent=INTENTS[job],
            content=content,
            risk_tier=RiskTier(spec["risk_tier"]),
            data_class=DataClass(spec["data_class"]),
            action_mode=ActionMode(spec["action_mode"]),
            target_tenant=tenant,
            data_zone=DataZone(spec["data_zone"]),
        ))

    def _require_reviewed(self, prep: _Prepared, reviewed_sha256: str | None) -> None:
        if reviewed_sha256 != prep.sha:
            raise ClassifierError(
                "what JEV would be sent changed after you reviewed it, or was not reviewed;"
                " review it again"
            )

    # -- sending --------------------------------------------------------------

    def _ask(self, prep: _Prepared, by: str, started: int) -> tuple[
            str, dict[str, dict[str, Any]] | None, tuple[str, str] | None, int | None, int]:
        """Ask JEV once. Returns (request id, checked answers, failure, input tokens,
        stop generation).

        The request is recorded as it is sent and left unfinished while it
        runs, so a crash still counts against the limit and "Assistants at
        work" shows it. The caller finishes it, and keeps a result only if no
        stop came since the request began, decided inside its write.
        """
        try:
            key = self.keystore.get(self.account)
        except KeyStoreUnavailable as exc:
            return "", None, ("provider_failed", f"The JEV key could not be read from"
                                                 f" {self.keystore.name}: {exc}."), None, started
        if key is None:
            return "", None, ("provider_failed", f"The JEV key is no longer in"
                                                 f" {self.keystore.name}. Connect JEV again."), \
                None, started
        client = self.client_factory(key, prep.model)
        resolve = getattr(client, "resolve", None)
        if resolve is not None:
            # Looked up before the lock, while the stop control is watched: a
            # stop during a slow lookup returns as quickly as one during the
            # request, and nothing is sent.
            looked: dict[str, Any] = {}
            found = threading.Event()

            def look() -> None:
                try:
                    resolve(min(self.timeout, CONNECT_TIMEOUT_SECONDS))
                except ClassifierUnavailable as exc:
                    looked["error"] = exc
                except Exception:  # noqa: BLE001 — any lookup failure: JEV is not reached
                    looked["error"] = ClassifierUnavailable(
                        "JEV could not be reached; check this computer's internet connection")
                finally:
                    found.set()

            threading.Thread(target=look, name="classifier-resolve", daemon=True).start()
            while not found.wait(self.stop_poll):
                if self._stopped_since(started):
                    request_id = self._record(prep, *STOPPED_BEFORE, by, finished=True)
                    return request_id, None, STOPPED_BEFORE, None, started
            if "error" in looked:
                return "", None, ("provider_failed", f"JEV did not answer: {looked['error']}."), \
                    None, started
        outcome: dict[str, Any] = {}
        sent = threading.Event()
        done = threading.Event()

        def call() -> None:
            try:
                outcome["reply"] = client.ask(prep.text, timeout=self.timeout, on_sent=sent.set)
            except BaseException as exc:  # noqa: BLE001 — reported below
                outcome["error"] = exc
            finally:
                done.set()

        with self.ws.store.transaction():
            # As for the AI model: the last stop check and the send are one
            # step, so a stop either comes first (nothing is sent) or after
            # the request left (the answer is discarded).
            if self._stopped_since(started):
                request_id = self._record(prep, *STOPPED_BEFORE, by, finished=True)
                return request_id, None, STOPPED_BEFORE, None, started
            # Checked again here, where requests are counted one at a time, so
            # two at once cannot both take the last request of the day.
            limit = self.settings()["daily_request_limit"]
            if self._sent_since(self.ws.clock()[:10]) >= limit:
                over = ("refused_budget", f"Nothing was sent: today's limit of {limit} JEV"
                                          " requests has been reached.")
                return self._record(prep, *over, by, finished=True), None, over, None, started
            request_id = self._record(prep, "provider_failed", "interrupted before JEV replied",
                                      by, finished=False)
            threading.Thread(target=call, name=f"classifier-{request_id}", daemon=True).start()
            while not sent.wait(0.01) and not done.is_set():
                pass
        # One deadline for the whole reply, however slowly it arrives.
        deadline = time.monotonic() + self.timeout
        while not done.wait(self.stop_poll):
            if self._stopped_since(started):
                return request_id, None, STOPPED_DURING, None, started
            if time.monotonic() > deadline:
                return request_id, None, ("provider_failed", "JEV did not answer: JEV did not"
                                                             " reply in time."), None, started
        if self._stopped_since(started):
            return request_id, None, STOPPED_DURING, None, started
        error = outcome.get("error")
        if isinstance(error, ClassifierUnavailable):
            return request_id, None, ("provider_failed", f"JEV did not answer: {error}."), \
                None, started
        if error is not None and not isinstance(error, Exception):
            raise error  # an interrupt, not a failure: the request stays counted
        if error is not None:
            return request_id, None, ("provider_failed", "The JEV connection failed"
                                                         " unexpectedly."), None, started
        checked = check_answers(prep.body["questions"], outcome["reply"], prep.model)
        if isinstance(checked, str):
            return request_id, None, ("output_refused", f"JEV's answer was not used: {checked}."), \
                None, started
        answers, tokens = checked
        return request_id, answers, None, tokens, started

    def _turned_off(self, job: str) -> tuple[str, str] | None:
        """Why an answer that just came back is not used: JEV, or this job, was
        turned off while JEV worked. Read inside the write that would use it."""
        settings = self.settings()
        if settings["provider"] != PROVIDER or not settings["jobs"][job]:
            return ("stopped", f"JEV's {JOB_NAMES[job]} was turned off while JEV worked, so its"
                               " answer was not used.")
        return None

    def _stopped_since(self, generation: int) -> bool:
        control = self.control.state()
        return control["stopped"] or control["generation"] != generation

    def _record(self, prep: _Prepared, outcome: str, reason: str, by: str, *,
                finished: bool) -> str:
        request_id = new_id("clr")
        now = self.ws.clock()
        with self.ws.store.transaction() as db:
            db.execute(
                "INSERT INTO classifier_requests (id, workspace_id, job, provider, model,"
                " state_sha256, outcome, reason, requested_by, created_at, finished_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (request_id, self.ws.info.id, prep.job, PROVIDER, prep.model, prep.sha,
                 outcome, reason, by, now, now if finished else None),
            )
            self.ws.store.log(by, "classifier_request", "classifier_request", request_id)
        return request_id

    def _finish(self, request_id: str, outcome: str, reason: str, *, result: str = "",
                confidence: float | None = None, tokens: int | None = None) -> None:
        if not request_id:
            return
        with self.ws.store.transaction() as db:
            db.execute(
                "UPDATE classifier_requests SET outcome = ?, reason = ?, result = ?,"
                " confidence = ?, input_tokens = ?, finished_at = ? WHERE id = ?",
                (outcome, reason, result, confidence, tokens, self.ws.clock(), request_id),
            )
            self.ws.store.log(self.ws.info.owner, f"classifier:{outcome}", "classifier_request",
                              request_id)

    def _blocked_record(self, prep: _Prepared, by: str) -> str:
        """A request refused before sending is recorded too, unless JEV is off."""
        outcome, reason = prep.blocked
        if outcome in ("not_connected", "job_off"):
            return ""
        return self._record(prep, outcome, reason, by, finished=True)

    # -- 1. action review -------------------------------------------------------

    def _action_prep(self, action_id: str) -> tuple[_Prepared, Any]:
        boundary = ActionBoundary(self.ws)
        action = boundary.get(action_id)
        content = "no content"
        if action.artifact_revision_id:
            status = BriefService(self.ws).revision(action.artifact_revision_id).status
            content = {"accepted": "an accepted brief",
                       "draft": "a draft brief not yet accepted"}.get(status, f"a {status} revision")
        state = {
            "workspace": "a Personal Manager workspace: one nurse manager's own planning"
                         " records, kept on their computer",
            "proposed_by": "the nurse manager" if action.origin == "human" else "an AI assistant",
            "effect": action.effect,
            "destination": action.destination,
            "carrying": content,
            "purpose": action.purpose,
        }
        prep = self._prepare("action_review", state, action_questions())
        if prep.blocked is None:
            if action.status != "awaiting_approval":
                prep.blocked = ("not_waiting", f"This action is {action.status}, not waiting for"
                                               " approval, so there is nothing for JEV to"
                                               " review.")
            elif self.action_classification(action_id) is not None:
                prep.blocked = ("already_reviewed", "JEV has already reviewed this action.")
        return prep, action

    def preview_action(self, action_id: str) -> dict[str, Any]:
        """Exactly what asking JEV about this action would send. Sends nothing."""
        prep, _action = self._action_prep(action_id)
        return {**self._preview(prep), "action_id": action_id}

    def review_action(self, action_id: str, by: str, reviewed_sha256: str | None) -> dict[str, Any]:
        """Ask JEV about one proposed action. It can add a hold; it never removes one."""
        by = self._owner(by)
        started = self.control.state()["generation"]
        prep, action = self._action_prep(action_id)
        core = _CORE_TO_OPTION[action.policy_decision]

        def result(outcome: str, reason: str, request_id: str) -> dict[str, Any]:
            return {**self._action_view(action_id, core), "outcome": outcome, "reason": reason,
                    "request_id": request_id}

        if prep.blocked:
            if prep.blocked[0] in ("not_waiting", "already_reviewed"):
                raise ClassifierError(prep.blocked[1])
            return result(*prep.blocked, self._blocked_record(prep, by))
        self._require_reviewed(prep, reviewed_sha256)
        request_id, answers, failure, tokens, generation = self._ask(prep, by, started)
        if failure:
            self._finish(request_id, *failure, tokens=tokens)
            return result(*failure, request_id)
        decision = answers["decision"]
        # The most probable option, a tie going to the stricter one: the same
        # rule the shadow harness reads (Choice.suggested).
        suggestion = Choice(decision["probabilities"]).suggested
        decision = {**decision, "choice": suggestion}
        confidence = decision["confidence"]
        stricter = STRICTNESS[suggestion] > STRICTNESS[core]
        hold = stricter and confidence >= CONFIDENT
        if hold:
            reason = (f"JEV suggests this should be {OPTION_LABELS[suggestion]}, which is stricter"
                      " than the policy's decision. Read its suggestion, then acknowledge it"
                      " before you approve. The policy's decision is unchanged.")
        elif stricter:
            reason = ("JEV leans stricter than the policy, but not confidently, so nothing"
                      " changes. The policy decides.")
        else:
            reason = "JEV's suggestion is not stricter than the policy's, so nothing changes."
        changed = False
        with self.ws.store.transaction() as db:
            if self._stopped_since(generation):
                self._finish(request_id, *STOPPED_DURING, tokens=tokens)
                return result(*STOPPED_DURING, request_id)
            off = self._turned_off(prep.job)
            if off:
                self._finish(request_id, *off, tokens=tokens)
                return result(*off, request_id)
            current = ActionBoundary(self.ws).get(action_id)
            changed = (current.status != "awaiting_approval"
                       or self.action_classification(action_id) is not None)
            if changed:
                # Decided inside the write: an approval or another review that
                # landed meanwhile wins; JEV's answer is kept only as a ledger row.
                self._finish(request_id, "answered", "the action changed while JEV was asked",
                             result=suggestion, confidence=confidence, tokens=tokens)
            else:
                self._hold(db, action_id, request_id, prep.model, decision, core, hold, by)
                self._finish(request_id, "answered", "", result=suggestion,
                             confidence=confidence, tokens=tokens)
        if changed:
            # Raised only after the ledger row is committed.
            raise ClassifierError("the action changed while JEV was being asked; nothing was"
                                  " recorded on it")
        return result("answered", reason, request_id)

    def _hold(self, db, action_id: str, request_id: str, model: str, decision: dict[str, Any],
              core: str, hold: bool, by: str) -> None:
        """Record JEV's suggestion on the action (the one writer of action_classifications)."""
        db.execute(
            "INSERT INTO action_classifications (action_id, workspace_id, request_id, model,"
            " suggestion, probabilities, confidence, core_decision, hold, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (action_id, self.ws.info.id, request_id, model, decision["choice"],
             json.dumps(decision["probabilities"], sort_keys=True), decision["confidence"],
             core, int(hold), self.ws.clock()),
        )
        self.ws.store.log(by, "hold" if hold else "classify", "action_classification",
                          action_id)

    def acknowledge(self, action_id: str, by: str) -> dict[str, Any]:
        """The manager has read JEV's stricter suggestion. The hold is lifted;
        the action still needs the manager's own approval."""
        by = self._owner(by)
        action = ActionBoundary(self.ws).get(action_id)
        with self.ws.store.transaction() as db:
            changed = db.execute(
                "UPDATE action_classifications SET acknowledged_by = ?, acknowledged_at = ?"
                " WHERE action_id = ? AND workspace_id = ? AND hold = 1"
                " AND acknowledged_at IS NULL",
                (by, self.ws.clock(), action_id, self.ws.info.id),
            ).rowcount
            if changed != 1:
                raise ClassifierError("there is no JEV hold waiting on this action")
            self.ws.store.log(by, "acknowledge", "action_classification", action_id)
        view = self._action_view(action_id, _CORE_TO_OPTION[action.policy_decision])
        return {**view, "outcome": "acknowledged",
                "reason": "You acknowledged JEV's suggestion. The action still needs your own"
                          " approval.", "request_id": view["request_id"]}

    def action_classification(self, action_id: str) -> Any:
        return self.ws.store.conn.execute(
            "SELECT * FROM action_classifications WHERE action_id = ? AND workspace_id = ?",
            (action_id, self.ws.info.id),
        ).fetchone()

    def _action_view(self, action_id: str, core: str) -> dict[str, Any]:
        row = self.action_classification(action_id)
        return {
            "action_id": action_id,
            "model": row["model"] if row else "",
            "core_decision": core,
            "suggestion": row["suggestion"] if row else "",
            "probabilities": json.loads(row["probabilities"]) if row else {},
            "confidence": row["confidence"] if row else None,
            "hold": bool(row["hold"]) if row else False,
            "acknowledged": bool(row and row["acknowledged_at"]),
            "request_id": row["request_id"] if row else "",
        }

    # -- 2. refusal check ---------------------------------------------------------

    def _refusal_prep(self, question: str) -> _Prepared:
        state = {"request": question}
        questions = {category: {"type": "noul", "instructions": spec[0]}
                     for category, spec in REFUSALS.items()}
        return self._prepare("refusal_check", state, questions)

    def preview_refusal(self, question: str, *, model_will_send: bool = True) -> dict[str, Any]:
        """Exactly what the refusal check would send for this question. Sends nothing.

        JEV is asked only when the question would otherwise go to the AI model.
        """
        prep = self._refusal_prep(question)
        if prep.blocked is None and not model_will_send:
            prep.blocked = ("model_not_asked", "JEV checks a question only when it would go to"
                                               " the AI model.")
        return self._preview(prep)

    def check_refusal(self, question: str, by: str, reviewed_sha256: str | None,
                      started: int) -> dict[str, Any]:
        """Check a question before the AI model sees it.

        Returns ``{"outcome": ..., "refusal": ..., "reason": ..., "request_id": ...}``.
        Only ``outcome == "refused"`` stops the question; the reason says why
        in every other case, for the manager:

        - ``"off"``: JEV or the check is off; JEV was not asked (no reason).
        - ``"clear"``: JEV found nothing to refuse, or was not sure.
        - ``"skipped"``: JEV was unavailable, refused by a gate, turned off
          meanwhile, or answered outside the contract; the question goes on
          as it would without JEV.
        - ``"stopped"``: the manager had stopped assistants; nothing was sent.
        - ``"stopped_during"``: the manager stopped assistants while JEV had
          the question; its answer was discarded.
        """
        prep = self._refusal_prep(question)

        def outcome(kind: str, reason: str, request_id: str,
                    refusal: dict[str, str] | None = None) -> dict[str, Any]:
            return {"outcome": kind, "refusal": refusal, "reason": reason,
                    "request_id": request_id}

        if prep.blocked:
            if prep.blocked[0] in ("not_connected", "job_off"):
                return outcome("off", "", "")
            if prep.blocked[0] == "refused_stopped":
                return outcome("stopped", prep.blocked[1], self._blocked_record(prep, by))
            return outcome("skipped", f"{prep.blocked[1]} The question went on without JEV's"
                                      " check.", self._blocked_record(prep, by))
        self._require_reviewed(prep, reviewed_sha256)
        request_id, answers, failure, tokens, generation = self._ask(prep, by, started)
        if failure:
            self._finish(request_id, *failure, tokens=tokens)
            if failure == STOPPED_DURING:
                # The question reached JEV; only the AI model never saw it.
                return outcome("stopped_during", failure[1], request_id)
            if failure[0] in ("stopped", "refused_stopped"):
                return outcome("stopped", failure[1], request_id)
            return outcome("skipped", f"{failure[1]} The question went on without JEV's check.",
                           request_id)
        category, yes = max(((c, answers[c]["noul"]) for c in REFUSALS), key=lambda cy: cy[1])
        with self.ws.store.transaction():
            if self._stopped_since(generation):
                self._finish(request_id, *STOPPED_DURING, tokens=tokens)
                return outcome("stopped_during", STOPPED_DURING[1], request_id)
            off = self._turned_off(prep.job)
            if off:
                self._finish(request_id, *off, tokens=tokens)
                return outcome("skipped", f"{off[1]} The question went on without JEV's check.",
                               request_id)
            if yes >= CONFIDENT:
                _question, label, path = REFUSALS[category]
                self._finish(request_id, "answered", "", result=f"refused:{category}",
                             confidence=yes, tokens=tokens)
                return outcome("refused", f"Not sent to the AI model: JEV found {label} in the"
                                          f" question. {path}", request_id,
                               {"category": category, "label": label, "nearest_path": path})
            self._finish(request_id, "answered", "", result="clear", confidence=yes,
                         tokens=tokens)
        if yes >= SUGGEST:
            _question, label, _path = REFUSALS[category]
            return outcome("clear", f"JEV was not sure whether the question has {label}, so it was"
                                    " not refused. Check it yourself.", request_id)
        return outcome("clear", "JEV checked the question and found nothing to refuse.",
                       request_id)

    # -- 3. routing ---------------------------------------------------------------

    def _route_prep(self, request: str) -> _Prepared:
        questions = {"route": {
            "type": "choice",
            "instructions": "Which part of a nurse manager's planning workspace fits this"
                            " request best?",
            "criteria": {key: spec[0] for key, spec in ROUTES.items()},
        }}
        return self._prepare("routing", {"request": _clean_request(request)}, questions)

    def preview_route(self, request: str) -> dict[str, Any]:
        """Exactly what asking JEV where this request belongs would send. Sends nothing."""
        return self._preview(self._route_prep(request))

    def route(self, request: str, by: str, reviewed_sha256: str | None) -> dict[str, Any]:
        """Suggest where a request belongs. The manager chooses; nothing starts."""
        by = self._owner(by)
        started = self.control.state()["generation"]
        prep = self._route_prep(request)
        alternatives = [{"route": key, "label": spec[1]} for key, spec in ROUTES.items()]

        def result(outcome: str, reason: str, request_id: str, suggested: str = "",
                   confidence: float | None = None) -> dict[str, Any]:
            return {"outcome": outcome, "reason": reason, "request_id": request_id,
                    "model": prep.model if outcome == "answered" else "",
                    "request": prep.body["state"]["request"], "suggested": suggested,
                    "label": ROUTES[suggested][1] if suggested else "",
                    "confidence": confidence, "alternatives": alternatives}

        if prep.blocked:
            return result(*prep.blocked, self._blocked_record(prep, by))
        self._require_reviewed(prep, reviewed_sha256)
        request_id, answers, failure, tokens, generation = self._ask(prep, by, started)
        if failure:
            self._finish(request_id, *failure, tokens=tokens)
            return result(failure[0], f"{failure[1]} Choose where to go yourself.", request_id)
        choice, confidence = answers["route"]["choice"], answers["route"]["confidence"]
        sure = confidence >= SUGGEST
        with self.ws.store.transaction():
            if self._stopped_since(generation):
                self._finish(request_id, *STOPPED_DURING, tokens=tokens)
                return result(*STOPPED_DURING, request_id)
            off = self._turned_off(prep.job)
            if off:
                self._finish(request_id, *off, tokens=tokens)
                return result(off[0], f"{off[1]} Choose where to go yourself.", request_id)
            self._finish(request_id, "answered", "",
                         result=choice if sure else f"unsure:{choice}",
                         confidence=confidence, tokens=tokens)
        if not sure:
            return result("answered", "JEV was not sure where this belongs. Choose where to go"
                                      " yourself.", request_id, confidence=confidence)
        return result("answered", "", request_id, choice, confidence)

    # -- 4. attention order -------------------------------------------------------

    def _order_prep(self, today: str, week_of: str) -> tuple[_Prepared, list[str]]:
        from .views import mission_control  # noqa: PLC0415 - views import this module's peers

        items = mission_control(self.ws, today=today, week_of=week_of)["needs_my_judgment"]["items"]
        due = {row["id"]: row["due_date"] for row in self.ws.store.conn.execute(
            "SELECT id, due_date FROM tasks WHERE workspace_id = ?", (self.ws.info.id,))}
        state = {"today": today, "items": [
            {"item": n, "kind": _ITEM_KINDS[i["kind"]], "title": i["title"],
             "due": due.get(i["id"]) or "none"}
            for n, i in enumerate(items, start=1)
        ]}
        questions = {f"item_{n}": {
            "type": "score",
            "instructions": f"How soon does item {n} need the nurse manager's attention?",
            "criteria": list(ORDER_LEVELS),
        } for n in range(1, len(items) + 1)}
        prep = self._prepare("attention", state, questions)
        if prep.blocked is None and not items:
            prep.blocked = ("nothing_to_order", "Nothing needs your judgment, so there is nothing"
                                                " to order.")
        elif prep.blocked is None and len(items) > MAX_ORDER_ITEMS:
            prep.blocked = ("too_many", f"JEV orders at most {MAX_ORDER_ITEMS} items; your usual"
                                        " order is kept.")
        return prep, [i["id"] for i in items]

    def preview_order(self, today: str, week_of: str) -> dict[str, Any]:
        """Exactly what asking JEV for an order would send. Sends nothing."""
        prep, _ids = self._order_prep(today, week_of)
        return self._preview(prep)

    def order(self, today: str, week_of: str, by: str,
              reviewed_sha256: str | None) -> dict[str, Any]:
        """Suggest an order for "Needs my judgment". Nothing is hidden or scored on screen."""
        by = self._owner(by)
        started = self.control.state()["generation"]
        prep, ids = self._order_prep(today, week_of)

        def result(outcome: str, reason: str, request_id: str, order: list[str] | None = None,
                   ) -> dict[str, Any]:
            order = order or ids
            return {"outcome": outcome, "reason": reason, "request_id": request_id,
                    "model": prep.model if outcome == "answered" else "", "order": order,
                    "reordered": order != ids}

        if prep.blocked:
            if prep.blocked[0] in ("nothing_to_order", "too_many"):
                return result(prep.blocked[0], prep.blocked[1], "")
            return result(*prep.blocked, self._blocked_record(prep, by))
        self._require_reviewed(prep, reviewed_sha256)
        request_id, answers, failure, tokens, generation = self._ask(prep, by, started)
        if failure:
            self._finish(request_id, *failure, tokens=tokens)
            return result(failure[0], f"{failure[1]} Your usual order is kept.", request_id)
        scored = [answers[f"item_{n}"] for n in range(1, len(ids) + 1)]
        confidence = sum(a["confidence"] for a in scored) / len(scored)
        sure = confidence >= SUGGEST
        order = ids
        if sure:
            ranked = sorted(range(len(ids)), key=lambda i: (-scored[i]["position"], i))
            order = [ids[i] for i in ranked]
        with self.ws.store.transaction():
            if self._stopped_since(generation):
                self._finish(request_id, *STOPPED_DURING, tokens=tokens)
                return result(*STOPPED_DURING, request_id)
            off = self._turned_off(prep.job)
            if off:
                self._finish(request_id, *off, tokens=tokens)
                return result(off[0], f"{off[1]} Your usual order is kept.", request_id)
            self._finish(request_id, "answered", "",
                         result=("reordered" if order != ids else "unchanged") if sure
                         else "unsure", confidence=confidence, tokens=tokens)
        if not sure:
            return result("answered", "JEV was not sure, so your usual order is kept.",
                          request_id)
        return result("answered", "" if order != ids else "JEV suggests the usual order.",
                      request_id, order)


# -- the shadow harness (step 4.5b) ---------------------------------------------


class JevDecisionAdapter:
    """JEV behind the shadow harness's ``DecisionAdapter`` (decision_adapter.py).

    Used only by ``tools/shadow_report.py`` on the reviewed, pinned synthetic
    set. The harness decides with EDENA first; nothing JEV answers reaches a
    decision.
    """

    name = "jev"
    version = JEV_MODEL

    def __init__(self, client: Client, *, timeout: float = REQUEST_TIMEOUT_SECONDS):
        self.client = client
        self.timeout = timeout

    def choose(self, question: str, options) -> Choice:
        options = list(options)
        if set(options) != set(OPTIONS):
            raise ValueError("JEV is asked only the harness's three options")
        questions = action_questions()
        reply = self.client.ask(request_text({"model": self.client.model, "state": question,
                                              "questions": questions}),
                                timeout=self.timeout, on_sent=lambda: None)
        checked = check_answers(questions, reply, self.client.model)
        if isinstance(checked, str):
            raise ValueError(checked)
        answers, _tokens = checked
        return Choice(answers["decision"]["probabilities"], answers["decision"]["confidence"])


__all__ = [
    "CONFIDENT", "JEV_ENDPOINT", "JEV_MODEL", "JOBS", "REFUSALS", "ROUTES", "SUGGEST",
    "ClassifierError", "ClassifierService", "ClassifierUnavailable", "JevClient",
    "JevDecisionAdapter", "check_answers", "check_endpoint", "default_client_factory",
]
