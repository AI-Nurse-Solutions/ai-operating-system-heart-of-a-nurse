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
    """The digest recorded in a signed manifest has to be a function of source."""

    def test_two_builds_of_one_tree_are_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            digests = []
            for n in (1, 2):
                out = Path(tmp) / f"mc-{n}.zip"
                r = run([sys.executable, "tools/release.py", "--skip-tests",
                         "--zip", str(out)], MC, {"SOURCE_DATE_EPOCH": "1785024000"})
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                digests.append(hashlib.sha256(out.read_bytes()).hexdigest())
            self.assertEqual(digests[0], digests[1],
                             "the release archive is not reproducible")

    def test_a_bad_source_date_epoch_is_refused(self) -> None:
        """Silently falling back to the clock would reintroduce the problem."""
        r = run([sys.executable, "tools/release.py", "--skip-tests"], MC,
                {"SOURCE_DATE_EPOCH": "yesterday"})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("SOURCE_DATE_EPOCH", r.stdout + r.stderr)


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
