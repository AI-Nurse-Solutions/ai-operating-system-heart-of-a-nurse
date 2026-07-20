#!/usr/bin/env python3
"""Deterministic contracts for the multidimensional Nurse AI OS SOUL Quiz."""

from __future__ import annotations

import html.parser
import hashlib
import json
import re
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
QUIZ_HTML = ROOT / "soul-quiz.html"
QUIZ_DIR = ROOT / "soul-quiz"
MODEL = QUIZ_DIR / "soul-quiz-model.mjs"
APP = QUIZ_DIR / "soul-quiz-app.mjs"
CSS = QUIZ_DIR / "soul-quiz.css"
SCHEMA = ROOT / "naio-os" / "schema" / "naio-soul.schema.json"
IMPORTER = ROOT / "naio-os" / "scripts" / "import-soul.py"
GUIDE = ROOT / "soul-quiz-guide.html"
DESIGN = ROOT / "naio-os" / "SOUL-QUIZ-ROLE-CONSTELLATION-DESIGN.md"
PREFLIGHT = ROOT / "naio-os" / "scripts" / "preflight.sh"
REQUIREMENTS = ROOT / "naio-os" / "requirements-import-soul.txt"
MANIFEST = ROOT / "naio-os" / "manifest.yaml"
RELEASE_VERIFIER = ROOT / "naio-os" / "scripts" / "verify-release.py"


class QuizParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.scripts: list[dict[str, str | None]] = []
        self.progressbars = 0
        self.mains = 0
        self.buttons: list[dict[str, str | None]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        data = dict(attrs)
        if data.get("id"):
            self.ids.append(str(data["id"]))
        if tag == "script":
            self.scripts.append(data)
        if data.get("role") == "progressbar":
            self.progressbars += 1
        if tag == "main":
            self.mains += 1
        if tag == "button":
            self.buttons.append(data)


def node_eval(source: str) -> Any:
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", source],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise AssertionError(f"node_eval failed (exit {completed.returncode}):\n{completed.stderr}")
    return json.loads(completed.stdout)


def representative_state_js() -> str:
    return """
      const s=createInitialState('2026-07-20T00:00:00.000Z');
      s.name='Jordan';
      s.roleSelections=[
        {roleId:'bedside-nurse',status:'primary',attention:5,responsibility:5,identity:5,confidence:4,authorization:'licensed-or-credentialed-unverified',competenceEvidence:'self-reported-practice-not-verified',credentialStatus:'self-reported-not-verified'},
        {roleId:'clinical-preceptor',status:'supporting',attention:3,responsibility:4,identity:4,confidence:4,authorization:'formally-assigned-unverified',competenceEvidence:'self-reported-practice-not-verified',credentialStatus:'not-claimed'},
        {roleId:'quality-improvement-specialist',status:'supporting',attention:3,responsibility:3,identity:3,confidence:3,authorization:'formally-assigned-unverified',competenceEvidence:'developing-not-verified',credentialStatus:'not-claimed'},
        {roleId:'nurse-entrepreneur',status:'emerging',attention:2,responsibility:1,identity:3,confidence:2,authorization:'self-declared',competenceEvidence:'developing-not-verified',credentialStatus:'not-claimed'}
      ];
      s.spheres=['personal','professional','community','sidegig','interest'];
      s.developmentalStages=['experienced-clinician','certification-candidate','entrepreneur-innovator'];
      s.advancedStudies={active:true,pathways:[{type:'specialty-certification',target:'CCRN',motivation:'Deepen critical-care practice',outcome:'Certification preparation',stage:'active-preparation',milestoneDate:'2026-11-01',requiredCompetencies:'Critical-care knowledge domains',progressEvidence:'Study plan and practice scores',gaps:'Hemodynamics',priorities:'Weekly review',formats:['practice-questions','concept-maps'],availableTime:'4 hours/week',constraints:'Night shifts',accountability:'Weekly check-in',mentorship:'Critical-care mentor',roleRelationship:'Supports bedside and preceptor roles',financialBarriers:'',workloadBarriers:'Night shifts',familyResponsibilities:'Shared caregiving',wellnessConsiderations:'Protect recovery sleep',institutionalSupport:'Education days',applicationOpportunities:'Teach a synthetic review session',renewalRequirements:'Not applicable yet',integrityBoundary:'AI may tutor and quiz; it may not impersonate me or complete prohibited work'},{type:'masters-degree',target:'MSN',motivation:'Develop an additional evidence and leadership pathway',outcome:'Graduate preparation',stage:'exploring',milestoneDate:'',requiredCompetencies:'Not yet mapped',progressEvidence:'Planning only',gaps:'Program selection',priorities:'Compare programs',formats:[],availableTime:'Not yet set',constraints:'Shift work',accountability:'Not yet set',mentorship:'Needed',roleRelationship:'Supports emerging education and leadership roles',financialBarriers:'Tuition',workloadBarriers:'Capacity',familyResponsibilities:'Shared caregiving',wellnessConsiderations:'Do not overload',institutionalSupport:'Unknown',applicationOpportunities:'Future project',renewalRequirements:'Not applicable',integrityBoundary:'AI may compare public program information; it may not complete applications or assignments'}]};
      s.core={values:['dignity','evidence','family','growth'],mission:'Serve critically ill adults and help newer nurses learn safely.',populations:'Adult critical-care patients indirectly, learners, and the unit team',sharedGoals:'Prepare safely for CCRN while strengthening preceptor and quality work.',commitmentBoundaries:'Protect recovery sleep after night shifts; use broad calendar blocks only.',motivations:['service','mastery','stewardship'],strengths:'Calm communication and pattern recognition',workStyles:['structured','collaborative'],learningStyles:['practice','teach-back'],voice:{length:'Bulleted & structured',formality:'Professional',pushback:'Push back when stakes are high',avoid:'No toxic positivity'},alwaysRemember:'Works nights'};
      s.pressures={selected:['workload','study-time','family-care'],load:4,wellnessLimit:'Protect post-shift sleep and one no-study day'};
      s.decisionStyle={evidence:5,uncertainty:3,risk:2,collaboration:4,accountability:5,innovation:3,conflict:3,timePressure:4,ethicalConcerns:5,competingPriorities:3};
      s.ai={relationshipModes:['tutor','research-assistant','project-manager','governance-monitor'],primaryMode:'tutor',delegation:{'public-source-summary':'independent-private','private-plan-draft':'independent-private','external-send':'independent-private','patient-specific-clinical-decision':'independent-private','graded-or-evaluative-work':'prepare-only','institutional-change':'explicit-confirmation'},memoryAllowed:['communication preferences','stable professional goals'],memoryForbidden:['PHI','student or employee records','credentials or secrets'],escalationTriggers:['patient-specific or clinical content','academic integrity concern','employment or institutional authority']};
      s.safety={noPhi:true,noClinicalAuthority:true,noAcademicDishonesty:true,noCredentialInference:true};
      s.moduleAnswers={
        'clinical-care':{clinicalEnvironmentResponsibilities:'Adult critical-care role; no patient details',clinicalAuthorizationSupervision:'Licensed role reported; institutional policy remains controlling'},
        'education-mentorship':{educationResponsibilities:'Preceptor preparation and synthetic teaching support',educationAuthority:'Assignment reported; not verified here'}
      };
    """


class SoulQuizConstellationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.quiz = QUIZ_HTML.read_text(encoding="utf-8") if QUIZ_HTML.exists() else ""
        cls.model = MODEL.read_text(encoding="utf-8") if MODEL.exists() else ""
        cls.app = APP.read_text(encoding="utf-8") if APP.exists() else ""
        cls.css = CSS.read_text(encoding="utf-8") if CSS.exists() else ""

    def test_required_artifacts_exist(self) -> None:
        for path in (QUIZ_HTML, MODEL, APP, CSS, SCHEMA, GUIDE, DESIGN):
            self.assertTrue(path.is_file(), path)
            self.assertGreater(path.stat().st_size, 500, path)

    def test_javascript_syntax(self) -> None:
        for source in (MODEL, APP):
            completed = subprocess.run(["node", "--check", str(source)], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_fourteen_domain_taxonomy_and_required_roles(self) -> None:
        result = node_eval("""
          import {ROLE_DOMAINS,ROLE_TAXONOMY} from './soul-quiz/soul-quiz-model.mjs';
          console.log(JSON.stringify({domains:ROLE_DOMAINS.map(x=>x.id),roles:ROLE_TAXONOMY.map(x=>x.id),unique:new Set(ROLE_TAXONOMY.map(x=>x.id)).size===ROLE_TAXONOMY.length}));
        """)
        self.assertEqual(result["domains"], [
            "learning-formation", "direct-clinical-care", "advanced-clinical-practice",
            "education-mentorship", "leadership-management", "administration-operations",
            "quality-safety-governance", "research-evidence", "informatics-technology-ai",
            "innovation-product", "entrepreneurship-business", "community-population-health",
            "wellness-sustainability", "advocacy-stewardship",
        ])
        required = {
            "prelicensure-nursing-student", "nursing-assistant-pct", "bedside-nurse",
            "advanced-practice-clinician", "clinical-preceptor", "nurse-educator",
            "nurse-manager", "healthcare-leader", "nurse-researcher",
            "quality-improvement-specialist", "nurse-entrepreneur", "ai-innovator",
            "medical-resident-fellow", "physician", "hospital-administrator",
            "clinic-manager", "wellness-manager",
        }
        self.assertTrue(required.issubset(set(result["roles"])))
        self.assertTrue(result["unique"])

    def test_every_role_has_domain_module_dashboard_and_authority_disclaimer(self) -> None:
        result = node_eval("""
          import {ROLE_DOMAINS,ROLE_TAXONOMY,CONDITIONAL_MODULES,DASHBOARD_CATALOG} from './soul-quiz/soul-quiz-model.mjs';
          const domains=new Set(ROLE_DOMAINS.map(x=>x.id)); const modules=new Set(Object.keys(CONDITIONAL_MODULES)); const dashboards=new Set(Object.keys(DASHBOARD_CATALOG));
          console.log(JSON.stringify(ROLE_TAXONOMY.map(r=>({id:r.id,domain:domains.has(r.domainId),module:modules.has(r.moduleId),dashboards:r.dashboardIds.length>0&&r.dashboardIds.every(x=>dashboards.has(x)),disclaimer:typeof r.authorityDisclaimer==='string'&&r.authorityDisclaimer.length>30}))));
        """)
        self.assertTrue(all(all(item[k] for k in ("domain", "module", "dashboards", "disclaimer")) for item in result))

    def test_custom_role_removal_is_atomic_and_reassigns_primary(self) -> None:
        result = node_eval("""
          import {createInitialState,addCustomRole,removeCustomRole} from './soul-quiz/soul-quiz-model.mjs';
          const s=createInitialState('2026-07-20T00:00:00.000Z');
          s.roleSelections=[{roleId:'bedside-nurse',status:'supporting',attention:3,responsibility:3,identity:3,confidence:3,authorization:'self-declared',competenceEvidence:'not-assessed',credentialStatus:'not-claimed'}];
          addCustomRole(s,'Rural Health Coordinator','community-population-health','primary');
          const id=s.customRoles[0].id;
          removeCustomRole(s,id);
          let taxonomyRemovalBlocked=false;
          try { removeCustomRole(s,'bedside-nurse'); } catch { taxonomyRemovalBlocked=true; }
          console.log(JSON.stringify({customRoles:s.customRoles,roles:s.roleSelections,taxonomyRemovalBlocked}));
        """)
        self.assertEqual(result["customRoles"], [])
        self.assertEqual(result["roles"][0]["roleId"], "bedside-nurse")
        self.assertEqual(result["roles"][0]["status"], "primary")
        self.assertTrue(result["taxonomyRemovalBlocked"])

    def test_student_and_assistant_are_distinct_but_share_a_combined_module(self) -> None:
        result = node_eval("""
          import {roleById,CONDITIONAL_MODULES} from './soul-quiz/soul-quiz-model.mjs';
          const student=roleById('prelicensure-nursing-student'); const assistant=roleById('nursing-assistant-pct'); const mod=CONDITIONAL_MODULES['student-assistant'];
          console.log(JSON.stringify({student,assistant,moduleQuestionIds:mod.questions.map(x=>x.id),safeguards:mod.safeguards}));
        """)
        student = result["student"]
        assistant = result["assistant"]
        ids = set(result["moduleQuestionIds"])
        self.assertNotEqual(result["student"]["id"], result["assistant"]["id"])
        self.assertEqual(student["moduleId"], "student-assistant")
        self.assertEqual(assistant["moduleId"], "student-assistant")
        self.assertNotEqual(student["label"], assistant["label"])
        self.assertEqual(assistant["legacyRole"], "staff")
        self.assertIn("Healthcare Assistant", assistant["label"])
        for required in ("studentAssistantCombination", "programAndStage", "trainingEmploymentStatus", "authorizedScope", "delegatedDuties", "supervision", "clinicalSimulationExperience", "confidenceVsCompetence", "entranceProgressionNclex", "transitionGoals", "studentAssistantAiBoundary"):
            self.assertIn(required, ids)
        text = " ".join(result["safeguards"]).lower()
        for phrase in ("authorized scope", "faculty", "academic dishonesty", "verified competence", "unsupervised clinical authority"):
            self.assertIn(phrase, text)

    def test_student_and_assistant_dashboards_separate_unless_both_selected(self) -> None:
        result = node_eval("""
          import {createInitialState,recommendDashboards} from './soul-quiz/soul-quiz-model.mjs';
          const selection=(roleId,status='primary')=>({roleId,status,attention:3,responsibility:3,identity:3,confidence:3,authorization:'self-declared',competenceEvidence:'not-assessed',credentialStatus:'not-claimed'});
          const ids=(roles)=>{const s=createInitialState('2026-07-20T00:00:00.000Z');s.roleSelections=roles;return recommendDashboards(s).map(x=>x.id)};
          console.log(JSON.stringify({student:ids([selection('prelicensure-nursing-student')]),assistant:ids([selection('nursing-assistant-pct')]),both:ids([selection('prelicensure-nursing-student'),selection('nursing-assistant-pct','supporting')])}));
        """)
        self.assertIn("prelicensure-student", result["student"])
        self.assertNotIn("nursing-assistant-workforce", result["student"])
        self.assertIn("nursing-assistant-workforce", result["assistant"])
        self.assertNotIn("prelicensure-student", result["assistant"])
        self.assertIn("student-assistant-bridge", result["both"])
        self.assertNotIn("prelicensure-student", result["both"])
        self.assertNotIn("nursing-assistant-workforce", result["both"])

    def test_advanced_studies_is_cross_role_and_complete(self) -> None:
        result = node_eval("""
          import {ADVANCED_STUDY_TYPES,CONDITIONAL_MODULES} from './soul-quiz/soul-quiz-model.mjs';
          const mod=CONDITIONAL_MODULES['advanced-studies'];
          console.log(JSON.stringify({types:ADVANCED_STUDY_TYPES.map(x=>x.id),overlay:mod.crossRoleOverlay,ids:mod.questions.map(x=>x.id)}));
        """)
        self.assertTrue(result["overlay"])
        self.assertIn("specialty-certification", result["types"])
        self.assertIn("doctoral-degree", result["types"])
        self.assertIn("residency-fellowship", result["types"])
        self.assertIn("continuing-professional-development", result["types"])
        for required in ("pathwayTarget", "motivationOutcome", "preparationStage", "competenciesMilestones", "progressEvidenceGaps", "learningTimeSupport", "roleRelationship", "barriersWellness", "applicationRenewal", "academicIntegrityBoundary"):
            self.assertIn(required, result["ids"])

    def test_every_question_has_purpose_and_output_mapping(self) -> None:
        result = node_eval("""
          import {CORE_QUESTIONS,CONDITIONAL_MODULES} from './soul-quiz/soul-quiz-model.mjs';
          const questions=[...CORE_QUESTIONS,...Object.values(CONDITIONAL_MODULES).flatMap(m=>m.questions)];
          console.log(JSON.stringify({count:questions.length,unique:new Set(questions.map(x=>x.id)).size===questions.length,bad:questions.filter(x=>!x.id||!x.purpose||!Array.isArray(x.outputs)||x.outputs.length===0).map(x=>x.id)}));
        """)
        self.assertGreaterEqual(result["count"], 45)
        self.assertTrue(result["unique"])
        self.assertEqual(result["bad"], [])

    def test_role_scoring_preserves_constellation_without_inferred_winner(self) -> None:
        script = """
          import {createInitialState,scoreRoleConstellation} from './soul-quiz/soul-quiz-model.mjs';
        """ + representative_state_js() + """
          const result=scoreRoleConstellation(s);
          console.log(JSON.stringify(result));
        """
        result = node_eval(script)
        self.assertEqual(result["primary"][0]["roleId"], "bedside-nurse")
        self.assertEqual({x["roleId"] for x in result["supporting"]}, {"clinical-preceptor", "quality-improvement-specialist"})
        self.assertEqual(result["emerging"][0]["roleId"], "nurse-entrepreneur")
        self.assertIn("role synergies", " ".join(result["synergies"]).lower())
        self.assertTrue(result["tensions"])
        self.assertNotIn("winner", json.dumps(result).lower())

    def test_state_normalization_is_deep_fail_closed_and_deterministic(self) -> None:
        result = node_eval("""
          import {createInitialState,normalizeState,scoreRoleConstellation} from './soul-quiz/soul-quiz-model.mjs';
          const role=(roleId,status='supporting',authorization='self-declared')=>({roleId,status,attention:3,responsibility:3,identity:3,confidence:3,authorization,competenceEvidence:'not-assessed',credentialStatus:'not-claimed'});
          const base=createInitialState('2026-07-20T00:00:00.000Z');
          base.roleSelections=[role('nurse-manager'),role('bedside-nurse')];
          base.advancedStudies={active:true,pathways:[{type:'masters-degree',target:'MSN',stage:'exploring',formats:[]}]};
          const restored=normalizeState(base);
          const malformed=[{...base,ai:'bad'},{...base,core:{...base.core,values:'bad'}},{...base,roleSelections:[role('unknown-role')]},{...base,roleSelections:[role('bedside-nurse','primary','not-current')]},{...base,advancedStudies:{active:false,pathways:[{type:'masters-degree',target:'MSN',stage:'exploring'}]}}];
          console.log(JSON.stringify({restoredId:restored?.advancedStudies.pathways[0].id,bad:malformed.map(x=>normalizeState(x)),tie:scoreRoleConstellation(base).supporting.map(x=>x.roleId)}));
        """)
        self.assertEqual(result["restoredId"], "study-pathway-1")
        self.assertTrue(all(item is None for item in result["bad"]))
        self.assertEqual(result["tie"], ["bedside-nurse", "nurse-manager"])

    def test_confidence_does_not_create_competence_credential_or_authority(self) -> None:
        result = node_eval("""
          import {createInitialState,scoreRoleConstellation} from './soul-quiz/soul-quiz-model.mjs';
          const s=createInitialState('2026-07-20T00:00:00.000Z');s.name='Test';s.roleSelections=[{roleId:'physician',status:'primary',attention:5,responsibility:5,identity:5,confidence:5,authorization:'self-declared',competenceEvidence:'developing-not-verified',credentialStatus:'aspirational-not-verified'}];
          const r=scoreRoleConstellation(s).primary[0];console.log(JSON.stringify(r));
        """)
        self.assertEqual(result["confidence"], 5)
        self.assertFalse(result["authorityGranted"])
        self.assertEqual(result["verification"], "self-reported-not-verified")
        self.assertIn("developing-not-verified", result["competenceEvidence"])
        self.assertIn("aspirational-not-verified", result["credentialStatus"])

    def test_governance_floors_block_authority_laundering(self) -> None:
        result = node_eval("""
          import {applyGovernanceFloor} from './soul-quiz/soul-quiz-model.mjs';
          const requested='independent-private';
          console.log(JSON.stringify({clinical:applyGovernanceFloor('patient-specific-clinical-decision',requested),external:applyGovernanceFloor('external-send',requested),graded:applyGovernanceFloor('graded-or-evaluative-work',requested),institutional:applyGovernanceFloor('institutional-change',requested),publicSummary:applyGovernanceFloor('public-source-summary',requested)}));
        """)
        self.assertEqual(result["clinical"], "never-delegate")
        self.assertEqual(result["external"], "explicit-confirmation")
        self.assertIn(result["graded"], ("professional-supervision", "never-delegate"))
        self.assertIn(result["institutional"], ("accountable-human-judgment", "explicit-confirmation"))
        self.assertEqual(result["publicSummary"], "independent-private")

    def test_dashboard_recommendations_coordinate_one_identity(self) -> None:
        script = """
          import {createInitialState,recommendDashboards} from './soul-quiz/soul-quiz-model.mjs';
        """ + representative_state_js() + """
          console.log(JSON.stringify(recommendDashboards(s)));
        """
        result = node_eval(script)
        ids = {item["id"] for item in result}
        self.assertTrue({"bedside-clinical-command", "education-mentorship", "quality-safety-governance", "entrepreneurship-business", "advanced-studies-certification"}.issubset(ids))
        for dashboard in result:
            for key in ("name", "purpose", "rolesSupported", "primaryObjectives", "currentPriorities", "informationRequirements", "recommendedAgents", "coreWorkflows", "learningGoals", "milestones", "performanceIndicators", "permissions", "dataBoundaries", "humanReview", "safeguards", "relationships"):
                self.assertIn(key, dashboard)
            self.assertEqual(dashboard["sharedFoundation"], "one-core-soul")
            self.assertEqual(dashboard["autonomy"], "A0-recommendation-only")

    def test_agent_recommendations_are_governed_and_not_activated(self) -> None:
        script = """
          import {createInitialState,recommendAgents} from './soul-quiz/soul-quiz-model.mjs';
        """ + representative_state_js() + """
          console.log(JSON.stringify(recommendAgents(s)));
        """
        result = node_eval(script)
        ids = {item["id"] for item in result}
        self.assertTrue({"tutor", "research-assistant", "project-manager", "governance-monitor"}.issubset(ids))
        self.assertTrue(all(item["activation"] == "not-authorized" for item in result))
        self.assertTrue(all(item["humanGate"] for item in result))

    def test_v2_config_keeps_v1_bridge_and_adds_constellation(self) -> None:
        script = """
          import {createInitialState,buildOsConfig} from './soul-quiz/soul-quiz-model.mjs';
        """ + representative_state_js() + """
          console.log(JSON.stringify(buildOsConfig(s,'2026-07-20T00:00:00.000Z')));
        """
        config = node_eval(script)
        self.assertEqual(config["schema_version"], "2.0.0")
        self.assertIn(config["identity"]["role"], ("student", "staff", "leader", "other"))
        self.assertEqual(config["role_constellation"]["primary"][0]["role_id"], "bedside-nurse")
        self.assertEqual(config["spheres"], ["personal", "professional", "community", "sidegig", "interest"])
        self.assertEqual(config["tier_ceilings"], {"personal": "green", "professional": "yellow", "community": "yellow", "sidegig": "green", "interest": "green"})
        self.assertIn("CCRN", config["mission"]["shared_goals"])
        self.assertIn("recovery sleep", config["mission"]["commitment_boundaries"])
        self.assertTrue(config["advanced_studies"]["active"])
        self.assertEqual(len(config["advanced_studies"]["pathways"]), 2)
        self.assertGreaterEqual(len(config["mission_controls"]), 5)
        self.assertIn("clinical-care", config["role_module_context"])
        self.assertEqual(config["capacity"]["self_reported_load"], 4)
        self.assertTrue(config["boundaries"]["no_phi_confirmed"])
        self.assertTrue(config["boundaries"]["no_clinical_decisions_confirmed"])
        self.assertFalse(config["authority"]["credentials_verified"])
        self.assertFalse(config["authority"]["professional_authority_granted"])
        self.assertEqual([item["id"] for item in config["advanced_studies"]["pathways"]], ["study-pathway-1", "study-pathway-2"])
        self.assertEqual([item["target"] for item in config["advanced_studies"]["pathways"]], ["CCRN", "MSN"])

    def test_export_boundary_coercion_keeps_live_state_schema_safe(self) -> None:
        script = """
          import {createInitialState,buildOsConfig} from './soul-quiz/soul-quiz-model.mjs';
        """ + representative_state_js() + """
          s.decisionStyle={evidence:99,unexpected:5};
          s.ai.memoryAllowed=['x'.repeat(500)];
          s.ai.memoryForbidden=['y'.repeat(500)];
          s.ai.escalationTriggers=['z'.repeat(500)];
          s.advancedStudies.pathways[0].motivation='m'.repeat(3000);
          s.advancedStudies.pathways[0].accountability='a'.repeat(2000);
          const config=buildOsConfig(s,'2026-07-20T00:00:00.000Z');
          console.log(JSON.stringify({decision:config.decision_style,memoryAllowed:config.boundaries.memory_allowed[0].length,memoryForbidden:config.boundaries.memory_forbidden[0].length,escalation:config.boundaries.escalation_triggers[0].length,motivation:config.advanced_studies.pathways[0].motivation.length,accountability:config.advanced_studies.pathways[0].accountability.length}));
        """
        result = node_eval(script)
        self.assertEqual(set(result["decision"]), {"evidence", "uncertainty", "risk", "collaboration", "accountability", "innovation", "conflict", "timePressure", "ethicalConcerns", "competingPriorities"})
        self.assertTrue(all(value == 3 for value in result["decision"].values()))
        self.assertEqual(result["memoryAllowed"], 200)
        self.assertEqual(result["memoryForbidden"], 200)
        self.assertEqual(result["escalation"], 300)
        self.assertEqual(result["motivation"], 2000)
        self.assertEqual(result["accountability"], 1000)

    def test_schema_accepts_legacy_v1_and_representative_v2(self) -> None:
        try:
            import jsonschema
            from jsonschema import Draft7Validator, FormatChecker
        except Exception as exc:
            self.skipTest(f"jsonschema unavailable: {exc}")
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        legacy = {
            "schema_version": "1.0.0", "generated_at": "2026-07-20T00:00:00Z", "generator": "soul-quiz",
            "identity": {"name": "Legacy", "role": "staff", "role_label": "Staff nurse", "one_liner": "", "always_remember": ""},
            "voice": {"length": "Short & direct", "formality": "Professional", "pushback": "", "avoid": ""},
            "values": ["dignity"], "spheres": ["professional"], "interests": [], "tier_ceilings": {"professional": "yellow"},
            "boundaries": {"no_phi_confirmed": True, "no_clinical_decisions_confirmed": True, "confidential_list": [], "wellbeing_rule": "", "decisions_always_mine": [], "drafts_without_asking": []},
            "doctrine": {"edena": "edena-policy@2.0.0", "florence_x": "florence-x@2.0.0", "core_line": "Agents propose. Humans judge. Nurses steward."},
        }
        script = """
          import {createInitialState,buildOsConfig} from './soul-quiz/soul-quiz-model.mjs';
        """ + representative_state_js() + """
          console.log(JSON.stringify(buildOsConfig(s,'2026-07-20T00:00:00.000Z')));
        """
        v2 = node_eval(script)
        validator = Draft7Validator(schema, format_checker=FormatChecker())
        validator.validate(legacy)
        validator.validate(v2)

        unsafe_delegation = json.loads(json.dumps(v2))
        unsafe_delegation["boundaries"]["delegation_matrix"]["external-send"] = "independent-private"
        unsafe_delegation["ai_operating_preferences"]["delegation_matrix"]["external-send"] = "independent-private"
        with self.assertRaises(jsonschema.ValidationError):
            validator.validate(unsafe_delegation)

        incomplete_delegation = json.loads(json.dumps(v2))
        incomplete_delegation["boundaries"]["delegation_matrix"] = {}
        with self.assertRaises(jsonschema.ValidationError):
            validator.validate(incomplete_delegation)

        invalid_time = json.loads(json.dumps(v2))
        invalid_time["generated_at"] = "not-a-date"
        with self.assertRaises(jsonschema.ValidationError):
            validator.validate(invalid_time)

        hybrid = json.loads(json.dumps(legacy))
        hybrid["role_constellation"] = v2["role_constellation"]
        with self.assertRaises(jsonschema.ValidationError):
            validator.validate(hybrid)

    def test_importer_dry_run_accepts_v2_without_writes(self) -> None:
        try:
            import jsonschema  # noqa: F401
        except Exception as exc:
            self.skipTest(f"jsonschema unavailable: {exc}")
        script = """
          import {createInitialState,buildOsConfig} from './soul-quiz/soul-quiz-model.mjs';
        """ + representative_state_js() + """
          console.log(JSON.stringify(buildOsConfig(s,'2026-07-20T00:00:00.000Z')));
        """
        config = node_eval(script)
        with tempfile.TemporaryDirectory() as tmp:
            soul = Path(tmp) / "naio-soul.json"
            soul.write_text(json.dumps(config), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, "-I", str(IMPORTER), str(soul), "--schema", str(SCHEMA)],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertEqual(list(Path(tmp).iterdir()), [soul])

    def test_importer_fails_closed_without_jsonschema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            soul = Path(tmp) / "naio-soul.json"
            soul.write_text('{"schema_version":"1.0.0"}', encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, "-I", "-S", str(IMPORTER), str(soul), "--schema", str(SCHEMA)],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("required jsonschema validator unavailable", completed.stderr)

    def test_importer_rejects_duplicate_keys_and_unknown_versions_before_validation(self) -> None:
        probes = [
            ('{"schema_version":"1.0.0","schema_version":"2.0.0"}', "duplicate JSON key"),
            ('{"schema_version":"3.0.0"}', "unsupported schema_version"),
            ('[]', "JSON root must be an object"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            soul = Path(tmp) / "naio-soul.json"
            for raw, expected in probes:
                soul.write_text(raw, encoding="utf-8")
                completed = subprocess.run(
                    [sys.executable, "-I", str(IMPORTER), str(soul), "--schema", str(SCHEMA)],
                    cwd=ROOT, capture_output=True, text=True,
                )
                self.assertEqual(completed.returncode, 2, completed.stdout + completed.stderr)
                self.assertIn(expected, completed.stderr)

    def test_importer_semantic_guards_reject_contradictory_v2_profiles(self) -> None:
        try:
            import jsonschema  # noqa: F401
        except Exception as exc:
            self.skipTest(f"jsonschema unavailable: {exc}")
        script = """
          import {createInitialState,buildOsConfig} from './soul-quiz/soul-quiz-model.mjs';
        """ + representative_state_js() + """
          console.log(JSON.stringify(buildOsConfig(s,'2026-07-20T00:00:00.000Z')));
        """
        valid = node_eval(script)
        mismatched = json.loads(json.dumps(valid))
        mismatched["tier_ceilings"].pop("interest")
        duplicate_roles = json.loads(json.dumps(valid))
        duplicate_roles["role_constellation"]["supporting"][0]["role_id"] = duplicate_roles["role_constellation"]["primary"][0]["role_id"]
        bucket_mismatch = json.loads(json.dumps(valid))
        bucket_mismatch["role_constellation"]["supporting"][0]["status"] = "emerging"
        arbitrary_authority = json.loads(json.dumps(valid))
        arbitrary_authority["role_constellation"]["primary"][0]["authorization"] = "independently-verified-licensed-authority"
        inactive_with_pathways = json.loads(json.dumps(valid))
        inactive_with_pathways["advanced_studies"]["active"] = False
        duplicate_pathways = json.loads(json.dumps(valid))
        duplicate_pathways["advanced_studies"]["pathways"][1]["id"] = duplicate_pathways["advanced_studies"]["pathways"][0]["id"]
        not_current_primary = json.loads(json.dumps(valid))
        not_current_primary["role_constellation"]["primary"][0]["authorization"] = "not-current"
        custom_mismatch = json.loads(json.dumps(valid))
        custom_mismatch["role_constellation"]["supporting"][0]["role_id"] = "local-role-community-writer"
        custom_mismatch["role_constellation"]["supporting"][0]["label"] = "Community Writer"
        custom_mismatch["role_constellation"]["custom_roles"] = [{"role_id": "local-role-community-writer", "label": "Different Local Role", "domain_id": custom_mismatch["role_constellation"]["supporting"][0]["domain_id"], "status": "local-draft-not-reviewed", "authority_granted": False}]
        delegation_mismatch = json.loads(json.dumps(valid))
        delegation_mismatch["ai_operating_preferences"]["delegation_matrix"]["external-send"] = "professional-supervision"
        with tempfile.TemporaryDirectory() as tmp:
            soul = Path(tmp) / "naio-soul.json"
            for payload, expected in (
                (mismatched, "tier_ceilings keys must exactly match"),
                (duplicate_roles, "selected role IDs must be unique"),
                (bucket_mismatch, "schema validation failed"),
                (arbitrary_authority, "schema validation failed"),
                (inactive_with_pathways, "schema validation failed"),
                (duplicate_pathways, "pathway IDs must be unique"),
                (not_current_primary, "cannot use not-current authorization"),
                (custom_mismatch, "custom role label/domain mismatch"),
                (delegation_mismatch, "delegation matrices must be identical"),
            ):
                soul.write_text(json.dumps(payload), encoding="utf-8")
                completed = subprocess.run(
                    [sys.executable, "-I", str(IMPORTER), str(soul), "--schema", str(SCHEMA)],
                    cwd=ROOT, capture_output=True, text=True,
                )
                self.assertEqual(completed.returncode, 2, completed.stdout + completed.stderr)
                self.assertIn(expected, completed.stderr)

    def test_soul_documents_include_requested_outputs(self) -> None:
        script = """
          import {createInitialState,buildSoulDocuments} from './soul-quiz/soul-quiz-model.mjs';
        """ + representative_state_js() + """
          console.log(JSON.stringify(buildSoulDocuments(s,'2026-07-20T00:00:00.000Z')));
        """
        docs = node_eval(script)
        names = {item["name"] for item in docs}
        self.assertTrue({"Core-SOUL.md", "Role-Constellation.md", "Role-Context-Deep-Dives.md", "Mission-Control-Recommendations.md", "AI-Governance-Profile.md", "SOUL-Profile-Metadata.md", "Advanced-Studies-SOUL.md"}.issubset(names))
        combined = "\n".join(item["content"] for item in docs)
        self.assertIn("MSN", combined)
        self.assertIn("every 90 days", combined)
        self.assertIn("Do not treat a profile update as verification", combined)
        for phrase in ("Primary roles", "Supporting roles", "Emerging roles", "Core values", "Human judgment", "What AI must never do", "Shared foundation", "Advanced Studies", "Adult critical-care role", "self-reported context, not verification"):
            self.assertIn(phrase, combined)

    def test_html_is_semantic_private_and_module_driven(self) -> None:
        parser = QuizParser()
        parser.feed(self.quiz)
        self.assertEqual(parser.mains, 1)
        self.assertEqual(parser.progressbars, 1)
        self.assertIn("quiz-app", parser.ids)
        self.assertIn("quiz-status", parser.ids)
        self.assertTrue(any(item.get("type") == "module" and item.get("src") == "soul-quiz/soul-quiz-app.mjs" for item in parser.scripts))
        combined = self.quiz + self.app + self.model
        for forbidden in ("fetch(", "XMLHttpRequest", "WebSocket", "sendBeacon", "gtag(", "mixpanel", "segment.io"):
            self.assertNotIn(forbidden, combined)
        self.assertIn("sessionStorage", self.app)
        self.assertIn("No PHI", self.quiz)
        self.assertIn("one integrated professional soul", self.quiz.lower())

    def test_ui_controls_preserve_labels_pathways_and_schema_limits(self) -> None:
        self.assertNotIn('aria-label="${attr(name)}"', self.app)
        self.assertIn("const primaryOptions = AI_RELATIONSHIP_MODES;", self.app)
        self.assertIn("state.ai.relationshipModes.includes(requestedPrimaryMode)", self.app)
        self.assertIn("if (matchingMode) matchingMode.checked = true", self.app)
        self.assertIn("else primaryMode.value = relationshipModes.find((input) => input.checked)?.value || ''", self.app)
        self.assertIn("if (input.checked && primaryMode && !primaryMode.value) primaryMode.value = input.value", self.app)
        self.assertIn("primaryMode.value = relationshipModes.find((mode) => mode.checked)?.value || ''", self.app)
        add_handler = self.app[self.app.index("app.querySelector('[data-action=\"add-study-pathway\"]')"):]
        self.assertLess(add_handler.index("form.elements['advanced-active'].checked = true"), add_handler.index("collectCurrent();"))
        for fragment in (
            "splitList(form.elements['memory-allowed'].value, 200)",
            "splitList(form.elements['memory-forbidden'].value, 200)",
            "splitList(form.elements['escalation-triggers'].value, 300)",
            "pathway.motivation, 2000",
            "pathway.accountability, 1000",
            "pathway.roleRelationship, 2000",
            "pathway.integrityBoundary, 2000",
        ):
            self.assertIn(fragment, self.app)

    def test_release_version_ranks_include_patch_without_weakening_phase_order(self) -> None:
        for script in (
            ROOT / "naio-os/scripts/check-update.py",
            ROOT / "naio-os/scripts/verify-release.py",
        ):
            rank = runpy.run_path(str(script))["version_rank"]
            self.assertGreater(rank("2.0.1-phase23"), rank("2.0.0-phase23"), script)
            self.assertGreater(rank("2.0.0-phase24"), rank("2.99.99-phase23"), script)
            self.assertEqual(rank("invalid"), (0, 0, 0, 0), script)

    def test_required_validator_dependencies_block_preflight_and_ship_in_manifest(self) -> None:
        preflight = PREFLIGHT.read_text(encoding="utf-8")
        requirements = REQUIREMENTS.read_text(encoding="utf-8")
        manifest = MANIFEST.read_text(encoding="utf-8")
        self.assertIn('fail "python jsonschema missing', preflight)
        self.assertIn('fail "python pyyaml missing', preflight)
        self.assertIn("jsonschema[format-nongpl]==4.25.1", requirements)
        self.assertIn("PyYAML==6.0.3", requirements)
        self.assertIn("path: requirements-import-soul.txt", manifest)

    def test_signed_bundle_manifest_checksums_and_signature_are_current(self) -> None:
        try:
            import yaml
        except Exception as exc:
            self.skipTest(f"pyyaml unavailable: {exc}")
        manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
        for item in manifest["contents"]:
            if item.get("self_checksum_excluded"):
                continue
            path = MANIFEST.parent / item["path"]
            self.assertTrue(path.is_file(), path)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), item["sha256"], item["path"])
        completed = subprocess.run(
            [sys.executable, "-I", str(RELEASE_VERIFIER), "--quiet"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_design_document_has_all_seventeen_requested_sections(self) -> None:
        text = DESIGN.read_text(encoding="utf-8")
        headings = re.findall(r"^##\s+(\d+)\.\s+(.+)$", text, flags=re.MULTILINE)
        self.assertEqual([int(number) for number, _ in headings], list(range(1, 18)))
        required_titles = [
            "Design philosophy", "Role, identity, and developmental framework", "Professional role taxonomy",
            "Core quiz", "Conditional role modules", "Prelicensure Nursing Student and Nursing Assistant module",
            "Advanced Studies cross-role module", "Answer formats and response scales", "Multidimensional scoring methodology",
            "Role-constellation interpretation rules", "Soul Document output template", "Mission Control dashboard recommendation logic",
            "AI-agent and workflow recommendation logic", "Example result", "Example result", "Privacy, academic-integrity, clinical-safety, and governance safeguards",
            "Process for periodically reviewing and updating the profile",
        ]
        self.assertEqual([title for _, title in headings], required_titles)

    def test_companion_guide_reflects_integrated_roles(self) -> None:
        text = GUIDE.read_text(encoding="utf-8")
        for phrase in ("role constellation", "primary, supporting, emerging, and contextual", "one Core SOUL", "Advanced Studies", "Nursing Assistant", "organizational view"):
            self.assertIn(phrase, text)
        self.assertNotIn("Pick the closest — right now, not your whole history", text)
        self.assertIn("fitness-for-duty", self.model)
        self.assertIn("official local emergency routes", self.model)


if __name__ == "__main__":
    unittest.main()
