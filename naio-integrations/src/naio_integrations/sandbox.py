"""Healthcare sandbox (patterns: synthetichealth/synthea, hapifhir/hapi-fhir).

Phase 3 of the Mission Control release sequence: a safe place to practice
on patient-shaped data with **no patients in it**. The sandbox expands a
reviewed case catalog into FHIR-shaped resource bundles (the Synthea
pattern: generated records with numeric-suffix names that are
unmistakably synthetic) and serves them through a read/search surface
shaped like a FHIR server (the HAPI FHIR pattern) — without vendoring
either project, per the Integration Contract.

Boundary invariants, enforced at admission and never waived:

* every resource must carry the sandbox synthetic security label —
  unlabeled content is refused, so nothing can pose as sandbox data;
* every string in every resource must pass the privacy screen — content
  that looks like real identifiers is refused, so real patient data
  cannot be smuggled in under a synthetic label;
* reads and searches are tenant-scoped; another tenant's request reads
  as "unknown resource" (existence is not disclosed);
* the sandbox is D0 by construction (synthetic), but detection reduces
  risk — it never proves content is de-identified, so admission still
  screens everything.

The sandbox plugs into the existing contract surfaces rather than adding
new ones: ``as_knowledge_sources`` feeds governed retrieval, and
``start_case_workflow`` seeds the ADPIE orchestration runtime with a
synthetic-flagged context.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from .contract import KnowledgeSource
from .privacy import PrivacyScreen

DEFAULT_CASE_CATALOG_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "healthcare-sandbox-cases.json"
)

SANDBOX_SECURITY_SYSTEM = "urn:naio:healthcare-sandbox"
SANDBOX_SECURITY_CODE = "SYNTHETIC"

SANDBOX_BANNER = (
    "SYNTHETIC RECORD — generated for practice and demonstration."
    " No real person exists behind this data, and it is not clinical"
    " evidence. Numeric-suffix names mark every generated record."
)


class SandboxIntegrityError(ValueError):
    """Content violated a sandbox boundary invariant and was refused."""


def _synthetic_meta() -> dict[str, Any]:
    return {
        "security": [
            {
                "system": SANDBOX_SECURITY_SYSTEM,
                "code": SANDBOX_SECURITY_CODE,
                "display": SANDBOX_BANNER,
            }
        ]
    }


def _is_synthetic(resource: dict[str, Any]) -> bool:
    for label in resource.get("meta", {}).get("security", []):
        if (
            label.get("system") == SANDBOX_SECURITY_SYSTEM
            and label.get("code") == SANDBOX_SECURITY_CODE
        ):
            return True
    return False


def _iter_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _iter_strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _iter_strings(item)


class SyntheticPatientSandbox:
    """Deterministic synthetic-patient store behind a FHIR-shaped surface."""

    def __init__(
        self,
        catalog_path: Path | None = None,
        privacy: PrivacyScreen | None = None,
    ):
        path = catalog_path or DEFAULT_CASE_CATALOG_PATH
        self.catalog: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        self.privacy = privacy or PrivacyScreen()
        # tenant -> resource_type -> resource_id -> resource
        self._store: dict[str, dict[str, dict[str, dict[str, Any]]]] = {}

    # ------------------------------------------------------------------
    # Case generation (Synthea pattern: catalog in, synthetic bundle out)

    def case_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self.catalog["cases"]))

    def _case(self, case_id: str) -> dict[str, Any]:
        cases = self.catalog["cases"]
        if case_id not in cases:
            raise SandboxIntegrityError(f"unknown sandbox case: {case_id}")
        return cases[case_id]

    def build_case(self, case_id: str) -> dict[str, Any]:
        """Expand one catalog case into a FHIR-shaped collection bundle."""
        case = self._case(case_id)
        person = case["person"]
        patient_id = f"{case_id}-person"
        subject = {"reference": f"Patient/{patient_id}"}
        resources: list[dict[str, Any]] = [
            {
                "resourceType": "Patient",
                "id": patient_id,
                "meta": _synthetic_meta(),
                "identifier": [
                    {
                        "system": "urn:naio:sandbox-id",
                        "value": person["sandbox_id"],
                    }
                ],
                "name": [
                    {"family": person["family"], "given": [person["given"]]}
                ],
                "gender": person["gender"],
                "birthDate": person["birth_date"],
            },
            {
                "resourceType": "Encounter",
                "id": f"{case_id}-encounter",
                "meta": _synthetic_meta(),
                "status": "finished",
                "class": {"code": case["encounter"]["class_code"]},
                "type": [{"text": case["encounter"]["description"]}],
                "period": {
                    "start": case["encounter"]["period_start"],
                    "end": case["encounter"]["period_end"],
                },
                "subject": subject,
            },
        ]
        for index, condition in enumerate(case["conditions"], start=1):
            resources.append(
                {
                    "resourceType": "Condition",
                    "id": f"{case_id}-condition-{index}",
                    "meta": _synthetic_meta(),
                    "clinicalStatus": {"text": "active"},
                    "verificationStatus": {"text": "confirmed"},
                    "code": {"text": condition["text"]},
                    "onsetDateTime": condition["onset"],
                    "subject": subject,
                }
            )
        for index, medication in enumerate(case["medications"], start=1):
            resources.append(
                {
                    "resourceType": "MedicationRequest",
                    "id": f"{case_id}-medication-{index}",
                    "meta": _synthetic_meta(),
                    "status": "active",
                    "intent": "order",
                    "medicationCodeableConcept": {"text": medication["text"]},
                    "dosageInstruction": [{"text": medication["instruction"]}],
                    "subject": subject,
                }
            )
        for index, observation in enumerate(case["observations"], start=1):
            resources.append(
                {
                    "resourceType": "Observation",
                    "id": f"{case_id}-observation-{index}",
                    "meta": _synthetic_meta(),
                    "status": "final",
                    "code": {"text": observation["text"]},
                    "valueQuantity": {
                        "value": observation["value"],
                        "unit": observation["unit"],
                    },
                    "effectiveDateTime": observation["effective"],
                    "subject": subject,
                }
            )
        return {
            "resourceType": "Bundle",
            "id": f"{case_id}-bundle",
            "type": "collection",
            "meta": _synthetic_meta(),
            "entry": [{"resource": resource} for resource in resources],
        }

    def case_summary(self, case_id: str) -> str:
        """Deterministic human-readable summary, banner first."""
        case = self._case(case_id)
        person = case["person"]
        lines = [
            f"# {case['title']} (synthetic sandbox case)",
            "",
            f"> **{SANDBOX_BANNER}**",
            "",
            f"Sandbox case `{case_id}` · record {person['sandbox_id']}",
            "",
            f"Synthetic person on record — {person['given']} {person['family']}"
            f" ({person['gender']}, born {person['birth_date']}).",
            "",
            "## Learning focus",
            "",
            case["learning_focus"],
            "",
            "## Encounter",
            "",
            f"- {case['encounter']['description']}"
            f" ({case['encounter']['period_start']}"
            f" to {case['encounter']['period_end']}).",
            "",
            "## Active problems",
            "",
        ]
        lines += [f"- {condition['text']}" for condition in case["conditions"]]
        lines += ["", "## Medications in the scenario", ""]
        lines += [
            f"- {medication['text']} — {medication['instruction']}"
            for medication in case["medications"]
        ]
        lines += ["", "## Recent observations", ""]
        lines += [
            f"- {observation['text']}:"
            f" {observation['value']} {observation['unit']}"
            f" ({observation['effective']})"
            for observation in case["observations"]
        ]
        lines.append("")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Admission boundary and the FHIR-shaped surface (HAPI pattern)

    def admit(self, tenant: str, resource: dict[str, Any]) -> dict[str, Any]:
        """Admit one resource after the boundary checks; refuse otherwise."""
        if not _is_synthetic(resource):
            raise SandboxIntegrityError(
                "resource lacks the sandbox synthetic security label; "
                "the sandbox only holds labeled synthetic content"
            )
        for text in _iter_strings(resource):
            findings = self.privacy.analyze(text)
            if findings:
                kinds = ", ".join(sorted({f.entity_type for f in findings}))
                raise SandboxIntegrityError(
                    "resource content tripped the privacy screen "
                    f"({kinds}); real-looking identifiers are refused even "
                    "under a synthetic label"
                )
        resource_type = resource.get("resourceType")
        resource_id = resource.get("id")
        if not resource_type or not resource_id:
            raise SandboxIntegrityError("resource requires resourceType and id")
        stored = copy.deepcopy(resource)
        self._store.setdefault(tenant, {}).setdefault(resource_type, {})[
            resource_id
        ] = stored
        return copy.deepcopy(stored)

    def load_case(self, tenant: str, case_id: str) -> int:
        """Build a case and admit every resource into one tenant's sandbox."""
        bundle = self.build_case(case_id)
        count = 0
        for entry in bundle["entry"]:
            self.admit(tenant, entry["resource"])
            count += 1
        return count

    def read(
        self, tenant: str, resource_type: str, resource_id: str
    ) -> dict[str, Any] | None:
        """FHIR-style read. Foreign tenants see 'unknown', not 'forbidden'."""
        resource = (
            self._store.get(tenant, {}).get(resource_type, {}).get(resource_id)
        )
        return copy.deepcopy(resource) if resource else None

    def search(
        self, tenant: str, resource_type: str, **params: str
    ) -> tuple[dict[str, Any], ...]:
        """FHIR-style search over one tenant's admitted resources.

        Supported parameters: ``subject`` (exact reference), ``status``
        (exact), and ``code`` (case-insensitive substring of code.text).
        Unknown parameters match nothing — fail closed, never broaden.
        """
        supported = {"subject", "status", "code"}
        if set(params) - supported:
            return ()
        results = []
        for resource in self._store.get(tenant, {}).get(resource_type, {}).values():
            if "subject" in params and (
                resource.get("subject", {}).get("reference") != params["subject"]
            ):
                continue
            if "status" in params and resource.get("status") != params["status"]:
                continue
            if "code" in params and (
                params["code"].lower()
                not in resource.get("code", {}).get("text", "").lower()
            ):
                continue
            results.append(copy.deepcopy(resource))
        results.sort(key=lambda item: item["id"])
        return tuple(results)

    # ------------------------------------------------------------------
    # Existing contract surfaces: retrieval and orchestration

    def as_knowledge_sources(
        self, tenant: str, case_id: str
    ) -> tuple[KnowledgeSource, ...]:
        """Case summary as a governed-retrieval source, marked synthetic."""
        case = self._case(case_id)
        return (
            KnowledgeSource(
                source_id=f"sandbox-{case_id}",
                title=f"[SYNTHETIC] {case['title']}",
                doc_type="synthetic_case",
                effective_date=self.catalog["effective_date"],
                expires_date=None,
                jurisdiction=self.catalog["jurisdiction"],
                content=self.case_summary(case_id),
                tenant=tenant,
            ),
        )

    def start_case_workflow(
        self,
        workflow: Any,
        tenant: str,
        case_id: str,
        workflow_id: str,
    ) -> dict[str, Any]:
        """Seed an ADPIE workflow with a synthetic-flagged case context.

        The workflow runtime keeps its own rules — including the hard
        human-authorization gate — untouched; the sandbox only supplies
        an assessment context that is explicit about being synthetic.
        """
        case = self._case(case_id)
        person = case["person"]
        context = {
            "tenant": tenant,
            "case_id": case_id,
            "synthetic": True,
            "banner": SANDBOX_BANNER,
            "case_title": case["title"],
            "learning_focus": case["learning_focus"],
            "person_display": f"{person['given']} {person['family']}",
        }
        return workflow.start(workflow_id, context)
