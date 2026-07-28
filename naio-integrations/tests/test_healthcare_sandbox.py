import json
import tempfile
import unittest
from pathlib import Path

import _bootstrap  # noqa: F401

from naio_integrations.contract import (
    ActionMode,
    Actor,
    DataClass,
    Decision,
    GatewayRequest,
    RiskTier,
)
from naio_integrations.knowledge import GovernedKnowledge
from naio_integrations.orchestration import AdpieWorkflow, WorkflowError
from naio_integrations.policy import EdenaPolicyEngine
from naio_integrations.sandbox import (
    SANDBOX_BANNER,
    SANDBOX_SECURITY_CODE,
    SANDBOX_SECURITY_SYSTEM,
    SandboxIntegrityError,
    SyntheticPatientSandbox,
    _synthetic_meta,
)

TENANT = "personal:jordan"
OTHER_TENANT = "personal:rival"
REPO_ROOT = Path(__file__).resolve().parents[2]
COMMITTED_ROOT = REPO_ROOT / "mission-control" / "healthcare-sandbox"


def fixed_clock():
    return "2026-07-01T09:00:00+00:00"


class CaseGenerationTests(unittest.TestCase):
    def setUp(self):
        self.sandbox = SyntheticPatientSandbox()

    def test_catalog_ships_three_phase3_cases(self):
        self.assertEqual(
            self.sandbox.case_ids(),
            ("dm2-education-002", "hf-transitions-001", "postop-mobility-003"),
        )

    def test_every_resource_in_every_case_is_labeled_synthetic(self):
        for case_id in self.sandbox.case_ids():
            bundle = self.sandbox.build_case(case_id)
            resources = [entry["resource"] for entry in bundle["entry"]]
            self.assertGreaterEqual(len(resources), 5, case_id)
            for resource in resources + [bundle]:
                labels = resource["meta"]["security"]
                self.assertTrue(
                    any(
                        label["system"] == SANDBOX_SECURITY_SYSTEM
                        and label["code"] == SANDBOX_SECURITY_CODE
                        for label in labels
                    ),
                    f"{case_id}: {resource.get('resourceType')} missing label",
                )

    def test_person_names_carry_the_synthea_numeric_suffix(self):
        for case_id in self.sandbox.case_ids():
            bundle = self.sandbox.build_case(case_id)
            patient = bundle["entry"][0]["resource"]
            self.assertEqual(patient["resourceType"], "Patient")
            name = patient["name"][0]
            self.assertTrue(name["family"][-1].isdigit(), case_id)
            self.assertTrue(name["given"][0][-1].isdigit(), case_id)

    def test_bundles_are_deterministic(self):
        again = SyntheticPatientSandbox()
        for case_id in self.sandbox.case_ids():
            self.assertEqual(
                json.dumps(self.sandbox.build_case(case_id), sort_keys=True),
                json.dumps(again.build_case(case_id), sort_keys=True),
                case_id,
            )

    def test_unknown_case_fails_closed(self):
        with self.assertRaises(SandboxIntegrityError):
            self.sandbox.build_case("real-ward-census")

    def test_case_summary_leads_with_the_banner(self):
        for case_id in self.sandbox.case_ids():
            summary = self.sandbox.case_summary(case_id)
            self.assertIn(SANDBOX_BANNER, summary.splitlines()[2], case_id)
            self.assertIn("synthetic", summary.lower(), case_id)

    def test_all_generated_content_passes_the_privacy_screen(self):
        for case_id in self.sandbox.case_ids():
            summary = self.sandbox.case_summary(case_id)
            findings = self.sandbox.privacy.analyze(summary)
            self.assertEqual([f.entity_type for f in findings], [], case_id)


class AdmissionBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.sandbox = SyntheticPatientSandbox()

    def test_load_case_admits_every_bundle_resource(self):
        count = self.sandbox.load_case(TENANT, "hf-transitions-001")
        bundle = self.sandbox.build_case("hf-transitions-001")
        self.assertEqual(count, len(bundle["entry"]))

    def test_unlabeled_resource_is_refused(self):
        with self.assertRaises(SandboxIntegrityError) as ctx:
            self.sandbox.admit(
                TENANT,
                {"resourceType": "Patient", "id": "walk-in", "name": []},
            )
        self.assertIn("synthetic security label", str(ctx.exception))

    def test_real_looking_identifiers_are_refused_even_when_labeled(self):
        smuggled = {
            "resourceType": "Condition",
            "id": "smuggled",
            "meta": _synthetic_meta(),
            "code": {"text": "Noted SSN 123-45-6789 copied from a real chart"},
        }
        with self.assertRaises(SandboxIntegrityError) as ctx:
            self.sandbox.admit(TENANT, smuggled)
        self.assertIn("privacy screen", str(ctx.exception))
        self.assertIsNone(self.sandbox.read(TENANT, "Condition", "smuggled"))

    def test_ordinary_demographics_are_refused_despite_the_label(self):
        # A caller-controlled label plus a real person's demographics —
        # the generation markers must refuse the ordinary name outright.
        relabeled = {
            "resourceType": "Patient",
            "id": "relabeled-real-record",
            "meta": _synthetic_meta(),
            "name": [{"family": "Smith", "given": ["Jane"]}],
            "gender": "female",
            "birthDate": "1980-01-01",
        }
        with self.assertRaises(SandboxIntegrityError) as ctx:
            self.sandbox.admit(TENANT, relabeled)
        self.assertIn("numeric-suffix", str(ctx.exception))
        self.assertIsNone(
            self.sandbox.read(TENANT, "Patient", "relabeled-real-record")
        )

    def test_fields_outside_the_admission_schema_are_refused(self):
        with_address = {
            "resourceType": "Patient",
            "id": "with-address",
            "meta": _synthetic_meta(),
            "name": [{"family": "Kestrel842", "given": ["Amara701"]}],
            "address": [{"line": ["12 Real Street"], "city": "Springfield"}],
        }
        with self.assertRaises(SandboxIntegrityError) as ctx:
            self.sandbox.admit(TENANT, with_address)
        self.assertIn("admission schema", str(ctx.exception))

    def test_nested_extra_keys_are_refused(self):
        with_name_text = {
            "resourceType": "Patient",
            "id": "with-name-text",
            "meta": _synthetic_meta(),
            "name": [{"family": "Kestrel842", "text": "Jane Smith"}],
        }
        with self.assertRaises(SandboxIntegrityError):
            self.sandbox.admit(TENANT, with_name_text)

    def test_real_world_identifier_systems_are_refused(self):
        foreign_identifier = {
            "resourceType": "Patient",
            "id": "foreign-identifier",
            "meta": _synthetic_meta(),
            "name": [{"family": "Kestrel842", "given": ["Amara701"]}],
            "identifier": [
                {"system": "urn:oid:2.16.840.1.113883", "value": "SYN-REAL"}
            ],
        }
        with self.assertRaises(SandboxIntegrityError) as ctx:
            self.sandbox.admit(TENANT, foreign_identifier)
        self.assertIn("identifier system", str(ctx.exception))

    def test_resource_types_outside_the_schema_are_refused(self):
        document = {
            "resourceType": "DocumentReference",
            "id": "scanned-chart",
            "meta": _synthetic_meta(),
        }
        with self.assertRaises(SandboxIntegrityError) as ctx:
            self.sandbox.admit(TENANT, document)
        self.assertIn("admission schema", str(ctx.exception))

    def test_extra_meta_fields_are_refused(self):
        meta = _synthetic_meta()
        meta["source"] = "https://real-hospital.example/fhir"
        with self.assertRaises(SandboxIntegrityError):
            self.sandbox.admit(
                TENANT,
                {"resourceType": "Patient", "id": "meta-extra", "meta": meta},
            )

    def test_catalog_with_real_looking_identifiers_is_refused_at_construction(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad_catalog = Path(tmp) / "cases.json"
            bad_catalog.write_text(
                json.dumps(
                    {
                        "effective_date": "2026-07-01",
                        "jurisdiction": "US",
                        "cases": {
                            "bad-case": {
                                "learning_focus": "Review chart, SSN 123-45-6789"
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(SandboxIntegrityError) as ctx:
                SyntheticPatientSandbox(catalog_path=bad_catalog)
            self.assertIn("case catalog", str(ctx.exception))

    def test_load_case_is_atomic_when_a_later_resource_fails(self):
        class DoctoredSandbox(SyntheticPatientSandbox):
            def build_case(self, case_id):
                bundle = super().build_case(case_id)
                bundle["entry"].append(
                    {
                        "resource": {
                            "resourceType": "Condition",
                            "id": "poison",
                            "meta": _synthetic_meta(),
                            "code": {"text": "Noted SSN 123-45-6789"},
                        }
                    }
                )
                return bundle

        sandbox = DoctoredSandbox()
        with self.assertRaises(SandboxIntegrityError):
            sandbox.load_case(TENANT, "hf-transitions-001")
        self.assertIsNone(
            sandbox.read(TENANT, "Patient", "hf-transitions-001-person"),
            "a refusal partway through must leave the tenant unchanged",
        )

    def test_resource_without_type_or_id_is_refused(self):
        with self.assertRaises(SandboxIntegrityError):
            self.sandbox.admit(TENANT, {"meta": _synthetic_meta(), "id": "x"})

    def test_admitted_resources_are_copies_not_references(self):
        self.sandbox.load_case(TENANT, "dm2-education-002")
        first = self.sandbox.read(TENANT, "Patient", "dm2-education-002-person")
        first["gender"] = "edited"
        second = self.sandbox.read(TENANT, "Patient", "dm2-education-002-person")
        self.assertEqual(second["gender"], "male")


class FhirSurfaceTests(unittest.TestCase):
    def setUp(self):
        self.sandbox = SyntheticPatientSandbox()
        self.sandbox.load_case(TENANT, "hf-transitions-001")

    def test_read_returns_the_resource_for_the_owning_tenant(self):
        patient = self.sandbox.read(
            TENANT, "Patient", "hf-transitions-001-person"
        )
        self.assertEqual(patient["name"][0]["family"], "Kestrel842")

    def test_foreign_tenant_reads_unknown_not_forbidden(self):
        self.assertIsNone(
            self.sandbox.read(
                OTHER_TENANT, "Patient", "hf-transitions-001-person"
            )
        )

    def test_search_by_subject_scopes_to_one_synthetic_person(self):
        conditions = self.sandbox.search(
            TENANT,
            "Condition",
            subject="Patient/hf-transitions-001-person",
        )
        self.assertEqual(len(conditions), 2)
        self.assertEqual(
            [c["id"] for c in conditions],
            ["hf-transitions-001-condition-1", "hf-transitions-001-condition-2"],
        )

    def test_search_by_code_substring_is_case_insensitive(self):
        observations = self.sandbox.search(TENANT, "Observation", code="heart rate")
        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0]["valueQuantity"]["unit"], "beats/min")

    def test_unknown_search_parameter_matches_nothing(self):
        self.assertEqual(
            self.sandbox.search(TENANT, "Condition", severity="all"), ()
        )

    def test_foreign_tenant_search_is_empty(self):
        self.assertEqual(self.sandbox.search(OTHER_TENANT, "Condition"), ())


class ContractSurfaceTests(unittest.TestCase):
    def setUp(self):
        self.sandbox = SyntheticPatientSandbox()

    def test_case_feeds_governed_retrieval_marked_synthetic(self):
        knowledge = GovernedKnowledge()
        knowledge.index(self.sandbox.as_knowledge_sources(TENANT, "dm2-education-002"))
        answer = knowledge.retrieve(TENANT, "diabetes education", "2026-07-28")
        self.assertFalse(answer.refused)
        self.assertTrue(answer.passages[0]["title"].startswith("[SYNTHETIC]"))
        self.assertEqual(answer.passages[0]["doc_type"], "synthetic_case")
        self.assertTrue(
            any("SYNTHETIC" in warning for warning in answer.warnings),
            answer.warnings,
        )

    def test_sandbox_sources_stay_tenant_scoped_in_retrieval(self):
        knowledge = GovernedKnowledge()
        knowledge.index(self.sandbox.as_knowledge_sources(TENANT, "dm2-education-002"))
        answer = knowledge.retrieve(OTHER_TENANT, "diabetes education", "2026-07-28")
        self.assertTrue(answer.refused)

    def test_case_workflow_starts_at_assess_with_synthetic_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            workflow = AdpieWorkflow(Path(tmp), now=fixed_clock)
            state = self.sandbox.start_case_workflow(
                workflow, TENANT, "postop-mobility-003", "sandbox-run-1"
            )
            self.assertEqual(state["stage"], "assess")
            self.assertIs(state["context"]["synthetic"], True)
            self.assertEqual(state["context"]["banner"], SANDBOX_BANNER)
            self.assertEqual(
                state["context"]["person_display"], "Ilse902 Farrow516"
            )

    def test_case_workflow_keeps_the_human_authorization_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            workflow = AdpieWorkflow(Path(tmp), now=fixed_clock)
            self.sandbox.start_case_workflow(
                workflow, TENANT, "postop-mobility-003", "sandbox-run-2"
            )
            for _ in ("assess", "diagnose", "plan"):
                workflow.advance("sandbox-run-2", note="synthetic step")
            state = workflow.state("sandbox-run-2")
            self.assertEqual(state["stage"], "human_authorization")
            with self.assertRaises(WorkflowError):
                workflow.advance("sandbox-run-2", note="cannot skip the gate")


class GovernanceTests(unittest.TestCase):
    """Synthetic data lowers the data class, never the governance rules."""

    def setUp(self):
        self.engine = EdenaPolicyEngine()
        self.sandbox = SyntheticPatientSandbox()

    def _request(self, role: str, intent: str) -> GatewayRequest:
        return GatewayRequest(
            request_id="sbx-1",
            actor=Actor(actor_id="u-1", role=role, tenant=TENANT),
            intent=intent,
            content=self.sandbox.case_summary("hf-transitions-001"),
            risk_tier=RiskTier.GREEN,
            data_class=DataClass.D0,
            action_mode=ActionMode.DRAFT,
        )

    def test_sandbox_case_review_is_allowed_at_green_d0(self):
        decision = self.engine.decide(self._request("nurse", "sandbox_case_review"))
        self.assertIs(decision.decision, Decision.ALLOW)

    def test_student_gate_holds_even_on_synthetic_content(self):
        decision = self.engine.decide(
            self._request("student", "patient_specific_recommendation")
        )
        self.assertIs(decision.decision, Decision.DENY)


class CommittedArtifactTests(unittest.TestCase):
    """The committed sandbox artifacts must match a fresh deterministic build."""

    def _fresh_files(self) -> dict[str, str]:
        sandbox = SyntheticPatientSandbox()
        files = {}
        for case_id in sandbox.case_ids():
            bundle = sandbox.build_case(case_id)
            files[f"cases/{case_id}/bundle.json"] = (
                json.dumps(bundle, indent=2, sort_keys=True) + "\n"
            )
            files[f"cases/{case_id}/case-summary.md"] = sandbox.case_summary(case_id)
        return files

    def test_committed_cases_match_fresh_build_exactly(self):
        fresh = self._fresh_files()
        committed = {
            path.relative_to(COMMITTED_ROOT).as_posix(): path.read_text(
                encoding="utf-8"
            )
            for path in COMMITTED_ROOT.rglob("*")
            if path.is_file() and path.name != "README.md"
        }
        self.assertEqual(set(committed), set(fresh))
        for name, content in fresh.items():
            self.assertEqual(committed[name], content, name)

    def test_committed_readme_states_the_boundary(self):
        readme = (COMMITTED_ROOT / "README.md").read_text(encoding="utf-8")
        for phrase in (
            "synthetic",
            "never proves",
            "privacy screen",
            "synthetichealth/synthea",
            "hapifhir/hapi-fhir",
        ):
            self.assertIn(phrase, readme, phrase)


if __name__ == "__main__":
    unittest.main()
