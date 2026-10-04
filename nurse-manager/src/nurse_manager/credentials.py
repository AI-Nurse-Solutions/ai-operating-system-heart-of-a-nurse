"""Where a service key is kept: the operating system's credential store (ADR 0004, ADR 0006).

A key for a cloud service is a secret the manager pastes in once. It is
never written to the workspace database, a backup, an export, an IPC
envelope, an error message, or a log. It goes to the credential store the
operating system already protects:

* **macOS:** the login Keychain, through ``/usr/bin/security``. The key is
  passed on standard input (``security -i``), never on a command line
  another program could read.
* **Windows:** Credential Manager, through ``advapi32`` (``CredWriteW``).
* **Linux:** the Secret Service (GNOME Keyring, KWallet), through
  ``secret-tool``, with the key on standard input.

When none of these is usable, the store says so and refuses to keep the
key. Nothing falls back to a file: a service that needs a key then stays
off, and the manager is told why.
"""

from __future__ import annotations

import ctypes
import os
import re
import subprocess  # noqa: S404 - fixed programs, fixed arguments, key on stdin only
import sys
from typing import Protocol

SERVICE = "Nurse AI OS"
# Accounts are built from workspace ids; secrets are API keys. Both are
# checked against narrow patterns, so neither can carry a quote, a space, or
# a newline into a command the store runs.
ACCOUNT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
SECRET = re.compile(r"^[A-Za-z0-9._~+/=-]{16,512}$")
TIMEOUT_SECONDS = 15


class KeyStoreUnavailable(Exception):
    """This computer has no credential store the app can use. Said to the manager."""


class KeyStore(Protocol):
    """Keeps one secret per account, in a store the operating system protects."""

    name: str  # said to the manager: where the key is kept

    def available(self) -> bool: ...

    def get(self, account: str) -> str | None: ...

    def set(self, account: str, secret: str) -> None: ...

    def delete(self, account: str) -> None: ...


def _check(account: str, secret: str | None = None) -> None:
    if not ACCOUNT.fullmatch(account):
        raise ValueError("invalid credential account")
    if secret is not None and not SECRET.fullmatch(secret):
        raise ValueError("invalid secret")


