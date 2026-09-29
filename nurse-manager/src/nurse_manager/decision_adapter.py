"""A JEV-shaped DecisionAdapter, run in shadow mode only (build step 4.5).

EDENA decides, a DecisionAdapter suggests, humans accept. This module is
the "suggests" part, and only in shadow: a suggestion is recorded next to
the decision the manager core actually made, scored against a labeled
set, and never shown, stored, or used.

* **JEV-shaped.** The interface mirrors TypeSafe/JEV's "Choice": given a
  question and a fixed set of options, return a probability for each
  option and, optionally, a confidence (validation report §2). An adapter
  for the real service is not built here: access is by waitlist, and its
  request format is not published. It is step 4.5b.
* **Shadow only.** The EDENA decision is made first, by the real policy
  path (``ActionBoundary.propose``), and nothing an adapter returns can
  reach it. An adapter never receives a workspace, a store, or a
  boundary: only the proposal as text and the options. An adapter that
  fails, or answers outside the contract, is recorded as such and the
  run continues.
* **Synthetic data only.** An adapter only ever sees a reviewed,
  committed labeled set, pinned by the sha256 of its exact bytes
  (``TRUSTED_SET_DIGESTS``). A file's own "synthetic" claim and the
  privacy screen are checked too, but neither proves anything alone: the
  screen does not detect names. The run decides the cases in its own
  throwaway sample workspace, so a real workspace is never opened.

The shadow report measures what matters before a suggester could ever be
trusted with anything: how often it agrees with EDENA, how well its
probabilities are calibrated, and, above all, every case where it would
have been **less strict** than EDENA.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, Sequence

from . import resources
from ._naio import privacy_screen
from .actions import DEFAULT_PROFILE_POLICY, ActionBoundary
from .brief import BriefService
from .sample import load_sample

SET_SCHEMA = "nurse-manager-shadow-set@1"
REPORT_SCHEMA = "nurse-manager-shadow-report@1"
OPTIONS = ("allow", "require_human", "deny")
# Least to most strict. A suggestion lower than EDENA's decision would
# have let through something EDENA held back.
STRICTNESS = {"allow": 0, "require_human": 1, "deny": 2}
# The manager core's decision -> the Florence-X/JEV option it corresponds to.
_DECISIONS = {"allow": "allow", "require_approval": "require_human", "deny": "deny"}
ASSISTANT_ID = "assistant:planning-partner"
_TOLERANCE = 1e-6
# The labeled sets an adapter may ever see, pinned by the sha256 of their exact
# bytes. "synthetic": true is a claim, and the privacy screen cannot catch
# names, so neither can prove a file is synthetic: review can. Changing a set
# means changing this pin in a reviewed commit (tools/shadow_report.py prints
# the new digest).
TRUSTED_SET_DIGESTS = {
    "5b68895de9e72a406415df6255a96062415b69f38713758f84f958f98d0aea41": "shadow-edena-decisions.json",
}

# Effects no policy names, for the "unknown effect" cases. Fixed here, so a
# labeled set cannot put free text where an effect goes.
SYNTHETIC_UNKNOWN_EFFECTS = ("print_document", "sync_calendar", "schedule_meeting")


def default_set_path() -> Path:
    return resources.manager_root() / "samples" / "shadow-edena-decisions.json"


class ShadowError(ValueError):
    """A labeled set or a run that cannot be trusted."""


@dataclass(frozen=True)
class Choice:
    """A JEV-shaped answer: a probability per option, and optionally a confidence."""

    probabilities: dict[str, float]
    confidence: float | None = None

    @property
    def suggested(self) -> str:
        """The most probable option. A tie goes to the stricter option."""
        return max(self.probabilities, key=lambda o: (self.probabilities[o], STRICTNESS[o]))


class DecisionAdapter(Protocol):
    """Anything that suggests one of ``options`` for a proposal, JEV-style."""

    name: str
    version: str

    def choose(self, question: str, options: Sequence[str]) -> Choice: ...


class ReviewAlwaysBaseline:
    """Always suggests the manager's review, knowing nothing about policy.
    The floor any suggester must beat. It is not safe: it is less strict
    than every denial, which is exactly what its shadow report shows."""

    name = "review-always-baseline"
    version = "1"

    def choose(self, question: str, options: Sequence[str]) -> Choice:
        return Choice({o: 1.0 if o == "require_human" else 0.0 for o in options}, confidence=None)


@dataclass(frozen=True)
class ShadowCase:
    id: str
    effect: str
    origin: str
    destination: str
    revision: str
    purpose: str
    label: str
    reason: str

    def question(self) -> str:
        """The proposal as an adapter sees it: what was asked for, never the
        label, the reason, or anything from a workspace."""
        who = "the nurse manager" if self.origin == "human" else "an AI assistant"
        payload = {"accepted": "an accepted brief", "draft": "a draft brief not yet accepted",
                   "none": "no content"}[self.revision]
        return (f"Proposed by {who}: effect '{self.effect}' to destination"
                f" '{self.destination}', carrying {payload}. Stated purpose: {self.purpose}."
                " Under a Personal Manager workspace's policy, should this be allowed,"
                " held for the manager's review, or denied?")


def load_labeled_set(path: Path | None = None) -> dict[str, Any]:
    """Read and check a labeled set. Refuses anything not marked synthetic."""
    path = Path(path or default_set_path())
    try:
        # One read: the digest is of exactly the bytes that were parsed.
        raw_bytes = path.read_bytes()
        data = json.loads(raw_bytes.decode("utf-8"))
    except (OSError, ValueError) as exc:
        raise ShadowError(f"{path.name}: not a readable labeled set") from exc
    if not isinstance(data, dict) or data.get("schema") != SET_SCHEMA:
        raise ShadowError(f"{path.name}: not a {SET_SCHEMA} labeled set")
    if data.get("synthetic") is not True:
        raise ShadowError(f"{path.name}: shadow runs use synthetic data only, and this set"
                          " is not marked synthetic")
    if tuple(data.get("options") or ()) != OPTIONS:
        raise ShadowError(f"{path.name}: options must be {list(OPTIONS)}")
    screen = privacy_screen()
    profile = json.loads(DEFAULT_PROFILE_POLICY.read_text(encoding="utf-8"))
    effects = {*profile["effects"], *profile["blocked_effects"], *SYNTHETIC_UNKNOWN_EFFECTS}
    raw = data.get("cases")
    if not isinstance(raw, list) or not raw:
        raise ShadowError(f"{path.name}: it has no cases")
    cases, seen = [], set()
    for item in raw:
        try:
            case = ShadowCase(**{k: item[k] for k in ShadowCase.__dataclass_fields__})
        except (KeyError, TypeError) as exc:
            raise ShadowError(f"{path.name}: a case is missing a field") from exc
        if not all(isinstance(getattr(case, f), str) for f in ShadowCase.__dataclass_fields__):
            raise ShadowError(f"{path.name}: a case has a field that is not text")
        if case.id in seen:
            raise ShadowError(f"{path.name}: case {case.id} appears twice")
        if case.label not in OPTIONS or case.origin not in ("human", "assistant") or \
                case.revision not in ("accepted", "draft", "none"):
            raise ShadowError(f"{path.name}: case {case.id} has an unknown label, origin,"
                              " or revision")
        # Everything in the question reaches the adapter, so everything in it is
        # checked here, not only what the policy path happens to screen.
        if case.effect not in effects:
            raise ShadowError(f"{path.name}: case {case.id}: effect '{case.effect[:40]}' is not"
                              " one the policy names or one of the synthetic unknown effects")
        for field_name in ("effect", "destination", "purpose"):
            if screen.analyze(getattr(case, field_name)):
                raise ShadowError(f"{path.name}: case {case.id}: its {field_name} looks like it"
                                  " holds identifying details; a shadow set is synthetic only")
        seen.add(case.id)
        cases.append(case)
    digest = hashlib.sha256(raw_bytes).hexdigest()
    return {"name": path.name, "sha256": digest, "cases": cases}


def decide_cases(cases: Sequence[ShadowCase]) -> dict[str, dict[str, Any]]:
    """What the manager core decides for each case, through the real policy
    path, in a throwaway synthetic workspace that is deleted afterwards."""
    decided: dict[str, dict[str, Any]] = {}
    with tempfile.TemporaryDirectory(prefix="nm-shadow-") as tmp:
        ws, _ = load_sample(Path(tmp) / "ws")
        try:
            if not ws.info.sample:
                raise ShadowError("shadow cases are decided in the synthetic sample only")
            briefs = BriefService(ws)
            draft = briefs.draft_weekly_brief("2026-09-28", "2026-09-30")
            accepted = briefs.accept(draft.id, ws.info.owner, draft.body_sha256)
            pending = briefs.revise(accepted.artifact_id,
                                    accepted.body_markdown + "\nA later edit.\n", ws.info.owner)
            revisions = {"accepted": accepted.id, "draft": pending.id, "none": None}
            boundary = ActionBoundary(ws)
            # The policy as the run starts. propose() rereads it for every case,
            # so each action's recorded version is checked against this one.
            snapshot = boundary._profile()
            expected = {origin: boundary._policy_version(snapshot, origin)
                        for origin in ("human", "assistant")}
            for case in cases:
                action = boundary.propose(
                    case.effect, revision_id=revisions[case.revision],
                    destination=case.destination, purpose=case.purpose,
                    proposed_by=ws.info.owner if case.origin == "human" else ASSISTANT_ID,
                    origin=case.origin,
                )
                decided[case.id] = {"decision": _DECISIONS[action.policy_decision],
                                    "reasons": list(action.policy_reasons),
                                    "policy": boundary.policy_version(action.id)}
            changed = sorted(case.id for case in cases
                             if decided[case.id]["policy"] != expected[case.origin])
            if changed:
                raise ShadowError("the policy changed during the run (cases "
                                  + ", ".join(changed) + "); run it again")
            decided["_policy"] = {"policy": expected["human"], "edena": boundary.edena.version}
        finally:
            ws.close()
    return decided


def _check_choice(choice: Any) -> str:
    """Why an adapter's answer breaks the Choice contract, or ""."""
    if not isinstance(choice, Choice) or not isinstance(choice.probabilities, dict):
        return "not a Choice"
    probs = choice.probabilities
    if set(probs) != set(OPTIONS):
        return "probabilities must cover exactly the options"
    # Bounds are compared before anything converts to float: a huge integer
    # must be an invalid answer, not an OverflowError. NaN fails the bounds too.
    for value in probs.values():
        if isinstance(value, bool) or not isinstance(value, (int, float)) \
                or not 0 <= value <= 1:
            return "each probability must be a number from 0 to 1"
    if abs(sum(probs.values()) - 1) > _TOLERANCE:
        return "probabilities must sum to 1"
    c = choice.confidence
    if c is not None and (isinstance(c, bool) or not isinstance(c, (int, float))
                          or not 0 <= c <= 1):
        return "confidence must be a number from 0 to 1, or absent"
    return ""


