"""Healthcare sandbox (patterns: synthetichealth/synthea, hapifhir/hapi-fhir).

Phase 3 of the Mission Control release sequence: a safe place to practice
on patient-shaped data with **no patients in it**. The sandbox expands a
reviewed case catalog into FHIR-shaped resource bundles (the Synthea
pattern: generated records with numeric-suffix names that are
unmistakably synthetic) and serves them through a read/search surface
shaped like a FHIR server (the HAPI FHIR pattern) — without vendoring
either project, per the Integration Contract.

Boundary invariants, enforced at admission and never waived. The
synthetic label is caller-controlled, so a label alone proves nothing;
admission layers four independent checks:

* every resource must carry the sandbox synthetic security label —
  unlabeled content is refused, so nothing can pose as sandbox data;
* every resource must fit the strict admission schema — only the five
  generated resource types, only their generated fields, scalar values
  only. There is deliberately nowhere to put an address, phone number,
  note, photo, or free-form demographics;
* every Patient must carry the generation markers — numeric-suffix
  names (the Synthea convention) and the sandbox identifier system
  only — so an ordinary real name or a real-world identifier system is
  refused outright;
* every string in every resource must additionally pass the privacy
  screen, catching identifier formats the schema cannot exclude.

Reads and searches are tenant-scoped; another tenant's request reads
as "unknown resource" (existence is not disclosed). The sandbox is D0
by construction, but detection reduces risk — it never proves content
is de-identified, which is why every layer still runs on data that is
synthetic by construction.

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
SANDBOX_IDENTIFIER_SYSTEM = "urn:naio:sandbox-id"
SANDBOX_IDENTIFIER_PREFIX = "SYN-"

# The admission schema: the only resource types the sandbox generates,
# and for each, the only fields generation produces. None marks a
# scalar field; a set marks an object with exactly those keys; a
# one-element list marks a list of such objects. Anything outside this
# shape is refused — free-form demographics have nowhere to live.
_TEXT_ONLY = frozenset({"text"})
ADMISSION_SCHEMA: dict[str, dict[str, Any]] = {
    "Patient": {
        "identifier": [frozenset({"system", "value"})],
        "name": [frozenset({"family", "given"})],
        "gender": None,
        "birthDate": None,
    },
    "Encounter": {
        "status": None,
        "class": frozenset({"code"}),
        "type": [_TEXT_ONLY],
        "period": frozenset({"start", "end"}),
        "subject": frozenset({"reference"}),
    },
    "Condition": {
        "clinicalStatus": _TEXT_ONLY,
        "verificationStatus": _TEXT_ONLY,
        "code": _TEXT_ONLY,
        "onsetDateTime": None,
        "subject": frozenset({"reference"}),
    },
    "MedicationRequest": {
        "status": None,
        "intent": None,
        "medicationCodeableConcept": _TEXT_ONLY,
        "dosageInstruction": [_TEXT_ONLY],
        "subject": frozenset({"reference"}),
    },
    "Observation": {
        "status": None,
        "code": _TEXT_ONLY,
        "valueQuantity": frozenset({"value", "unit"}),
        "effectiveDateTime": None,
        "subject": frozenset({"reference"}),
    },
}

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


def _check_object(label: str, item: Any, allowed_keys: frozenset[str]) -> None:
    if not isinstance(item, dict):
        raise SandboxIntegrityError(f"{label} must be an object")
    extra = set(item) - allowed_keys
    if extra:
        raise SandboxIntegrityError(
            f"{label} carries fields outside the admission schema:"
            f" {sorted(extra)}; there is deliberately nowhere to put"
            " free-form demographics"
        )
    for key, value in item.items():
        if key == "given":
            if not isinstance(value, list) or not all(
                isinstance(part, str) for part in value
            ):
                raise SandboxIntegrityError(f"{label}.given must be a list of strings")
        elif not isinstance(value, (str, int, float)) or isinstance(value, bool):
            raise SandboxIntegrityError(f"{label}.{key} must be a scalar")


def _check_shape(resource: dict[str, Any]) -> None:
    """Refuse anything outside the strict admission schema."""
    resource_type = resource.get("resourceType")
    if resource_type not in ADMISSION_SCHEMA:
        raise SandboxIntegrityError(
            f"resource type {resource_type!r} is not in the sandbox"
            " admission schema"
        )
    meta = resource.get("meta", {})
    if not isinstance(meta, dict):
        raise SandboxIntegrityError(f"{resource_type}.meta must be an object")
    extra_meta = set(meta) - {"security"}
    if extra_meta:
        raise SandboxIntegrityError(
            f"{resource_type}.meta carries fields outside the admission"
            f" schema: {sorted(extra_meta)}"
        )
    security = meta.get("security")
    if not isinstance(security, list):
        raise SandboxIntegrityError(
            f"{resource_type}.meta.security must be a list of labels"
        )
    for index, entry in enumerate(security):
        _check_object(
            f"{resource_type}.meta.security[{index}]",
            entry,
            frozenset({"system", "code", "display"}),
        )
    allowed = ADMISSION_SCHEMA[resource_type]
    for key, value in resource.items():
        if key in ("resourceType", "id", "meta"):
            continue
        if key not in allowed:
            raise SandboxIntegrityError(
                f"field {resource_type}.{key} is outside the admission"
                " schema; there is deliberately nowhere to put free-form"
                " demographics"
            )
        spec = allowed[key]
        label = f"{resource_type}.{key}"
        if spec is None:
            if not isinstance(value, (str, int, float)) or isinstance(value, bool):
                raise SandboxIntegrityError(f"{label} must be a scalar")
        elif isinstance(spec, list):
            if not isinstance(value, list):
                raise SandboxIntegrityError(f"{label} must be a list")
            for index, item in enumerate(value):
                _check_object(f"{label}[{index}]", item, spec[0])
        else:
            _check_object(label, value, spec)


def _check_generation_markers(resource: dict[str, Any]) -> None:
    """Enforce the markers only sandbox generation produces on a Patient."""
    if resource.get("resourceType") != "Patient":
        return
    for name in resource.get("name", []):
        parts = [name.get("family", "")] + list(name.get("given", []))
        for part in parts:
            if not part or not part[-1].isdigit():
                raise SandboxIntegrityError(
                    "person names in the sandbox must carry the"
                    " numeric-suffix generation marker (the Synthea"
                    " convention); ordinary names are refused"
                )
    for identifier in resource.get("identifier", []):
        if identifier.get("system") != SANDBOX_IDENTIFIER_SYSTEM or not str(
            identifier.get("value", "")
        ).startswith(SANDBOX_IDENTIFIER_PREFIX):
            raise SandboxIntegrityError(
                "patient identifiers must use the sandbox identifier"
                " system; real-world identifier systems are refused"
            )


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
        # The catalog feeds committed artifacts, summaries, and retrieval
        # content without crossing the admission boundary, so it is
        # screened once here: a custom catalog carrying real-looking
        # identifiers never gets as far as generation.
        for text in _iter_strings(self.catalog):
            findings = self.privacy.analyze(text)
            if findings:
                kinds = ", ".join(sorted({f.entity_type for f in findings}))
                raise SandboxIntegrityError(
                    f"case catalog content tripped the privacy screen ({kinds});"
                    " refusing to generate from it"
                )
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

    def _validate(self, resource: dict[str, Any]) -> None:
        """Run every boundary check on one resource without storing it.

        The synthetic label is caller-controlled and therefore never
        sufficient on its own: the admission schema and the generation
        markers are what keep ordinary demographics out, and the
        privacy screen catches identifier formats on top of that.
        """
        if not resource.get("resourceType") or not resource.get("id"):
            raise SandboxIntegrityError("resource requires resourceType and id")
        if not _is_synthetic(resource):
            raise SandboxIntegrityError(
                "resource lacks the sandbox synthetic security label; "
                "the sandbox only holds labeled synthetic content"
            )
        _check_shape(resource)
        _check_generation_markers(resource)
        for text in _iter_strings(resource):
            findings = self.privacy.analyze(text)
            if findings:
                kinds = ", ".join(sorted({f.entity_type for f in findings}))
                raise SandboxIntegrityError(
                    "resource content tripped the privacy screen "
                    f"({kinds}); real-looking identifiers are refused even "
                    "under a synthetic label"
                )

    def _store_resource(self, tenant: str, resource: dict[str, Any]) -> dict[str, Any]:
        stored = copy.deepcopy(resource)
        self._store.setdefault(tenant, {}).setdefault(resource["resourceType"], {})[
            resource["id"]
        ] = stored
        return copy.deepcopy(stored)

    def admit(self, tenant: str, resource: dict[str, Any]) -> dict[str, Any]:
        """Admit one resource after the layered boundary checks."""
        self._validate(resource)
        return self._store_resource(tenant, resource)

    def load_case(self, tenant: str, case_id: str) -> int:
        """Build a case and admit it into one tenant's sandbox atomically.

        Every resource is validated before any resource is stored, so a
        refusal partway through leaves the tenant's sandbox unchanged.
        """
        bundle = self.build_case(case_id)
        resources = [entry["resource"] for entry in bundle["entry"]]
        for resource in resources:
            self._validate(resource)
        for resource in resources:
            self._store_resource(tenant, resource)
        return len(resources)

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
