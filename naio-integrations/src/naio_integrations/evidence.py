"""Knowledge and Evidence Center (Mission Control spec section 3.4).

Three capabilities on top of governed retrieval:

* **Evidence question builder** — structured PICO/PICOT questions with
  privacy screening on every component (an evidence question never
  carries a patient identifier) and derived search terms that feed
  ``GovernedKnowledge.retrieve`` directly.
* **Claim-to-source traceability** — every claim carries one of the five
  evidence labels and, for source-backed labels, citations that must
  exist in the tenant's knowledge index. No citation, no claim. An
  assumption is stored as awaiting confirmation and stays out of the
  bibliography until a named human confirms it against real sources.
* **"What changed" comparison** — a deterministic statement-level diff
  between two guideline versions, with warnings for date direction,
  jurisdiction changes, and document-type changes.

Evidence never crosses tenant boundaries: the ledger validates every
citation against the same tenant's index, and tracing a claim replays
its sources with full governance metadata (dates, jurisdiction, type),
including the local-policy precedence indicator.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, replace

from .knowledge import STOPWORDS, GovernedKnowledge
from .contract import KnowledgeSource
from .privacy import PrivacyScreen

EVIDENCE_LABELS = (
    "verified_source",
    "local_policy",
    "user_provided_context",
    "ai_synthesis",
    "assumption_requiring_confirmation",
)

SOURCE_BACKED_LABELS = ("verified_source", "local_policy", "ai_synthesis")

_SENTENCES = re.compile(r"(?<=[.!?])\s+|\n+")


class EvidenceError(ValueError):
    pass


@dataclass(frozen=True)
class EvidenceQuestion:
    framework: str  # "PICO" | "PICOT"
    population: str
    intervention: str
    comparison: str
    outcome: str
    timeframe: str | None
    question: str
    search_terms: tuple[str, ...]


class EvidenceQuestionBuilder:
    """Builds structured, privacy-screened PICO/PICOT questions."""

    def __init__(self, privacy: PrivacyScreen | None = None):
        self.privacy = privacy or PrivacyScreen()

    def build(
        self,
        population: str,
        intervention: str,
        comparison: str,
        outcome: str,
        timeframe: str | None = None,
    ) -> EvidenceQuestion:
        components = {
            "population": population,
            "intervention": intervention,
            "comparison": comparison,
            "outcome": outcome,
        }
        screened: dict[str, str] = {}
        for name, value in components.items():
            if not str(value).strip():
                raise EvidenceError(f"a PICO question requires a {name}")
            screened[name] = self.privacy.transform(str(value)).transformed_text
        screened_timeframe = (
            self.privacy.transform(str(timeframe)).transformed_text
            if timeframe and str(timeframe).strip()
            else None
        )
        framework = "PICOT" if screened_timeframe else "PICO"
        question = (
            f"In {screened['population']}, does {screened['intervention']}"
            f" compared with {screened['comparison']}"
            f" affect {screened['outcome']}"
        )
        if screened_timeframe:
            question += f" within {screened_timeframe}"
        question += "?"
        terms: list[str] = []
        for value in [*screened.values(), screened_timeframe or ""]:
            for word in re.findall(r"[A-Za-z][A-Za-z-]+", value.lower()):
                if word not in STOPWORDS and word not in terms:
                    terms.append(word)
        return EvidenceQuestion(
            framework=framework,
            population=screened["population"],
            intervention=screened["intervention"],
            comparison=screened["comparison"],
            outcome=screened["outcome"],
            timeframe=screened_timeframe,
            question=question,
            search_terms=tuple(terms),
        )


@dataclass(frozen=True)
class Claim:
    claim_id: str
    tenant: str
    text: str
    label: str
    source_ids: tuple[str, ...]
    status: str  # "supported" | "awaiting_confirmation"
    confirmed_by: str | None = None
    confirmed_on: str | None = None


class ClaimLedger:
    """Claim-to-source traceability over a tenant's knowledge index."""

    def __init__(
        self,
        knowledge: GovernedKnowledge,
        privacy: PrivacyScreen | None = None,
    ):
        self.knowledge = knowledge
        self.privacy = privacy or PrivacyScreen()
        self._claims: dict[str, Claim] = {}

    def record_claim(
        self,
        tenant: str,
        text: str,
        label: str,
        source_ids: tuple[str, ...] = (),
    ) -> Claim:
        if label not in EVIDENCE_LABELS:
            raise EvidenceError(f"unknown evidence label: {label}")
        if not str(text).strip():
            raise EvidenceError("a claim requires text")
        # Every supplied citation must exist in this tenant's index —
        # including tentative citations on assumptions — so trace() can
        # always replay what a claim cites.
        if source_ids:
            self._require_sources(tenant, source_ids)
        if label in SOURCE_BACKED_LABELS:
            if not source_ids:
                raise EvidenceError(
                    f"a {label} claim requires at least one citation:"
                    " no citation, no claim"
                )
            if label == "local_policy":
                self._require_policy_source(tenant, source_ids)
            status = "supported"
        elif label == "assumption_requiring_confirmation":
            status = "awaiting_confirmation"
        else:  # user_provided_context — provenance is the user themself
            status = "supported"
        screened = self.privacy.transform(str(text)).transformed_text
        seed = json.dumps(
            {"tenant": tenant, "text": screened, "label": label,
             "sources": sorted(source_ids)},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        claim_id = "clm-" + hashlib.sha256(seed).hexdigest()[:16]
        existing = self._claims.get(claim_id)
        if existing is not None:
            # Recording is idempotent: a duplicate never downgrades an
            # already-confirmed claim back to awaiting confirmation.
            return existing
        claim = Claim(
            claim_id=claim_id,
            tenant=tenant,
            text=screened,
            label=label,
            source_ids=tuple(sorted(source_ids)),
            status=status,
        )
        self._claims[claim.claim_id] = claim
        return claim

    def confirm_assumption(
        self,
        claim_id: str,
        source_ids: tuple[str, ...],
        confirmed_by: str,
        confirmed_on: str,
        new_label: str = "verified_source",
    ) -> Claim:
        claim = self._claims.get(claim_id)
        if claim is None:
            raise EvidenceError(f"unknown claim: {claim_id}")
        if claim.status != "awaiting_confirmation":
            raise EvidenceError("only an awaiting assumption can be confirmed")
        if not confirmed_by.strip():
            raise EvidenceError("confirmation requires a named accountable human")
        if not confirmed_on.strip():
            raise EvidenceError("confirmation requires an explicit date")
        if new_label not in SOURCE_BACKED_LABELS:
            raise EvidenceError(
                "a confirmed assumption must take a source-backed label"
            )
        if not source_ids:
            raise EvidenceError("confirmation requires at least one citation")
        self._require_sources(claim.tenant, source_ids)
        if new_label == "local_policy":
            self._require_policy_source(claim.tenant, source_ids)
        confirmed = replace(
            claim,
            label=new_label,
            source_ids=tuple(sorted(source_ids)),
            status="supported",
            confirmed_by=confirmed_by,
            confirmed_on=confirmed_on,
        )
        self._claims[claim_id] = confirmed
        return confirmed

    def unconfirmed_assumptions(self, tenant: str) -> tuple[Claim, ...]:
        return tuple(
            claim
            for claim in sorted(self._claims.values(), key=lambda c: c.claim_id)
            if claim.tenant == tenant and claim.status == "awaiting_confirmation"
        )

    def trace(self, claim_id: str) -> dict:
        """A claim plus the full governance metadata of every cited source."""
        claim = self._claims.get(claim_id)
        if claim is None:
            raise EvidenceError(f"unknown claim: {claim_id}")
        sources = []
        for source_id in claim.source_ids:
            source = self.knowledge.source(claim.tenant, source_id)
            if source is None:
                raise EvidenceError(
                    f"cited source is no longer indexed: {source_id}"
                )
            sources.append(
                {
                    "source_id": source.source_id,
                    "title": source.title,
                    "doc_type": source.doc_type,
                    "effective_date": source.effective_date,
                    "expires_date": source.expires_date,
                    "jurisdiction": source.jurisdiction,
                }
            )
        return {
            "claim_id": claim.claim_id,
            "text": claim.text,
            "label": claim.label,
            "status": claim.status,
            "confirmed_by": claim.confirmed_by,
            "confirmed_on": claim.confirmed_on,
            "sources": sources,
            "local_policy_precedence": any(
                s["doc_type"] == "policy" for s in sources
            ),
        }

    def bibliography(self, tenant: str) -> tuple[str, ...]:
        """Citations for every supported claim; assumptions stay out."""
        cited: dict[str, KnowledgeSource] = {}
        for claim in self._claims.values():
            if claim.tenant != tenant or claim.status != "supported":
                continue
            for source_id in claim.source_ids:
                source = self.knowledge.source(tenant, source_id)
                if source is not None:
                    cited[source_id] = source
        return tuple(
            f"{source.title} ({source.doc_type}, effective"
            f" {source.effective_date}, {source.jurisdiction})"
            f" [{source.source_id}]"
            for source_id, source in sorted(cited.items())
        )

    def _require_sources(self, tenant: str, source_ids: tuple[str, ...]) -> None:
        for source_id in source_ids:
            if self.knowledge.source(tenant, source_id) is None:
                raise EvidenceError(
                    f"citation does not exist in this tenant's index: {source_id}"
                )

    def _require_policy_source(
        self, tenant: str, source_ids: tuple[str, ...]
    ) -> None:
        """A local-policy claim must actually cite a policy document."""
        for source_id in source_ids:
            source = self.knowledge.source(tenant, source_id)
            if source is not None and source.doc_type == "policy":
                return
        raise EvidenceError(
            "a local_policy claim must cite at least one source whose"
            " document type is policy"
        )


def _statements(text: str) -> list[str]:
    return [part.strip() for part in _SENTENCES.split(text) if part.strip()]


def compare_guidelines(old: KnowledgeSource, new: KnowledgeSource) -> dict:
    """Deterministic 'what changed' between two guideline versions."""
    old_statements = _statements(old.content)
    new_statements = _statements(new.content)
    old_set, new_set = set(old_statements), set(new_statements)
    warnings: list[str] = []
    if new.effective_date <= old.effective_date:
        warnings.append(
            "DIRECTION: the 'new' version is not more recent than the 'old'"
            f" ({new.effective_date} vs {old.effective_date}); check the order."
        )
    if old.jurisdiction != new.jurisdiction:
        warnings.append(
            f"JURISDICTION: changed from {old.jurisdiction} to"
            f" {new.jurisdiction}; local applicability must be re-checked."
        )
    if old.doc_type != new.doc_type:
        warnings.append(
            f"DOCUMENT TYPE: changed from {old.doc_type} to {new.doc_type};"
            " policy and research carry different authority."
        )
    return {
        "old_source_id": old.source_id,
        "new_source_id": new.source_id,
        "effective_dates": (old.effective_date, new.effective_date),
        "added": sorted(new_set - old_set),
        "removed": sorted(old_set - new_set),
        "unchanged_count": len(old_set & new_set),
        "warnings": tuple(warnings),
    }
