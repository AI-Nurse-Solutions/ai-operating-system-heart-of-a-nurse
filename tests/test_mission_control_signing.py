#!/usr/bin/env python3
"""
Contracts for the Mission Control signing chain (naio-os/scripts/sign-mission-control.py).

This suite exists because the procedure it covers is run once per release, by
one person, with a key that is deliberately not in this repository. Everything
about that shape resists testing: it cannot be exercised on the way past, a
mistake is discovered by a fail-closed verifier rather than by a stack trace,
and the cost of getting it wrong is a published release nobody can re-cut.

So the script carries a --rehearse mode that runs the entire procedure against
a throwaway keypair in a scratch copy, and these tests run that rehearsal. A
change that breaks release day fails here instead.

The tests live at the repository level, outside naio-os, on purpose:
naio-os/scripts/self-test.py is checksum-pinned inside the bundle's own signed
manifest, so adding checks to it would invalidate the recorded digest and take
`install.sh --apply` from passing to refusing — the exact failure this work
exists to prevent.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAIO = ROOT / "naio-os"
SIGNER = NAIO / "scripts" / "sign-mission-control.py"
MC = NAIO / "mission-control"

HAVE_OPENSSL = shutil.which("openssl") is not None


def run(cmd: list[str], cwd: Path, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True,
                          timeout=900, env={**os.environ, **(env or {})})


def load_signer():
    spec = importlib.util.spec_from_file_location("signer", SIGNER)
    signer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(signer)
    return signer


# -- reading Mission Control's self-test ------------------------------------

_ANSI = re.compile(r"\x1b\[[0-9;]*m")
_SUMMARY = re.compile(r"(\d+) passed, (\d+) failed")
_SKIPPED = re.compile(r"^\s*–\s+(.*?) — SKIPPED: (.*)$")
# A skip for one of these reasons says how busy the machine was, not what the
# run could see: under load, one run can time out where another does not.
_TIMING = ("timed out", "did not finish inside")


@dataclass
class SelfTestRun:
    passed: int
    failed: int
    skipped: list[tuple[str, str]] = field(default_factory=list)

    @property
    def structural_skips(self) -> set[str]:
        """Checks skipped because something was missing, not because of time."""
        return {name for name, why in self.skipped if not any(t in why for t in _TIMING)}

    def describe(self, label: str) -> str:
        skips = "".join(f"\n      - {name} — {why}" for name, why in self.skipped) or " none"
        return (f"  {label}: {self.passed} passed, {self.failed} failed; skipped:{skips}")


def read_self_test(output: str) -> SelfTestRun | None:
    """The summary and every SKIPPED line of one self_test.py run."""
    text = _ANSI.sub("", output)
    summary = _SUMMARY.findall(text)
    if not summary:
        return None
    passed, failed = map(int, summary[-1])
    skipped = [m.groups() for m in map(_SKIPPED.match, text.splitlines()) if m]
    return SelfTestRun(passed, failed, skipped)


def run_self_test(mc: Path) -> SelfTestRun:
    r = run([sys.executable, "tests/self_test.py"], mc)
    report = read_self_test(r.stdout)
    if report is None:
        raise AssertionError(f"could not read the self-test result in {mc}:\n"
                             f"{r.stdout[-2000:]}{r.stderr[-2000:]}")
    return report


def timing_sensitive_checks(source: str) -> set[str]:
    """Checks self_test.py skips when a subprocess times out, read from its source."""
    return {name for name, why in re.findall(r'skip\(\s*"([^"]+)",\s*"([^"]*)"\s*\)', source)
            if any(t in why for t in _TIMING)}


def full_suite_problems(tree: SelfTestRun, staged: SelfTestRun, rehearsal: tuple[int, int],
                        timing_sensitive: set[str]) -> str:
    """
    Why the rehearsal did not run the full suite, or "" if it did.

    `tree` is a run in the working tree; `staged` a run in a copy staged by
    the signer's own stage(), the copy the rehearsal ran in; `rehearsal` the
    (passed, failed) the rehearsal printed. Only a timing skip may differ.
    """
    problems = []
    for label, failed in (("the tree's run", tree.failed), ("the staged run", staged.failed),
                          ("the rehearsal", rehearsal[1])):
        if failed:
            problems.append(f"{label} reported {failed} failed")
    lost = staged.structural_skips - tree.structural_skips
    if lost:
        problems.append("the staged copy skipped checks the tree runs, so something the"
                        " self-test needs was not staged: " + ", ".join(sorted(lost)))
    # A timing-sensitive check the tree passed may be skipped in another run.
    may_time_out = len(timing_sensitive - {name for name, _ in tree.skipped})
    for label, passed in (("the staged run", staged.passed), ("the rehearsal", rehearsal[0])):
        if passed < tree.passed - may_time_out:
            problems.append(f"{label} passed {passed} checks, the tree {tree.passed}; only"
                            f" {may_time_out} can be lost to a timeout")
    if not problems:
        return ""
    return "\n".join(["the rehearsal did not run the full Mission Control suite:",
                      *(f"  * {p}" for p in problems),
                      tree.describe("tree"), staged.describe("staged copy"),
                      f"  rehearsal: {rehearsal[0]} passed, {rehearsal[1]} failed (the signer"
                      " prints no skip names; the staged copy above is what it ran in)"])


class SigningRehearsalTests(unittest.TestCase):
    """The procedure works, and rehearsing it changes nothing."""

    @classmethod
    def setUpClass(cls) -> None:
        if not HAVE_OPENSSL:
            raise unittest.SkipTest("openssl not available")
        cls.result = run([sys.executable, str(SIGNER), "--rehearse"], NAIO)

    def test_rehearsal_completes_the_whole_chain(self) -> None:
        self.assertEqual(self.result.returncode, 0,
                         f"rehearsal failed:\n{self.result.stdout}{self.result.stderr}")
        self.assertIn("REHEARSAL PASSED", self.result.stdout)

    def test_rehearsal_covers_both_halves_of_the_chain(self) -> None:
        """
        The nested manifest makes the checksums signed; the archive makes them
        fetched. Shipping only the first is the half-measure ARCHITECTURE.md §11
        warns about — a downloader gets an authenticated list of files and none
        of the files on it — so the rehearsal has to prove both went in.
        """
        self.assertIn("nested manifest", self.result.stdout)
        self.assertIn("archive", self.result.stdout)
        self.assertIn("mission-control.zip", self.result.stdout)

    def test_rehearsal_runs_the_full_mission_control_suite(self) -> None:
        """
        Guards a bug this suite was written after hitting: the scratch copy
        originally held naio-os alone, so Mission Control's self-test could not
        see its sibling directories, SKIPPED the checks that need them, and
        release.py stamped that smaller number into manifest.json and README.md
        as the release's test count. A release should not quietly report fewer
        tests than the tree actually passes.

        The count is compared as what it measures, not as a string: a check
        self_test.py skips because a subprocess timed out under runner load is
        machine speed, not a missing directory, so one timing skip may differ
        between runs. A structural skip may not, and neither may a failure.
        The rehearsal prints only its totals, so what it could see is checked
        by running the self-test in a copy staged by the signer's own stage().
        """
        m = re.search(r"self-test: (\d+) passed, (\d+) failed", self.result.stdout)
        self.assertIsNotNone(m, f"the rehearsal printed no self-test count:\n{self.result.stdout}")
        tree = run_self_test(MC)
        with tempfile.TemporaryDirectory(prefix="naio-stage-") as tmp:
            staged = run_self_test(load_signer().stage(Path(tmp)) / "mission-control")
        sensitive = timing_sensitive_checks((MC / "tests" / "self_test.py").read_text("utf-8"))
        problems = full_suite_problems(tree, staged, (int(m[1]), int(m[2])), sensitive)
        self.assertEqual(problems, "", problems)

    def test_rehearsal_leaves_the_bundle_verifying(self) -> None:
        verify = run([sys.executable, "scripts/verify-release.py", "--quiet"], NAIO)
        self.assertEqual(verify.returncode, 0,
                         f"the bundle stopped verifying:\n{verify.stdout}{verify.stderr}")

    def test_rehearsal_writes_nothing_into_the_repository(self) -> None:
        dirty = run(["git", "status", "--porcelain", "naio-os"], ROOT).stdout
        self.assertNotIn("manifest.sig", dirty)
        self.assertNotIn("mission-control.zip", dirty)


class FullSuiteComparisonTests(unittest.TestCase):
    """
    The full-suite guard tells a missing directory from a slow machine.

    It was a string match on the first number of the summary, which failed
    whenever one run's node probe timed out under load (124 against 123) and
    said nothing about which check was missing.
    """

    SENSITIVE = {"the committed v2 fixture still matches what soul-quiz emits",
                 "every quiz role maps to a preset"}
    FULL = SelfTestRun(124, 0)

    def test_a_timeout_in_one_run_is_not_a_smaller_suite(self) -> None:
        slow = SelfTestRun(122, 0, [
            ("the committed v2 fixture still matches what soul-quiz emits",
             "the node probe did not finish inside 60s"),
            ("every quiz role maps to a preset", "the node probe timed out")])
        self.assertEqual(full_suite_problems(self.FULL, self.FULL, (123, 0), self.SENSITIVE), "")
        self.assertEqual(full_suite_problems(self.FULL, slow, (122, 0), self.SENSITIVE), "")
        self.assertEqual(full_suite_problems(slow, self.FULL, (124, 0), self.SENSITIVE), "")

    def test_a_missing_sibling_fails_and_names_the_check(self) -> None:
        missing = SelfTestRun(123, 0, [
            ("the committed v2 fixture still matches what soul-quiz emits",
             "soul-quiz not present — running outside the site repo")])
        problems = full_suite_problems(self.FULL, missing, (123, 0), self.SENSITIVE)
        self.assertIn("something the self-test needs was not staged", problems)
        self.assertIn("soul-quiz not present", problems)

    def test_more_lost_than_a_timeout_explains_fails(self) -> None:
        problems = full_suite_problems(self.FULL, self.FULL, (120, 0), self.SENSITIVE)
        self.assertIn("the rehearsal passed 120 checks, the tree 124", problems)

    def test_a_failure_in_any_run_fails(self) -> None:
        for runs in ((SelfTestRun(123, 1), self.FULL, (124, 0)),
                     (self.FULL, SelfTestRun(123, 1), (124, 0)),
                     (self.FULL, self.FULL, (123, 1))):
            with self.subTest(runs=runs):
                self.assertIn("1 failed", full_suite_problems(*runs, self.SENSITIVE))

    def test_the_timing_sensitive_checks_are_read_from_the_suite(self) -> None:
        source = (MC / "tests" / "self_test.py").read_text(encoding="utf-8")
        self.assertEqual(timing_sensitive_checks(source), self.SENSITIVE)

    def test_a_copy_staged_without_its_siblings_is_caught(self) -> None:
        """The bug itself, for real: a staged copy that cannot see soul-quiz or
        the Starter Kit runs a smaller suite, and the guard says which checks."""
        with tempfile.TemporaryDirectory(prefix="naio-stage-") as tmp:
            staged = load_signer().stage(Path(tmp))
            for sibling in Path(tmp).iterdir():
                if sibling.is_symlink():
                    sibling.unlink()
            alone = run_self_test(staged / "mission-control")
        tree = run_self_test(MC)
        sensitive = timing_sensitive_checks((MC / "tests" / "self_test.py").read_text("utf-8"))
        problems = full_suite_problems(tree, alone, (alone.passed, 0), sensitive)
        self.assertIn("something the self-test needs was not staged", problems)
        self.assertIn("configure --kit accepts the published Starter Kit", problems)


class ReproducibleArchiveTests(unittest.TestCase):
    """
    The digest recorded in a signed manifest has to be a function of source.

    Every build here runs in a COPY of Mission Control, never in the checkout.
    `release.py` rewrites manifest.json on each run and deletes a manifest.sig
    it did not just produce, so pointing these at the working tree would make
    running the test suite quietly overwrite release provenance — and after a
    real signing, destroy the signature. That is not hypothetical: the first
    version of this file did exactly that, and committed a manifest.json
    claiming `0 passed` with a test's pinned build time.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.mc = Path(self._tmp.name) / "mission-control"
        shutil.copytree(MC, self.mc, symlinks=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc",
                                                      "mission_control.db", "backups"))
        self.addCleanup(self._tmp.cleanup)

    def test_two_builds_of_one_tree_are_byte_identical(self) -> None:
        digests = []
        for n in (1, 2):
            out = self.mc.parent / f"mc-{n}.zip"
            r = run([sys.executable, "tools/release.py", "--skip-tests",
                     "--zip", str(out)], self.mc, {"SOURCE_DATE_EPOCH": "1785024000"})
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            digests.append(hashlib.sha256(out.read_bytes()).hexdigest())
        self.assertEqual(digests[0], digests[1],
                         "the release archive is not reproducible")

    def test_a_bad_source_date_epoch_is_refused(self) -> None:
        """Silently falling back to the clock would reintroduce the problem."""
        r = run([sys.executable, "tools/release.py", "--skip-tests"], self.mc,
                {"SOURCE_DATE_EPOCH": "yesterday"})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("SOURCE_DATE_EPOCH", r.stdout + r.stderr)


