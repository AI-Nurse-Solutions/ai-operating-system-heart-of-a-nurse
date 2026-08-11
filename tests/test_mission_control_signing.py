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
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAIO = ROOT / "naio-os"
SIGNER = NAIO / "scripts" / "sign-mission-control.py"
MC = NAIO / "mission-control"

HAVE_OPENSSL = shutil.which("openssl") is not None


def run(cmd: list[str], cwd: Path, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True,
                          timeout=900, env={**os.environ, **(env or {})})


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
        """
        local = run([sys.executable, "tests/self_test.py"], MC)
        expected = next((ln for ln in local.stdout.splitlines() if "passed," in ln), "")
        count = expected.strip().split()[0] if expected else None
        self.assertIsNotNone(count, "could not read the local self-test count")
        self.assertIn(f"self-test: {count} passed", self.result.stdout,
                      f"rehearsal reported a different count than a local run ({count})")

    def test_rehearsal_leaves_the_bundle_verifying(self) -> None:
        verify = run([sys.executable, "scripts/verify-release.py", "--quiet"], NAIO)
        self.assertEqual(verify.returncode, 0,
                         f"the bundle stopped verifying:\n{verify.stdout}{verify.stderr}")

    def test_rehearsal_writes_nothing_into_the_repository(self) -> None:
        dirty = run(["git", "status", "--porcelain", "naio-os"], ROOT).stdout
        self.assertNotIn("manifest.sig", dirty)
        self.assertNotIn("mission-control.zip", dirty)


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
        spec = importlib.util.spec_from_file_location("signer", SIGNER)
        self.signer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.signer)
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
