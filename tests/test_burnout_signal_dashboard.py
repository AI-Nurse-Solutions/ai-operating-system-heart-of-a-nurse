#!/usr/bin/env python3
"""Governance contracts for the Span-of-Control & Burnout Signal Dashboard.

The dashboard is Observe-mode only (retrieve, aggregate, describe), aggregate-only
by design (D1), browser-local, and never recommends an action. These tests pin
those properties so they cannot regress silently.
"""

from __future__ import annotations

import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "burnout-signal-dashboard.html"
LEADER_TEMPLATE = (
    ROOT / "mission-control" / "packets" / "leader" / "templates" / "dashboard-summary.md"
)
DATA_INPUT_IDS = (
    "week-of",
    "staff-count",
    "shifts-worked",
    "late-departures",
    "breaks-missed",
    "staff-no-pto",
)


class FormFieldParser(HTMLParser):
    """Collect form fields, label targets, and external URLs from the page."""

    def __init__(self) -> None:
        super().__init__()
        self.input_types: list[str] = []
        self.input_ids: list[str] = []
        self.textareas = 0
        self.selects = 0
        self.label_targets: list[str] = []
        self.external_hosts: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "input":
            self.input_types.append(attributes.get("type") or "text")
            if attributes.get("id"):
                self.input_ids.append(attributes["id"])
        elif tag == "textarea":
            self.textareas += 1
        elif tag == "select":
            self.selects += 1
        elif tag == "label" and attributes.get("for"):
            self.label_targets.append(attributes["for"])
        for name in ("href", "src"):
            value = attributes.get(name)
            if value and value.startswith(("http://", "https://")):
                self.external_hosts.add(urlsplit(value).hostname or "")


class BurnoutSignalDashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.page = PAGE.read_text(encoding="utf-8")
        cls.template = LEADER_TEMPLATE.read_text(encoding="utf-8")
        cls.parser = FormFieldParser()
        cls.parser.feed(cls.page)

    # ---------- shell and navigation policy ----------

    def test_page_uses_shared_shell_and_policy_compliant_nav(self) -> None:
        self.assertIn('class="site-header"', self.page)
        self.assertIn('<script src="assets/site-shell.js" defer></script>', self.page)
        self.assertIn(
            'href="https://nurse-ai-os.org/burnout-signal-dashboard.html"', self.page
        )
        nav = self.page.split('<div class="nav-links">', 1)[1].split("</div>", 1)[0]
        self.assertEqual(1, nav.count('class="nav-cta"'))
        self.assertIn('class="nav-cta" href="soul-quiz.html"', nav)
        for competing in ("start-here.html", "faq.html", "nurse-station.html", "#founding-year"):
            self.assertNotIn(competing, nav)

    # ---------- aggregate-only by design (D1) ----------

    def test_form_is_aggregate_only_with_no_free_text_fields(self) -> None:
        self.assertEqual(0, self.parser.textareas)
        self.assertEqual(0, self.parser.selects)
        self.assertEqual(
            {"date", "number", "file"},
            set(self.parser.input_types),
            "only date, number, and the JSON import file input may exist — a text "
            "field would let an individual be named",
        )
        self.assertIn("aggregate-only by design", self.page)
        self.assertIn("no free-text fields", self.page)
        self.assertIn("no name, ID, or per-person record can be entered", self.page)
        for input_id in DATA_INPUT_IDS:
            self.assertIn(input_id, self.parser.input_ids)
            self.assertIn(input_id, self.parser.label_targets, f"{input_id} needs a label")

    def test_individual_identifiable_timekeeping_data_is_prohibited_in_copy(self) -> None:
        for phrase in (
            "never a person",
            "Count of shifts, not of people",
            "A count, never a list",
            "never be used to identify or evaluate an individual",
        ):
            self.assertIn(phrase, self.page)

    def test_minimum_aggregation_threshold_is_enforced_and_explained(self) -> None:
        self.assertIn("var MIN_STAFF_FOR_TRENDS = 5;", self.page)
        self.assertIn("staffCount >= MIN_STAFF_FOR_TRENDS", self.page)
        self.assertIn("'withheld'", self.page)
        self.assertIn("excluded from trends", self.page)
        self.assertIn("Minimum aggregation threshold.", self.page)
        self.assertIn('an "aggregate" number can point at a person', self.page)

    def test_entry_validation_blocks_impossible_aggregates(self) -> None:
        self.assertIn("week.lateDepartures > week.shiftsWorked", self.page)
        self.assertIn("week.breaksMissed > week.shiftsWorked", self.page)
        self.assertIn("week.staffNoRecentPto > week.staffCount", self.page)
        self.assertIn("cannot exceed their denominators", self.page)

    # ---------- Observe mode (§20): describe, never recommend ----------

    def test_observe_mode_is_stated_and_no_action_is_recommended(self) -> None:
        for phrase in (
            "Observe mode only.",
            "Directive §20",
            "It does not score, rank, predict, or recommend",
            "the tool never recommends an action",
            "It never recommends an action.",
            "not a workforce-management, performance, or surveillance instrument",
            "EDENA <strong>Green</strong>",
            "no institutional timekeeping connector is part of this build",
        ):
            self.assertIn(phrase, self.page)
        self.assertIn("var CONSECUTIVE_WEEKS_FOR_FLAG = 3;", self.page)
        self.assertIn("A flag is a prompt to look, never a verdict", self.page)

    def test_falling_indicators_carry_the_section_21a_ambiguity_rule(self) -> None:
        self.assertIn("§21A interpretation rules", self.page)
        self.assertGreaterEqual(
            self.page.count("ambiguous signal, not automatically a success"),
            2,
            "the ambiguity rule must appear in the interpretation rules AND in the "
            "generated flag text for falling indicators",
        )
        self.assertGreaterEqual(self.page.count("underreporting"), 3)
        self.assertIn("Patterns, not people.", self.page)
        self.assertIn("Association is not prediction.", self.page)

    # ---------- evidence basis ----------

    def test_indicator_set_cites_laudio_aonl_without_overclaiming(self) -> None:
        self.assertIn("Laudio Insights", self.page)
        self.assertIn("American Organization for Nursing Leadership (AONL)", self.page)
        self.assertIn("association, not a causal or predictive claim", self.page)
        self.assertIn("reviewed quarterly", self.page)
        self.assertIn("not a predictive or diagnostic instrument", self.page)

    # ---------- Mission Control integration ----------

    def test_summary_export_mirrors_leader_packet_template_and_draft_rule(self) -> None:
        template_sections = re.findall(r"^## (.+)$", self.template, re.M)
        self.assertEqual(
            ["Measures included", "What changed", "Limitations", "Suggested attention"],
            template_sections,
            "leader packet template changed — update the dashboard export to match",
        )
        for section in template_sections:
            self.assertIn(f"'## {section}'", self.page)
        self.assertIn(
            "Not final and not approved. A named, accountable human must review, "
            "edit, and approve this content before it is used anywhere. Generation "
            "alone never makes content final.",
            self.page,
        )
        self.assertIn("**Generated from workspace sources:**", self.page)
        self.assertIn("Contains synthetic example data.", self.page)
        self.assertIn("suggestions to look, not conclusions and not recommended actions", self.page)

    # ---------- browser-local workspace ----------

    def test_everything_stays_in_the_browser(self) -> None:
        for forbidden in ("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket(", "EventSource("):
            self.assertNotIn(forbidden, self.page)
        self.assertIn("localStorage", self.page)
        self.assertIn("'naio-burnout-signal-v1'", self.page)
        self.assertLessEqual(
            self.parser.external_hosts,
            {"fonts.googleapis.com", "fonts.gstatic.com", "nurse-ai-os.org"},
            "no external destinations beyond fonts and the canonical URL",
        )
        self.assertIn("Nothing is uploaded", self.page)

    # ---------- accessibility ----------

    def test_accessible_landmarks_summaries_and_chart_alternatives(self) -> None:
        for token in (
            'class="skip-link" href="#main-content"',
            '<main id="main-content" tabindex="-1">',
            '<nav class="nav-bar" aria-label="Primary navigation">',
            "<fieldset>",
            "<legend>",
            'aria-live="polite"',
            'role="status"',
            '<th scope="col">',
            "<noscript>",
        ):
            self.assertIn(token, self.page)
        self.assertIn("svg.setAttribute('role', 'img')", self.page)
        self.assertIn("svg.setAttribute('aria-label'", self.page)
        self.assertIn("head.scope = 'row'", self.page)
        self.assertIn("accessible source of truth", self.page)
        self.assertIn("plain-language reading beside each chart", self.page)

    # ---------- discoverability and harness wiring ----------

    def test_page_is_discoverable_from_sitemap_and_resources(self) -> None:
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        self.assertEqual(
            1, sitemap.count("https://nurse-ai-os.org/burnout-signal-dashboard.html")
        )
        resources = (ROOT / "resources.html").read_text(encoding="utf-8")
        self.assertEqual(1, resources.count('href="burnout-signal-dashboard.html"'))

    def test_browser_test_is_wired_into_the_npm_suite(self) -> None:
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        script = package["scripts"]["test:burnout-signal-browser"]
        self.assertEqual("node tests/test_burnout_signal_dashboard_browser.mjs", script)
        self.assertIn("npm run test:burnout-signal-browser", package["scripts"]["test"])
        self.assertTrue((ROOT / "tests" / "test_burnout_signal_dashboard_browser.mjs").is_file())


if __name__ == "__main__":
    unittest.main()
