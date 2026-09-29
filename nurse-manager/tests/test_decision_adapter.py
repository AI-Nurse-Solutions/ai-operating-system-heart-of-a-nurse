"""A JEV-shaped DecisionAdapter in shadow mode (build step 4.5).

EDENA decides; an adapter only suggests, and in shadow its suggestion is
recorded, scored, and never used. These tests hold that line: the labeled
set cannot drift from policy, no adapter can change a decision, and a
suggester that would be less strict than EDENA is always called out.
"""

import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import _bootstrap  # noqa: F401

from nurse_manager.decision_adapter import (
    OPTIONS,
    Choice,
    ReviewAlwaysBaseline,
    ShadowError,
    default_set_path,
    load_labeled_set,
    render_markdown,
    run_shadow,
)

ROOT = Path(__file__).resolve().parents[1]
# Every reason the shipped profile gives, and so every path a suggester must learn.
PROFILE_REASONS = {"MGR-EFFECT-BLOCKED", "MGR-EFFECT-UNKNOWN", "MGR-DESTINATION-SCOPE",
                   "MGR-NO-PAYLOAD", "MGR-NOT-ACCEPTED", "MGR-HUMAN-REVIEW"}


class _Fixed:
    """A stand-in adapter that answers the same thing for every case."""

    version = "test"

    def __init__(self, name, answer):
        self.name, self.answer, self.seen = name, answer, []

    def choose(self, question, options):
        self.seen.append((question, options))
        if isinstance(self.answer, BaseException):
            raise self.answer
        return self.answer


class _Oracle:
    """Knows each case's label from its question: what a perfect suggester would say."""

    name, version = "oracle", "test"

    def __init__(self, cases, confidence=0.9):
        self.labels = {c.question(): c.label for c in cases}
        self.confidence = confidence

    def choose(self, question, options):
        label = self.labels[question]
        return Choice({o: 1.0 if o == label else 0.0 for o in options}, self.confidence)


def _write_set(tmp, **changes):
    data = json.loads(default_set_path().read_text(encoding="utf-8"))
    data.update(changes)
    path = Path(tmp) / "set.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


class LabeledSetTests(unittest.TestCase):
    def setUp(self):
        self.labeled = load_labeled_set()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_every_label_is_what_the_policy_decides(self):
        # run_shadow refuses to compare against a set that disagrees with policy.
        report = run_shadow(ReviewAlwaysBaseline(), self.labeled)
        self.assertEqual(report["cases"], len(self.labeled["cases"]))

    def test_the_set_covers_every_reason_and_both_origins(self):
        cases = self.labeled["cases"]
        self.assertEqual({c.reason for c in cases}, PROFILE_REASONS)
        for origin in ("human", "assistant"):
            with self.subTest(origin=origin):
                self.assertEqual({c.label for c in cases if c.origin == origin},
                                 {"require_human", "deny"})

    def test_a_label_that_drifts_from_policy_is_refused(self):
        data = json.loads(default_set_path().read_text(encoding="utf-8"))
        data["cases"][0]["label"] = "allow"
        with self.assertRaisesRegex(ShadowError, "no longer matches the policy for: export-accepted"):
            run_shadow(ReviewAlwaysBaseline(), load_labeled_set(_write_set(self.tmp.name, cases=data["cases"])))

    def test_only_synthetic_sets_are_used(self):
        for value in (False, None, "yes"):
            with self.subTest(synthetic=value):
                with self.assertRaisesRegex(ShadowError, "synthetic data only"):
                    load_labeled_set(_write_set(self.tmp.name, synthetic=value))

    def test_malformed_sets_are_refused(self):
        cases = json.loads(default_set_path().read_text(encoding="utf-8"))["cases"]
        bad = {
            "schema": {"schema": "something-else@1"},
            "options": {"options": ["allow", "deny"]},
            "no cases": {"cases": []},
            "duplicate": {"cases": [cases[0], cases[0]]},
            "unknown label": {"cases": [{**cases[0], "label": "maybe"}]},
            "missing field": {"cases": [{k: v for k, v in cases[0].items() if k != "purpose"}]},
        }
        for label, change in bad.items():
            with self.subTest(label):
                with self.assertRaises(ShadowError):
                    load_labeled_set(_write_set(self.tmp.name, **change))


