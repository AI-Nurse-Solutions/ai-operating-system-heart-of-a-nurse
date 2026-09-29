"""The update feed and safe upgrades (build step 6.2).

A feed is believed only when its exact bytes carry a signature from a
pinned key, and never backwards: a replayed, contradicted, or expired feed
is refused. The check is advisory and never runs by itself. Upgrading a
workspace makes a backup first, and a failed step is repaired forward.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

import _bootstrap  # noqa: F401

from nurse_manager import cli, update
from nurse_manager import store as store_module
from nurse_manager.store import MigrationFailed, Store, StoreError, _connect, _split_sql
from nurse_manager.update import UpdateError

ROOT = Path(__file__).resolve().parents[1]
FEEDS = ROOT / "tests" / "fixtures" / "update"
TODAY = date(2026, 9, 29)
OPENSSL = shutil.which("openssl")


def _feed(name):
    return (FEEDS / name).read_bytes(), (FEEDS / f"{name}.sig").read_bytes()


class _Tmp(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.state = self.tmp / "update-state.json"
        self.config = update.load_config(FEEDS / "config.json")

    def check(self, name, **kwargs):
        feed, sig = _feed(name)
        return update.check_feed(feed, sig, config=self.config, state_file=self.state,
                                 today=kwargs.pop("today", TODAY), **kwargs)

    def openssl(self, *args, **kwargs):
        return subprocess.run([OPENSSL, *map(str, args)], check=True, capture_output=True, **kwargs)

    def keypair(self, *genpkey_args):
        key, pub = self.tmp / "key.pem", self.tmp / "pub.pem"
        self.openssl("genpkey", *genpkey_args, "-out", key)
        self.openssl("pkey", "-in", key, "-pubout", "-out", pub)
        return key, pub.read_text()


class SignatureTests(_Tmp):
    def test_a_signed_feed_verifies_and_any_change_does_not(self):
        (_, n, e), = self.config["keys"]
        feed, sig = _feed("feed-seq5.json")
        self.assertTrue(update.verify_signature(n, e, feed, sig))
        bad = {
            "a byte of the feed": (feed[:10] + bytes([feed[10] ^ 1]) + feed[11:], sig),
            "an added byte": (feed + b" ", sig),
            "a byte of the signature": (feed, sig[:-1] + bytes([sig[-1] ^ 1])),
            "a truncated signature": (feed, sig[:-1]),
            "another feed's signature": (feed, _feed("feed-seq4.json")[1]),
            "a signature at or above the modulus": (feed, n.to_bytes(len(sig), "big")),
            "no signature": (feed, b""),
        }
        for label, (f, s) in bad.items():
            with self.subTest(label):
                self.assertFalse(update.verify_signature(n, e, f, s))

    def test_a_feed_that_does_not_verify_is_refused_and_leaves_no_trace(self):
        feed, sig = _feed("feed-seq5.json")
        with self.assertRaisesRegex(UpdateError, "does not verify"):
            update.check_feed(feed.replace(b"0.2.0", b"9.9.9"), sig, config=self.config,
                              state_file=self.state, today=TODAY)
        self.assertFalse(self.state.exists())

    def test_keys_are_checked_before_they_are_trusted(self):
        pem = (FEEDS / "public.pem").read_text()
        body = pem.strip().splitlines()
        bad = {
            "not a PEM": "hello",
            "a private-key header": pem.replace("PUBLIC KEY", "PRIVATE KEY"),
            "corrupted base64": "\n".join([body[0], "!!!" + body[1][3:], *body[2:]]),
            "trailing garbage": "\n".join([body[0], *body[1:-1], "AAAA", body[-1]]),
        }
        for label, text in bad.items():
            with self.subTest(label):
                with self.assertRaises(UpdateError):
                    update.load_public_key(text)
        config = json.loads((FEEDS / "config.json").read_text())
        config["trusted_keys"][0]["key_id"] = "0" * 64
        path = self.tmp / "config.json"
        path.write_text(json.dumps(config))
        with self.assertRaisesRegex(UpdateError, "id does not match"):
            update.load_config(path)

    @unittest.skipUnless(OPENSSL, "OpenSSL is not installed")
    def test_weak_or_non_rsa_keys_are_refused(self):
        for label, args in (("1024-bit RSA", ("-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:1024")),
                            ("EC", ("-algorithm", "EC", "-pkeyopt", "ec_paramgen_curve:P-256")),
                            ("Ed25519", ("-algorithm", "ED25519"))):
            with self.subTest(label):
                _, pub = self.keypair(*args)
                with self.assertRaises(UpdateError):
                    update.load_public_key(pub)

    @unittest.skipUnless(OPENSSL, "OpenSSL is not installed")
    def test_it_agrees_with_openssl(self):
        """Verification here, without OpenSSL, accepts exactly what OpenSSL signs
        with SHA-256, and nothing signed another way or by another key."""
        key, pub = self.keypair("-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:3072")
        n, e, _ = update.load_public_key(pub)
        for size in (0, 1, 55, 4096):
            message = self.tmp / "m.bin"
            message.write_bytes(bytes(range(256)) * (size // 256) + b"x" * (size % 256))
            with self.subTest(size=size):
                sha256 = self.openssl("dgst", "-sha256", "-sign", key, message).stdout
                sha1 = self.openssl("dgst", "-sha1", "-sign", key, message).stdout
                self.assertTrue(update.verify_signature(n, e, message.read_bytes(), sha256))
                self.assertFalse(update.verify_signature(n, e, message.read_bytes(), sha1))
        (_, n2, e2), = self.config["keys"]
        self.assertFalse(update.verify_signature(n2, e2, message.read_bytes(), sha256))


class FeedTests(_Tmp):
    def test_nothing_is_trusted_or_fetched_until_a_key_and_address_are_pinned(self):
        shipped = update.load_config()
        self.assertEqual((shipped["keys"], shipped["feed_url"]), ([], None))
        with mock.patch.object(update, "fetch", side_effect=AssertionError("no network")):
            result = update.check(state_file=self.state)
            self.assertEqual(result["status"], "not_configured")
            feed, sig = _feed("feed-seq5.json")
            self.assertEqual(update.check_feed(feed, sig, config=shipped, state_file=self.state,
                                               today=TODAY)["status"], "not_configured")
        self.assertFalse(self.state.exists())

    def test_a_newer_release_is_offered_with_its_signed_digests(self):
        result = self.check("feed-seq5.json")
        self.assertEqual((result["status"], result["latest"]["version"], result["sequence"]),
                         ("update_available", "0.2.0", 5))
        self.assertEqual(result["key_id"], self.config["keys"][0][0])
        self.assertEqual({a["platform"] for a in result["latest"]["artifacts"]},
                         {"windows-x64", "macos-arm64"})
        self.assertEqual(self.check("feed-seq5.json")["status"], "update_available")  # same feed again

    def test_an_older_release_is_never_offered(self):
        self.assertEqual(self.check("feed-seq5.json", current_version="0.2.0")["status"], "current")
        self.assertEqual(self.check("feed-seq5.json", current_version="0.3.0")["latest"], None)
        self.assertEqual(self.check("feed-current.json")["status"], "current")

    def test_a_replayed_older_feed_is_refused(self):
        self.check("feed-seq5.json")
        before = self.state.read_bytes()
        with self.assertRaisesRegex(UpdateError, "older than one already seen"):
            self.check("feed-seq4.json")
        self.assertEqual(self.state.read_bytes(), before)

    def test_two_feeds_under_one_sequence_are_both_refused(self):
        self.check("feed-seq5.json")
        with self.assertRaisesRegex(UpdateError, "same sequence"):
            self.check("feed-seq5-other.json")

    def test_an_expired_feed_is_refused(self):
        with self.assertRaisesRegex(UpdateError, "expired on 2020-02-01"):
            self.check("feed-expired.json")
        self.assertFalse(self.state.exists())
        self.assertEqual(self.check("feed-seq5.json", today=date(2099, 12, 31))["status"],
                         "update_available")
        with self.assertRaisesRegex(UpdateError, "expired"):
            self.check("feed-current.json", today=date(2100, 1, 1))

    def test_a_concurrent_check_cannot_roll_the_record_back(self):
        """Two checks at once: the one holding an older sequence must not
        overwrite a newer one recorded meanwhile, or an older feed would be
        believed again."""
        real_version, raced, calls = update._version, [], []

        def race(value):
            # The first two calls parse feed-seq5's releases; the third comes after
            # the comparison and before the write. There, another check records 7.
            calls.append(value)
            if len(calls) == 3 and not raced:
                raced.append(1)
                try:
                    self.check("feed-current.json")
                except UpdateError:
                    raced.append("held off")
            return real_version(value)

        with mock.patch.object(update, "STATE_LOCK_TIMEOUT_SECONDS", 0.1), \
                mock.patch.object(update, "_version", race):
            self.check("feed-seq5.json")
        if "held off" in raced:  # the other check waits its turn, then runs
            self.check("feed-current.json")
        with self.assertRaisesRegex(UpdateError, "older than one already seen"):
            self.check("feed-seq5.json")

    def test_a_contradicted_sequence_stays_refused(self):
        """Once two signed feeds are seen under one sequence, neither is trusted,
        now or later; only a later sequence is."""
        self.check("feed-seq5.json")
        with self.assertRaisesRegex(UpdateError, "same sequence"):
            self.check("feed-seq5-other.json")
        for name in ("feed-seq5.json", "feed-seq5-other.json"):
            with self.subTest(feed=name):
                with self.assertRaisesRegex(UpdateError, "same sequence"):
                    self.check(name)
        self.assertEqual(self.check("feed-current.json")["sequence"], 7)

    def test_a_feed_for_another_channel_is_refused(self):
        self.config["channel"] = "beta"
        with self.assertRaisesRegex(UpdateError, "another channel"):
            self.check("feed-seq5.json")

    def test_an_unreadable_record_of_feeds_seen_trusts_nothing(self):
        self.state.write_text("{not json")
        with self.assertRaisesRegex(UpdateError, "unreadable"):
            self.check("feed-seq5.json")

    def test_oversized_input_is_refused_before_it_is_verified(self):
        feed, sig = _feed("feed-seq5.json")
        with mock.patch.object(update, "verify_signature", side_effect=AssertionError):
            with self.assertRaisesRegex(UpdateError, "too large"):
                update.check_feed(feed + b" " * update.MAX_FEED_BYTES, sig, config=self.config,
                                  state_file=self.state, today=TODAY)

    def test_the_feed_address_must_be_https_and_redirects_are_not_followed(self):
        with self.assertRaisesRegex(UpdateError, "https"):
            update.fetch("http://example.org/feed.json", limit=10)
        config = json.loads((FEEDS / "config.json").read_text())
        config["feed_url"] = "http://example.org/feed.json"
        path = self.tmp / "config.json"
        path.write_text(json.dumps(config))
        with self.assertRaisesRegex(UpdateError, "https"):
            update.load_config(path)

        class Response:
            status = 200

            def __init__(self, body):
                self.body = body

            def read(self, n):
                return self.body[:n]

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        opened = []

        class Opener:
            def __init__(self, *handlers):
                opened.extend(handlers)

            def open(self, request, timeout):
                return Response(b"x" * 50)

        with mock.patch.object(update.urllib.request, "build_opener", Opener):
            with self.assertRaisesRegex(UpdateError, "more than a feed"):
                update.fetch("https://example.org/feed.json", limit=10)
        redirect = opened[0]
        self.assertIsNone(redirect().redirect_request(None, None, 302, "Found", {}, "https://evil"))

    def test_a_download_is_checked_against_the_signed_digest(self):
        artifact = self.tmp / "Nurse-AI-OS.zip"
        artifact.write_bytes(b"synthetic installer bytes")
        good = hashlib.sha256(artifact.read_bytes()).hexdigest()
        self.assertTrue(update.verify_download(artifact, good))
        self.assertFalse(update.verify_download(artifact, "0" * 64))
        with self.assertRaises(UpdateError):
            update.verify_download(artifact, "not-a-digest")

    def test_the_cli_answers_in_the_ipc_contract(self):
        code, env = cli.run([str(a) for a in (
            "update-check", "--feed", FEEDS / "feed-seq5.json", "--signature",
            FEEDS / "feed-seq5.json.sig", "--config", FEEDS / "config.json",
            "--state", self.state, "--today", "2026-09-29")])
        self.assertEqual((code, env["data"]["status"]), (0, "update_available"))
        code, env = cli.run(["update-check", "--feed", str(FEEDS / "feed-seq5.json"),
                             "--state", str(self.state)])
        self.assertEqual((code, env["error"]["type"]), (2, "UpdateError"))


@unittest.skipUnless(OPENSSL, "OpenSSL is not installed")
class SigningToolTests(_Tmp):
    def test_the_steward_tool_signs_what_the_app_verifies(self):
        key, pub = self.keypair("-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048")
        (self.tmp / "pub.pem").write_text(pub)
        tool = ROOT / "tools" / "sign_update_feed.py"
        entry = json.loads(subprocess.run([sys.executable, tool, "--key-entry", self.tmp / "pub.pem"],
                                          check=True, capture_output=True, text=True).stdout)
        config = {"schema": update.CONFIG_SCHEMA, "channel": "pilot", "feed_url": None,
                  "trusted_keys": [entry]}
        (self.tmp / "config.json").write_text(json.dumps(config))
        feed = self.tmp / "feed.json"
        feed.write_bytes((FEEDS / "feed-seq5.json").read_bytes())
        subprocess.run([sys.executable, tool, feed, "--key", key], check=True, capture_output=True)
        result = update.check(feed_file=feed, signature_file=self.tmp / "feed.json.sig",
                              config_file=self.tmp / "config.json", state_file=self.state,
                              today=TODAY)
        self.assertEqual(result["status"], "update_available")
        expired = self.tmp / "old.json"
        expired.write_bytes((FEEDS / "feed-expired.json").read_bytes())
        r = subprocess.run([sys.executable, tool, expired, "--key", key], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertFalse((self.tmp / "old.json.sig").exists())


def _old_workspace(path: Path, before: str) -> None:
    """A workspace as a release before migration ``before`` left it, with a record."""
    conn = _connect(path)
    conn.execute("CREATE TABLE schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
    for version, sql in (m for m in store_module._migrations() if m[0] < before):
        conn.execute("BEGIN IMMEDIATE")
        for statement in _split_sql(sql):
            conn.execute(statement)
        conn.execute("INSERT INTO schema_migrations VALUES (?, 'then')", (version,))
        conn.execute("COMMIT")
    conn.execute("INSERT INTO workspaces (id, name, profile, owner, sample, created_at) VALUES"
                 " ('ws-000000000001', 'W', 'personal_manager', 'M', 0, '2026-09-01T09:00:00+00:00')")
    conn.close()


class UpgradeTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "workspace.sqlite"
        self.latest = store_module._migrations()[-1][0]
        self.previous = store_module._migrations()[-2][0]

    def backups(self):
        return sorted((self.path.parent / "backups").glob("pre-migration-*.sqlite"))

    def test_a_workspace_is_backed_up_before_it_is_upgraded(self):
        _old_workspace(self.path, self.latest)
        store = Store(self.path)
        self.addCleanup(store.close)
        self.assertEqual(store.schema_version, self.latest)
        (backup,) = self.backups()
        self.assertIn(f"pre-migration-{self.previous[:4]}-to-{self.latest[:4]}-", backup.name)
        old = sqlite3.connect(str(backup))
        self.addCleanup(old.close)
        self.assertEqual(old.execute("SELECT max(version) FROM schema_migrations").fetchone()[0],
                         self.previous)
        self.assertEqual(old.execute("SELECT count(*) FROM workspaces").fetchone()[0], 1)

    def test_a_new_or_current_workspace_needs_no_backup(self):
        Store(self.path).close()
        Store(self.path).close()
        self.assertEqual(self.backups(), [])

    def test_no_upgrade_happens_without_a_backup(self):
        _old_workspace(self.path, self.latest)
        with mock.patch.object(Store, "backup", side_effect=OSError("disk full")):
            with self.assertRaisesRegex(StoreError, "backup could not be made first"):
                Store(self.path)
        conn = sqlite3.connect(str(self.path))
        self.addCleanup(conn.close)
        self.assertEqual(conn.execute("SELECT max(version) FROM schema_migrations").fetchone()[0],
                         self.previous)

    def test_a_busy_or_full_workspace_is_not_called_a_broken_release(self):
        """A lock held elsewhere, a full disk, or an I/O error means try again,
        not install a corrected release."""
        _old_workspace(self.path, self.latest)
        holder = sqlite3.connect(str(self.path), isolation_level=None)
        self.addCleanup(holder.close)
        holder.execute("BEGIN IMMEDIATE")
        real_connect = store_module._connect

        def impatient(path):
            conn = real_connect(path)
            conn.execute("PRAGMA busy_timeout = 100")
            return conn

        with mock.patch.object(store_module, "_connect", impatient):
            with self.assertRaises(StoreError) as caught:
                Store(self.path)
        self.assertNotIsInstance(caught.exception, MigrationFailed)
        self.assertIn("try again", str(caught.exception))
        self.assertNotIn("corrects this step", str(caught.exception))
        holder.execute("ROLLBACK")
        store = Store(self.path)  # once the other copy lets go, the upgrade completes
        self.addCleanup(store.close)
        self.assertEqual(store.schema_version, self.latest)

    def test_a_disk_that_fills_during_a_step_is_not_called_a_broken_release(self):
        """SQLite may roll a transaction back by itself when the disk fills; the
        full disk must still be what the manager is told."""
        _old_workspace(self.path, self.latest)
        filler = [*store_module._migrations(),
                  ("9998_example", "CREATE TABLE example_big (body TEXT)"),
                  # The ROLLBACK stands in for SQLite rolling the transaction back
                  # by itself when the disk fills; then the disk does fill.
                  ("9999_example", "ROLLBACK; INSERT INTO example_big SELECT"
                   " hex(randomblob(4000)) FROM (WITH RECURSIVE n(i) AS (SELECT 1"
                   " UNION ALL SELECT i + 1 FROM n WHERE i < 200) SELECT i FROM n)")]
        real_connect = store_module._connect

        def small_disk(path):
            conn = real_connect(path)
            if Path(path) == self.path:
                pages = conn.execute("PRAGMA page_count").fetchone()[0]
                conn.execute(f"PRAGMA max_page_count = {pages + 40}")
            return conn

        with mock.patch.object(store_module, "_migrations", return_value=filler), \
                mock.patch.object(store_module, "_connect", small_disk):
            with self.assertRaises(StoreError) as caught:
                Store(self.path)
        self.assertNotIsInstance(caught.exception, MigrationFailed)
        self.assertIn("the disk is full", str(caught.exception))
        conn = sqlite3.connect(str(self.path))
        self.addCleanup(conn.close)
        self.assertEqual(conn.execute("SELECT max(version) FROM schema_migrations").fetchone()[0],
                         "9998_example")

    def test_a_full_disk_is_named_plainly_and_a_bad_step_is_not(self):
        full = sqlite3.OperationalError("database or disk is full")
        full.sqlite_errorname = "SQLITE_FULL"
        bad = sqlite3.OperationalError("no such table: nowhere")
        bad.sqlite_errorname = "SQLITE_ERROR"
        self.assertTrue(store_module._environmental(full))
        self.assertFalse(store_module._environmental(bad))
        message = str(store_module.UpgradeInterrupted("0013_x", "0012_y", None, full))
        self.assertIn("the disk is full", message)
        self.assertIn("intact at step 0012_y", message)

    def test_a_failed_step_is_repaired_forward_never_backwards(self):
        _old_workspace(self.path, self.latest)
        broken = [*store_module._migrations(),
                  ("9998_example", "CREATE TABLE example_one (id TEXT PRIMARY KEY)"),
                  ("9999_example", "CREATE TABLE example_two (id TEXT PRIMARY KEY);"
                                   " INSERT INTO no_such_table VALUES (1)")]
        with mock.patch.object(store_module, "_migrations", return_value=broken):
            with self.assertRaises(MigrationFailed) as caught:
                Store(self.path)
        failure = caught.exception
        self.assertEqual((failure.version, failure.reached), ("9999_example", "9998_example"))
        self.assertTrue(failure.backup.is_file())
        self.assertIn(str(failure.backup), str(failure))
        conn = sqlite3.connect(str(self.path))
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertIn("example_one", tables)
        self.assertNotIn("example_two", tables)  # the failed step left nothing behind
        self.assertEqual(conn.execute("SELECT count(*) FROM workspaces").fetchone()[0], 1)
        conn.close()
        # This release, which lacks the new steps, refuses the partly upgraded workspace...
        with self.assertRaisesRegex(StoreError, "newer schema"):
            Store(self.path)
        # ...and a release with the step corrected carries it forward.
        fixed = [*broken[:-1], ("9999_example", "CREATE TABLE example_two (id TEXT PRIMARY KEY)")]
        with mock.patch.object(store_module, "_migrations", return_value=fixed):
            store = Store(self.path)
            self.addCleanup(store.close)
            self.assertEqual(store.schema_version, "9999_example")


if __name__ == "__main__":
    unittest.main()
