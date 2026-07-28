"""First-run example workspace (Mission Control spec sections 13 and 14).

Builds the synthetic example workspace every packet ships with: a
completed sample ADPIE project (a genuine ``AdpieWorkflow`` checkpoint,
not a mock), a labeled evidence library, a sample deliverable that went
through the full draft-review lifecycle, and the first-run pathway that
turns one of the section 13 choices into a real, editable artifact in a
single call — the ten-minute-first-artifact acceptance criterion.

Everything *committed in the example workspace* is synthetic and says
so: every JSON record carries ``"synthetic": true`` and every example
document carries the synthetic banner. The one deliberate exception is
``first_run()``: its product is the user's own real first draft (spec
section 13 calls it "one real artifact"), so it carries the draft
banner, not the synthetic banner.
Content is written to pass the privacy screen — an example workspace
that trips its own identifier detection would be teaching the wrong
lesson. The workspace can be reset or removed (spec section 16).

Deterministic: the builder takes a fixed clock so committed artifacts
rebuild byte-identically in CI.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from .deliverables import Deliverable, DeliverableStudio
from .orchestration import AdpieWorkflow

SYNTHETIC_LABEL = (
    "SYNTHETIC EXAMPLE — every person, organization, and detail is fictional"
    " teaching material. Not a real patient, colleague, or institution."
)

FIRST_RUN_CHOICES = {
    "learning-plan": "personal-development-plan",
    "structured-question": "structured-question",
    "project-one-pager": "project-one-pager",
    "lesson-plan": "education-plan",
    "executive-brief": "executive-brief",
    "evidence-question": "evidence-question",
    "research-question": "research-question",
}

EXAMPLE_TIMESTAMP = "2026-07-01T09:00:00+00:00"
EXAMPLE_REVIEW_DATE = "2026-07-01"


class WorkspaceError(RuntimeError):
    pass


class ExampleWorkspace:
    """Builds, resets, and removes the synthetic example workspace."""

    def __init__(self, root: Path, studio: DeliverableStudio | None = None):
        self.root = root
        self.studio = studio or DeliverableStudio()

    def build(self) -> dict[str, Any]:
        if self.root.exists() and any(self.root.iterdir()):
            raise WorkspaceError(
                "workspace directory is not empty; use reset() to rebuild"
            )
        self.root.mkdir(parents=True, exist_ok=True)
        manifest = {
            "synthetic": True,
            "label": SYNTHETIC_LABEL,
            "contents": {
                "project": "project/sample-improvement-project.json",
                "evidence": "evidence/evidence-library.json",
                "deliverable": "deliverables/sample-project-charter.md",
                "first_run": "first-run/pathway.json",
            },
            "reset_note": (
                "This example workspace can be reset or removed at any time;"
                " it exists only to show what working content looks like."
            ),
        }
        self._build_sample_project()
        self._build_evidence_library()
        self._build_sample_deliverable()
        self._build_first_run_pathway()
        self._write_json(self.root / "workspace.json", manifest)
        return manifest

    def reset(self) -> dict[str, Any]:
        self.remove()
        return self.build()

    def remove(self) -> bool:
        if self.root.exists():
            shutil.rmtree(self.root)
            return True
        return False

    def first_run(self, choice: str, answers: dict[str, str] | None = None) -> Deliverable:
        """One call from onboarding choice to real, editable artifact."""
        template_id = FIRST_RUN_CHOICES.get(choice)
        if template_id is None:
            raise WorkspaceError(
                f"unknown first-run choice: {choice}; "
                f"choose one of {sorted(FIRST_RUN_CHOICES)}"
            )
        return self.studio.scaffold(
            template_id,
            context=answers or {},
            provenance=("first-run onboarding answers",),
        )

    def _build_sample_project(self) -> None:
        checkpoints = self.root / "project"
        runtime = AdpieWorkflow(checkpoints, now=lambda: EXAMPLE_TIMESTAMP)
        workflow_id = "sample-improvement-project"
        runtime.start(
            workflow_id,
            {
                "synthetic": True,
                "label": SYNTHETIC_LABEL,
                "project": "Reduce end-of-shift huddle overruns on a fictional unit",
            },
        )
        runtime.advance(
            workflow_id,
            findings="Fictional baseline: huddles ran long on 6 of 10 observed days.",
        )
        runtime.advance(
            workflow_id,
            problem="Huddle agenda has no owner and no timekeeper (synthetic scenario).",
        )
        runtime.advance(
            workflow_id,
            plan="Pilot a one-page timed agenda with a rotating timekeeper for two weeks.",
        )
        runtime.authorize(workflow_id, approver="Example Charge Nurse (fictional)", approved=True)
        runtime.advance(workflow_id, implemented="Timed agenda piloted (synthetic).")
        runtime.advance(
            workflow_id,
            outcome="Fictional result: overruns fell from 6 of 10 days to 2 of 10.",
        )
        runtime.advance(workflow_id, lesson="Keep the timekeeper; revisit agenda quarterly.")

    def _build_evidence_library(self) -> None:
        library = {
            "synthetic": True,
            "label": SYNTHETIC_LABEL,
            "items": [
                {
                    "source_id": "example-verified-1",
                    "title": "Fictional systematic review of huddle structure",
                    "evidence_label": "verified_source",
                    "doc_type": "research",
                    "effective_date": "2025-11-01",
                    "expires_date": None,
                    "jurisdiction": "US",
                    "note": "Illustrates how a verified source is captured with dates.",
                },
                {
                    "source_id": "example-policy-1",
                    "title": "Fictional unit huddle standard",
                    "evidence_label": "local_policy",
                    "doc_type": "policy",
                    "effective_date": "2026-01-01",
                    "expires_date": "2027-01-01",
                    "jurisdiction": "US",
                    "note": "Local policy takes precedence over general findings.",
                },
                {
                    "source_id": "example-synthesis-1",
                    "title": "Assistant-drafted summary of the two sources above",
                    "evidence_label": "ai_synthesis",
                    "doc_type": "research",
                    "effective_date": "2026-07-01",
                    "expires_date": None,
                    "jurisdiction": "US",
                    "note": "AI synthesis is labeled and never outranks its sources.",
                },
                {
                    "source_id": "example-assumption-1",
                    "title": "Assumed staffing pattern on the fictional unit",
                    "evidence_label": "assumption_requiring_confirmation",
                    "doc_type": "local_practice",
                    "effective_date": "2026-07-01",
                    "expires_date": None,
                    "jurisdiction": "US",
                    "note": "Assumptions are labeled until a human confirms them.",
                },
            ],
        }
        self._write_json(self.root / "evidence" / "evidence-library.json", library)

    def _build_sample_deliverable(self) -> None:
        draft = self.studio.scaffold(
            "project-charter",
            context={
                "problem_and_background": (
                    "On a fictional medical unit, end-of-shift huddles overran"
                    " their ten-minute window on 6 of 10 observed days,"
                    " delaying handoff (synthetic example)."
                ),
                "aim": (
                    "Reduce huddle overruns from 6 of 10 days to 2 of 10 days"
                    " within two weeks on the fictional unit."
                ),
            },
            provenance=(
                "project/sample-improvement-project.json",
                "evidence/evidence-library.json",
            ),
            synthetic=True,
        )
        reviewed = self.studio.record_review(
            draft,
            reviewer="Example Reviewer (fictional)",
            disposition="approved",
            reviewed_on=EXAMPLE_REVIEW_DATE,
            notes="Approved as a synthetic teaching example only.",
        )
        target = self.root / "deliverables" / "sample-project-charter.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.studio.render(reviewed), encoding="utf-8")

    def _build_first_run_pathway(self) -> None:
        pathway = {
            "synthetic": True,
            "label": SYNTHETIC_LABEL,
            "goal": (
                "Within ten minutes of onboarding, the user completes one real"
                " artifact (Mission Control spec, section 13, step 5)."
            ),
            "choices": {
                choice: {
                    "template_id": template_id,
                    "produces": self.studio.describe(template_id)["title"],
                }
                for choice, template_id in sorted(FIRST_RUN_CHOICES.items())
            },
            "how": (
                "Call ExampleWorkspace.first_run(choice, answers) — one call"
                " returns an editable draft with the mandatory draft banner."
            ),
        }
        self._write_json(self.root / "first-run" / "pathway.json", pathway)

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