class ShadowModeTests(unittest.TestCase):
    def setUp(self):
        self.labeled = load_labeled_set()
        self.cases = self.labeled["cases"]

    def edena(self, report):
        return {r["id"]: r["edena"] for r in report["rows"]}

    def test_no_adapter_changes_a_decision(self):
        expected = {c.id: c.label for c in self.cases}
        adapters = [
            _Fixed("allow-everything", Choice({"allow": 1.0, "require_human": 0.0, "deny": 0.0}, 1.0)),
            _Fixed("raises", RuntimeError("the service is down")),
            _Fixed("garbage", "allow"),
            _Oracle(self.cases),
        ]
        for adapter in adapters:
            with self.subTest(adapter=adapter.name):
                self.assertEqual(self.edena(run_shadow(adapter, self.labeled)), expected)

    def test_a_less_strict_suggester_is_called_out_case_by_case(self):
        report = run_shadow(_Fixed("allow-everything", Choice(
            {"allow": 0.9, "require_human": 0.1, "deny": 0.0}, 0.95)), self.labeled)
        self.assertEqual(report["less_strict"], len(self.cases))
        self.assertEqual(report["less_strict_cases"], [c.id for c in self.cases])
        self.assertEqual(report["agree"], 0)
        text = render_markdown(report)
        self.assertIn(f"**Less strict than EDENA** | **{len(self.cases)}/{len(self.cases)} (100%)**", text)
        self.assertIn("- `send-email-fyi`", text)

    def test_the_baseline_is_the_floor_and_is_not_safe(self):
        report = run_shadow(ReviewAlwaysBaseline(), self.labeled)
        denials = sum(1 for c in self.cases if c.label == "deny")
        self.assertEqual((report["agree"], report["less_strict"], report["stricter"]),
                         (len(self.cases) - denials, denials, 0))

    def test_a_perfect_suggester_scores_perfectly(self):
        report = run_shadow(_Oracle(self.cases, confidence=0.8), self.labeled)
        self.assertEqual((report["agree"], report["less_strict"], report["brier"]),
                         (len(self.cases), 0, 0.0))
        self.assertEqual(report["mean_confidence_when_agreeing"], 0.8)
        self.assertIsNone(report["mean_confidence_when_not"])
        self.assertIn("None. It never suggested less than EDENA required.", render_markdown(report))

    def test_a_failing_adapter_is_a_finding_not_a_crash(self):
        report = run_shadow(_Fixed("raises", TimeoutError()), self.labeled)
        self.assertEqual((report["adapter_errors"], report["answered"], report["brier"]),
                         (len(self.cases), 0, None))
        self.assertEqual({r["outcome"] for r in report["rows"]}, {"adapter_error:TimeoutError"})

    def test_answers_outside_the_contract_are_recorded_not_trusted(self):
        bad = {
            "not a choice": {"allow": 1.0},
            "missing option": Choice({"allow": 0.5, "deny": 0.5}),
            "extra option": Choice({"allow": 0.5, "deny": 0.5, "require_human": 0.0, "maybe": 0.0}),
            "does not sum to 1": Choice({"allow": 0.5, "require_human": 0.2, "deny": 0.2}),
            "not a number": Choice({"allow": "1", "require_human": 0, "deny": 0}),
            "boolean": Choice({"allow": True, "require_human": 0, "deny": 0}),
            "negative": Choice({"allow": 1.5, "require_human": -0.5, "deny": 0.0}),
            "nan": Choice({"allow": math.nan, "require_human": 0.5, "deny": 0.5}),
            "confidence too high": Choice({"allow": 0.0, "require_human": 0.0, "deny": 1.0}, 1.5),
            "confidence nan": Choice({"allow": 0.0, "require_human": 0.0, "deny": 1.0}, math.nan),
        }
        for label, answer in bad.items():
            with self.subTest(label):
                report = run_shadow(_Fixed(label, answer), self.labeled)
                self.assertEqual((report["invalid_outputs"], report["answered"], report["agree"]),
                                 (len(self.cases), 0, 0))

    def test_a_tie_goes_to_the_stricter_option(self):
        self.assertEqual(Choice({"allow": 0.5, "require_human": 0.0, "deny": 0.5}).suggested, "deny")
        self.assertEqual(Choice({"allow": 0.5, "require_human": 0.5, "deny": 0.0}).suggested,
                         "require_human")

    def test_an_adapter_sees_the_proposal_and_the_options_only(self):
        spy = _Fixed("spy", Choice({"allow": 0.0, "require_human": 0.0, "deny": 1.0}))
        run_shadow(spy, self.labeled)
        self.assertEqual(len(spy.seen), len(self.cases))
        blob = json.dumps([q for q, _ in spy.seen])
        for secret in ("MGR-", "EDENA-", "require_approval", "Sample Manager", tempfile.gettempdir()):
            self.assertNotIn(secret, blob)
        for question, options in spy.seen:
            self.assertIsInstance(question, str)
            self.assertEqual(options, OPTIONS)

    def test_the_throwaway_workspace_is_removed(self):
        before = set(Path(tempfile.gettempdir()).glob("nm-shadow-*"))
        run_shadow(ReviewAlwaysBaseline(), self.labeled)
        self.assertEqual(set(Path(tempfile.gettempdir()).glob("nm-shadow-*")), before)

    def test_the_same_inputs_give_the_same_report(self):
        self.assertEqual(run_shadow(ReviewAlwaysBaseline(), self.labeled),
                         run_shadow(ReviewAlwaysBaseline(), self.labeled))


class CommittedReportTests(unittest.TestCase):
    def test_the_committed_shadow_report_is_current(self):
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "shadow_report.py"), "--check"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
