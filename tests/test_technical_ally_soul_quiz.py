#!/usr/bin/env python3
"""Contracts for the separate Technical Ally SOUL Quiz and dashboard package."""

from __future__ import annotations

import base64
import hashlib
import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "technical-ally-soul-quiz" / "ally-quiz-model.mjs"
SCHEMA = ROOT / "technical-ally-soul-quiz" / "technical-ally-soul-profile.schema.json"
PAGE = ROOT / "technical-ally-soul-quiz" / "index.html"
APP = ROOT / "technical-ally-soul-quiz" / "ally-quiz-app.mjs"
SITEMAP = ROOT / "sitemap.xml"
RESOURCES = ROOT / "resources.html"
POST_SETUP = ROOT / "post-setup" / "index.html"
NURSE_QUIZ = ROOT / "soul-quiz.html"
PRIVACY = ROOT / "privacy.html"
TERMS = ROOT / "terms.html"
PUBLIC_URL = "https://nurse-ai-os.org/technical-ally-soul-quiz/"


def node_eval(source: str) -> Any:
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", source],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise AssertionError(f"node_eval failed ({completed.returncode}):\n{completed.stderr}")
    return json.loads(completed.stdout)


def valid_state_js() -> str:
    return """
      const state=createInitialState('2026-09-05T00:00:00.000Z');
      state.safety={noPhi:true,noNursingAuthority:true,nursesDecide:true,noInstitutionalAuthority:true,noUnapprovedAction:true};
      state.identity={displayName:'Alex & Team',backgrounds:['software-engineering','automation-integrations','technical-business'],experience:'founder',relationship:'invited-by-nurse'};
      state.collaboration={contributionAreas:['workflow-mapping','prototype-building','business-validation'],managerNeeds:['meeting-action','workflow-spec'],firstOutcome:'meeting-to-action',outcomeDetail:'Turn approved non-sensitive meeting notes into a review-ready action brief.',allyResponsibility:'Build the draft-only prototype, tests, documentation, and rollback path.',nurseDecisionRights:'The nurse manager defines nursing meaning, accepts the result, and decides whether work continues.',reviewCadence:'weekly',successSignal:'The manager accepts the brief with less rework and returns with a second bounded problem.',stopConditions:['phi-sensitive-data','authority-expansion','nurse-disagreement','unexpected-permission']};
      state.venture={businessStage:'customer-discovery',businessModel:'professional-service',businessBoundary:'No clinical automation, workforce scoring, or unsupported outcome claims.',nurseParticipation:true,attributionCompensation:true,evidenceBeforeClaims:true,conflictDisclosure:true};
    """


