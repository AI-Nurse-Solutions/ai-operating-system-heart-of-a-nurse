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
            "student_nurse", "staff_nurse", "nurse_leader_manager", "nurse_educator", "nurse_connected_ally"
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

    def test_all_lane_tasks_are_explicitly_no_phi(self):
        result = node_eval("""
          import {POST_SETUP_LANES,safeTaskForLane} from './setup-helper/setup-helper-model.mjs';
          console.log(JSON.stringify(Object.fromEntries(POST_SETUP_LANES.map(x=>[x.value,safeTaskForLane(x.value).startsWith('No-PHI task:')]))));
        """)
        self.assertEqual(len(result), 5)
        self.assertTrue(all(result.values()))

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
        self.assertIn("<noscript>", self.html)

    def test_honest_time_and_nonclaim_copy(self):
        combined = (self.html + self.model + self.app).lower()
        for phrase in (
            "30–45 minutes", "the wait is worth it", "no phi", "no clinical decisions",
            "does not activate enforcement", "shadow/observe-only", "neither verifies licensure"
        ):
            self.assertIn(phrase, combined)
        self.assertNotIn("2-minute soul", combined)
        self.assertNotIn("fully automated installation", combined)

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
