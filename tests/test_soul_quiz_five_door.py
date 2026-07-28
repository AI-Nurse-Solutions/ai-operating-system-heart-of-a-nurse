#!/usr/bin/env python3
"""Contracts for the progressive five-door SOUL Quiz quick start."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "soul-quiz" / "soul-quiz-model.mjs"
SCHEMA = ROOT / "naio-os" / "schema" / "naio-soul.schema.json"


def node_eval(source: str) -> Any:
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", source],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"node_eval failed (exit {completed.returncode}):\n{completed.stderr}"
        )
    return json.loads(completed.stdout)


class SoulQuizFiveDoorTests(unittest.TestCase):
    def test_exactly_five_primary_lanes_hide_the_full_taxonomy(self) -> None:
        result = node_eval("""
          import {QUICK_START_LANES,ROLE_TAXONOMY} from './soul-quiz/soul-quiz-model.mjs';
          console.log(JSON.stringify({
            ids: QUICK_START_LANES.map((lane) => lane.id),
            complete: QUICK_START_LANES.every((lane) => lane.label && lane.promise && lane.boundary && lane.defaultRoleId && lane.contexts.length && lane.missions.length && lane.artifacts.length),
            taxonomyCount: ROLE_TAXONOMY.length
          }));
        """)
        self.assertEqual(result["ids"], [
            "prelicensure-student",
            "staff-nurse",
            "leader",
            "educator",
            "licensed-clinician",
        ])
        self.assertTrue(result["complete"])
        self.assertGreater(result["taxonomyCount"], 5)

    def test_every_context_projects_to_a_known_role_without_authority(self) -> None:
        result = node_eval("""
          import {QUICK_START_LANES,ROLE_TAXONOMY,createInitialState,applyQuickStartRouting} from './soul-quiz/soul-quiz-model.mjs';
          const known=new Set(ROLE_TAXONOMY.map((role)=>role.id));
          const projections=[];
          for (const lane of QUICK_START_LANES) {
            for (const context of lane.contexts) {
              const state=createInitialState('2026-07-28T00:00:00.000Z');
              state.quickStart.primaryLane=lane.id;
              state.quickStart.roleContext=context.id;
              state.quickStart.currentMission=lane.missions[0].id;
              state.quickStart.projectState='no-project';
              state.quickStart.firstArtifact=lane.artifacts[0].id;
              applyQuickStartRouting(state);
              projections.push({
                lane:lane.id,
                context:context.id,
                primary:state.roleSelections.filter((item)=>item.status==='primary'),
                known:state.roleSelections.every((item)=>known.has(item.roleId)),
                safe:state.roleSelections.every((item)=>item.authorization==='self-declared' && item.competenceEvidence==='not-assessed' && item.credentialStatus==='not-claimed')
              });
            }
          }
          console.log(JSON.stringify(projections));
        """)
        self.assertTrue(result)
        for projection in result:
            self.assertEqual(len(projection["primary"]), 1, projection)
            self.assertTrue(projection["known"], projection)
            self.assertTrue(projection["safe"], projection)

    def test_staff_no_project_stays_project_free_and_quality_branch_is_explicit(self) -> None:
        result = node_eval("""
          import {createInitialState,applyQuickStartRouting} from './soul-quiz/soul-quiz-model.mjs';
          const make=(mission,projectState)=>{
            const state=createInitialState('2026-07-28T00:00:00.000Z');
            Object.assign(state.quickStart,{primaryLane:'staff-nurse',roleContext:'staff-practice',currentMission:mission,projectState,firstArtifact:'structured-question'});
            applyQuickStartRouting(state);
            return state.quickStart;
          };
          console.log(JSON.stringify({daily:make('improve-daily-work','no-project'),quality:make('start-quality-project','active-project')}));
        """)
        self.assertEqual(result["daily"]["activeOverlays"], [])
        self.assertEqual(result["daily"]["projectState"], "no-project")
        self.assertIn("quality-improvement", result["quality"]["activeOverlays"])

    def test_clinician_research_routes_to_governance_overlay_not_authority(self) -> None:
        result = node_eval("""
          import {createInitialState,applyQuickStartRouting,buildOsConfig} from './soul-quiz/soul-quiz-model.mjs';
          const state=createInitialState('2026-07-28T00:00:00.000Z');
          state.name='Jordan';
          state.safety={noPhi:true,noClinicalAuthority:true,noAcademicDishonesty:true,noCredentialInference:true};
          Object.assign(state.quickStart,{primaryLane:'licensed-clinician',roleContext:'nurse-practitioner',currentMission:'conduct-research',projectState:'active-approved-research',secondaryLanes:['educator'],firstArtifact:'research-question'});
          applyQuickStartRouting(state);
          const config=buildOsConfig(state,'2026-07-28T00:00:00.000Z');
          console.log(JSON.stringify({quick:state.quickStart,roles:state.roleSelections,routing:config.workspace_routing,authority:config.authority}));
        """)
        self.assertIn("research-evidence", result["quick"]["activeOverlays"])
        self.assertEqual(result["routing"]["primary_lane"], "licensed-clinician")
        self.assertEqual(result["routing"]["secondary_lanes"], ["educator"])
        self.assertEqual(result["routing"]["project_state"], "active-approved-research")
        self.assertFalse(result["authority"]["professional_authority_granted"])
        self.assertFalse(result["authority"]["institutional_authority_granted"])
        self.assertTrue(all(item["authorization"] == "self-declared" for item in result["roles"]))

    def test_secondary_hats_are_optional_unique_and_capped_at_two(self) -> None:
        result = node_eval("""
          import {createInitialState,applyQuickStartRouting} from './soul-quiz/soul-quiz-model.mjs';
          const attempt=(secondaryLanes)=>{
            const state=createInitialState('2026-07-28T00:00:00.000Z');
            Object.assign(state.quickStart,{primaryLane:'staff-nurse',roleContext:'staff-practice',currentMission:'improve-daily-work',projectState:'no-project',secondaryLanes,firstArtifact:'structured-question'});
            try { applyQuickStartRouting(state); return {ok:true,roles:state.roleSelections}; }
            catch (error) { return {ok:false,message:error.message}; }
          };
          console.log(JSON.stringify({none:attempt([]),two:attempt(['educator','leader']),three:attempt(['educator','leader','licensed-clinician']),duplicate:attempt(['educator','educator']),primaryAgain:attempt(['staff-nurse'])}));
        """)
        self.assertTrue(result["none"]["ok"])
        self.assertTrue(result["two"]["ok"])
        self.assertEqual(len(result["two"]["roles"]), 3)
        self.assertFalse(result["three"]["ok"])
        self.assertFalse(result["duplicate"]["ok"])
        self.assertFalse(result["primaryAgain"]["ok"])

    def test_project_state_is_scoped_to_the_selected_lane(self) -> None:
        result = node_eval("""
          import {createInitialState,applyQuickStartRouting} from './soul-quiz/soul-quiz-model.mjs';
          const state=createInitialState('2026-07-28T00:00:00.000Z');
          Object.assign(state.quickStart,{
            primaryLane:'prelicensure-student',roleContext:'student-only',
            currentMission:'understand-concept',projectState:'active-approved-research',
            firstArtifact:'learning-plan'
          });
          let refused=false;
          try { applyQuickStartRouting(state); } catch { refused=true; }
          console.log(JSON.stringify({refused}));
        """)
        self.assertTrue(result["refused"])

    def test_clinician_project_state_activates_governance_overlays_independently_of_mission(self) -> None:
        result = node_eval("""
          import {createInitialState,applyQuickStartRouting,normalizeState} from './soul-quiz/soul-quiz-model.mjs';
          const route=(projectState)=>{
            const state=createInitialState('2026-07-28T00:00:00.000Z');
            Object.assign(state.quickStart,{
              primaryLane:'licensed-clinician',roleContext:'nurse-practitioner',
              currentMission:'improve-workflow',projectState,
              firstArtifact:'professional-workflow-brief'
            });
            applyQuickStartRouting(state);
            return state.quickStart.activeOverlays;
          };
          const tampered=createInitialState('2026-07-28T00:00:00.000Z');
          Object.assign(tampered.quickStart,{
            primaryLane:'licensed-clinician',roleContext:'nurse-practitioner',
            currentMission:'improve-workflow',projectState:'active-approved-research',
            firstArtifact:'professional-workflow-brief',activeOverlays:[]
          });
          const repaired=normalizeState(tampered);
          console.log(JSON.stringify({quality:route('quality-improvement'),research:route('active-approved-research'),undetermined:route('determination-needed'),repaired:repaired.quickStart.activeOverlays}));
        """)
        self.assertEqual(result["quality"], ["quality-improvement"])
        self.assertEqual(result["research"], ["research-evidence"])
        self.assertEqual(result["undetermined"], ["quality-improvement", "research-evidence"])
        self.assertEqual(result["repaired"], ["research-evidence"])

    def test_legacy_drafts_restore_and_quick_state_round_trips_fail_closed(self) -> None:
        result = node_eval("""
          import {createInitialState,normalizeState,applyQuickStartRouting} from './soul-quiz/soul-quiz-model.mjs';
          const legacy=createInitialState('2026-07-28T00:00:00.000Z');
          delete legacy.quickStart;
          legacy.roleSelections=[{roleId:'bedside-nurse',status:'primary',attention:3,responsibility:3,identity:3,confidence:3,authorization:'self-declared',competenceEvidence:'not-assessed',credentialStatus:'not-claimed'}];
          const restoredLegacy=normalizeState(legacy);
          const quick=createInitialState('2026-07-28T00:00:00.000Z');
          Object.assign(quick.quickStart,{primaryLane:'educator',roleContext:'clinical-preceptor',currentMission:'prepare-feedback',projectState:'no-project',secondaryLanes:['staff-nurse'],firstArtifact:'feedback-plan'});
          applyQuickStartRouting(quick);
          const restoredQuick=normalizeState(JSON.parse(JSON.stringify(quick)));
          const invalid=JSON.parse(JSON.stringify(quick));
          invalid.quickStart.secondaryLanes=['staff-nurse','leader','licensed-clinician'];
          console.log(JSON.stringify({legacy:restoredLegacy?.quickStart,quick:restoredQuick?.quickStart,invalid:normalizeState(invalid)}));
        """)
        self.assertEqual(result["legacy"]["mode"], "deep")
        self.assertEqual(result["quick"]["primaryLane"], "educator")
        self.assertEqual(result["quick"]["secondaryLanes"], ["staff-nurse"])
        self.assertIsNone(result["invalid"])

    def test_quick_start_bundle_contains_a_focused_mission_control_starter(self) -> None:
        result = node_eval(
            """
            import {applyQuickStartRouting,buildSoulDocuments,createInitialState} from './soul-quiz/soul-quiz-model.mjs';
            const state = createInitialState();
            Object.assign(state.quickStart, {
              primaryLane: 'staff-nurse', roleContext: 'staff-practice',
              currentMission: 'improve-daily-work', projectState: 'no-project',
              firstArtifact: 'structured-question'
            });
            applyQuickStartRouting(state);
            console.log(JSON.stringify(buildSoulDocuments(state, '2026-07-28T00:00:00.000Z')));
            """
        )
        documents = {item["name"]: item["content"] for item in result}
        self.assertIn("Focused-Mission-Control.md", documents)
        starter = documents["Focused-Mission-Control.md"]
        self.assertIn("Staff nurse", starter)
        self.assertIn("Improve or organize daily professional work", starter)
        self.assertIn("No current project", starter)
        self.assertIn("Structured professional question", starter)
        self.assertIn("Write the broad professional question without PHI", starter)
        self.assertIn("No PHI", starter)
        self.assertIn("human review", starter.lower())

    def test_every_first_artifact_has_role_relevant_prompts_and_private_reflection_stays_private(self) -> None:
        result = node_eval("""
          import {QUICK_START_LANES,quickArtifactStarterPrompts} from './soul-quiz/soul-quiz-model.mjs';
          const ids=[...new Set(QUICK_START_LANES.flatMap((lane)=>lane.artifacts.map((item)=>item.id)))];
          const prompts=Object.fromEntries(ids.map((id)=>[id,quickArtifactStarterPrompts(id)]));
          console.log(JSON.stringify({ids,prompts,signatures:new Set(Object.values(prompts).map((items)=>items.join('|'))).size}));
        """)
        self.assertTrue(all(len(result["prompts"][artifact_id]) >= 3 for artifact_id in result["ids"]))
        self.assertGreaterEqual(result["signatures"], 20)
        reflection = " ".join(result["prompts"]["reflection-prompt"]).lower()
        self.assertIn("private local file", reflection)
        self.assertIn("faculty, manager, organizational, cohort, or aggregate reporting", reflection)

    def test_quick_export_validates_against_v2_schema(self) -> None:
        try:
            from jsonschema import Draft7Validator, FormatChecker
        except Exception as exc:  # pragma: no cover
            self.skipTest(f"jsonschema unavailable: {exc}")
        config = node_eval("""
          import {createInitialState,applyQuickStartRouting,buildOsConfig} from './soul-quiz/soul-quiz-model.mjs';
          const state=createInitialState('2026-07-28T00:00:00.000Z');
          state.name='Jordan';
          state.safety={noPhi:true,noClinicalAuthority:true,noAcademicDishonesty:true,noCredentialInference:true};
          Object.assign(state.quickStart,{primaryLane:'prelicensure-student',roleContext:'student-and-assistant',currentMission:'prepare-clinical-simulation',projectState:'no-project',secondaryLanes:[],firstArtifact:'clinical-preparation-plan'});
          applyQuickStartRouting(state);
          console.log(JSON.stringify(buildOsConfig(state,'2026-07-28T00:00:00.000Z')));
        """)
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        Draft7Validator(schema, format_checker=FormatChecker()).validate(config)
        self.assertEqual(config["schema_version"], "2.0.0")
        self.assertEqual(config["workspace_routing"]["deep_profile_status"], "not-started")
        self.assertEqual(len(config["role_constellation"]["primary"]), 1)
        config["workspace_routing"]["role_context"] = "nurse-practitioner"
        with self.assertRaises(Exception):
            Draft7Validator(schema, format_checker=FormatChecker()).validate(config)

    def test_every_lane_context_mission_project_and_artifact_combination_matches_schema(self) -> None:
        from jsonschema import Draft7Validator

        routings = node_eval("""
          import {QUICK_START_LANES,QUICK_START_PROJECT_OPTIONS,createInitialState,applyQuickStartRouting,buildOsConfig} from './soul-quiz/soul-quiz-model.mjs';
          const output=[];
          for (const lane of QUICK_START_LANES) for (const context of lane.contexts)
            for (const mission of lane.missions) for (const project of QUICK_START_PROJECT_OPTIONS[lane.id])
              for (const artifact of lane.artifacts) {
                const state=createInitialState('2026-07-28T00:00:00.000Z');
                state.name='Contract';
                Object.assign(state.quickStart,{
                  primaryLane:lane.id,roleContext:context.id,currentMission:mission.id,
                  projectState:project.id,firstArtifact:artifact.id
                });
                applyQuickStartRouting(state);
                output.push(buildOsConfig(state,'2026-07-28T00:00:00.000Z').workspace_routing);
              }
          console.log(JSON.stringify(output));
        """)
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))["properties"]["workspace_routing"]
        validator = Draft7Validator(schema)
        failures = [(routing, list(validator.iter_errors(routing))) for routing in routings]
        failures = [(routing, errors) for routing, errors in failures if errors]
        self.assertFalse(failures, failures[:3])
        self.assertEqual(len(routings), 2382)
        repeated_lane_failures = []
        for routing in routings:
            repeated_lane = json.loads(json.dumps(routing))
            repeated_lane["secondary_lanes"] = [routing["primary_lane"]]
            if not list(validator.iter_errors(repeated_lane)):
                repeated_lane_failures.append(repeated_lane)
        self.assertFalse(repeated_lane_failures, repeated_lane_failures[:3])
        research = next(item for item in routings if item["project_state"] == "active-approved-research" and item["current_mission"] == "improve-workflow")
        research["active_overlays"] = []
        self.assertTrue(list(validator.iter_errors(research)))
        daily = next(item for item in routings if item["primary_lane"] == "staff-nurse" and item["current_mission"] == "improve-daily-work" and item["project_state"] == "no-project")
        daily["active_overlays"] = ["quality-improvement"]
        self.assertTrue(list(validator.iter_errors(daily)))

    def test_importer_refuses_quick_routing_that_contradicts_projected_roles(self) -> None:
        config = node_eval("""
          import {createInitialState,applyQuickStartRouting,buildOsConfig} from './soul-quiz/soul-quiz-model.mjs';
          const state=createInitialState('2026-07-28T00:00:00.000Z');
          state.name='Import contract';
          Object.assign(state.safety,{noPhi:true,noClinicalAuthority:true,noAcademicDishonesty:true,noCredentialInference:true});
          Object.assign(state.quickStart,{primaryLane:'staff-nurse',roleContext:'staff-practice',currentMission:'improve-daily-work',projectState:'no-project',firstArtifact:'structured-question'});
          applyQuickStartRouting(state);
          console.log(JSON.stringify(buildOsConfig(state,'2026-07-28T00:00:00.000Z')));
        """)
        with tempfile.TemporaryDirectory() as tmp:
            valid_path = Path(tmp) / "valid.json"
            invalid_path = Path(tmp) / "invalid.json"
            duplicate_path = Path(tmp) / "duplicate.json"
            valid_config = json.loads(json.dumps(config))
            valid_path.write_text(json.dumps(config), encoding="utf-8")
            valid = subprocess.run(["python3", str(ROOT / "naio-os/scripts/import-soul.py"), str(valid_path)], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)
            config["workspace_routing"].update({
                "primary_lane": "educator",
                "role_context": "clinical-preceptor",
                "current_mission": "prepare-feedback",
                "project_state": "no-project",
                "active_overlays": ["education-mentorship"],
                "first_artifact": "feedback-plan",
            })
            invalid_path.write_text(json.dumps(config), encoding="utf-8")
            invalid = subprocess.run(["python3", str(ROOT / "naio-os/scripts/import-soul.py"), str(invalid_path)], cwd=ROOT, capture_output=True, text=True)
            valid_config["workspace_routing"]["secondary_lanes"] = ["staff-nurse"]
            duplicate_path.write_text(json.dumps(valid_config), encoding="utf-8")
            duplicate = subprocess.run(["python3", str(ROOT / "naio-os/scripts/import-soul.py"), str(duplicate_path)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(invalid.returncode, 2, invalid.stdout + invalid.stderr)
        self.assertIn("workspace routing", (invalid.stdout + invalid.stderr).lower())
        self.assertEqual(duplicate.returncode, 2, duplicate.stdout + duplicate.stderr)
        self.assertIn("workspace_routing.secondary_lanes", (duplicate.stdout + duplicate.stderr).lower())


if __name__ == "__main__":
    unittest.main()
