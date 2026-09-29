"""The update feed: signed, advisory, and never automatic (build step 6.2).

A release is announced in a small JSON feed with a detached signature. This
module decides whether a feed can be believed and what it offers. It never
downloads or installs anything, and it only goes to the network when the
manager asks it to check:

* **Signed.** The feed's exact bytes must carry an RSA-SHA256 (PKCS #1 v1.5)
  signature from a key pinned in ``config/update-feed.json``, the scheme the
  NAIO OS release chain already uses (``openssl dgst -sha256 -sign``). It is
  verified here with the standard library alone, so the check works on a
  laptop with no OpenSSL. Until the steward pins a key and a feed address,
  every check answers "not configured" and trusts nothing.
* **Never backwards.** Each feed carries a sequence number and an expiry
  date. An older sequence (a replayed feed), a different feed under a
  sequence already seen, or an expired feed is refused, so an old signed
  feed cannot be used to hold a manager on a release with known problems.
  A release older than the running one is never offered.
* **Advisory.** A check reports what is available and its download's
  sha256; ``verify_download`` checks a file the manager fetched against
  that signed digest. Installing stays a person's decision.

Updating a workspace's records is the store's side (``Store._migrate``): a
backup before any migration, and forward repair when one fails.
"""

from __future__ import annotations

import base64
import contextlib
import hashlib
import hmac
import json
import re
import sqlite3
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any, Iterator

from . import __version__, resources
from .services import ManagerError