class TechnicalAllySoulQuizTests(unittest.TestCase):
    def test_catalog_is_focused_on_five_non_nurse_technical_orientations(self) -> None:
        result = node_eval("""
          import {ARCHETYPES} from './technical-ally-soul-quiz/ally-quiz-model.mjs';
          console.log(JSON.stringify(ARCHETYPES.map(({id,label})=>({id,label}))));
        """)
        self.assertEqual([item["id"] for item in result], [
            "workflow-engineer",
            "model-evidence-evaluator",
            "security-reliability-steward",
            "product-experience-builder",
            "technical-founder-operator",
        ])
        self.assertTrue(all("Nurse" in item["label"] or "Model" in item["label"] or "Security" in item["label"] or "Product" in item["label"] for item in result))

    def test_normalizer_allowlists_fields_and_rejects_sensitive_or_markup_text(self) -> None:
        result = node_eval("""
          import {createInitialState,normalizeState,containsRestrictedText} from './technical-ally-soul-quiz/ally-quiz-model.mjs';
          const clean=createInitialState('2026-09-05T00:00:00.000Z');
          clean.unknown='discard'; clean.identity.unknown='discard'; clean.identity.displayName='Alex';
          const normalized=normalizeState(clean);
          const bad=JSON.parse(JSON.stringify(clean)); bad.collaboration.outcomeDetail='Patient Jane Doe MRN 123456';
          const markup=JSON.parse(JSON.stringify(clean)); markup.identity.displayName='<script>alert(1)</script>';
          console.log(JSON.stringify({
            top:Object.keys(normalized),identity:Object.keys(normalized.identity),
            bad:normalizeState(bad),markup:normalizeState(markup),
            email:containsRestrictedText('contact me at ally@example.com')
          }));
        """)
        self.assertNotIn("unknown", result["top"])
        self.assertNotIn("unknown", result["identity"])
        self.assertIsNone(result["bad"])
        self.assertIsNone(result["markup"])
        self.assertTrue(result["email"])

    def test_restored_progress_fails_closed_and_broader_named_subject_patterns_are_rejected(self) -> None:
        result = node_eval("""
          import {createInitialState,normalizeState,containsRestrictedText} from './technical-ally-soul-quiz/ally-quiz-model.mjs';
          const incomplete=createInitialState(); incomplete.step=5;
          const restored=normalizeState(incomplete);
          console.log(JSON.stringify({
            restoredStep:restored?.step,
            namedPatient:containsRestrictedText('Patient: Jane Doe'),
            namedEmployee:containsRestrictedText('employee name = John Smith'),
            plainBroadWork:containsRestrictedText('a non-identifying workforce workflow')
          }));
        """)
        self.assertEqual(result["restoredStep"], 0)
        self.assertTrue(result["namedPatient"])
        self.assertTrue(result["namedEmployee"])
        self.assertFalse(result["plainBroadWork"])

    def test_every_stewardship_confirmation_is_required(self) -> None:
        result = node_eval("""
          import {createInitialState,validateStep} from './technical-ally-soul-quiz/ally-quiz-model.mjs';
          const state=createInitialState(); state.identity.displayName='Alex';
          const before=validateStep(state,0);
          state.safety={noPhi:true,noNursingAuthority:true,nursesDecide:true,noInstitutionalAuthority:true,noUnapprovedAction:true};
          console.log(JSON.stringify({before,after:validateStep(state,0)}));
        """)
        self.assertIn("every stewardship boundary", result["before"])
        self.assertEqual(result["after"], "")

    def test_orientation_is_deterministic_and_does_not_claim_competence(self) -> None:
        result = node_eval(f"""
          import {{createInitialState,deriveResult,buildProfile}} from './technical-ally-soul-quiz/ally-quiz-model.mjs';
          {valid_state_js()}
          const result=deriveResult(state); const profile=buildProfile(state,'2026-09-05T00:00:00.000Z');
          console.log(JSON.stringify({{primary:result.primary.id,supporting:result.supporting.map(x=>x.id),authority:profile.authority,posture:profile.governance_posture}}));
        """)
        self.assertEqual(result["primary"], "workflow-engineer")
        self.assertIn("technical-founder-operator", result["supporting"])
        self.assertTrue(all(value is False for value in result["authority"].values()))
        self.assertEqual(result["posture"]["edena"], "not-evaluated")
        self.assertEqual(result["posture"]["autonomy"], "A0-no-action")
        self.assertEqual(result["posture"]["execution"], "draft-only")

    def test_each_technical_orientation_is_reachable_without_becoming_a_score_of_ability(self) -> None:
        result = node_eval("""
          import {createInitialState,deriveResult} from './technical-ally-soul-quiz/ally-quiz-model.mjs';
          const cases=[
            ['software-engineering','workflow-mapping'],
            ['data-ai','model-evaluation'],
            ['cybersecurity-privacy','security-boundaries'],
            ['product-ux-accessibility','product-experience'],
            ['technical-business','business-validation']
          ];
          console.log(JSON.stringify(cases.map(([background,contribution])=>{
            const state=createInitialState(); state.identity.backgrounds=[background]; state.collaboration.contributionAreas=[contribution];
            const result=deriveResult(state); return {primary:result.primary.id,score:result.primary.score,label:result.primary.label};
          })));
        """)
        self.assertEqual([item["primary"] for item in result], [
            "workflow-engineer", "model-evidence-evaluator", "security-reliability-steward",
            "product-experience-builder", "technical-founder-operator",
        ])
        self.assertTrue(all(item["score"] > 0 for item in result))
        self.assertTrue(all("competence" not in item["label"].casefold() for item in result))

    def test_zip_writer_rejects_unsafe_and_colliding_names_and_has_known_crc(self) -> None:
        result = node_eval("""
          import {createStoredZip,crc32} from './technical-ally-soul-quiz/zip-store.mjs';
          const enc=new TextEncoder(); const failures=[];
          for (const entries of [
            [{name:'../escape.txt',data:'x'}],
            [{name:'A.txt',data:'x'},{name:'a.txt',data:'y'}],
            [{name:'/absolute.txt',data:'x'}],
            [{name:'back\\\\slash.txt',data:'x'}]
          ]) { try { createStoredZip(entries); failures.push(false); } catch { failures.push(true); } }
          console.log(JSON.stringify({failures,crc:crc32(enc.encode('123456789')).toString(16)}));
        """)
        self.assertTrue(all(result["failures"]))
        self.assertEqual(result["crc"], "cbf43926")

    def test_export_passes_closed_structural_schema_and_rejects_authority_escalation(self) -> None:
        result = node_eval(f"""
          import fs from 'node:fs';
          import Ajv from 'ajv/dist/2020.js';
          import {{createInitialState,buildProfile}} from './technical-ally-soul-quiz/ally-quiz-model.mjs';
          {valid_state_js()}
          const schema=JSON.parse(fs.readFileSync('./technical-ally-soul-quiz/technical-ally-soul-profile.schema.json','utf8'));
          const ajv=new Ajv({{strict:false,formats:{{'date-time':true}}}}); const validate=ajv.compile(schema);
          const profile=buildProfile(state,'2026-09-05T00:00:00.000Z');
          const valid=validate(profile); const elevated=JSON.parse(JSON.stringify(profile)); elevated.authority.managerial_authority_granted=true;
          const elevatedValid=validate(elevated); const unknown=JSON.parse(JSON.stringify(profile)); unknown.extra='unsafe'; const unknownValid=validate(unknown);
          console.log(JSON.stringify({{valid,errors:validate.errors,elevatedValid,unknownValid}}));
        """)
        self.assertTrue(result["valid"])
        self.assertFalse(result["elevatedValid"])
        self.assertFalse(result["unknownValid"])

    def test_semantic_validator_rejects_schema_valid_derived_result_contradictions(self) -> None:
        result = node_eval(f"""
          import fs from 'node:fs';
          import Ajv from 'ajv/dist/2020.js';
          import {{createInitialState,buildProfile,validateProfileSemantics}} from './technical-ally-soul-quiz/ally-quiz-model.mjs';
          {valid_state_js()}
          const schema=JSON.parse(fs.readFileSync('./technical-ally-soul-quiz/technical-ally-soul-profile.schema.json','utf8'));
          const ajv=new Ajv({{strict:false,formats:{{'date-time':true}}}}); const validate=ajv.compile(schema);
          const profile=buildProfile(state,'2026-09-05T00:00:00.000Z');
          profile.result.primary_orientation='model-evidence-evaluator';
          profile.result.primary_label='Model and Evidence Evaluator';
          profile.result.first_move='Run one source-linked local-versus-frontier comparison in shadow mode.';
          console.log(JSON.stringify({{schemaValid:validate(profile),semantic:validateProfileSemantics(profile)}}));
        """)
        self.assertTrue(result["schemaValid"], "portable schema intentionally cannot derive scoring results")
        self.assertFalse(result["semantic"]["valid"])
        self.assertTrue(any("orientation" in error.casefold() for error in result["semantic"]["errors"]))

    def test_generated_zip_contains_results_dashboard_manifest_and_valid_checksums(self) -> None:
        result = node_eval(f"""
          import {{createInitialState,buildPackageZip,PACKAGE_FILENAME}} from './technical-ally-soul-quiz/ally-quiz-model.mjs';
          {valid_state_js()}
          const pkg=await buildPackageZip(state,'2026-09-05T00:00:00.000Z');
          console.log(JSON.stringify({{filename:PACKAGE_FILENAME,base64:Buffer.from(pkg.bytes).toString('base64')}}));
        """)
        self.assertEqual(result["filename"], "Nurse-AI-OS-Technical-Ally-Manager-Collaboration-Dashboard.zip")
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / result["filename"]
            path.write_bytes(base64.b64decode(result["base64"]))
            with zipfile.ZipFile(path) as archive:
                self.assertIsNone(archive.testzip())
                names = set(archive.namelist())
                self.assertEqual(names, {
                    "README-FIRST.md",
                    "ally-soul-profile.json",
                    "ALLY-SOUL.md",
                    "MANAGER-ALLY-COLLABORATION-CHARTER.md",
                    "manager-ally-collaboration-dashboard.html",
                    "PACKAGE-MANIFEST.json",
                    "SHA256SUMS.txt",
                })
                manifest = json.loads(archive.read("PACKAGE-MANIFEST.json"))
                self.assertFalse(manifest["install_on_download"])
                self.assertTrue(manifest["static_dashboard_only"])
                self.assertFalse(manifest["authority_granted"])
                self.assertEqual(manifest["edena"], "not-evaluated")
                self.assertEqual(manifest["autonomy"], "A0-no-action")
                self.assertEqual(len(manifest["file_inventory"]), 5)
                for item in manifest["file_inventory"]:
                    payload = archive.read(item["path"])
                    self.assertEqual(len(payload), item["bytes"])
                    self.assertEqual(hashlib.sha256(payload).hexdigest(), item["sha256"])
                ledger = archive.read("SHA256SUMS.txt").decode("utf-8").splitlines()
                self.assertEqual(len(ledger), 6)
                for row in ledger:
                    digest, name = row.split("  ", 1)
                    self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), digest)
                dashboard = archive.read("manager-ally-collaboration-dashboard.html").decode("utf-8")
                self.assertIn("Alex &amp; Team", dashboard)
                self.assertIn("Manager–Technical Ally Dashboard", dashboard)
                self.assertIn("EDENA: Not evaluated · A0/no action", dashboard)
                self.assertIn("Governed technical service, consulting, or implementation sprint", dashboard)
                self.assertNotIn("fetch(", dashboard)
                profile = json.loads(archive.read("ally-soul-profile.json"))
                self.assertTrue(all(profile["stewardship_confirmations"].values()))
                readme = archive.read("README-FIRST.md").decode("utf-8")
                self.assertIn("This is not a Hermes self-install build kit", readme)
                self.assertIn("Opening or unzipping creates no installation", readme)

    def test_same_profile_and_timestamp_produce_identical_package_bytes(self) -> None:
        result = node_eval(f"""
          import {{createInitialState,buildPackageZip,sha256Hex}} from './technical-ally-soul-quiz/ally-quiz-model.mjs';
          {valid_state_js()}
          const first=await buildPackageZip(state,'2026-09-05T00:00:00.000Z');
          const second=await buildPackageZip(state,'2026-09-05T00:00:00.000Z');
          console.log(JSON.stringify({{first:await sha256Hex(first.bytes),second:await sha256Hex(second.bytes),bytes:first.bytes.length}}));
        """)
        self.assertEqual(result["first"], result["second"])
        self.assertGreater(result["bytes"], 10_000)

    def test_public_page_is_separate_and_linked_to_manager_downloads(self) -> None:
        page = PAGE.read_text(encoding="utf-8")
        nurse_quiz = NURSE_QUIZ.read_text(encoding="utf-8")
        resources = RESOURCES.read_text(encoding="utf-8")
        post_setup = POST_SETUP.read_text(encoding="utf-8")
        sitemap = SITEMAP.read_text(encoding="utf-8")
        self.assertIn("Technical Ally SOUL Quiz", page)
        self.assertIn("Separate from the nurse SOUL Quiz", page)
        self.assertIn("Results + dashboard ZIP", page)
        self.assertNotEqual(PAGE.resolve(), NURSE_QUIZ.resolve())
        self.assertIn('href="technical-ally-soul-quiz/"', resources)
        self.assertIn('href="../technical-ally-soul-quiz/"', post_setup)
        self.assertIn(PUBLIC_URL, sitemap)
        self.assertIn('href="technical-ally-soul-quiz/"', nurse_quiz)
        privacy = PRIVACY.read_text(encoding="utf-8")
        self.assertIn("separate Technical Ally SOUL Quiz", privacy)
        self.assertIn("session storage", privacy)
        self.assertIn("locally generated results-plus-dashboard ZIP", privacy)
        terms = TERMS.read_text(encoding="utf-8")
        self.assertIn("Completing a Technical Ally profile", terms)
        self.assertIn("does not verify technical competence", terms)
        self.assertIn("planning draft, not a contract", terms)

    def test_quiz_has_no_submission_or_network_execution_path(self) -> None:
        combined = PAGE.read_text(encoding="utf-8") + APP.read_text(encoding="utf-8") + MODEL.read_text(encoding="utf-8")
        for forbidden in ("fetch(", "XMLHttpRequest", "WebSocket", "sendBeacon", "navigator.sendBeacon"):
            self.assertNotIn(forbidden, combined)
        self.assertIn("sessionStorage", APP.read_text(encoding="utf-8"))
        self.assertNotIn("localStorage", APP.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
