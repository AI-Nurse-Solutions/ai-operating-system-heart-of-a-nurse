#!/usr/bin/env python3
"""Deterministic tests for the browser-local Nurse AI OS Switchboard preview."""

from __future__ import annotations

import hashlib
import html.parser
import json
import re
import subprocess
import unittest
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SWITCHBOARD = ROOT / "switchboard"
HTML = (SWITCHBOARD / "index.html").read_text(encoding="utf-8")
CSS = (SWITCHBOARD / "switchboard.css").read_text(encoding="utf-8")
APP = (SWITCHBOARD / "switchboard.mjs").read_text(encoding="utf-8")
MODEL = (SWITCHBOARD / "switchboard-model.mjs").read_text(encoding="utf-8")
REGISTRY = json.loads((SWITCHBOARD / "data" / "role-registry.json").read_text(encoding="utf-8"))
STATE_SCHEMA = json.loads((SWITCHBOARD / "schema" / "switchboard.schema.json").read_text(encoding="utf-8"))
REGISTRY_SCHEMA = json.loads((SWITCHBOARD / "schema" / "role-registry-entry.schema.json").read_text(encoding="utf-8"))


class Parser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.hrefs: list[str] = []
        self.inputs: list[dict[str, str | None]] = []
        self.dialogs = 0
        self.mains = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        if data.get("id"):
            self.ids.append(str(data["id"]))
        if tag == "a" and data.get("href"):
            self.hrefs.append(str(data["href"]))
        if tag == "input":
            self.inputs.append(data)
        if tag == "dialog":
            self.dialogs += 1
        if tag == "main":
            self.mains += 1