FEED_SCHEMA = "nurse-manager-update-feed@1"
CONFIG_SCHEMA = "nurse-manager-update-config@1"
MAX_FEED_BYTES = 256 * 1024
MAX_SIGNATURE_BYTES = 4096
MIN_KEY_BITS = 2048
FETCH_TIMEOUT_SECONDS = 15
STATE_LOCK_TIMEOUT_SECONDS = 10
_VERSION = re.compile(r"(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_PLATFORM = re.compile(r"[a-z0-9][a-z0-9-]{1,31}")
# DigestInfo for SHA-256 (RFC 8017 §9.2, note 1).
_SHA256_DIGEST_INFO = bytes.fromhex("3031300d060960864801650304020105000420")
_RSA_OID = bytes.fromhex("2a864886f70d010101")
# Recorded in place of a digest when two feeds claim one sequence: matches no feed.
_CONTRADICTED = "contradicted"


class UpdateError(ManagerError):
    """A feed, key, or download that cannot be trusted."""


# -- RSA-SHA256 verification (standard library only) -------------------------

def _der(data: bytes, pos: int, tag: int) -> tuple[bytes, int]:
    """Read one DER element with ``tag`` at ``pos``; return (content, next pos)."""
    if pos + 2 > len(data) or data[pos] != tag:
        raise UpdateError("not a valid public key")
    length, pos = data[pos + 1], pos + 2
    if length & 0x80:
        count = length & 0x7F
        if count == 0 or count > 4 or pos + count > len(data):
            raise UpdateError("not a valid public key")
        length = int.from_bytes(data[pos:pos + count], "big")
        pos += count
    if pos + length > len(data):
        raise UpdateError("not a valid public key")
    return data[pos:pos + length], pos + length


def _der_int(data: bytes, pos: int) -> tuple[int, int]:
    raw, pos = _der(data, pos, 0x02)
    if not raw or raw[0] & 0x80:
        raise UpdateError("not a valid public key")
    return int.from_bytes(raw, "big"), pos


def load_public_key(pem: str) -> tuple[int, int, str]:
    """An RSA SubjectPublicKeyInfo PEM -> (n, e, key id). The key id is the
    sha256 of the key's DER, so a configured id is checked against the key."""
    lines = [line.strip() for line in pem.strip().splitlines()]
    if not lines or lines[0] != "-----BEGIN PUBLIC KEY-----" or lines[-1] != "-----END PUBLIC KEY-----":
        raise UpdateError("a trusted key must be a PEM public key")
    try:
        der = base64.b64decode("".join(lines[1:-1]), validate=True)
    except ValueError as exc:
        raise UpdateError("not a valid public key") from exc
    spki, end = _der(der, 0, 0x30)
    if end != len(der):
        raise UpdateError("not a valid public key")
    algorithm, pos = _der(spki, 0, 0x30)
    oid, _ = _der(algorithm, 0, 0x06)
    if oid != _RSA_OID:
        raise UpdateError("a trusted key must be an RSA key")
    bits, pos = _der(spki, pos, 0x03)
    if pos != len(spki) or not bits or bits[0] != 0:
        raise UpdateError("not a valid public key")
    rsa, rsa_end = _der(bits, 1, 0x30)
    if rsa_end != len(bits):
        raise UpdateError("not a valid public key")
    n, pos = _der_int(rsa, 0)
    e, pos = _der_int(rsa, pos)
    if pos != len(rsa):
        raise UpdateError("not a valid public key")
    if n.bit_length() < MIN_KEY_BITS:
        raise UpdateError(f"a trusted key must be at least {MIN_KEY_BITS} bits")
    if e < 3 or e % 2 == 0:
        raise UpdateError("not a valid public key")
    return n, e, hashlib.sha256(der).hexdigest()


def verify_signature(n: int, e: int, message: bytes, signature: bytes) -> bool:
    """RSASSA-PKCS1-v1_5 with SHA-256 (RFC 8017 §8.2.2): the expected encoding
    is built and compared whole, never parsed out of the signature."""
    k = (n.bit_length() + 7) // 8
    if len(signature) != k:
        return False
    s = int.from_bytes(signature, "big")
    if s >= n:
        return False
    t = _SHA256_DIGEST_INFO + hashlib.sha256(message).digest()
    expected = b"\x00\x01" + b"\xff" * (k - len(t) - 3) + b"\x00" + t
    return hmac.compare_digest(pow(s, e, n).to_bytes(k, "big"), expected)


# -- configuration and state ---------------------------------------------------

def config_path() -> Path:
    return resources.manager_root() / "config" / "update-feed.json"


def state_path() -> Path:
    return resources.user_data_dir() / "update-state.sqlite"


def load_config(path: Path | None = None) -> dict[str, Any]:
    data = json.loads(Path(path or config_path()).read_text(encoding="utf-8"))
    if data.get("schema") != CONFIG_SCHEMA:
        raise UpdateError(f"the update settings are not {CONFIG_SCHEMA}")
    keys = []
    for entry in data.get("trusted_keys") or []:
        n, e, key_id = load_public_key(entry.get("pem", ""))
        if entry.get("key_id") != key_id:
            raise UpdateError("a trusted key's id does not match the key; check the settings")
        keys.append((key_id, n, e))
    url = data.get("feed_url")
    if url is not None and not (isinstance(url, str) and url.startswith("https://")):
        raise UpdateError("the feed address must be https")
    return {"channel": data.get("channel") or "", "feed_url": url, "keys": keys}


@contextlib.contextmanager
def _seen_feeds(path: Path) -> Iterator[sqlite3.Connection]:
    """The record of feeds already seen, held under a write lock for the whole
    compare-and-record, so two checks at once cannot roll it back."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        conn = sqlite3.connect(str(path), timeout=STATE_LOCK_TIMEOUT_SECONDS, isolation_level=None)
    except sqlite3.Error as exc:
        raise UpdateError("the record of feeds already seen cannot be opened") from exc
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("CREATE TABLE IF NOT EXISTS feeds_seen (channel TEXT PRIMARY KEY,"
                     " sequence INTEGER NOT NULL, feed_sha256 TEXT NOT NULL)")
        try:
            yield conn
        except BaseException:
            if conn.in_transaction:  # SQLite may already have rolled back by itself
                conn.execute("ROLLBACK")
            raise
        try:
            conn.execute("COMMIT")
        except BaseException:
            if conn.in_transaction:  # a COMMIT held off by a reader keeps its lock
                conn.execute("ROLLBACK")
            raise
    except sqlite3.OperationalError as exc:
        if getattr(exc, "sqlite_errorname", "").startswith(("SQLITE_BUSY", "SQLITE_LOCKED")):
            raise UpdateError("another update check is running; try again in a moment") from exc
        raise UpdateError("the record of feeds already seen is unreadable; nothing is trusted"
                          " until it is repaired or removed by hand") from exc
    except sqlite3.DatabaseError as exc:
        raise UpdateError("the record of feeds already seen is unreadable; nothing is trusted"
                          " until it is repaired or removed by hand") from exc
    finally:
        conn.close()


# -- the feed ------------------------------------------------------------------

def _version(value: Any) -> tuple[int, int, int]:
    match = _VERSION.fullmatch(value) if isinstance(value, str) else None
    if not match:
        raise UpdateError("the feed names a version that is not like 1.2.3")
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def _date(value: Any, what: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise UpdateError(f"the feed's {what} is not a date") from exc


def _parse_feed(feed: dict[str, Any], channel: str) -> dict[str, Any]:
    if not isinstance(feed, dict) or feed.get("schema") != FEED_SCHEMA:
        raise UpdateError(f"not a {FEED_SCHEMA} feed")
    if feed.get("channel") != channel:
        raise UpdateError(f"the feed is for another channel ({feed.get('channel')!r})")
    sequence = feed.get("sequence")
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 1:
        raise UpdateError("the feed's sequence is not a positive whole number")
    issued, expires = _date(feed.get("issued"), "issue date"), _date(feed.get("expires"), "expiry date")
    if expires <= issued:
        raise UpdateError("the feed expires before it was issued")
    releases = []
    for item in feed.get("releases") or []:
        if not isinstance(item, dict):
            raise UpdateError("a release entry is not an object")
        version = _version(item.get("version"))
        artifacts = item.get("artifacts") or []
        if not artifacts:
            raise UpdateError(f"release {item.get('version')} lists no downloads")
        for art in artifacts:
            fields = [art.get(k) for k in ("platform", "sha256", "url")] \
                if isinstance(art, dict) else [None]
            if not all(isinstance(f, str) for f in fields) \
                    or not _PLATFORM.fullmatch(art["platform"]) \
                    or not _SHA256.fullmatch(art["sha256"]) \
                    or not art["url"].startswith("https://"):
                raise UpdateError(f"release {item.get('version')} has a download without a"
                                  " platform, an https address, and a sha256")
        releases.append({"version": item["version"], "rank": version,
                         "schema": str(item.get("schema") or ""),
                         "notes": str(item.get("notes") or ""),
                         "artifacts": [{"platform": a["platform"], "url": a["url"],
                                        "sha256": a["sha256"]} for a in artifacts]})
    return {"sequence": sequence, "issued": issued, "expires": expires, "releases": releases}


def check_feed(feed_bytes: bytes, signature: bytes, *, config: dict[str, Any],
               state_file: Path, today: date, current_version: str = __version__) -> dict[str, Any]:
    """Decide whether this feed is believed, and what it offers. The record of
    feeds already seen is updated only after every check has passed."""
    result: dict[str, Any] = {"current_version": current_version, "status": "refused",
                              "reason": "", "latest": None, "sequence": None, "key_id": None}
    if not config["keys"]:
        return {**result, "status": "not_configured",
                "reason": "no update key is pinned yet, so no feed is trusted"}
    if len(feed_bytes) > MAX_FEED_BYTES or len(signature) > MAX_SIGNATURE_BYTES:
        raise UpdateError("the feed or its signature is too large to be genuine")
    key_id = next((kid for kid, n, e in config["keys"]
                   if verify_signature(n, e, feed_bytes, signature)), None)
    if key_id is None:
        raise UpdateError("the feed's signature does not verify with a trusted key")
    try:
        feed = _parse_feed(json.loads(feed_bytes.decode("utf-8")), config["channel"])
    except (UnicodeDecodeError, ValueError) as exc:
        if isinstance(exc, UpdateError):
            raise
        raise UpdateError("the signed feed is not valid JSON") from exc
    if today < feed["issued"]:
        raise UpdateError(f"the feed is not issued until {feed['issued'].isoformat()}; it is"
                          " not believed before then")
    if today > feed["expires"]:
        raise UpdateError(f"the feed expired on {feed['expires'].isoformat()}; an old feed"
                          " cannot be trusted to say what is current")
    digest = hashlib.sha256(feed_bytes).hexdigest()
    refusal = ""
    with _seen_feeds(Path(state_file)) as db:
        seen = db.execute("SELECT sequence, feed_sha256 FROM feeds_seen WHERE channel = ?",
                          (config["channel"],)).fetchone()
        if seen and feed["sequence"] < seen[0]:
            raise UpdateError(f"this feed (sequence {feed['sequence']}) is older than one"
                              f" already seen (sequence {seen[0]}); it may be replayed")
        if seen and feed["sequence"] == seen[0] and digest != seen[1]:
            # Committed, not rolled back: once a sequence is contradicted, no feed
            # under it is trusted again. Only a later sequence can be.
            db.execute("UPDATE feeds_seen SET feed_sha256 = ? WHERE channel = ?",
                       (_CONTRADICTED, config["channel"]))
            refusal = "two different feeds carry the same sequence; neither is trusted"
        else:
            current = _version(current_version)
            newer = sorted((r for r in feed["releases"] if r["rank"] > current),
                           key=lambda r: r["rank"])
            latest = newer[-1] if newer else None
            db.execute("INSERT INTO feeds_seen (channel, sequence, feed_sha256) VALUES (?, ?, ?)"
                       " ON CONFLICT (channel) DO UPDATE SET sequence = excluded.sequence,"
                       " feed_sha256 = excluded.feed_sha256",
                       (config["channel"], feed["sequence"], digest))
    if refusal:
        raise UpdateError(refusal)
    return {**result, "status": "update_available" if latest else "current",
            "reason": "" if latest else "this is the newest release the feed lists",
            "latest": None if latest is None else {k: v for k, v in latest.items() if k != "rank"},
            "sequence": feed["sequence"], "key_id": key_id}


def fetch(url: str, *, limit: int) -> bytes:
    """GET ``url`` over https, following no redirects, reading at most ``limit`` bytes."""
    if not url.startswith("https://"):
        raise UpdateError("updates are only fetched over https")

    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):  # noqa: ANN002, ANN003
            return None

    opener = urllib.request.build_opener(_NoRedirect)
    request = urllib.request.Request(url, headers={"User-Agent": f"nurse-ai-os/{__version__}",
                                                   "Cache-Control": "no-cache"})
    try:
        with opener.open(request, timeout=FETCH_TIMEOUT_SECONDS) as response:
            if response.status != 200:
                raise UpdateError(f"the update server answered {response.status}")
            body = response.read(limit + 1)
    except urllib.error.HTTPError as exc:
        raise UpdateError(f"the update server answered {exc.code}") from exc
    except (urllib.error.URLError, OSError) as exc:
        raise UpdateError("the update server could not be reached") from exc
    if len(body) > limit:
        raise UpdateError("the update server sent more than a feed can be")
    return body


def _read_at_most(path: Path, limit: int) -> bytes:
    """A file given by hand is read like a download: never more than a feed can be."""
    with path.open("rb") as fh:
        data = fh.read(limit + 1)
    if len(data) > limit:
        raise UpdateError(f"{path.name} is too large to be a genuine feed or signature")
    return data


def check(*, feed_file: Path | None = None, signature_file: Path | None = None,
          config_file: Path | None = None, state_file: Path | None = None,
          today: date | None = None) -> dict[str, Any]:
    """The manager's "check for updates": from files they were given, or from
    the configured feed address. Never runs on its own."""
    config = load_config(config_file)
    today = today or date.today()
    if (feed_file is None) != (signature_file is None):
        raise UpdateError("give both the feed and its signature, or neither")
    if feed_file is not None:
        feed_bytes = _read_at_most(Path(feed_file), MAX_FEED_BYTES)
        signature = _read_at_most(Path(signature_file), MAX_SIGNATURE_BYTES)
    elif config["keys"] and config["feed_url"]:
        feed_bytes = fetch(config["feed_url"], limit=MAX_FEED_BYTES)
        signature = fetch(config["feed_url"] + ".sig", limit=MAX_SIGNATURE_BYTES)
    else:
        return {"current_version": __version__, "status": "not_configured",
                "reason": "no update key and feed address are set yet, so nothing is checked",
                "latest": None, "sequence": None, "key_id": None}
    return check_feed(feed_bytes, signature, config=config,
                      state_file=Path(state_file or state_path()), today=today)


def verify_download(path: Path, expected_sha256: str) -> bool:
    """Whether a downloaded file is byte for byte the one the signed feed names."""
    if not _SHA256.fullmatch(expected_sha256 or ""):
        raise UpdateError("the expected sha256 is not 64 hex characters")
    digest = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return hmac.compare_digest(digest.hexdigest(), expected_sha256)


__all__ = ["UpdateError", "check", "check_feed", "fetch", "load_config", "load_public_key",
           "verify_download", "verify_signature"]
