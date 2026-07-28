import errno
import unittest

import _bootstrap  # noqa: F401

from naio_integrations import locking


class LockContentionClassificationTests(unittest.TestCase):
    """Only genuine lock contention may be retried; permanent OS failures
    (bad descriptor, invalid argument) must propagate immediately instead
    of spinning forever in the Windows retry loop."""

    def test_locking_violation_is_retryable_contention(self):
        self.assertTrue(locking.is_lock_contention(OSError(errno.EACCES, "locked")))

    def test_permanent_failures_are_not_contention(self):
        for code in (errno.EBADF, errno.EINVAL, errno.ENOSPC):
            self.assertFalse(
                locking.is_lock_contention(OSError(code, "permanent")), code
            )

    def test_errno_less_oserror_is_not_contention(self):
        self.assertFalse(locking.is_lock_contention(OSError("no errno")))


class LockRoundTripTests(unittest.TestCase):
    def test_acquire_and_release_round_trip(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "lockfile"
            with path.open("a+", encoding="utf-8") as handle:
                locking.acquire(handle)
                locking.release(handle)


if __name__ == "__main__":
    unittest.main()