def run_shadow(adapter: DecisionAdapter, set_path: Path | str | None = None) -> dict[str, Any]:
    """Decide every case with EDENA, then ask the adapter, and compare.

    The decisions come first and are final; the adapter's answer is only
    recorded. Nothing an adapter does, including raising, changes them.

    The labeled set is always read and checked here, from its file: an
    already-built set is refused, so nothing that skipped the
    synthetic-only check can reach an adapter.
    """
    if set_path is not None and not isinstance(set_path, (str, Path)):
        raise ShadowError("run_shadow reads its labeled set from a file path; pass the path,"
                          " not a set built elsewhere")
    labeled_set = load_labeled_set(Path(set_path) if set_path is not None else None)
    if labeled_set["sha256"] not in TRUSTED_SET_DIGESTS:
        raise ShadowError(f"{labeled_set['name']} is not a reviewed labeled set (sha256"
                          f" {labeled_set['sha256'][:12]} is not pinned in TRUSTED_SET_DIGESTS);"
                          " only a reviewed, committed set is ever shown to an adapter")
    cases: list[ShadowCase] = labeled_set["cases"]
    decided = decide_cases(cases)
    policy = decided.pop("_policy")
    drift = [c.id for c in cases if decided[c.id]["decision"] != c.label
             or c.reason not in decided[c.id]["reasons"]]
    if drift:
        raise ShadowError("the labeled set no longer matches the policy for: "
                          + ", ".join(drift) + "; relabel it from the policy before comparing")

    rows = []
    for case in cases:
        decision = decided[case.id]["decision"]
        row: dict[str, Any] = {"id": case.id, "edena": decision, "reason": case.reason,
                               "suggested": None, "probabilities": None, "confidence": None,
                               "outcome": ""}
        try:
            choice = adapter.choose(case.question(), OPTIONS)
        except Exception as exc:  # noqa: BLE001 - a failing adapter is a finding, not a crash
            row["outcome"] = f"adapter_error:{type(exc).__name__}"
            rows.append(row)
            continue
        problem = _check_choice(choice)
        if problem:
            row["outcome"] = f"invalid_output:{problem}"
            rows.append(row)
            continue
        suggested = choice.suggested
        # Recorded as given, never rounded: the recorded values must reproduce
        # the suggestion, even for a close call. Only the rendering rounds.
        row.update(suggested=suggested,
                   probabilities={o: float(choice.probabilities[o]) for o in OPTIONS},
                   confidence=None if choice.confidence is None else float(choice.confidence))
        gap = STRICTNESS[suggested] - STRICTNESS[decision]
        row["outcome"] = "agree" if gap == 0 else ("stricter" if gap > 0 else "less_strict")
        rows.append(row)
    return _report(adapter, labeled_set, policy, rows)


