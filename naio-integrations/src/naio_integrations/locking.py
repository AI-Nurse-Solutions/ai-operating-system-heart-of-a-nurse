"""Cross-platform exclusive file locking, standard library only.

POSIX platforms use ``flock``; Windows uses ``msvcrt`` byte-range
locking. Both serialize cooperating writers that follow the same
lock-file protocol. If no locking mechanism exists on a platform, the
functions raise instead of silently degrading to no mutual exclusion —
a transactional guarantee that can quietly vanish is worse than a loud
failure.
"""

from __future__ import annotations

import errno
import time
from typing import IO

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX platform
    fcntl = None

try:
    import msvcrt
except ImportError:
    msvcrt = None


class LockUnavailableError(RuntimeError):
    pass


def is_lock_contention(exc: OSError) -> bool:
    """Only a locking violation (EACCES) means "held by someone else, retry".

    Permanent failures — bad descriptor, invalid argument — must propagate
    immediately instead of spinning forever.
    """
    return exc.errno == errno.EACCES


def acquire(handle: IO) -> None:
    """Block until an exclusive lock is held on the open file handle."""
    if fcntl is not None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        return
    if msvcrt is not None:  # pragma: no cover - exercised on Windows only
        while True:
            try:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                return
            except OSError as exc:
                if not is_lock_contention(exc):
                    raise
                time.sleep(0.05)
    raise LockUnavailableError(
        "no exclusive file-locking mechanism is available on this platform;"
        " refusing to write shared state without mutual exclusion"
    )


def release(handle: IO) -> None:
    """Release the exclusive lock held on the open file handle."""
    if fcntl is not None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        return
    if msvcrt is not None:  # pragma: no cover - exercised on Windows only
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        return
    raise LockUnavailableError(
        "no exclusive file-locking mechanism is available on this platform"
    )
