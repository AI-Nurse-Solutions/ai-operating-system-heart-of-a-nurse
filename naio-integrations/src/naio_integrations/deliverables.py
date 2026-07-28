"""Deliverable Studio (Mission Control spec section 3.6).

Generates editable first drafts from approved workspace content. The
section 3.6 rule is structural here, not advisory: **no output may be
presented as final or approved merely because it was generated.**

* Every scaffold is born with status ``draft`` and renders with a
  mandatory draft banner. ``render()`` has no way to omit it.
* The only path out of draft is ``record_review`` by a named human with
  an explicit disposition and date. Approved renders carry the review
  attestation instead of silently looking finished.
* Workspace content passed into a scaffold is privacy-screened first,
  so identifiers cannot ride into a deliverable.
* Synthetic deliverables are labeled as synthetic in every render.

Deterministic by construction: no clocks, no randomness — the same
template and context always produce the same deliverable, which lets
example artifacts be committed and rebuilt byte-identically in CI.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from .privacy import PrivacyScreen

DEFAULT_TEMPLATE_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "deliverable-templates.json"
)

DRAFT_BANNER = (
    "> **DRAFT — AI-generated scaffold.** Not final and not approved. A named,"
    " accountable human must review, edit, and approve this content before it"
    " is used anywhere. Generation alone never makes content final."
)

SYNTHETIC_BANNER = (
    "> **SYNTHETIC EXAMPLE.** Every person, organization, and detail in this"
    " document is fictional teaching material — not a real patient, colleague,"
    " or institution, and not clinically validated evidence."
)

VALID_DISPOSITIONS = ("approved", "needs_changes", "rejected")


class DeliverableError(ValueError):
    pass


@dataclass(frozen=True)
class Deliverable:
    deliverable_id: str
    template_id: str
    title: str
    body_markdown: str
    status: str  # "draft" | "reviewed"
    provenance: tuple[str, ...]
    synthetic: bool = False
    review: dict[str, str] | None = None

    @property
    def approved(self) -> bool:
        return (
            self.status == "reviewed"
            and self.review is not None
            and self.review.get("disposition") == "approved"
        )


class DeliverableStudio:
    """Template-driven scaffold generator with the never-final rule."""

    def __init__(
        self,
        template_path: Path | None = None,
        privacy: PrivacyScreen | None = None,
    ):
        path = template_path or DEFAULT_TEMPLATE_PATH
        self.catalog: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        self.privacy = privacy or PrivacyScreen()

    def templates(self, group: str | None = None) -> tuple[str, ...]:
        items = self.catalog["templates"]
        if group is None:
            return tuple(sorted(items))
        return tuple(
            sorted(t for t, spec in items.items() if spec.get("group") == group)
        )

    def describe(self, template_id: str) -> dict[str, Any]:
        template = self.catalog["templates"].get(template_id)
        if template is None:
            raise DeliverableError(f"unknown deliverable template: {template_id}")
        return template

    def scaffold(
        self,
        template_id: str,
        context: dict[str, str] | None = None,
        provenance: tuple[str, ...] = (),
        synthetic: bool = False,
    ) -> Deliverable:
        template = self.describe(template_id)
        context = context or {}
        screened: dict[str, str] = {}
        redacted_fields: list[str] = []
        for key in sorted(context):
            result = self.privacy.transform(str(context[key]))
            screened[key] = result.transformed_text
            if result.findings:
                redacted_fields.append(key)

        lines: list[str] = [f"# {template['title']}", ""]
        if synthetic:
            lines += [SYNTHETIC_BANNER, ""]
        lines += [DRAFT_BANNER, ""]
        if provenance:
            lines.append("**Generated from workspace sources:**")
            lines += [f"- {source}" for source in provenance]
        else:
            lines.append(
                "**Generated from workspace sources:** none recorded — add the"
                " sources this draft relies on."
            )
        lines.append("")
        if redacted_fields:
            lines += [
                "> **Privacy screen:** identifying content was redacted from"
                f" the supplied fields: {', '.join(redacted_fields)}. Review"
                " whether this material belongs in a deliverable at all.",
                "",
            ]
        for section in template["sections"]:
            key = section["heading"].lower().replace(" ", "_")
            lines += [f"## {section['heading']}", ""]
            lines += [f"_{section['guidance']}_", ""]
            if key in screened:
                lines += [screened[key], ""]
            else:
                lines += ["*(draft your content here)*", ""]

        body = "\n".join(lines).rstrip() + "\n"
        seed = json.dumps(
            {
                "template": template_id,
                "context": screened,
                "provenance": list(provenance),
                "synthetic": synthetic,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        deliverable_id = "dlv-" + hashlib.sha256(seed).hexdigest()[:16]
        return Deliverable(
            deliverable_id=deliverable_id,
            template_id=template_id,
            title=template["title"],
            body_markdown=body,
            status="draft",
            provenance=provenance,
            synthetic=synthetic,
        )

    def record_review(
        self,
        deliverable: Deliverable,
        reviewer: str,
        disposition: str,
        reviewed_on: str,
        notes: str = "",
    ) -> Deliverable:
        if not reviewer.strip():
            raise DeliverableError("review requires a named, accountable human")
        if disposition not in VALID_DISPOSITIONS:
            raise DeliverableError(f"unknown disposition: {disposition}")
        if not reviewed_on.strip():
            raise DeliverableError("review requires an explicit review date")
        return replace(
            deliverable,
            status="reviewed",
            review={
                "reviewer": reviewer,
                "disposition": disposition,
                "reviewed_on": reviewed_on,
                "notes": notes,
            },
        )

    def render(self, deliverable: Deliverable) -> str:
        """The only rendering path — the status banner cannot be omitted."""
        if deliverable.approved:
            review = deliverable.review or {}
            attestation = (
                f"> **Reviewed draft.** Approved by {review.get('reviewer')} on"
                f" {review.get('reviewed_on')}. Approval was a human decision;"
                " generation alone never makes content final."
            )
            return deliverable.body_markdown.replace(DRAFT_BANNER, attestation, 1)
        if deliverable.status == "reviewed":
            review = deliverable.review or {}
            verdict = (
                f"> **Reviewed draft — {review.get('disposition')}.** Reviewed by"
                f" {review.get('reviewer')} on {review.get('reviewed_on')}."
                " This content is not approved for use."
            )
            return deliverable.body_markdown.replace(DRAFT_BANNER, verdict, 1)
        return deliverable.body_markdown
