"""Bounded assistance (G4, ADR 0004): provider-neutral, off by default.

A workspace has no AI model until its manager connects one. The only
provider shipped today is a model running on the manager's own computer
(an Ollama-compatible server on localhost). No cloud service ships until
the steward chooses one; when it does, it plugs in behind ``Provider``
and passes exactly the same gates:

1. **Data rules.** The text to send is built only from workspace records
   (which were screened at capture) and is screened again. A finding
   stops the request; nothing is sent.
2. **EDENA at ``recommend``.** The authoritative engine decides whether
   an assistant may draft this at all (ADR 0002).
3. **Budget before the request.** A daily request limit and a monthly
   cost budget are checked before any provider is called. Each request is
   recorded before the call, so a crash still counts against the budget.
4. **Draft only.** Model output is screened, its record citations are
   checked against the records actually sent, and it is saved as a draft
   revision that only the manager can accept.
5. **Honest fallback.** If any gate stops the request, or the provider
   fails, the manager gets the records-only draft and the reason. There
   is never a silent switch to another service.

The request ledger keeps metadata only: hashes, outcomes, and costs,
never the text sent or received.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
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
from .actions import DEFAULT_PROFILE_POLICY
from .brief import ASSISTANT_PREFIX, BriefService, compose_weekly_brief, sha256_text
from .services import ManagerError, ManagerWorkspace
from .views import project_dashboard
from .store import new_id

DEFAULT_LOCAL_ENDPOINT = "http://127.0.0.1:11434"
LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "::1")
MODEL_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,99}$")
CITATION = re.compile(r"`([a-z]{2,5}-[0-9a-f]{12})`")

MAX_OUTPUT_TOKENS = 1200
MAX_OUTPUT_CHARS = 20_000
MAX_RESPONSE_BYTES = 256 * 1024
REQUEST_TIMEOUT_SECONDS = 60.0

# Requests that reached a provider count against the budget, whatever
# became of their output.
_SENT = ("drafted", "answered", "provider_failed", "output_refused")

GATES = (
    "Only material your workspace's data rules admit is sent, and it is checked again first.",
    "The EDENA policy decides whether an assistant may draft this; assistants only recommend.",
    "A daily request limit and a monthly cost budget are checked before anything is sent.",
    "What the model writes is never final: a brief becomes a draft only you can accept, and an"
    " answer about a project is shown to you and not saved.",
    "If the model is unavailable, nothing goes anywhere else, and you are told why. A brief is"
    " drafted from your records instead.",
)

SYSTEM_PROMPT = (
    "You help a nurse manager prepare their weekly brief. Rewrite the brief below"
    " so it is clear and concise. Use only the facts it contains; never add names,"
    " numbers, dates, or events that are not in it. Every line you write must keep the"
    " record citation of the fact it states, exactly as written, in backticks. Keep"
    " the section headings. Write Markdown with no title line and no preamble."
)


PROJECT_SYSTEM_PROMPT = (
    "You are a thinking partner for a nurse manager. Answer their question about one"
    " project using only the project records below. After each fact, cite the record it"
    " came from exactly as written, in backticks; every line must cite a record. If the"
    ' records do not answer the question, reply with exactly: "The records do not answer this."'
    " Offer options and considerations; the manager decides."
    " Never add names, numbers, dates, or events that are not in the records. Write short"
    " Markdown with no preamble."
)

MAX_QUESTION_CHARS = 500
NO_ANSWER = "The records do not answer this."

# The screens' wording for task status, so the model reads what the manager reads.
STATUS_LABELS = {"idea": "Idea", "ready": "Ready", "in_progress": "In progress",
                 "needs_judgment": "Needs my judgment", "completed": "Completed"}


class AssistantError(ManagerError):
    pass


class ProviderUnavailable(Exception):
    """The provider could not produce a reply. The message is shown to the manager."""


@dataclass(frozen=True)
class ProviderReply:
    text: str
    cost_cents: int = 0


class Provider(Protocol):
    """What every AI provider adapter implements, local or cloud."""

    kind: str  # the settings value: "local" today; one cloud value later
    model: str
    runs_on: str  # said to the manager: where the text goes

    def estimate_cents(self, system: str, prompt: str, max_output_tokens: int) -> int: ...

    def complete(
        self, system: str, prompt: str, *, max_output_tokens: int, timeout: float
    ) -> ProviderReply: ...


# -- the local option --------------------------------------------------------


def check_local_endpoint(endpoint: str) -> str:
    """Accept only plain HTTP to this computer; return it normalized."""
    parsed = urllib.parse.urlsplit(endpoint.strip())
    if (
        parsed.scheme != "http"
        or parsed.hostname not in LOOPBACK_HOSTS
        or parsed.username
        or parsed.password
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise AssistantError(
            "a local model must run on this computer: use an address like"
            f" {DEFAULT_LOCAL_ENDPOINT}"
        )
    try:
        port = parsed.port
    except ValueError as exc:
        raise AssistantError("the local model address has an invalid port") from exc
    host = f"[{parsed.hostname}]" if ":" in parsed.hostname else parsed.hostname
    return f"http://{host}:{port or 80}"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # noqa: ANN002, ANN003
        return None  # a local server must not send the request anywhere else


class LocalModelProvider:
    """A model on this computer via the Ollama-compatible ``/api/generate``.

    Text never leaves the device: the endpoint must be loopback, proxies
    are bypassed, and redirects are refused.
    """

    kind = "local"
    runs_on = "this computer"

    def __init__(self, model: str, endpoint: str = DEFAULT_LOCAL_ENDPOINT):
        self.model = model
        self.endpoint = check_local_endpoint(endpoint)
        self._opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}), _NoRedirect()
        )

    def estimate_cents(self, system: str, prompt: str, max_output_tokens: int) -> int:
        return 0  # runs on the manager's own hardware

    def complete(
        self, system: str, prompt: str, *, max_output_tokens: int, timeout: float
    ) -> ProviderReply:
        body = json.dumps({
            "model": self.model,
            "system": system,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_output_tokens, "temperature": 0.2},
        }).encode("utf-8")
        request = urllib.request.Request(
            f"{self.endpoint}/api/generate", data=body, method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with self._opener.open(request, timeout=timeout) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
        except urllib.error.HTTPError as exc:
            raise ProviderUnavailable(
                f"the local model server answered {exc.code}; check that the model"
                f" '{self.model}' is installed"
            ) from exc
        except (urllib.error.URLError, OSError) as exc:
            raise ProviderUnavailable(
                "the local model server is not reachable on this computer; start it"
                " and try again"
            ) from exc
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ProviderUnavailable("the local model's reply was too large")
        try:
            text = json.loads(raw.decode("utf-8"))["response"]
        except (ValueError, KeyError, TypeError) as exc:
            raise ProviderUnavailable("the local model server's reply was not understood") from exc
        if not isinstance(text, str):
            raise ProviderUnavailable("the local model server's reply was not understood")
        return ProviderReply(text=text, cost_cents=0)


def default_provider_factory(settings: dict[str, Any]) -> Provider | None:
    if settings["provider"] == "local":
        return LocalModelProvider(settings["model"], settings["endpoint"])
    return None


# -- the service -------------------------------------------------------------


class AssistantService:
    """Settings, budgets, and governed drafting for one workspace."""

    def __init__(
        self,
        ws: ManagerWorkspace,
        *,
        provider_factory: Callable[[dict[str, Any]], Provider | None] = default_provider_factory,
        edena: EdenaPolicyEngine | None = None,
        profile_policy: Path = DEFAULT_PROFILE_POLICY,
        timeout: float = REQUEST_TIMEOUT_SECONDS,
    ):
        self.ws = ws
        self.briefs = BriefService(ws)
        self.provider_factory = provider_factory
        self.edena = edena or edena_engine()
        self.profile = json.loads(Path(profile_policy).read_text(encoding="utf-8"))
        self.timeout = timeout

    # -- settings ---------------------------------------------------------

    def settings(self) -> dict[str, Any]:
        row = self.ws.store.conn.execute(
            "SELECT * FROM assistant_settings WHERE workspace_id = ?", (self.ws.info.id,)
        ).fetchone()
        if row is None:  # the default: no model
            return {"provider": "none", "model": "", "endpoint": "",
                    "monthly_budget_cents": 0, "daily_request_limit": 20}
        return {key: row[key] for key in ("provider", "model", "endpoint",
                                          "monthly_budget_cents", "daily_request_limit")}

    def status(self) -> dict[str, Any]:
        settings = self.settings()
        today, month = self.ws.clock()[:10], self.ws.clock()[:7]
        provider = settings["provider"]
        return {
            **settings,
            "runs_on": {"none": "nothing is connected", "local": "this computer"}[provider],
            "requests_today": self._sent_since(today),
            "spent_this_month_cents": self._spent_since(month),
            "cloud": {
                "available": False,
                "reason": "No cloud AI service has been chosen yet (ADR 0004).",
            },
            "gates": list(GATES),
        }

    def connect_local(
        self, by: str, model: str, *, endpoint: str = DEFAULT_LOCAL_ENDPOINT,
        daily_request_limit: int | None = None,
    ) -> dict[str, Any]:
        """The manager explicitly connects a model on their own computer."""
        self._owner(by)
        model = model.strip()
        if not MODEL_NAME.match(model):
            raise AssistantError(
                "enter the local model's name as the model server lists it, e.g. llama3.2"
            )
        endpoint = check_local_endpoint(endpoint)
        limit = self.settings()["daily_request_limit"] if daily_request_limit is None \
            else daily_request_limit
        if not 0 <= limit <= 500:
            raise AssistantError("the daily request limit must be between 0 and 500")
        self._save(by, provider="local", model=model, endpoint=endpoint,
                   monthly_budget_cents=0, daily_request_limit=limit)
        return self.status()

    def disconnect(self, by: str) -> dict[str, Any]:
        """Back to the default: no model."""
        self._owner(by)
        self._save(by, provider="none", model="", endpoint="",
                   monthly_budget_cents=0,
                   daily_request_limit=self.settings()["daily_request_limit"])
        return self.status()

    def _owner(self, by: str) -> None:
        if by.strip() != self.ws.info.owner:
            raise AssistantError(
                "only the accountable manager for this workspace can change its AI settings"
            )

    def _save(self, by: str, **values: Any) -> None:
        with self.ws.store.transaction() as db:
            db.execute(
                "INSERT INTO assistant_settings (workspace_id, provider, model, endpoint,"
                " monthly_budget_cents, daily_request_limit, updated_by, updated_at)"
                " VALUES (:ws, :provider, :model, :endpoint, :monthly_budget_cents,"
                " :daily_request_limit, :by, :at)"
                " ON CONFLICT (workspace_id) DO UPDATE SET provider = :provider,"
                " model = :model, endpoint = :endpoint,"
                " monthly_budget_cents = :monthly_budget_cents,"
                " daily_request_limit = :daily_request_limit, updated_by = :by,"
                " updated_at = :at",
                {**values, "ws": self.ws.info.id, "by": by.strip(), "at": self.ws.clock()},
            )
            self.ws.store.log(by.strip(), "configure", "assistant_settings", self.ws.info.id)

    # -- budget -----------------------------------------------------------

    def _sent_since(self, prefix: str) -> int:
        marks = ",".join("?" * len(_SENT))
        row = self.ws.store.conn.execute(
            f"SELECT count(*) AS n FROM assistant_requests WHERE workspace_id = ?"  # noqa: S608
            f" AND outcome IN ({marks}) AND created_at >= ?",
            (self.ws.info.id, *_SENT, prefix),
        ).fetchone()
        return row["n"]

    def _spent_since(self, prefix: str) -> int:
        row = self.ws.store.conn.execute(
            "SELECT coalesce(sum(coalesce(cost_cents, estimated_cents)), 0) AS c"
            " FROM assistant_requests WHERE workspace_id = ? AND created_at >= ?",
            (self.ws.info.id, prefix),
        ).fetchone()
        return row["c"]

    def _budget_refusal(self, settings: dict[str, Any], estimate: int) -> str | None:
        if self._sent_since(self.ws.clock()[:10]) >= settings["daily_request_limit"]:
            return (f"today's limit of {settings['daily_request_limit']} AI requests"
                    " has been reached")
        month = self._spent_since(self.ws.clock()[:7])
        if month + estimate > settings["monthly_budget_cents"]:
            return ("this request could exceed this month's AI budget"
                    f" ({month} of {settings['monthly_budget_cents']} cents used,"
                    f" up to {estimate} more needed)")
        return None

    # -- drafting ---------------------------------------------------------

    def _prepare(self, week_of: str, today: str) -> "_Prepared":
        """Build exactly what would be sent, and run every gate that comes
        before sending. Writes nothing. The preview and the real request
        both use this, so what the manager sees is what is sent."""
        settings = self.settings()
        body, refs = compose_weekly_brief(self.ws, week_of, today)
        provider = self.provider_factory(settings)
        if provider is None:
            return _Prepared(settings, body, refs, None, "", "", [],
                             ("no_model", "No AI model is connected. This draft was"
                              " composed from your records."))
        _title, prompt = _split_brief(body)
        checks, blocked, estimate = self._gates(provider, settings, SYSTEM_PROMPT, prompt,
                                                "draft_weekly_brief", "draft this")
        return _Prepared(settings, body, refs, provider, prompt,
                         _binding(provider, SYSTEM_PROMPT, prompt), checks, blocked, estimate)

    def _gates(self, provider: Provider, settings: dict[str, Any], system: str, prompt: str,
               intent: str, act: str) -> tuple[list[dict[str, Any]], tuple[str, str] | None, int]:
        """Every gate before sending, in order: (checks, first refusal, cost estimate)."""
        checks: list[dict[str, Any]] = []
        blocked: tuple[str, str] | None = None

        findings = self.ws.privacy.analyze(prompt)
        kinds = ", ".join(sorted({f.entity_type for f in findings}))
        checks.append({
            "gate": "data_rules", "passed": not findings,
            "detail": "No identifying details were found. The check cannot detect names,"
                      " so read the text yourself." if not findings else
                      f"The text includes details the data rules keep on this computer ({kinds}).",
        })
        if findings:
            blocked = ("refused_data_rules", "Nothing was sent: the text includes details"
                       f" the data rules keep on this computer ({kinds}).")

        decision = self._edena_decide(provider, intent, prompt)
        allowed = decision.decision is Decision.ALLOW
        codes = ", ".join(decision.reason_codes)
        checks.append({
            "gate": "edena", "passed": allowed,
            "detail": "The EDENA policy allows an assistant to recommend." if allowed
                      else f"The EDENA policy did not allow an assistant to {act} ({codes}).",
        })
        if not allowed and blocked is None:
            blocked = ("refused_policy", "Nothing was sent: the EDENA policy did not allow an"
                       f" assistant to {act} ({codes}).")

        estimate = provider.estimate_cents(system, prompt, MAX_OUTPUT_TOKENS)
        refusal = self._budget_refusal(settings, estimate)
        checks.append({
            "gate": "budget", "passed": refusal is None,
            "detail": f"Within today's limit ({self._sent_since(self.ws.clock()[:10])} of"
                      f" {settings['daily_request_limit']} requests used)."
                      if refusal is None else refusal[:1].upper() + refusal[1:] + ".",
        })
        if refusal and blocked is None:
            blocked = ("refused_budget", f"Nothing was sent: {refusal}.")
        return checks, blocked, estimate

    def preview_weekly_brief(self, week_of: str, today: str) -> dict[str, Any]:
        """Exactly what asking the model would send, and whether it would be sent."""
        prep = self._prepare(week_of, today)
        provider = prep.provider
        return {
            "week_of": week_of,
            "provider": provider.kind if provider else "none",
            "model": provider.model if provider else "",
            "runs_on": provider.runs_on if provider else "nothing is connected",
            "system": SYSTEM_PROMPT if provider else "",
            "prompt": prep.prompt,
            "prompt_sha256": prep.prompt_sha,
            "checks": prep.checks,
            "will_send": provider is not None and prep.blocked is None,
            "reason": prep.blocked[1] if prep.blocked else "",
        }

    def draft_weekly_brief(self, week_of: str, today: str, requested_by: str, *,
                           reviewed_prompt_sha256: str | None = None) -> dict[str, Any]:
        """Draft this week's brief with the connected model, or honestly without one.

        With ``reviewed_prompt_sha256`` (the app always sends it), the request
        is bound to the text the manager reviewed in the preview: if the
        records changed since, nothing is sent and nothing is drafted.
        """
        self._owner(requested_by)
        prep = self._prepare(week_of, today)
        body, refs, settings, provider = prep.body, prep.refs, prep.settings, prep.provider
        if (reviewed_prompt_sha256 is not None and provider is not None
                and reviewed_prompt_sha256 != prep.prompt_sha):
            raise AssistantError(
                "what would be sent changed after you reviewed it; review it again"
            )
        if prep.blocked:
            outcome, reason = prep.blocked
            return self._fallback(week_of, body, refs, requested_by, settings, outcome, reason,
                                  provider=provider, prompt_sha=prep.prompt_sha)
        prompt, prompt_sha, estimate = prep.prompt, prep.prompt_sha, prep.estimate
        title = body.split("\n", 1)[0]

        request_id, text, failure, cost = self._send(
            provider, SYSTEM_PROMPT, prompt, prompt_sha, estimate, refs, requested_by,
            "weekly_brief", "The AI draft was not saved")
        if failure:
            return self._fallback(week_of, body, refs, requested_by, settings, failure[0],
                                  failure[1], provider=provider, request_id=request_id,
                                  cost=cost)
        ai_body = "\n".join([
            title, "",
            f"**Workspace:** {self.ws.info.name} · **Prepared:** {today} by the AI model"
            f" `{provider.model}` on {provider.runs_on}, from the records cited below.",
            "", text, "",
        ])
        used = list(dict.fromkeys(CITATION.findall(text)))
        revision = self.briefs.add_weekly_draft(
            week_of, ai_body, used, f"{ASSISTANT_PREFIX}{provider.kind}"
        )
        self._finish(request_id, "drafted", "", cost, revision.id)
        return self._result("drafted", "", provider, request_id, revision)

    def _send(self, provider: Provider, system: str, prompt: str, prompt_sha: str,
              estimate: int, refs: list[str], by: str, task: str, refused: str,
              ) -> tuple[str, str, tuple[str, str] | None, int | None]:
        """Call the provider once and check what comes back.

        Returns (request id, checked text, failure, cost). The request is
        recorded before the call, so an interrupted one still counts.
        """
        request_id = self._record(provider, prompt_sha, "provider_failed",
                                  "interrupted before the model replied", estimate, by, task)
        try:
            reply = provider.complete(system, prompt,
                                      max_output_tokens=MAX_OUTPUT_TOKENS, timeout=self.timeout)
        except ProviderUnavailable as exc:
            return request_id, "", ("provider_failed", f"The AI model did not answer: {exc}."), None
        except Exception:  # noqa: BLE001 — an adapter bug must still fall back honestly
            return request_id, "", ("provider_failed",
                                    "The AI model connection failed unexpectedly."), None
        cost = max(0, int(reply.cost_cents))
        problem = self._check_output(reply.text, refs, prompt)
        if problem:
            return request_id, "", ("output_refused", f"{refused}: {problem}."), cost
        return request_id, reply.text.strip(), None, cost

    # -- thinking with one project ----------------------------------------

    def _prepare_project(self, project_id: str, question: str, today: str) -> "_Prepared":
        question = " ".join(question.split())
        if not question:
            raise AssistantError("type the question you want to think through")
        if len(question) > MAX_QUESTION_CHARS:
            raise AssistantError(f"keep the question under {MAX_QUESTION_CHARS} characters")
        context, refs = compose_project_context(self.ws, project_id, today)
        settings = self.settings()
        provider = self.provider_factory(settings)
        prompt = f"## Question\n\n{question}\n\n{context}"
        if provider is None:
            return _Prepared(settings, context, refs, None, "", "", [],
                             ("no_model", "No AI model is connected. The project dashboard"
                              " shows everything the records say."))
        checks, blocked, estimate = self._gates(provider, settings, PROJECT_SYSTEM_PROMPT,
                                                prompt, "answer_project_question",
                                                "answer this")
        return _Prepared(settings, context, refs, provider, prompt,
                         _binding(provider, PROJECT_SYSTEM_PROMPT, prompt), checks,
                         blocked, estimate)

    def preview_project_question(self, project_id: str, question: str,
                                 today: str) -> dict[str, Any]:
        """Exactly what asking about this project would send. Sends and writes nothing."""
        prep = self._prepare_project(project_id, question, today)
        provider = prep.provider
        return {
            "project_id": project_id,
            "provider": provider.kind if provider else "none",
            "model": provider.model if provider else "",
            "runs_on": provider.runs_on if provider else "nothing is connected",
            "system": PROJECT_SYSTEM_PROMPT if provider else "",
            "prompt": prep.prompt,
            "prompt_sha256": prep.prompt_sha,
            "checks": prep.checks,
            "will_send": provider is not None and prep.blocked is None,
            "reason": prep.blocked[1] if prep.blocked else "",
        }

    def answer_project_question(self, project_id: str, question: str, today: str,
                                requested_by: str, *,
                                reviewed_prompt_sha256: str | None = None) -> dict[str, Any]:
        """Ask the connected model about one project.

        The answer is a suggestion shown to the manager, never saved as a
        record. The same gates apply as for the brief, and the request is
        bound to the preview the manager reviewed.
        """
        self._owner(requested_by)
        prep = self._prepare_project(project_id, question, today)
        provider = prep.provider

        def result(outcome: str, reason: str, request_id: str, answer: str = "") -> dict[str, Any]:
            return {
                "outcome": outcome,
                "answered_by_model": outcome == "answered",
                "reason": reason,
                "provider": provider.kind if provider else "none",
                "model": provider.model if provider else "",
                "request_id": request_id,
                "project_id": project_id,
                "answer": answer,
                "source_refs": list(dict.fromkeys(CITATION.findall(answer))),
            }

        if (reviewed_prompt_sha256 is not None and provider is not None
                and reviewed_prompt_sha256 != prep.prompt_sha):
            raise AssistantError(
                "what would be sent changed after you reviewed it; review it again"
            )
        if prep.blocked:
            outcome, reason = prep.blocked
            request_id = self._record(provider, prep.prompt_sha, outcome, reason, 0,
                                      requested_by, "project_question")
            self._finish(request_id, outcome, reason, 0, None)
            return result(outcome, reason, request_id)
        request_id, text, failure, cost = self._send(
            provider, PROJECT_SYSTEM_PROMPT, prep.prompt, prep.prompt_sha, prep.estimate,
            prep.refs, requested_by, "project_question", "The AI answer was not shown")
        if failure:
            self._finish(request_id, failure[0], failure[1], cost, None)
            return result(failure[0], failure[1], request_id)
        self._finish(request_id, "answered", "", cost, None)
        return result("answered", "", request_id, text)

    def _check_output(self, text: str, refs: list[str], sent: str) -> str | None:
        """Why the model's text must not be shown, or None.

        Every line must be checkable: it cites a record that was sent, or it
        repeats a line that was sent word for word. One valid citation does
        not vouch for the other lines.
        """
        if not isinstance(text, str) or not text.strip():
            return "the model returned nothing"
        if len(text) > MAX_OUTPUT_CHARS:
            return "the model's reply was too long"
        findings = self.ws.privacy.analyze(text)
        if findings:
            kinds = ", ".join(sorted({f.entity_type for f in findings}))
            return f"it contained details the data rules do not keep ({kinds})"
        cited = set(CITATION.findall(text))
        invented = sorted(cited - set(refs))
        if invented:
            return "it cited records that were not sent to it (" + ", ".join(invented) + ")"
        if text.strip() == NO_ANSWER:
            return None
        sent_lines = {line.strip() for line in sent.splitlines() if line.strip()}
        # Headings get no exemption: only a heading that was sent word for
        # word passes without a citation, so an invented heading is refused.
        uncited = [
            line for line in text.splitlines()
            if line.strip()
            and not CITATION.search(line)
            and line.strip() not in sent_lines
        ]
        if uncited:
            # Report the count only: rejected text is never stored or shown.
            return (f"{len(uncited)} line(s) had no citation, so they could not be checked"
                    " against your records")
        return None

    def _edena_decide(self, provider: Provider, intent: str, content: str):
        spec = self.profile["assistant_evaluation"]
        tenant = f"personal:{self.ws.info.id}"
        return self.edena.decide(GatewayRequest(
            request_id=new_id("req"),
            actor=Actor(actor_id=f"{ASSISTANT_PREFIX}{provider.kind}", role=spec["role"],
                        tenant=tenant),
            intent=intent,
            content=content,
            risk_tier=RiskTier(spec["risk_tier"]),
            data_class=DataClass(spec["data_class"]),
            action_mode=ActionMode(spec["action_mode"]),
            target_tenant=tenant,
            data_zone=DataZone(spec["data_zone"]),
        ))

    # -- ledger -----------------------------------------------------------

    def _record(self, provider: Provider | None, prompt_sha: str, outcome: str, reason: str,
                estimate: int, by: str, task: str = "weekly_brief") -> str:
        request_id = new_id("air")
        with self.ws.store.transaction() as db:
            db.execute(
                "INSERT INTO assistant_requests (id, workspace_id, task, provider, model,"
                " prompt_sha256, outcome, reason, estimated_cents, requested_by, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (request_id, self.ws.info.id, task, provider.kind if provider else "none",
                 provider.model if provider else "", prompt_sha, outcome, reason,
                 estimate, by.strip(), self.ws.clock()),
            )
            self.ws.store.log(by.strip(), "assistant_request", "assistant_request", request_id)
        return request_id

    def _finish(self, request_id: str, outcome: str, reason: str, cost: int | None,
                revision_id: str | None) -> None:
        with self.ws.store.transaction() as db:
            db.execute(
                "UPDATE assistant_requests SET outcome = ?, reason = ?, cost_cents = ?,"
                " revision_id = ? WHERE id = ?",
                (outcome, reason, cost, revision_id, request_id),
            )

    def _fallback(self, week_of: str, body: str, refs: list[str], by: str,
                  settings: dict[str, Any], outcome: str, reason: str, *,
                  provider: Provider | None = None, prompt_sha: str = "",
                  request_id: str | None = None, cost: int | None = 0) -> dict[str, Any]:
        """The no-model path: the records-only draft, and the reason."""
        revision = self.briefs.add_weekly_draft(week_of, body, refs, self.ws.info.owner)
        if request_id is None:
            request_id = self._record(provider, prompt_sha, outcome, reason, 0, by)
        self._finish(request_id, outcome, reason, cost, revision.id)
        return self._result(outcome, reason, provider, request_id, revision)

    def _result(self, outcome: str, reason: str, provider: Provider | None,
                request_id: str, revision) -> dict[str, Any]:
        return {
            "outcome": outcome,
            "drafted_by_model": outcome == "drafted",
            "reason": reason,
            "provider": provider.kind if provider else "none",
            "model": provider.model if provider else "",
            "request_id": request_id,
            "revision": self.briefs.as_dict(revision),
        }


@dataclass
class _Prepared:
    settings: dict[str, Any]
    body: str
    refs: list[str]
    provider: Provider | None
    prompt: str
    prompt_sha: str
    checks: list[dict[str, Any]]
    blocked: tuple[str, str] | None
    estimate: int = 0


def _split_brief(body: str) -> tuple[str, str]:
    """(title line, the sections) — the records-only provenance line is dropped,
    because it would be untrue of a model's rewrite."""
    lines = body.split("\n")
    first_section = next(i for i, line in enumerate(lines) if line.startswith("## "))
    return lines[0], "\n".join(lines[first_section:]).strip() + "\n"


