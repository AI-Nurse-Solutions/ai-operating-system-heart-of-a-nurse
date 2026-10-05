# Copyright 2026 Robert Domondon
# SPDX-License-Identifier: Apache-2.0

"""The record-writer register must cover the database after all migrations."""

import re
import tempfile
import unittest
from collections import Counter
from pathlib import Path

import _bootstrap  # noqa: F401

from nurse_manager.store import Store

REGISTER = Path(__file__).resolve().parents[1] / "docs" / "02-contract-map.md"


def registered_tables(document):
    section = document.split("## 5. Record-writer register", 1)[1]
    counts = Counter()
    for line in section.splitlines():
        if not line.startswith("| "):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        tables = re.findall(r"`([a-z_][a-z0-9_]*)`", cells[1])
        if tables:
            if len(cells) != 4 or not cells[2] or not cells[3]:
                raise AssertionError("each record needs a writer and readers")
            counts.update(tables)
    return counts


class RecordWriterRegisterTests(unittest.TestCase):
    def setUp(self):
        self.document = REGISTER.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "workspace.sqlite")
            try:
                self.tables = {row[0] for row in store.conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                    " AND name NOT LIKE 'sqlite_%'")}
            finally:
                store.close()

    def assert_register_matches(self, document, tables):
        counts = registered_tables(document)
        self.assertEqual(set(counts), tables,
                         "the migrated schema and record-writer register differ")
        self.assertEqual({table: n for table, n in counts.items() if n != 1}, {},
                         "each table must have one logical writer entry")

    def test_register_matches_the_actual_migrated_schema(self):
        self.assert_register_matches(self.document, self.tables)

    def test_a_new_unregistered_table_is_detected(self):
        with self.assertRaises(AssertionError):
            self.assert_register_matches(self.document, self.tables | {"future_records"})

    def test_a_register_entry_for_a_missing_table_is_detected(self):
        with self.assertRaises(AssertionError):
            self.assert_register_matches(self.document, self.tables - {"pilot_feedback"})

    def test_duplicate_writer_entries_are_detected(self):
        with self.assertRaises(AssertionError):
            self.assert_register_matches(
                self.document + "\n| Duplicate | `pilot_feedback` | Another writer | views |\n",
                self.tables)

    def test_lifecycle_description_matches_the_shipped_one_way_adapter(self):
        self.assertNotIn("this PR", self.document)
        self.assertNotIn("once G2 step 2.11 lands", self.document)
        self.assertIn("one-way projection", self.document)