class CommittedProvenanceTests(unittest.TestCase):
    """
    What the packaged manifest claims about itself has to be true.

    `naio-mc verify` prints `self_test` as "the self-test at build time", so a
    manifest built with --skip-tests states, in a shipped artifact, that the
    suite passed nothing. This test exists because that is what got committed:
    a test suite building in the working tree left `0 passed` and a pinned
    epoch behind, and nothing downstream would have called it a lie.
    """

    def setUp(self) -> None:
        self.manifest = json.loads((MC / "manifest.json").read_text(encoding="utf-8"))

    def test_the_manifest_records_a_real_suite_result(self) -> None:
        result = self.manifest.get("self_test", {})
        self.assertEqual(result.get("failed"), 0, "packaged with a failing suite")
        self.assertGreater(result.get("passed", 0), 0,
                           "manifest.json claims the suite passed nothing — it was "
                           "built with --skip-tests and must be rebuilt")

    def test_the_manifest_agrees_with_the_documented_count(self) -> None:
        """README and the manifest are two copies of one number; they drift."""
        readme = (MC / "README.md").read_text(encoding="utf-8")
        passed = self.manifest["self_test"]["passed"]
        self.assertIn(f"{passed} checks", readme,
                      f"README does not mention the manifest's {passed} checks")


