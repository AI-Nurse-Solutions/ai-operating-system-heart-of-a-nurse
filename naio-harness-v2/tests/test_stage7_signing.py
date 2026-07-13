import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIGN = ROOT / "scripts" / "sign-release-evidence.py"
PREPARE = ROOT / "scripts" / "prepare-release-signing.py"


class Stage7SigningTests(unittest.TestCase):
    def make_keys(self, root: Path) -> tuple[Path, Path]:
        private = root / "private.pem"
        public = root / "public.pem"
        subprocess.run(
            ["openssl", "genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048", "-out", str(private)],
            check=True,
            capture_output=True,
        )
        private.chmod(0o600)
        subprocess.run(
            ["openssl", "pkey", "-in", str(private), "-pubout", "-out", str(public)],
            check=True,
            capture_output=True,
        )
        return private, public

    def test_prepare_and_sign_exact_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_dir = root / "evidence"
            evidence_dir.mkdir()
            artifact = evidence_dir / "release-evidence.json"
            artifact.write_text(json.dumps({"release_status": "unsigned_implementation_candidate"}) + "\n")
            private, public = self.make_keys(root)

            prepared = subprocess.run(
                [sys.executable, str(PREPARE), "--root", str(root), "--public-key", str(public),
                 "--key-id", "test-key", "--signer", "Synthetic Test Steward"],
                check=True,
                capture_output=True,
                text=True,
            )
            digest = json.loads(prepared.stdout)["artifact_sha256"]
            signature = evidence_dir / "release-evidence.sig"
            signed = subprocess.run(
                [sys.executable, str(SIGN), "--artifact", str(artifact), "--signature", str(signature),
                 "--private-key", str(private), "--public-key", str(public), "--expected-sha256", digest],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("VERIFIED", signed.stdout)
            self.assertTrue(signature.is_file())
            finalized = json.loads(artifact.read_text())
            self.assertTrue(finalized["signing"]["signed"])
            self.assertFalse(finalized["signing"]["trust_anchor_rotated"])

    def test_changed_artifact_refuses_signing(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact = root / "evidence.json"
            artifact.write_text("original\n")
            expected = hashlib.sha256(artifact.read_bytes()).hexdigest()
            private, public = self.make_keys(root)
            artifact.write_text("changed\n")
            result = subprocess.run(
                [sys.executable, str(SIGN), "--artifact", str(artifact), "--signature", str(root / "out.sig"),
                 "--private-key", str(private), "--public-key", str(public), "--expected-sha256", expected],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("artifact digest changed", result.stderr + result.stdout)
            self.assertFalse((root / "out.sig").exists())


if __name__ == "__main__":
    unittest.main()