def _run(argv: list[str], *, stdin: str | None = None) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(  # noqa: S603 - argv is fixed, never shell
            argv, input=stdin, capture_output=True, text=True, timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        # The command line holds no secret; the exception text is still not
        # passed on, so nothing a store prints can reach the manager.
        raise KeyStoreUnavailable("the credential store did not respond") from exc


class MacKeychain:
    """The login Keychain, through ``/usr/bin/security``."""

    name = "the macOS Keychain"
    TOOL = "/usr/bin/security"
    NOT_FOUND = 44  # errSecItemNotFound, as security(1) reports it

    def available(self) -> bool:
        return (sys.platform == "darwin" and os.path.isfile(self.TOOL)
                and os.access(self.TOOL, os.X_OK))

    def get(self, account: str) -> str | None:
        _check(account)
        done = _run([self.TOOL, "find-generic-password", "-s", SERVICE, "-a", account, "-w"])
        if done.returncode == self.NOT_FOUND:
            return None
        if done.returncode != 0:
            raise KeyStoreUnavailable("the Keychain could not be read")
        return done.stdout.strip() or None

    def set(self, account: str, secret: str) -> None:
        _check(account, secret)
        # Interactive mode reads its command from standard input, so the key
        # never appears in a process listing. The patterns above keep the
        # quoted values free of quotes and newlines.
        command = f'add-generic-password -U -s "{SERVICE}" -a "{account}" -w "{secret}"\n'
        done = _run([self.TOOL, "-i"], stdin=command)
        if done.returncode != 0 or self.get(account) != secret:
            raise KeyStoreUnavailable("the Keychain did not keep the key")

    def delete(self, account: str) -> None:
        _check(account)
        done = _run([self.TOOL, "delete-generic-password", "-s", SERVICE, "-a", account])
        if done.returncode not in (0, self.NOT_FOUND):
            raise KeyStoreUnavailable("the Keychain could not remove the key")


class SecretToolStore:
    """The freedesktop Secret Service, through ``secret-tool``."""

    name = "the system keyring"
    # Fixed places only, as for the Keychain's /usr/bin/security: the key is
    # handed to this program, so it is never found through PATH, which a
    # program planted earlier on PATH could answer.
    TOOLS = ("/usr/bin/secret-tool", "/bin/secret-tool")

    def _find(self) -> str | None:
        return next((t for t in self.TOOLS if os.path.isfile(t) and os.access(t, os.X_OK)), None)

    def _tool(self) -> str:
        path = self._find()
        if path is None:
            raise KeyStoreUnavailable("no system keyring is installed (secret-tool)")
        return path

    def available(self) -> bool:
        return sys.platform.startswith("linux") and self._find() is not None

    def get(self, account: str) -> str | None:
        _check(account)
        done = _run([self._tool(), "lookup", "service", SERVICE, "account", account])
        if done.returncode != 0:
            # secret-tool exits 1 both for "not found" and for a locked or
            # missing keyring; either way there is no key to use.
            return None
        return done.stdout.strip() or None

    def set(self, account: str, secret: str) -> None:
        _check(account, secret)
        done = _run([self._tool(), "store", "--label", f"{SERVICE} key ({account})",
                     "service", SERVICE, "account", account], stdin=secret)
        if done.returncode != 0 or self.get(account) != secret:
            raise KeyStoreUnavailable("the system keyring did not keep the key; is it unlocked?")

    def delete(self, account: str) -> None:
        _check(account)
        _run([self._tool(), "clear", "service", SERVICE, "account", account])
        if self.get(account) is not None:
            raise KeyStoreUnavailable("the system keyring could not remove the key")


class WindowsCredentialStore:
    """Windows Credential Manager, through ``advapi32``."""

    name = "Windows Credential Manager"
    CRED_TYPE_GENERIC = 1
    CRED_PERSIST_LOCAL_MACHINE = 2
    ERROR_NOT_FOUND = 1168

    def available(self) -> bool:
        return sys.platform == "win32"

    @staticmethod
    def _api():
        from ctypes import wintypes  # noqa: PLC0415 - Windows only

        class CREDENTIAL(ctypes.Structure):
            _fields_ = [
                ("Flags", wintypes.DWORD), ("Type", wintypes.DWORD),
                ("TargetName", wintypes.LPWSTR), ("Comment", wintypes.LPWSTR),
                ("LastWritten", wintypes.FILETIME), ("CredentialBlobSize", wintypes.DWORD),
                ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)), ("Persist", wintypes.DWORD),
                ("AttributeCount", wintypes.DWORD), ("Attributes", ctypes.c_void_p),
                ("TargetAlias", wintypes.LPWSTR), ("UserName", wintypes.LPWSTR),
            ]

        advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)  # type: ignore[attr-defined]
        return CREDENTIAL, advapi32

    def _target(self, account: str) -> str:
        return f"{SERVICE}/{account}"

    def get(self, account: str) -> str | None:
        _check(account)
        if not self.available():
            raise KeyStoreUnavailable("Windows Credential Manager is not on this computer")
        CREDENTIAL, advapi32 = self._api()
        pointer = ctypes.POINTER(CREDENTIAL)()
        if not advapi32.CredReadW(self._target(account), self.CRED_TYPE_GENERIC, 0,
                                  ctypes.byref(pointer)):
            if ctypes.get_last_error() == self.ERROR_NOT_FOUND:  # type: ignore[attr-defined]
                return None
            raise KeyStoreUnavailable("Windows Credential Manager could not be read")
        try:
            cred = pointer.contents
            blob = ctypes.string_at(cred.CredentialBlob, cred.CredentialBlobSize)
            return blob.decode("utf-8") or None
        finally:
            advapi32.CredFree(pointer)

    def set(self, account: str, secret: str) -> None:
        _check(account, secret)
        if not self.available():
            raise KeyStoreUnavailable("Windows Credential Manager is not on this computer")
        CREDENTIAL, advapi32 = self._api()
        blob = secret.encode("utf-8")
        buffer = (ctypes.c_ubyte * len(blob)).from_buffer_copy(blob)
        cred = CREDENTIAL()
        cred.Type = self.CRED_TYPE_GENERIC
        cred.TargetName = self._target(account)
        cred.CredentialBlobSize = len(blob)
        cred.CredentialBlob = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))
        cred.Persist = self.CRED_PERSIST_LOCAL_MACHINE
        cred.UserName = account
        if not advapi32.CredWriteW(ctypes.byref(cred), 0) or self.get(account) != secret:
            raise KeyStoreUnavailable("Windows Credential Manager did not keep the key")

    def delete(self, account: str) -> None:
        _check(account)
        if not self.available():
            raise KeyStoreUnavailable("Windows Credential Manager is not on this computer")
        _CREDENTIAL, advapi32 = self._api()
        if (not advapi32.CredDeleteW(self._target(account), self.CRED_TYPE_GENERIC, 0)
                and ctypes.get_last_error() != self.ERROR_NOT_FOUND):  # type: ignore[attr-defined]
            raise KeyStoreUnavailable("Windows Credential Manager could not remove the key")


class NoKeyStore:
    """This computer has no store the app can use. Nothing is ever kept."""

    name = "no credential store"

    def available(self) -> bool:
        return False

    def get(self, account: str) -> str | None:
        _check(account)
        return None

    def set(self, account: str, secret: str) -> None:
        raise KeyStoreUnavailable(
            "this computer has no credential store the app can use (Keychain, Credential"
            " Manager, or a system keyring), so the key cannot be kept safely"
        )

    def delete(self, account: str) -> None:
        _check(account)


class MemoryKeyStore:
    """For tests only: keeps keys in memory. Never chosen by ``default_keystore``."""

    name = "test memory"

    def __init__(self) -> None:
        self.keys: dict[str, str] = {}

    def available(self) -> bool:
        return True

    def get(self, account: str) -> str | None:
        _check(account)
        return self.keys.get(account)

    def set(self, account: str, secret: str) -> None:
        _check(account, secret)
        self.keys[account] = secret

    def delete(self, account: str) -> None:
        _check(account)
        self.keys.pop(account, None)


def default_keystore() -> KeyStore:
    """The operating system's own store, or one that refuses to keep anything."""
    for store in (MacKeychain(), WindowsCredentialStore(), SecretToolStore()):
        if store.available():
            return store
    return NoKeyStore()


__all__ = [
    "KeyStore", "KeyStoreUnavailable", "MacKeychain", "MemoryKeyStore", "NoKeyStore",
    "SecretToolStore", "WindowsCredentialStore", "default_keystore",
]
