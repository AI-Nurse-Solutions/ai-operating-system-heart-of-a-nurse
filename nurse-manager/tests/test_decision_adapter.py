"""A JEV-shaped DecisionAdapter in shadow mode (build step 4.5).

EDENA decides; an adapter only suggests, and in shadow its suggestion is
recorded, scored, and never used. These tests hold that line: the labeled
set cannot drift from policy, no adapter can change a decision, and a
suggester that would be less strict than EDENA is always called out.
"""

import hashlib
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
        report = run_shadow(ReviewAlwaysBaseline())
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
            run_shadow(ReviewAlwaysBaseline(), _write_set(self.tmp.name, cases=data["cases"]))

    def test_only_synthetic_sets_are_used(self):
        for value in (False, None, "yes"):
            with self.subTest(synthetic=value):
                with self.assertRaisesRegex(ShadowError, "synthetic data only"):
                    load_labeled_set(_write_set(self.tmp.name, synthetic=value))

    def test_a_set_that_skips_the_loader_never_reaches_an_adapter(self):
        """Only a set read and checked from a file is used: a hand-built one could
        carry real proposals past the synthetic-only rule."""
        real = load_labeled_set()
        spy = _Fixed("spy", Choice({"allow": 0.0, "require_human": 0.0, "deny": 1.0}))
        handmade = [
            {**real, "synthetic": False},
            {"name": "x", "sha256": "0" * 64, "cases": real["cases"]},
            {"cases": real["cases"]},
            real["cases"],
        ]
        for labeled in handmade:
            with self.subTest(kind=type(labeled).__name__):
                with self.assertRaises((ShadowError, TypeError)):
                    run_shadow(spy, labeled)
        self.assertEqual(spy.seen, [])

    def test_every_field_an_adapter_sees_is_checked(self):
        """The effect, destination, and purpose all reach the adapter's question,
        so each is checked, not only the ones the policy path screens."""
        base = json.loads(default_set_path().read_text(encoding="utf-8"))["cases"][15]
        self.assertEqual(base["reason"], "MGR-EFFECT-UNKNOWN")
        smuggled = {
            "effect as prose": {"effect": "call the family of the patient in room 12"},
            "effect with an identifier": {"effect": "mrn_12345678"},
            "effect as snake-case prose": {"effect": "call_patient_family"},
            "effect with an email": {"effect": "a.person@example.org"},
            "destination with a phone": {"destination": "call 555-867-5309"},
            "purpose with an SSN": {"purpose": "Record 123-45-6789 for payroll"},
        }
        for label, change in smuggled.items():
            with self.subTest(label):
                path = _write_set(self.tmp.name, cases=[{**base, **change}])
                with self.assertRaises(ShadowError):
                    load_labeled_set(path)
                spy = _Fixed("spy", Choice({"allow": 0.0, "require_human": 0.0, "deny": 1.0}))
                with self.assertRaises(ShadowError):
                    run_shadow(spy, path)
                self.assertEqual(spy.seen, [])

    def test_the_digest_is_of_the_bytes_that_were_parsed(self):
        path = _write_set(self.tmp.name)
        parsed = path.read_bytes()
        real_read_text, real_read_bytes = Path.read_text, Path.read_bytes

        def swap_after_first_read(self_path, *args, **kwargs):
            # Another writer replaces the file right after the loader reads it.
            data = real_read_bytes(self_path)
            if self_path == path:
                self_path.write_text(json.dumps({"replaced": True}), encoding="utf-8")
            return data

        from unittest import mock
        with mock.patch.object(Path, "read_bytes", swap_after_first_read), \
                mock.patch.object(Path, "read_text",
                                  lambda p, *a, **k: swap_after_first_read(p).decode("utf-8")):
            loaded = load_labeled_set(path)
        self.assertEqual(loaded["sha256"], hashlib.sha256(parsed).hexdigest())
        del real_read_text

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
                self.assertEqual(self.edena(run_shadow(adapter)), expected)

    def test_a_less_strict_suggester_is_called_out_case_by_case(self):
        report = run_shadow(_Fixed("allow-everything", Choice(
            {"allow": 0.9, "require_human": 0.1, "deny": 0.0}, 0.95)))
        self.assertEqual(report["less_strict"], len(self.cases))
        self.assertEqual(report["less_strict_cases"], [c.id for c in self.cases])
        self.assertEqual(report["agree"], 0)
        text = render_markdown(report)
        self.assertIn(f"**Less strict than EDENA** | **{len(self.cases)}/{len(self.cases)} (100%)**", text)
        self.assertIn("- `send-email-fyi`", text)

    def test_the_baseline_is_the_floor_and_is_not_safe(self):
        report = run_shadow(ReviewAlwaysBaseline())
        denials = sum(1 for c in self.cases if c.label == "deny")
        self.assertEqual((report["agree"], report["less_strict"], report["stricter"]),
                         (len(self.cases) - denials, denials, 0))

    def test_a_perfect_suggester_scores_perfectly(self):
        report = run_shadow(_Oracle(self.cases, confidence=0.8))
        self.assertEqual((report["agree"], report["less_strict"], report["brier"]),
                         (len(self.cases), 0, 0.0))
        self.assertEqual(report["mean_confidence_when_agreeing"], 0.8)
        self.assertIsNone(report["mean_confidence_when_not"])
        self.assertIn("None. It never suggested less than EDENA required.", render_markdown(report))

    def test_a_failing_adapter_is_a_finding_not_a_crash(self):
        report = run_shadow(_Fixed("raises", TimeoutError()))
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
                report = run_shadow(_Fixed(label, answer))
                self.assertEqual((report["invalid_outputs"], report["answered"], report["agree"]),
                                 (len(self.cases), 0, 0))

    def test_a_tie_goes_to_the_stricter_option(self):
        self.assertEqual(Choice({"allow": 0.5, "require_human": 0.0, "deny": 0.5}).suggested, "deny")
        self.assertEqual(Choice({"allow": 0.5, "require_human": 0.5, "deny": 0.0}).suggested,
                         "require_human")

    def test_an_adapter_sees_the_proposal_and_the_options_only(self):
        spy = _Fixed("spy", Choice({"allow": 0.0, "require_human": 0.0, "deny": 1.0}))
        run_shadow(spy)
        self.assertEqual(len(spy.seen), len(self.cases))
        blob = json.dumps([q for q, _ in spy.seen])
        for secret in ("MGR-", "EDENA-", "require_approval", "Sample Manager", tempfile.gettempdir()):
            self.assertNotIn(secret, blob)
        for question, options in spy.seen:
            self.assertIsInstance(question, str)
            self.assertEqual(options, OPTIONS)

    def test_the_throwaway_workspace_is_removed(self):
        before = set(Path(tempfile.gettempdir()).glob("nm-shadow-*"))
        run_shadow(ReviewAlwaysBaseline())
        self.assertEqual(set(Path(tempfile.gettempdir()).glob("nm-shadow-*")), before)

    def test_the_same_inputs_give_the_same_report(self):
        self.assertEqual(run_shadow(ReviewAlwaysBaseline()),
                         run_shadow(ReviewAlwaysBaseline()))


class CommittedReportTests(unittest.TestCase):
    def test_the_committed_shadow_report_is_current(self):
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "shadow_report.py"), "--check"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
