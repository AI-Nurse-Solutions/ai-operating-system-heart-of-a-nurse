"""Build inventory describes actual inputs and refuses outside artifacts."""
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_spec = importlib.util.spec_from_file_location('build_receipt', Path(__file__).parents[1] / 'tools/build_receipt.py')
receipt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(receipt)


class BuildReceiptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for folder in receipt.INPUTS:
            (self.root / folder).mkdir(parents=True, exist_ok=True)
        self.source = self.root / 'nurse-manager/src/example.py'
        self.source.write_text('public synthetic build fixture\n')
        (self.root / 'dist').mkdir()
        self.artifact = self.root / 'dist/test-build'
        self.artifact.write_bytes(b'synthetic executable bytes')

    def build(self, artifact=None):
        with mock.patch.object(receipt.subprocess, 'check_output', side_effect=['a'*40+'\n',' M example.py\n']):
            return receipt.create_receipt(self.root, artifact or self.artifact)

    def test_records_real_bytes_and_does_not_claim_release_checks(self):
        data = self.build()
        self.assertEqual(data['artifact']['sha256'], hashlib.sha256(self.artifact.read_bytes()).hexdigest())
        self.assertEqual(data['source_files']['nurse-manager/src/example.py'], hashlib.sha256(self.source.read_bytes()).hexdigest())
        self.assertTrue(data['tracked_or_untracked_changes'])
        self.assertEqual(set(data['release_gates'].values()), {'NOT RUN'})
        before = data['source_inputs_sha256']
        self.source.write_text('changed synthetic fixture\n')
        self.assertNotEqual(self.build()['source_inputs_sha256'], before)
        json.dumps(data)

    def test_refuses_outside_artifact_and_symlinked_source(self):
        outside = self.root / 'outside-build'
        outside.write_bytes(b'not in dist')
        with self.assertRaises(ValueError):
            self.build(outside)
        link = self.root / 'nurse-manager/config/linked-file'
        try:
            link.symlink_to(self.source)
        except (OSError, NotImplementedError):
            self.skipTest('symlink creation unavailable on this host')
        with self.assertRaises(ValueError):
            self.build()
