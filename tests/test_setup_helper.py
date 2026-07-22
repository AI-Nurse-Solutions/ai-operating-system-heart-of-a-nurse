#!/usr/bin/env python3
"""Regression tests for the deterministic Nurse AI OS Setup Helper Phase 1."""

from __future__ import annotations

import html.parser
import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "setup-helper"
HTML = HELPER / "index.html"
MODEL = HELPER / "setup-helper-model.mjs"
APP = HELPER / "setup-helper.mjs"
CSS = HELPER / "setup-helper.css"
PRIVACY = ROOT / "privacy.html"
ENGLISH_SETUP_PAGES = (
    ROOT / "setup.html",
    ROOT / "start-here.html",
    ROOT / "faq.html",
    ROOT / "cheat-sheet.html",
    ROOT / "hermes-downloads/index.html",
    ROOT / "about.html",
    ROOT / "hermes-masterclass.html",
    HTML,
)


class Parser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.inputs: list[dict[str, str | None]] = []
        self.textareas: list[dict[str, str | None]] = []
        self.hrefs: list[str] = []
        self.scripts: list[dict[str, str | None]] = []
        self.progressbars = 0
        self.dialogs = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        data = dict(attrs)
        element_id = data.get("id")
        if isinstance(element_id, str):
            self.ids.append(element_id)
        if tag == "input":
            self.inputs.append(data)
        if tag == "textarea":
            self.textareas.append(data)
        href = data.get("href")
        if tag == "a" and isinstance(href, str):
            self.hrefs.append(href)
        if tag == "script":
            self.scripts.append(data)
        if data.get("role") == "progressbar":
            self.progressbars += 1
        if tag == "dialog":
            self.dialogs += 1