def node_eval(source: str) -> Any:
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", source],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SwitchboardModelTests(unittest.TestCase):
    def test_two_dashboards_keep_same_person_role_contexts_separate(self) -> None:
        result = node_eval("""
          import {createInitialState,addDashboard,configurationPosture} from './switchboard/switchboard-model.mjs';
          let state=createInitialState('2026-07-17T00:00:00Z');
          state=addDashboard(state,{contextKey:'facility-a',departmentKey:'critical-care',primaryRoleId:'staff-nurse',supportingRoleIds:[],capabilityIds:['shift'],assignmentStatus:'organization-assigned-unverified',shiftWindow:'12-hours'},'2026-07-17T00:00:00Z','icu').state;
          state=addDashboard(state,{contextKey:'school-a',departmentKey:'education',primaryRoleId:'student-learner',supportingRoleIds:[],capabilityIds:['future','discover'],assignmentStatus:'education-enrolled-unverified',shiftWindow:'session'},'2026-07-17T01:00:00Z','school').state;
          console.log(JSON.stringify({count:state.dashboards.length,contexts:state.dashboards.map(x=>x.contextKey),active:state.activeDashboardId,cards:state.dashboards.map(x=>configurationPosture(x,state,'2026-07-17T02:00:00Z'))}));
        """)
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["contexts"], ["facility-a", "school-a"])
        self.assertNotEqual(result["cards"][0]["title"], result["cards"][1]["title"])
        self.assertTrue(all(card["autonomy"] == "A0 · no action" for card in result["cards"]))
        self.assertTrue(all(card["edena"] == "Not evaluated" for card in result["cards"]))

    def test_expired_or_ended_assignment_narrows_authority(self) -> None:
        result = node_eval("""
          import {createInitialState,addDashboard,configurationPosture,endDashboardSession} from './switchboard/switchboard-model.mjs';
          let state=createInitialState('2026-07-17T00:00:00Z');
          const made=addDashboard(state,{contextKey:'facility-a',departmentKey:'informatics',primaryRoleId:'nurse-informaticist',supportingRoleIds:[],capabilityIds:['orchestrate'],assignmentStatus:'organization-assigned-unverified',shiftWindow:'8-hours'},'2026-07-17T00:00:00Z','info');
          state=made.state;
          const active=configurationPosture(state.dashboards[0],state,'2026-07-17T07:59:00Z');
          const expired=configurationPosture(state.dashboards[0],state,'2026-07-17T08:01:00Z');
          state=endDashboardSession(state,made.dashboardId,'2026-07-17T03:00:00Z');
          const ended=configurationPosture(state.dashboards[0],state,'2026-07-17T03:01:00Z');
          console.log(JSON.stringify({active,expired,ended}));
        """)
        self.assertTrue(result["active"]["active"])
        self.assertFalse(result["expired"]["active"])
        self.assertEqual(result["expired"]["autonomy"], "A0 · no action")
        self.assertFalse(result["ended"]["active"])
        self.assertEqual(result["ended"]["edena"], "Not evaluated")

    def test_local_roles_and_assignments_remain_drafts(self) -> None:
        result = node_eval("""
          import {createInitialState,addLocalRole,addDashboard,configurationPosture} from './switchboard/switchboard-model.mjs';
          let state=createInitialState('2026-07-17T00:00:00Z');
          let added=addLocalRole(state,{displayName:'Nurse Navigation Steward',kind:'professional-community-role'},'2026-07-17T00:01:00Z','nav'); state=added.state; const roleId=added.roleId;
          added=addLocalRole(state,{displayName:'Coalition Project Lead',kind:'functional-assignment'},'2026-07-17T00:02:00Z','coalition'); state=added.state;
          state=addDashboard(state,{contextKey:'community-a',departmentKey:'community',primaryRoleId:roleId,supportingRoleIds:[],capabilityIds:[],assignmentStatus:'community-assigned-unverified',shiftWindow:'session'},'2026-07-17T00:03:00Z','custom').state;
          console.log(JSON.stringify({localRoles:state.localRoles,card:configurationPosture(state.dashboards[0],state,'2026-07-17T00:04:00Z')}));
        """)
        self.assertEqual(len(result["localRoles"]), 2)
        self.assertTrue(all(item["status"] == "local-draft-not-reviewed" for item in result["localRoles"]))
        self.assertTrue(any("Not NAIO-reviewed" in boundary for boundary in result["card"]["boundaries"]))
        self.assertEqual(result["card"]["autonomy"], "A0 · no action")

    def test_local_extension_removal_blocks_when_in_use(self) -> None:
        result = node_eval("""
          import {createInitialState,addLocalRole,addDashboard,removeLocalExtension} from './switchboard/switchboard-model.mjs';
          let state=createInitialState('2026-07-17T00:00:00Z');
          const added=addLocalRole(state,{displayName:'Nurse Navigation Steward',kind:'professional-community-role'},'2026-07-17T00:00:00Z','nav'); state=added.state;
          const separate=addLocalRole(state,{displayName:'Local Project Lead',kind:'functional-assignment'},'2026-07-17T00:00:00Z','builder'); state=separate.state;
          state=removeLocalExtension(state,separate.roleId,'2026-07-17T00:01:00Z');
          state=addDashboard(state,{contextKey:'personal',departmentKey:'personal-learning',primaryRoleId:added.roleId,supportingRoleIds:[],capabilityIds:[],assignmentStatus:'not-current',shiftWindow:'not-current'},'2026-07-17T00:02:00Z','nav-dash').state;
          let blocked=false;
          try { removeLocalExtension(state,added.roleId,'2026-07-17T00:03:00Z'); } catch { blocked=true; }
          console.log(JSON.stringify({blocked,remaining:state.localRoles.map((item)=>item.id)}));
        """)
        self.assertTrue(result["blocked"])
        self.assertEqual(len(result["remaining"]), 1)

    def test_reload_bound_session_fails_closed_on_reload(self) -> None:
        result = node_eval("""
          import {createInitialState,addDashboard,expireReloadBoundSessions,configurationPosture} from './switchboard/switchboard-model.mjs';
          let state=createInitialState('2026-07-17T00:00:00Z');
          state=addDashboard(state,{contextKey:'personal',departmentKey:'personal-learning',primaryRoleId:'student-learner',supportingRoleIds:[],capabilityIds:['future'],assignmentStatus:'self-declared',shiftWindow:'session'},'2026-07-17T00:00:00Z','session').state;
          state=expireReloadBoundSessions(state,'2026-07-17T00:01:00Z');
          console.log(JSON.stringify({dashboard:state.dashboards[0],card:configurationPosture(state.dashboards[0],state,'2026-07-17T00:01:00Z')}));
        """)
        self.assertEqual(result["dashboard"]["assignmentStatus"], "not-current")
        self.assertEqual(result["dashboard"]["shiftWindow"], "not-current")
        self.assertFalse(result["card"]["active"])

    def test_local_role_rejects_narrative_punctuation_and_unknown_type(self) -> None:
        result = node_eval("""
          import {createInitialState,addLocalRole} from './switchboard/switchboard-model.mjs';
          const state=createInitialState('2026-07-17T00:00:00Z');
          const errors=[];
          for (const input of [{displayName:'Jane Doe MRN 123',kind:'professional-community-role'},{displayName:'Patient Jane Doe',kind:'professional-community-role'},{displayName:'Valid Role',kind:'unknown'},{displayName:'Local Context',kind:'context-adapter'},{displayName:'Local Capability',kind:'capability'}]) {
            try { addLocalRole(state,input,'2026-07-17T00:00:00Z','x'); } catch (error) { errors.push(error.message); }
          }
          console.log(JSON.stringify(errors));
        """)
        self.assertEqual(len(result), 5)

    def test_generated_identifiers_cannot_collide(self) -> None:
        result = node_eval("""
          import {createInitialState,addLocalRole,addDashboard} from './switchboard/switchboard-model.mjs';
          let state=createInitialState('2026-07-17T00:00:00Z');
          state=addLocalRole(state,{displayName:'Local Assignment',kind:'functional-assignment'},'2026-07-17T00:00:00Z','same').state;
          let roleCollision=false;
          try { addLocalRole(state,{displayName:'Local Role',kind:'professional-community-role'},'2026-07-17T00:00:00Z','same'); } catch { roleCollision=true; }
          const input={contextKey:'personal',departmentKey:'personal-learning',primaryRoleId:'student-learner',supportingRoleIds:[],capabilityIds:[],assignmentStatus:'self-declared',shiftWindow:'not-current'};
          state=addDashboard(state,input,'2026-07-17T00:00:00Z','same').state;
          let dashboardCollision=false;
          try { addDashboard(state,input,'2026-07-17T00:00:00Z','same'); } catch { dashboardCollision=true; }
          console.log(JSON.stringify({roleCollision,dashboardCollision}));
        """)
        self.assertTrue(result["roleCollision"])
        self.assertTrue(result["dashboardCollision"])

    def test_local_extension_and_dashboard_limits_are_enforced(self) -> None:
        result = node_eval("""
          import {createInitialState,addLocalRole,addDashboard,normalizeState} from './switchboard/switchboard-model.mjs';
          let roleState=createInitialState('2026-07-17T00:00:00Z');
          for (let i=0;i<24;i++) roleState=addLocalRole(roleState,{displayName:`Local Role ${i}`,kind:'professional-community-role'},'2026-07-17T00:00:00Z',`role-${i}`).state;
          let roleLimit=false;
          try { addLocalRole(roleState,{displayName:'Overflow Role',kind:'professional-community-role'},'2026-07-17T00:00:00Z','overflow'); } catch { roleLimit=true; }
          const roleImportLimit=normalizeState({...roleState,localRoles:[...roleState.localRoles,{...roleState.localRoles[0],id:'local-role-overflow'}]})===null;
          let dashboardState=createInitialState('2026-07-17T00:00:00Z');
          const input={contextKey:'personal',departmentKey:'personal-learning',primaryRoleId:'student-learner',supportingRoleIds:[],capabilityIds:[],assignmentStatus:'not-current',shiftWindow:'not-current'};
          for (let i=0;i<24;i++) dashboardState=addDashboard(dashboardState,input,'2026-07-17T00:00:00Z',`dash-${i}`).state;
          let dashboardLimit=false;
          try { addDashboard(dashboardState,input,'2026-07-17T00:00:00Z','overflow'); } catch { dashboardLimit=true; }
          const dashboardImportLimit=normalizeState({...dashboardState,dashboards:[...dashboardState.dashboards,{...dashboardState.dashboards[0],id:'dashboard-overflow'}]})===null;
          console.log(JSON.stringify({roleLimit,dashboardLimit,roleImportLimit,dashboardImportLimit}));
        """)
        self.assertTrue(result["roleLimit"])
        self.assertTrue(result["dashboardLimit"])
        self.assertTrue(result["roleImportLimit"])
        self.assertTrue(result["dashboardImportLimit"])

    def test_all_six_legacy_lanes_migrate_inactive(self) -> None:
        result = node_eval("""
          import {migrateLegacySetupState} from './switchboard/switchboard-model.mjs';
          const lanes=['student_nurse','staff_nurse','nurse_leader_manager','nurse_educator','nurse_connected_ally','nurse_practitioner_usa'];
          const legacy=(postSetupLane)=>({schemaVersion:1,stage:3,safety:{noPhi:true,noClinical:true,noSecrets:true,guideOnly:true},door:'browser',environment:{device:'mac',ownership:'personal',admin:'yes',browser:'chrome',hermesStatus:'not-installed'},identityRole:'staff',postSetupLane,readiness:{time:false,folder:false,recovery:false,boundaries:false},route:'browser',flowIndex:0,completedFlowIds:[],issueCode:'',updatedAt:'2026-07-17T00:00:00.000Z'});
          const migrated=lanes.map((postSetupLane,index)=>migrateLegacySetupState(legacy(postSetupLane),'2026-07-17T00:00:00Z',`legacy-${index}`));
          console.log(JSON.stringify(migrated.map(state=>({count:state?.dashboards.length,status:state?.dashboards[0].assignmentStatus,shift:state?.dashboards[0].shiftWindow}))));
        """)
        self.assertEqual(len(result), 6)
        self.assertTrue(all(item == {"count": 1, "status": "not-current", "shift": "not-current"} for item in result))

    def test_legacy_migration_preserves_local_drafts_and_rejects_partial_state(self) -> None:
        result = node_eval("""
          import {createInitialState,addLocalRole,migrateLegacySetupState} from './switchboard/switchboard-model.mjs';
          let current=createInitialState('2026-07-17T00:00:00Z');
          current=addLocalRole(current,{displayName:'Local Steward',kind:'professional-community-role'},'2026-07-17T00:00:00Z','steward').state;
          const legacy={schemaVersion:1,stage:3,safety:{noPhi:true,noClinical:true,noSecrets:true,guideOnly:true},door:'browser',environment:{device:'mac',ownership:'personal',admin:'yes',browser:'chrome',hermesStatus:'not-installed'},identityRole:'staff',postSetupLane:'staff_nurse',readiness:{time:false,folder:false,recovery:false,boundaries:false},route:'browser',flowIndex:0,completedFlowIds:[],issueCode:'',updatedAt:'2026-07-17T00:00:00.000Z'};
          const migrated=migrateLegacySetupState(legacy,'2026-07-17T00:01:00Z','legacy',current);
          const partial=migrateLegacySetupState({schemaVersion:1,postSetupLane:'staff_nurse'},'2026-07-17T00:01:00Z','partial',current);
          const malformedTimestamp=migrateLegacySetupState({...legacy,updatedAt:'not-a-date'},'2026-07-17T00:01:00Z','bad-date',current);
          console.log(JSON.stringify({roles:migrated.localRoles.length,dashboards:migrated.dashboards.length,partial,malformedTimestamp}));
        """)
        self.assertEqual(result, {"roles": 1, "dashboards": 1, "partial": None, "malformedTimestamp": None})

    def test_import_rejects_fail_open_windows_and_incompatible_composition(self) -> None:
        result = node_eval("""
          import {createInitialState,addDashboard,normalizeState} from './switchboard/switchboard-model.mjs';
          let state=createInitialState('2026-07-17T00:00:00Z');
          state=addDashboard(state,{contextKey:'facility-a',departmentKey:'critical-care',primaryRoleId:'staff-nurse',supportingRoleIds:[],capabilityIds:['shift'],assignmentStatus:'organization-assigned-unverified',shiftWindow:'8-hours'},'2026-07-17T00:00:00Z','staff').state;
          const base=state.dashboards[0];
          const invalid=[
            {...base,assignmentExpiresAt:null},
            {...base,assignmentExpiresAt:'2026-07-17T07:59:59.999Z'},
            {...base,assignmentStartedAt:null},
            {...base,assignmentStatus:'not-current'},
            {...base,primaryRoleId:'legal-nurse-consultant'},
            {...base,capabilityIds:['orchestrate']},
            {...base,supportingRoleIds:['nurse-informaticist']}
          ].map((dashboard)=>normalizeState({...state,dashboards:[dashboard]})===null);
          console.log(JSON.stringify(invalid));
        """)
        self.assertEqual(result, [True] * 7)

    def test_elapsed_fixed_window_is_marked_not_current(self) -> None:
        result = node_eval("""
          import {createInitialState,addDashboard,expireElapsedAssignments,configurationPosture} from './switchboard/switchboard-model.mjs';
          let state=createInitialState('2026-07-17T00:00:00Z');
          state=addDashboard(state,{contextKey:'facility-a',departmentKey:'critical-care',primaryRoleId:'staff-nurse',supportingRoleIds:[],capabilityIds:['shift'],assignmentStatus:'organization-assigned-unverified',shiftWindow:'8-hours'},'2026-07-17T00:00:00Z','staff').state;
          state=expireElapsedAssignments(state,'2026-07-17T08:00:00Z');
          console.log(JSON.stringify({dashboard:state.dashboards[0],posture:configurationPosture(state.dashboards[0],state,'2026-07-17T08:00:01Z')}));
        """)
        self.assertEqual(result["dashboard"]["assignmentStatus"], "not-current")
        self.assertEqual(result["dashboard"]["shiftWindow"], "not-current")
        self.assertIsNone(result["dashboard"]["assignmentExpiresAt"])
        self.assertFalse(result["posture"]["active"])

    def test_import_is_closed_and_export_round_trips(self) -> None:
        result = node_eval("""
          import {createInitialState,exportState,importState} from './switchboard/switchboard-model.mjs';
          const state=createInitialState('2026-07-17T00:00:00Z');
          const round=importState(exportState(state));
          const bad=[];
          for (const text of [JSON.stringify({...state,secret:'x'}),'{bad json',JSON.stringify({...state,schemaVersion:99}),JSON.stringify({...state,updatedAt:'2026-07-17'}),JSON.stringify({...state,activeDashboardId:'-invalid'})]) {
            try { importState(text); bad.push(false); } catch { bad.push(true); }
          }
          console.log(JSON.stringify({round,bad}));
        """)
        self.assertEqual(result["round"]["schemaVersion"], 2)
        self.assertEqual(result["bad"], [True, True, True, True, True])