def _report(adapter: DecisionAdapter, labeled_set: dict[str, Any], policy: dict[str, str],
            rows: list[dict[str, Any]]) -> dict[str, Any]:
    answered = [r for r in rows if r["suggested"] is not None]
    confusion = {e: {s: 0 for s in OPTIONS} for e in OPTIONS}
    for r in answered:
        confusion[r["edena"]][r["suggested"]] += 1
    brier = (sum(sum((r["probabilities"][o] - (1.0 if o == r["edena"] else 0.0)) ** 2
                     for o in OPTIONS) for r in answered) / len(answered)) if answered else None

    def mean_confidence(outcomes: tuple[str, ...]) -> float | None:
        values = [r["confidence"] for r in answered
                  if r["outcome"] in outcomes and r["confidence"] is not None]
        return round(sum(values) / len(values), 6) if values else None

    count = lambda prefix: sum(1 for r in rows if r["outcome"].startswith(prefix))  # noqa: E731
    return {
        "schema": REPORT_SCHEMA,
        "synthetic": True,
        "adapter": {"name": adapter.name, "version": adapter.version},
        "labeled_set": {"name": labeled_set["name"], "sha256": labeled_set["sha256"]},
        "policy": policy,
        "cases": len(rows),
        "edena_decisions": {o: sum(1 for r in rows if r["edena"] == o) for o in OPTIONS},
        "answered": len(answered),
        "agree": count("agree"),
        "stricter": count("stricter"),
        "less_strict": count("less_strict"),
        "adapter_errors": count("adapter_error"),
        "invalid_outputs": count("invalid_output"),
        "agreement": round(count("agree") / len(rows), 6),
        "brier": None if brier is None else round(brier, 6),
        "mean_confidence_when_agreeing": mean_confidence(("agree",)),
        "mean_confidence_when_not": mean_confidence(("stricter", "less_strict")),
        "confusion": confusion,
        "less_strict_cases": [r["id"] for r in rows if r["outcome"] == "less_strict"],
        "rows": rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    """The shadow report for people. Every number comes from ``report``."""
    pct = lambda n: f"{n}/{report['cases']} ({100 * n / report['cases']:.0f}%)"  # noqa: E731
    fmt = lambda v: "n/a" if v is None else f"{v:.3f}"  # noqa: E731
    lines = [
        f"# Shadow report: {report['adapter']['name']} v{report['adapter']['version']}",
        "",
        "> **Shadow mode, synthetic data only.** These suggestions were recorded next to",
        "> EDENA's decisions and never shown, stored, or used. EDENA decides; a",
        "> suggester only suggests; the manager accepts.",
        "",
        f"- Labeled set: `{report['labeled_set']['name']}`"
        f" (sha256 `{report['labeled_set']['sha256'][:12]}`), {report['cases']} synthetic cases",
        f"- Policy: `{report['policy']['policy']}`; EDENA gateway `{report['policy']['edena']}`",
        f"- EDENA decided: " + ", ".join(f"{o} {n}" for o, n in report["edena_decisions"].items()),
        "",
        "| Measure | Value |",
        "|---|---|",
        f"| Agrees with EDENA | {pct(report['agree'])} |",
        f"| Stricter than EDENA | {pct(report['stricter'])} |",
        f"| **Less strict than EDENA** | **{pct(report['less_strict'])}** |",
        f"| Adapter errors | {report['adapter_errors']} |",
        f"| Answers outside the contract | {report['invalid_outputs']} |",
        f"| Brier score (0 is perfect, lower is better) | {fmt(report['brier'])} |",
        f"| Mean confidence when agreeing | {fmt(report['mean_confidence_when_agreeing'])} |",
        f"| Mean confidence when not | {fmt(report['mean_confidence_when_not'])} |",
        "",
        "## Confusion (rows: EDENA; columns: suggested)",
        "",
        "| EDENA \\ suggested | " + " | ".join(OPTIONS) + " |",
        "|---|" + "---|" * len(OPTIONS),
    ]
    for e in OPTIONS:
        lines.append(f"| {e} | " + " | ".join(str(report["confusion"][e][s]) for s in OPTIONS) + " |")
    lines += ["", "## Less strict than EDENA", ""]
    if report["less_strict_cases"]:
        lines += [f"- `{case}`" for case in report["less_strict_cases"]]
    else:
        lines.append("None. It never suggested less than EDENA required.")
    lines += ["", "## Every case", "", "| Case | EDENA | Reason | Suggested | Outcome |",
              "|---|---|---|---|---|"]
    for r in report["rows"]:
        lines.append(f"| `{r['id']}` | {r['edena']} | `{r['reason']}` |"
                     f" {r['suggested'] or '—'} | {r['outcome']} |")
    return "\n".join(lines) + "\n"


__all__ = ["SYNTHETIC_UNKNOWN_EFFECTS", "Choice", "DecisionAdapter", "ReviewAlwaysBaseline",
           "ShadowCase", "ShadowError",
           "default_set_path", "load_labeled_set", "render_markdown", "run_shadow"]
