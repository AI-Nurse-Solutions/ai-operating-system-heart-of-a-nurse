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
_SENT = ("drafted", "provider_failed", "output_refused")

GATES = (
    "Only material your workspace's data rules admit is sent, and it is checked again first.",
    "The EDENA policy decides whether an assistant may draft this; assistants only recommend.",
    "A daily request limit and a monthly cost budget are checked before anything is sent.",
    "What the model writes is saved as a draft. Only you can accept it.",
    "If the model is unavailable, you get the draft composed from your records, and the reason.",
)

SYSTEM_PROMPT = (
    "You help a nurse manager prepare their weekly brief. Rewrite the brief below"
    " so it is clear and concise. Use only the facts it contains; never add names,"
    " numbers, dates, or events that are not in it. Keep each record citation"
    " exactly as written, in backticks, next to the fact it supports. Keep the"
    " section headings. Write Markdown with no title line and no preamble."
)


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

    def draft_weekly_brief(self, week_of: str, today: str, requested_by: str) -> dict[str, Any]:
        """Draft this week's brief with the connected model, or honestly without one."""
        self._owner(requested_by)
        settings = self.settings()
        body, refs = compose_weekly_brief(self.ws, week_of, today)
        provider = self.provider_factory(settings)
        if provider is None:
            return self._fallback(
                week_of, body, refs, requested_by, settings, "no_model",
                "No AI model is connected. This draft was composed from your records.",
            )

        title, sections = _split_brief(body)
        prompt = sections
        prompt_sha = sha256_text(SYSTEM_PROMPT + "\n\n" + prompt)
        findings = self.ws.privacy.analyze(prompt)
        if findings:
            kinds = ", ".join(sorted({f.entity_type for f in findings}))
            return self._fallback(
                week_of, body, refs, requested_by, settings, "refused_data_rules",
                f"Nothing was sent: the records include details the data rules keep"
                f" on this computer ({kinds}).", provider=provider, prompt_sha=prompt_sha,
            )
        decision = self._edena_decide(provider, "draft_weekly_brief", prompt)
        if decision.decision is not Decision.ALLOW:
            return self._fallback(
                week_of, body, refs, requested_by, settings, "refused_policy",
                "Nothing was sent: the EDENA policy did not allow an assistant to draft"
                f" this ({', '.join(decision.reason_codes)}).",
                provider=provider, prompt_sha=prompt_sha,
            )
        estimate = provider.estimate_cents(SYSTEM_PROMPT, prompt, MAX_OUTPUT_TOKENS)
        refusal = self._budget_refusal(settings, estimate)
        if refusal:
            return self._fallback(
                week_of, body, refs, requested_by, settings, "refused_budget",
                f"Nothing was sent: {refusal}.", provider=provider, prompt_sha=prompt_sha,
            )

        # Recorded before the call, so an interrupted request still counts.
        request_id = self._record(provider, prompt_sha, "provider_failed",
                                  "interrupted before the model replied", estimate,
                                  requested_by)
        try:
            reply = provider.complete(SYSTEM_PROMPT, prompt,
                                      max_output_tokens=MAX_OUTPUT_TOKENS, timeout=self.timeout)
        except ProviderUnavailable as exc:
            return self._fallback(
                week_of, body, refs, requested_by, settings, "provider_failed",
                f"The AI model did not answer: {exc}.", provider=provider,
                request_id=request_id, cost=None,
            )
        except Exception:  # noqa: BLE001 — an adapter bug must still fall back honestly
            return self._fallback(
                week_of, body, refs, requested_by, settings, "provider_failed",
                "The AI model connection failed unexpectedly.", provider=provider,
                request_id=request_id, cost=None,
            )
        cost = max(0, int(reply.cost_cents))
        problem = self._check_output(reply.text, refs)
        if problem:
            return self._fallback(
                week_of, body, refs, requested_by, settings, "output_refused",
                f"The AI draft was not saved: {problem}.", provider=provider,
                request_id=request_id, cost=cost,
            )
        text = reply.text.strip()
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

    def _check_output(self, text: str, refs: list[str]) -> str | None:
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
            return "it cited records that were not in your brief (" + ", ".join(invented) + ")"
        if refs and not cited:
            return "it cited none of your records, so its lines could not be checked"
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
                estimate: int, by: str) -> str:
        request_id = new_id("air")
        with self.ws.store.transaction() as db:
            db.execute(
                "INSERT INTO assistant_requests (id, workspace_id, task, provider, model,"
                " prompt_sha256, outcome, reason, estimated_cents, requested_by, created_at)"
                " VALUES (?, ?, 'weekly_brief', ?, ?, ?, ?, ?, ?, ?, ?)",
                (request_id, self.ws.info.id, provider.kind if provider else "none",
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
                  request_id: str | None = None, cost: int = 0) -> dict[str, Any]:
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


def _split_brief(body: str) -> tuple[str, str]:
    """(title line, the sections) — the records-only provenance line is dropped,
    because it would be untrue of a model's rewrite."""
    lines = body.split("\n")
    first_section = next(i for i, line in enumerate(lines) if line.startswith("## "))
    return lines[0], "\n".join(lines[first_section:]).strip() + "\n"
