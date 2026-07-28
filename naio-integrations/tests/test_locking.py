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
    def test_acquire_holds_and_release_actually_unlocks(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "lockfile"
            with path.open("a+", encoding="utf-8") as first, path.open(
                "a+", encoding="utf-8"
            ) as second:
                locking.acquire(first)
                if locking.fcntl is not None:
                    # Non-blocking probe: while the first handle holds the
                    # lock, a second handle must be refused — proving
                    # acquire() is not a no-op.
                    with self.assertRaises(OSError):
                        locking.fcntl.flock(
                            second.fileno(),
                            locking.fcntl.LOCK_EX | locking.fcntl.LOCK_NB,
                        )
                locking.release(first)
                if locking.fcntl is not None:
                    # After release the same non-blocking probe must succeed
                    # immediately — proving release() actually unlocked.
                    locking.fcntl.flock(
                        second.fileno(),
                        locking.fcntl.LOCK_EX | locking.fcntl.LOCK_NB,
                    )
                    locking.fcntl.flock(second.fileno(), locking.fcntl.LOCK_UN)
                else:  # pragma: no cover - Windows path
                    locking.acquire(second)
                    locking.release(second)


if __name__ == "__main__":
    unittest.main()