class RegistryAndSchemaTests(unittest.TestCase):
    def test_json_documents_parse_and_use_closed_objects(self) -> None:
        self.assertEqual(STATE_SCHEMA["additionalProperties"], False)
        self.assertEqual(STATE_SCHEMA["$defs"]["dashboard"]["additionalProperties"], False)
        self.assertEqual(STATE_SCHEMA["properties"]["dashboards"]["maxItems"], 24)
        self.assertEqual(STATE_SCHEMA["properties"]["localRoles"]["maxItems"], 24)
        self.assertEqual(REGISTRY_SCHEMA["additionalProperties"], False)
        self.assertEqual(REGISTRY["registryStatus"], "documentation-only-draft-preview")

    def test_registry_entries_have_governance_fields_and_start_inactive(self) -> None:
        required = set(REGISTRY_SCHEMA["required"])
        allowed_contexts = set(REGISTRY_SCHEMA["properties"]["contexts"]["items"]["enum"])
        ids = set()
        for entry in REGISTRY["entries"]:
            self.assertTrue(required.issubset(entry), entry["id"])
            self.assertNotIn(entry["id"], ids)
            ids.add(entry["id"])
            self.assertFalse(entry["defaultActive"], entry["id"])
            self.assertEqual(entry["status"], "draft-preview")
            self.assertEqual(entry["edenaStatus"], "not-evaluated")
            self.assertEqual(entry["autonomyCeiling"], "A0")
            self.assertFalse(entry["review"]["edena"])
            self.assertTrue(set(entry["contexts"]).issubset(allowed_contexts), entry["id"])
            self.assertFalse(entry["review"]["independent"])
            self.assertGreaterEqual(len(entry["prohibited"]), 1)
        for identifier in (
            "nurse-informaticist",
            "legal-nurse-consultant",
            "nurse-ai-agent-orchestrator",
            "nurse-community-organizer-developer",
            "discover",
            "future",
            "organize",
            "orchestrate",
        ):
            self.assertIn(identifier, ids)

    def test_model_and_machine_registry_have_same_role_and_capability_ids(self) -> None:
        registry_ids = {entry["id"] for entry in REGISTRY["entries"]}
        model_ids = set(re.findall(r"\{ id: '([^']+)'", MODEL))
        self.assertEqual(registry_ids, model_ids)

    def test_registry_role_contexts_match_model_and_capabilities_are_universal(self) -> None:
        registry_by_id = {entry["id"]: entry for entry in REGISTRY["entries"]}
        role_rows = re.findall(r"\{ id: '([^']+)', displayName: '[^']+', kind: '(?:professional-community-role|functional-assignment)', status: 'draft-preview', contexts: \[([^\]]+)\], capabilities: \[([^\]]*)\]", MODEL)
        self.assertEqual(len(role_rows), 11)
        for role_id, context_source, capability_source in role_rows:
            model_contexts = {value.strip().strip("'") for value in context_source.split(",")}
            model_capabilities = {value.strip().strip("'") for value in capability_source.split(",") if value.strip()}
            self.assertEqual(set(registry_by_id[role_id]["contexts"]), model_contexts, role_id)
            self.assertEqual(set(registry_by_id[role_id]["compatibleCapabilities"]), model_capabilities, role_id)
            self.assertIn("discover", model_capabilities, role_id)
            self.assertIn("future", model_capabilities, role_id)
        for entry in REGISTRY["entries"]:
            if entry["kind"] == "capability":
                self.assertEqual(entry["contexts"], ["all"], entry["id"])


class PublicSurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.parser = Parser()
        cls.parser.feed(HTML)

    def test_accessibility_landmarks_controls_and_motion(self) -> None:
        self.assertIn('class="skip-link" href="#main-content"', HTML)
        self.assertIn('<main id="main-content" tabindex="-1">', HTML)
        self.assertEqual(self.parser.mains, 1)
        self.assertEqual(self.parser.dialogs, 3)
        self.assertEqual(len(self.parser.ids), len(set(self.parser.ids)))
        self.assertEqual(HTML.count('class="dialog-close" type="button"'), 3)
        self.assertIn('id="import-button" class="btn btn-quiet file-button" type="button"', HTML)
        self.assertIn("@media(prefers-reduced-motion:reduce)", CSS)
        for fragment in ('aria-live="polite"', 'aria-labelledby="configuration-posture-title"', 'aria-pressed='):
            self.assertIn(fragment, HTML + APP)
        self.assertIn('id="dashboard-view" class="dashboard-view" tabindex="-1"', HTML)
        self.assertNotIn('id="dashboard-view" class="dashboard-view" aria-live=', HTML)
        self.assertIn('.dashboard-link[aria-pressed="true"]', CSS)
        self.assertIn('flex:0 0 2.75rem', CSS)
        self.assertIn('.legacy-banner[hidden]{display:none}', CSS)
        self.assertIn('dialogInertState', APP)
        self.assertIn('dialogA11yState', APP)
        self.assertIn('dialog[data-fallback="true"][open]{position:fixed', CSS)
        for fragment in ("dialog[data-fallback=", "event.key === 'Escape'", "event.key !== 'Tab'"):
            self.assertIn(fragment, APP)

    def test_no_network_or_analytics_code(self) -> None:
        combined = APP + MODEL
        for forbidden in ("fetch(", "XMLHttpRequest", "WebSocket", "sendBeacon", "gtag(", "mixpanel", "segment.io"):
            self.assertNotIn(forbidden, combined)
        self.assertIn("localStorage", APP)
        self.assertIn("No Hermes mutation", HTML)
        self.assertIn("PHI and records prohibited", HTML)
        external_assets = set(re.findall(r'(?:href|src)="(https://[^"]+)', HTML))
        self.assertTrue(external_assets)
        self.assertTrue(all(url.startswith(("https://fonts.googleapis.com", "https://fonts.gstatic.com", "https://nurse-ai-os.org/")) for url in external_assets))

    def test_only_free_text_input_is_bounded_local_role_title(self) -> None:
        text_inputs = [item for item in self.parser.inputs if item.get("type") == "text"]
        self.assertEqual(len(text_inputs), 1)
        self.assertEqual(text_inputs[0].get("id"), "local-role-name")
        self.assertEqual(text_inputs[0].get("maxlength"), "60")
        self.assertIn("Do not enter names or narratives", HTML)

    def test_key_roles_and_nonclaims_are_visible(self) -> None:
        for phrase in (
            "Nurse Informaticist",
            "Medico-Legal / Legal Nurse Consultant",
            "Nurse AI Agent Orchestrator",
            "Nurse Community Organizer-Developer",
            "No authority by selection",
            "Cross-dashboard transfer is not implemented",
            "not a secure sandbox",
            "No mandate, automatic outreach, fundraising, or political authority",
        ):
            self.assertIn(phrase, HTML)

    def test_internal_links_exist(self) -> None:
        missing = []
        for href in self.parser.hrefs:
            if href.startswith(("http://", "https://", "mailto:", "#")):
                continue
            clean = href.split("#", 1)[0].split("?", 1)[0]
            target = (SWITCHBOARD / clean).resolve()
            if clean.endswith("/"):
                target = target / "index.html"
            if not target.exists():
                missing.append((href, str(target)))
        self.assertEqual(missing, [])

    def test_site_integration_and_privacy_disclosure(self) -> None:
        setup_app = (ROOT / "setup-helper" / "setup-helper.mjs").read_text(encoding="utf-8")
        post_setup = (ROOT / "post-setup" / "index.html").read_text(encoding="utf-8")
        privacy = (ROOT / "privacy.html").read_text(encoding="utf-8")
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn('../switchboard/', setup_app)
        self.assertIn('../switchboard/', post_setup)
        self.assertIn('https://nurse-ai-os.org/switchboard/', sitemap)
        for phrase in ("Switchboard configuration stays on your device", "browser-local storage is not a secure institutional vault", "local draft role title", "cannot reliably detect every name"):
            self.assertIn(phrase, privacy)

    def test_local_runtime_artifacts_are_ignored(self) -> None:
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        for pattern in (".gstack/", "node_modules/", "__pycache__/", "*.pyc"):
            self.assertIn(pattern, ignore)

    def test_role_package_bytes_and_manifest_remain_consistent(self) -> None:
        manifest = json.loads((ROOT / "post-setup" / "downloads" / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["packages"]), 6)
        for package in manifest["packages"]:
            path = ROOT / "post-setup" / package["download"]
            self.assertTrue(path.is_file(), path)
            self.assertEqual(path.stat().st_size, package["bytes"], path.name)
            self.assertEqual(sha256(path), package["sha256"], path.name)
            self.assertFalse(package["install_on_download"])

    def test_public_safety_scan(self) -> None:
        text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in SWITCHBOARD.rglob("*") if path.is_file())
        patterns = {
            "private key": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
            "generic api secret": r"(?i)(?:api[_-]?key|token|password)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}",
            "patient or mrn example": r"(?i)(?:patient|mrn)\s*(?:name|number)?\s*[:=]\s*[A-Z][a-z]+",
        }
        findings = [label for label, pattern in patterns.items() if re.search(pattern, text)]
        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