class PublicationRollbackTests(unittest.TestCase):
    """
    The write step is all-or-nothing, and that is checked rather than claimed.

    Staging already makes the computation transactional. The eight copies that
    follow were not: a failure partway through left a new manifest.yaml beside
    the nested artifacts it no longer described — a tree verifying as neither
    release, with no key on hand to re-cut it.
    """

    def setUp(self) -> None:
        self.signer = load_signer()
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

        # A destination tree where every output already exists with known
        # content, and a staged tree that would replace all of them.
        self.dest, self.staged = self.tmp / "dest", self.tmp / "staged"
        for rel in self.signer.OUTPUTS:
            for root, body in ((self.dest, "before"), (self.staged, "after")):
                p = root / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(body, encoding="utf-8")

    def _block_one_output(self, index: int) -> str:
        """
        Make one output impossible to write, the way a broken tree would.

        Its parent directory becomes a file, so the mkdir before the copy
        raises. Blocking it by making the *destination* a directory does not
        work — copy2 would cheerfully write the file inside it — which is
        exactly the kind of thing that makes an untested rollback worthless.
        """
        rel = self.signer.OUTPUTS[index]
        parent = (self.dest / rel).parent
        self.assertNotEqual(parent, self.dest, "pick an output inside a subdirectory")
        shutil.rmtree(parent)
        parent.write_text("this is a file where a directory must be", encoding="utf-8")
        return rel

    def test_a_failure_partway_through_restores_every_earlier_copy(self) -> None:
        blocked = self._block_one_output(4)
        earlier = self.signer.OUTPUTS[:4]

        with self.assertRaises(OSError):
            self.signer.publish(self.staged, self.dest, self.tmp / "rollback")

        for rel in earlier:
            self.assertEqual((self.dest / rel).read_text(encoding="utf-8"), "before",
                             f"{rel} was left holding a release that failed to publish "
                             f"at {blocked}")

    def test_a_file_that_did_not_exist_before_is_removed_on_failure(self) -> None:
        """Restoring means gone, not empty, for anything the run created."""
        fresh = self.signer.OUTPUTS[0]
        (self.dest / fresh).unlink()
        self._block_one_output(4)

        with self.assertRaises(OSError):
            self.signer.publish(self.staged, self.dest, self.tmp / "rollback")

        self.assertFalse((self.dest / fresh).exists(),
                         f"{fresh} was created by a run that failed")

    def test_a_clean_run_writes_every_artifact(self) -> None:
        written = self.signer.publish(self.staged, self.dest, self.tmp / "rollback")
        self.assertEqual(len(written), len(self.signer.OUTPUTS))
        for rel in self.signer.OUTPUTS:
            self.assertEqual((self.dest / rel).read_text(encoding="utf-8"), "after")


class RefusalTests(unittest.TestCase):
    """Fail-closed, and loudly."""

    def test_a_missing_key_is_refused_before_anything_is_touched(self) -> None:
        r = run([sys.executable, str(SIGNER), "--key", "/nonexistent/key.pem"], NAIO)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no signing key", r.stdout + r.stderr)

    def test_a_mode_must_be_chosen(self) -> None:
        """--key and --rehearse are exclusive, and one is required: a signing
        tool that does something plausible when invoked bare is a hazard."""
        r = run([sys.executable, str(SIGNER)], NAIO)
        self.assertNotEqual(r.returncode, 0)
        both = run([sys.executable, str(SIGNER), "--rehearse",
                    "--key", "/nonexistent/key.pem"], NAIO)
        self.assertNotEqual(both.returncode, 0)


if __name__ == "__main__":
    unittest.main()