def compose_project_context(ws: ManagerWorkspace, project_id: str,
                            today: str) -> tuple[str, list[str]]:
    """One project's records as text, with record citations. Deterministic.

    Built from the same read model as the project dashboard, so the model is
    given nothing the manager cannot see there.
    """
    data = project_dashboard(ws, project_id, today=today)
    project, ready = data["project"], data["readiness"]
    refs: list[str] = []

    def cite(record_id: str) -> str:
        refs.append(record_id)
        return f"`{record_id}`"

    lines = [
        "## Project", "",
        f"- Title: {project['title']} {cite(project['id'])}",
        f"- Purpose: {project['purpose']}",
        f"- Owner: {project['owner']}",
        f"- Next milestone: {project['next_milestone'] or 'none recorded'}",
        f"- Status: {project['status']}",
        "",
        "## Where it stands", "",
        f"- {ready['open_tasks']} open task(s), {ready['completed_tasks']} completed",
        f"- {ready['blocked_tasks']} blocked, {ready['overdue_tasks']} overdue,"
        f" {ready['needs_judgment']} waiting on the manager's judgment",
        f"- {ready['tasks_without_next_action']} active task(s) without a next action",
        "",
        "## Open tasks", "",
    ]
    open_rows = [t for t in data["tasks"] if t["status"] != "completed"]
    for t in open_rows:
        notes = [STATUS_LABELS[t["status"]], f"owner {t['owner']}"]
        if t["due_date"]:
            notes.append(f"due {t['due_date']}")
        if t["blocked"]:
            notes.append("blocked")
        if t["paused"]:
            notes.append("paused")
        if t["next_action"]:
            notes.append(f"next: {t['next_action']}")
        lines.append(f"- {t['task']} ({'; '.join(notes)}) {cite(t['id'])}")
    if not open_rows:
        lines.append("- none")
    lines += ["", "## Completed, with evidence", ""]
    for e in data["evidence"]:
        lines.append(f"- {e['task']} — evidence: {e['evidence']} {cite(e['task_id'])}")
    if not data["evidence"]:
        lines.append("- none")
    lines += ["", "## Decisions", ""]
    for d in data["decisions"]:
        lines.append(f"- {d['decided_on']}: {d['question']} Decision: {d['decision']}"
                     f" (by {d['decided_by']}) {cite(d['id'])}")
    if not data["decisions"]:
        lines.append("- none")
    lines += ["", "## Resources", ""]
    for r in data["resources"]:
        lines.append(f"- {r['title']} ({r['kind']}) {cite(r['id'])}")
    if not data["resources"]:
        lines.append("- none")
    return "\n".join(lines) + "\n", refs


def _binding(provider: Provider, system: str, prompt: str) -> str:
    """The hash a preview is bound to: which model, where, and exactly what text.

    Changing the model or its address after the preview changes the hash, so
    the request is refused rather than sent somewhere the manager did not review.
    """
    where = getattr(provider, "endpoint", "")
    return sha256_text(f"{provider.kind}\n{provider.model}\n{where}\n\n{system}\n\n{prompt}")