def node_eval(script: str) -> dict:
    proc = subprocess.run(
        ["node", "--input-type=module"],
        input=script,
        text=True,
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


class SetupHelperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = HTML.read_text(encoding="utf-8")
        cls.model = MODEL.read_text(encoding="utf-8")
        cls.app = APP.read_text(encoding="utf-8")
        cls.css = CSS.read_text(encoding="utf-8")
        cls.parser = Parser()
        cls.parser.feed(cls.html)

    def test_required_artifacts_exist(self):
        for path in (HTML, MODEL, APP, CSS):
            self.assertTrue(path.is_file(), path)
            self.assertGreater(path.stat().st_size, 500, path)

    def test_javascript_syntax(self):
        for path in (MODEL, APP):
            subprocess.run(["node", "--check", str(path)], check=True, capture_output=True, text=True)

    def test_exact_identity_and_lane_contract(self):
        result = node_eval("""
          import {IDENTITY_ROLES,POST_SETUP_LANES} from './setup-helper/setup-helper-model.mjs';
          console.log(JSON.stringify({roles:IDENTITY_ROLES.map(x=>x.value),lanes:POST_SETUP_LANES.map(x=>x.value)}));
        """)
        self.assertEqual(result["roles"], ["student", "staff", "leader", "other"])
        self.assertEqual(result["lanes"], [
            "student_nurse", "staff_nurse", "nurse_leader_manager", "nurse_educator", "nurse_connected_ally",
            "nurse_practitioner_usa"
        ])

    def test_identity_does_not_infer_lane(self):
        result = node_eval("""
          import {createInitialState,validateStage} from './setup-helper/setup-helper-model.mjs';
          const s=createInitialState(); s.identityRole='leader';
          const noLane=validateStage(3,s); s.postSetupLane='nurse_educator';
          const educator=validateStage(3,s); s.postSetupLane='nurse_connected_ally';
          const ally=validateStage(3,s);
          console.log(JSON.stringify({noLane,educator,ally}));
        """)
        self.assertFalse(result["noLane"])
        self.assertTrue(result["educator"])
        self.assertTrue(result["ally"])

    def test_environment_routing_fails_safe(self):
        result = node_eval("""
          import {createInitialState,determineRoute} from './setup-helper/setup-helper-model.mjs';
          function route(device,ownership,admin){const s=createInitialState();s.door='mac';s.environment={device,ownership,admin,browser:'safari',hermesStatus:'not-installed'};return determineRoute(s)}
          console.log(JSON.stringify({personal:route('mac','personal','yes'),authorized:route('mac','authorized','yes'),managed:route('mac','employer','yes'),shared:route('mac','shared','yes'),noAdmin:route('mac','personal','no'),windows:route('windows','personal','yes')}));
        """)
        self.assertEqual(result["personal"], "mac")
        self.assertEqual(result["authorized"], "mac")
        self.assertEqual(result["managed"], "browser")
        self.assertEqual(result["shared"], "browser")
        self.assertEqual(result["noAdmin"], "browser")
        self.assertEqual(result["windows"], "browser")

    def test_corrupt_saved_state_is_rejected_fail_closed(self):
        result = node_eval("""
          import {createInitialState,getFlow,normalizeSavedState} from './setup-helper/setup-helper-model.mjs';
          const valid=createInitialState();valid.updatedAt='2026-07-14T00:00:00Z';
          const partial={schemaVersion:1,safety:null};
          const badStage={...valid,stage:99};
          const badIndex={...valid,stage:5,route:'browser',flowIndex:999};
          const badIds={...valid,route:'browser',completedFlowIds:['mac-install']};
          console.log(JSON.stringify({valid:!!normalizeSavedState(valid),partial:normalizeSavedState(partial),badStage:normalizeSavedState(badStage),badIndex:normalizeSavedState(badIndex),badIds:normalizeSavedState(badIds),browserFlow:getFlow('browser').length}));
        """)
        self.assertTrue(result["valid"])
        for key in ("partial", "badStage", "badIndex", "badIds"):
            self.assertIsNone(result[key])

    def test_safety_and_readiness_are_fail_closed(self):
        result = node_eval("""
          import {createInitialState,validateStage} from './setup-helper/setup-helper-model.mjs';
          const s=createInitialState(); const emptySafety=validateStage(0,s);
          Object.keys(s.safety).forEach(k=>s.safety[k]=true); const fullSafety=validateStage(0,s);
          const emptyReady=validateStage(4,s); Object.keys(s.readiness).forEach(k=>s.readiness[k]=true); const fullReady=validateStage(4,s);
          console.log(JSON.stringify({emptySafety,fullSafety,emptyReady,fullReady}));
        """)
        self.assertEqual(result, {"emptySafety": False, "fullSafety": True, "emptyReady": False, "fullReady": True})

    def test_required_stage_fields_cannot_pass_vacuously(self):
        result = node_eval("""
          import {createInitialState,validateStage} from './setup-helper/setup-helper-model.mjs';
          const s=createInitialState();s.safety={};s.readiness={};
          console.log(JSON.stringify({safety:validateStage(0,s),readiness:validateStage(4,s)}));
        """)
        self.assertEqual(result, {"safety": False, "readiness": False})

    def test_both_flows_are_complete_and_verified(self):
        result = node_eval("""
          import {getFlow} from './setup-helper/setup-helper-model.mjs';
          const out={}; for(const route of ['browser','mac']){const f=getFlow(route);out[route]={count:f.length,unique:new Set(f.map(x=>x.id)).size===f.length,complete:f.every(x=>x.id&&x.title&&x.time&&x.risk&&x.why&&x.actions.length&&x.verify)}}
          console.log(JSON.stringify(out));
        """)
        self.assertGreaterEqual(result["browser"]["count"], 5)
        self.assertGreaterEqual(result["mac"]["count"], 8)
        self.assertTrue(result["browser"]["unique"] and result["browser"]["complete"])
        self.assertTrue(result["mac"]["unique"] and result["mac"]["complete"])

    def test_hermes_status_changes_the_mac_flow(self):
        result = node_eval("""
          import {getFlow} from './setup-helper/setup-helper-model.mjs';
          const describe=(status)=>{const f=getFlow('mac',status);return {ids:f.map(x=>x.id),commands:f.map(x=>x.command||'')}};
          console.log(JSON.stringify({notInstalled:describe('not-installed'),installed:describe('installed'),notSure:describe('not-sure')}));
        """)
        self.assertIn("mac-install", result["notInstalled"]["ids"])
        self.assertNotIn("mac-install", result["installed"]["ids"])
        self.assertIn("mac-doctor", result["installed"]["ids"])
        self.assertNotIn("curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash", result["installed"]["commands"])
        self.assertIn("mac-check-existing", result["notSure"]["ids"])
        self.assertNotIn("mac-install", result["notSure"]["ids"])
        self.assertEqual(result["notSure"]["commands"].count("hermes doctor"), 1)

    def test_all_lane_tasks_are_explicitly_no_phi(self):
        result = node_eval("""
          import {POST_SETUP_LANES,safeTaskForLane} from './setup-helper/setup-helper-model.mjs';
          console.log(JSON.stringify(Object.fromEntries(POST_SETUP_LANES.map(x=>[x.value,safeTaskForLane(x.value).startsWith('No-PHI task:')]))));
        """)
        self.assertEqual(len(result), 6)
        self.assertTrue(all(result.values()))

    def test_student_assistant_build_kit_is_preflight_first(self):
        result = node_eval("""
          import {POST_SETUP_LANES,safeTaskForLane} from './setup-helper/setup-helper-model.mjs';
          const lane=POST_SETUP_LANES.find(x=>x.value==='student_nurse');
          console.log(JSON.stringify({label:lane?.label,task:safeTaskForLane('student_nurse')}));
        """)
        self.assertEqual(result["label"], "Nursing Student, Nursing Assistant, or Bridge")
        task = result["task"]
        self.assertIn("without opening or requiring a package file", task)
        self.assertIn("one-page readiness checklist", task)
        self.assertIn("one synthetic seven-day first-win plan", task)
        self.assertIn("whether my SOUL files and basic Hermes setup are complete", task)
        self.assertIn("At the later post-setup stage", task)
        self.assertIn("give Hermes the complete ZIP", task)
        self.assertIn("manifest, checksums, source provenance", task)
        self.assertIn("Do not install, save, connect, share, transfer school or work context, or activate anything", task)
        self.assertIn("downloading, selecting, opening, or unzipping the ZIP does not install or activate anything", task)
        self.assertIn("one exact Implementation Activation Card with APPROVE, REVISE, and CANCEL", task)
        self.assertIn("136 canonical compatibility checks", task)
        self.assertIn("349 required execution records that all begin Not Run", task)
        self.assertIn("All eighteen optional FUTURE SuperPowers remain Available Inactive", task)
        self.assertIn("all ten suggested agents remain PERM-P0 Disabled", task)
        self.assertIn("Bridge contexts stay separate", task)
        self.assertIn("does not authorize school, clinical-site, employer, community, or organizational deployment", task)

    def test_nurse_practitioner_lane_is_usa_only_and_preflight_first(self):
        result = node_eval("""
          import {POST_SETUP_LANES,safeTaskForLane} from './setup-helper/setup-helper-model.mjs';
          const lane=POST_SETUP_LANES.find(x=>x.value==='nurse_practitioner_usa');
          console.log(JSON.stringify({label:lane?.label,task:safeTaskForLane('nurse_practitioner_usa')}));
        """)
        self.assertEqual(result["label"], "Nurse Practitioner (USA only)")
        self.assertIn("USA-only", result["task"])
        self.assertIn("read-only preflight checklist only", result["task"])
        self.assertIn("Do not install, save, connect, or activate anything", result["task"])

    def test_staff_nurse_quality_contributor_shift_starter_is_self_contained(self):
        result = node_eval("""
          import {POST_SETUP_LANES,safeTaskForLane} from './setup-helper/setup-helper-model.mjs';
          const lane=POST_SETUP_LANES.find(x=>x.value==='staff_nurse');
          console.log(JSON.stringify({label:lane?.label,task:safeTaskForLane('staff_nurse')}));
        """)
        self.assertEqual(result["label"], "Staff Nurse and Quality Contributor")
        task = result["task"]
        for phrase in (
            "without opening or requiring a package file",
            "Direct-Care Staff Nurse",
            "Chartered Staff-Nurse QI Project Lead",
            "one-page no-PHI readiness checklist",
            "one synthetic first-win",
            "SHIFT functional self-install Hermes build kit",
            "downloading, selecting, opening, and unzipping the ZIP do not install or activate anything",
            "complete ZIP",
            "manifest and checksums",
            "read-only preflight",
            "Implementation Activation Card",
            "176 canonical compatibility checks",
            "all initially Not Run",
            "Available Inactive",
            "PERM-P0 Disabled",
            "private build does not authorize institutional quality work",
        ):
            self.assertIn(phrase, task)

    def test_educator_designer_build_kit_starter_is_preflight_first(self):
        result = node_eval("""
          import {POST_SETUP_LANES,safeTaskForLane} from './setup-helper/setup-helper-model.mjs';
          const lane=POST_SETUP_LANES.find(x=>x.value==='nurse_educator');
          console.log(JSON.stringify({label:lane?.label,task:safeTaskForLane('nurse_educator')}));
        """)
        self.assertEqual(result["label"], "Nurse Educator and Instructional Designer")
        task = result["task"]
        for phrase in (
            "without opening or requiring a package file",
            "Nurse Educator, Instructional Designer, or Hybrid / Faculty Developer",
            "one-page no-PHI readiness checklist",
            "one synthetic first-win lesson or learning-design outline",
            "Do not save new memory, connect, share, grade, release, activate, automate, or modify my profile",
            "downloading, selecting, opening, and unzipping do not install anything",
            "TEACH self-install Hermes build kit",
            "complete ZIP",
            "manifest, checksums, authoritative unchanged outer ZIP",
            "read-only preflight",
            "Implementation Activation Card with APPROVE, REVISE, and CANCEL",
            "169 canonical checks and 433 required execution records that begin Not Run",
            "All twenty optional TEACH SuperPowers remain Available Inactive",
            "all ten suggested agents remain PERM-P0 Disabled",
            "private build does not authorize LMS",
        ):
            self.assertIn(phrase, task)

    def test_nurse_leader_build_kit_starter_is_preflight_first(self):
        result = node_eval("""
          import {safeTaskForLane} from './setup-helper/setup-helper-model.mjs';
          console.log(JSON.stringify({task:safeTaskForLane('nurse_leader_manager')}));
        """)
        task = result["task"]
        for phrase in (
            "without opening or requiring a package file",
            "Do not install, save, connect, share, send, schedule, create persistent memory, modify my profile, or activate anything",
            "downloading, selecting, opening, or unzipping the ZIP does not install or activate anything",
            "complete ZIP",
            "manifest, checksums, source provenance",
            "read-only preflight",
            "Implementation Activation Card with APPROVE, REVISE, and CANCEL",
            "113 canonical checks that begin Not Run",
            "No local route is preassigned",
            "Available Inactive",
            "PERM-P0 Disabled",
            "private build does not authorize organizational deployment",
        ):
            self.assertIn(phrase, task)

    def test_no_server_calls_or_analytics(self):
        combined = self.app + self.model
        for forbidden in ("fetch(", "XMLHttpRequest", "WebSocket", "sendBeacon", "gtag(", "mixpanel", "segment.io"):
            self.assertNotIn(forbidden, combined)
        self.assertIn("localStorage", self.app)
        self.assertIn("No free-text conversation is collected", self.html)

    def test_local_storage_is_disclosed_in_privacy_policy(self):
        privacy = PRIVACY.read_text(encoding="utf-8")
        self.assertIn("Setup Helper progress stays on your device", privacy)
        self.assertIn("local storage", privacy.lower())
        self.assertIn("Clear local progress and restart", privacy)
        self.assertIn("not transmitted", privacy)

    def test_no_free_text_intake(self):
        interactive_text_types = {"text", "email", "password", "search", "tel", "url"}
        for item in self.parser.inputs:
            self.assertNotIn((item.get("type") or "text").lower(), interactive_text_types)
        self.assertEqual(len(self.parser.textareas), 1)
        self.assertIn("readonly", self.parser.textareas[0])

    def test_accessibility_structure(self):
        self.assertEqual(len(self.parser.ids), len(set(self.parser.ids)))
        self.assertEqual(self.parser.progressbars, 1)
        self.assertEqual(self.parser.dialogs, 1)
        self.assertIn('aria-live="polite"', self.html)
        self.assertIn('aria-current="page"', self.html)
        self.assertIn('class="skip-link"', self.html)
        self.assertIn("focus-visible", self.css)
        self.assertIn("overflow-x:hidden", self.css)
        self.assertIn("grid-template-columns:repeat(2,minmax(0,1fr))", self.css)
        self.assertIn(".helper-hero-grid>*{min-width:0}", self.css)
        self.assertIn("clip-path:inset(50%)", self.css)
        self.assertIn("<noscript>", self.html)

    def test_ci_hardening_and_full_public_scan_scope(self):
        workflow = (ROOT / ".github/workflows/setup-helper.yml").read_text(encoding="utf-8")
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("scripts/build-lead-nurse-leader-build-kit.py", workflow)
        self.assertIn("scripts/scan-public-healthcare-artifacts.py setup-helper --label SETUP_HELPER", workflow)
        self.assertIn("scripts/scan-public-healthcare-artifacts.py post-setup --label POST_SETUP", workflow)
        for path in (
            "setup.html", "start-here.html", "privacy.html", "faq.html", "cheat-sheet.html",
            "hermes-downloads/index.html", "about.html", "hermes-masterclass.html",
        ):
            self.assertIn(path, workflow)

    def test_honest_time_and_nonclaim_copy(self):
        combined = (self.html + self.model + self.app).lower()
        for phrase in (
            "30–45 minutes", "the wait is worth it", "no phi", "no clinical decisions",
            "does not activate enforcement", "shadow/observe-only", "neither verifies licensure"
        ):
            self.assertIn(phrase, combined)
        self.assertNotIn("2-minute soul", combined)
        self.assertNotIn("fully automated installation", combined)

    def test_public_setup_copy_discloses_provider_boundary_and_no_enforcement(self):
        combined = "\n".join(path.read_text(encoding="utf-8") for path in ENGLISH_SETUP_PAGES).lower()
        for forbidden in (
            "you cannot break anything",
            "not in someone's cloud",
            "every action gets classified before it runs",
            "human authorization mandatory",
            "local-only setup helper",
            "deterministic · local-only",
        ):
            self.assertNotIn(forbidden, combined)
        self.assertIn("configured model provider", combined)
        self.assertIn("does not by itself enforce controls", combined)
        self.assertIn("shadow/observe-only", combined)

    def test_official_hermes_source_and_commands(self):
        self.assertIn("https://hermes-agent.nousresearch.com/install.sh", self.model)
        self.assertIn("https://hermes-agent.nousresearch.com/docs/getting-started/installation", self.model)
        self.assertIn("curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash", self.model)
        self.assertIn("hermes doctor", self.model)
        self.assertIn("hermes desktop", self.model)
        self.assertNotIn("--yolo", self.model + self.app + self.html)

    def test_internal_static_links_exist(self):
        hrefs = set(self.parser.hrefs)
        hrefs.update(re.findall(r"href:\s*'([^']+)'", self.model))
        missing = []
        for href in hrefs:
            if href.startswith(("http://", "https://", "mailto:", "#")):
                continue
            clean = href.split("#", 1)[0].split("?", 1)[0]
            if not clean:
                continue
            path = (HELPER / clean).resolve()
            if clean.endswith("/"):
                path = path / "index.html"
            if not path.exists():
                missing.append((href, str(path)))
        self.assertEqual(missing, [])

    def test_support_summary_is_structured_and_sanitized(self):
        result = node_eval("""
          import {createInitialState,buildSupportSummary} from './setup-helper/setup-helper-model.mjs';
          const s=createInitialState();s.door='mac';s.route='mac';s.environment={device:'mac',ownership:'personal',admin:'yes',browser:'safari',hermesStatus:'not-installed'};s.identityRole='staff';s.postSetupLane='staff_nurse';
          console.log(JSON.stringify({summary:buildSupportSummary(s,'hermes_doctor_failed')}));
        """)
        summary = result["summary"]
        self.assertIn("Issue code: hermes_doctor_failed", summary)
        self.assertIn("No PHI", summary)
        self.assertNotIn("Email:", summary)
        self.assertNotIn("Name:", summary)


if __name__ == "__main__":
    unittest.main(verbosity=2)
