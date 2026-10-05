#!/usr/bin/env python3
"""Record exact source inputs and one unsigned test artifact; never sign or release."""
from __future__ import annotations
import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path

INPUTS = ('nurse-manager/src', 'nurse-manager/renderer', 'nurse-manager/config',
          'nurse-manager/samples', 'nurse-manager/packs', 'nurse-manager/packaging',
          'naio-integrations/src', 'naio-integrations/config')


def source_inputs(repo: Path) -> dict[str, str]:
    result = {}
    for folder in INPUTS:
        root = repo / folder
        if not root.is_dir():
            raise ValueError(f'missing build input: {folder}')
        for path in sorted(root.rglob('*')):
            if '__pycache__' in path.parts or path.suffix == '.pyc':
                continue
            if path.is_symlink():
                raise ValueError('build inputs must not be symlinks')
            if path.is_file():
                result[path.relative_to(repo).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def create_receipt(repo: Path, artifact: Path) -> dict:
    repo = repo.resolve()
    artifact = artifact.resolve(strict=True)
    if not artifact.is_relative_to(repo / 'dist') or not artifact.is_file():
        raise ValueError('artifact must be a file inside this checkout dist directory')
    files = source_inputs(repo)
    canonical = json.dumps(files, sort_keys=True, separators=(',', ':')).encode()
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=repo, text=True).strip()
    digest = hashlib.sha256()
    with artifact.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return {'format': 'nurse-manager-unsigned-build@1',
            'git_head': git('rev-parse', 'HEAD'),
            'tracked_or_untracked_changes': bool(git('status', '--porcelain=v1')),
            'source_inputs_sha256': hashlib.sha256(canonical).hexdigest(),
            'source_files': files,
            'artifact': {'filename': artifact.name, 'size_bytes': artifact.stat().st_size,
                         'sha256': digest.hexdigest()},
            'build_host': {'os': platform.system(), 'architecture': platform.machine(),
                           'python': platform.python_version()},
            'distribution': 'UNSIGNED developer test only',
            'release_gates': {'signing': 'NOT RUN', 'notarization': 'NOT RUN',
                              'runtime_license_review': 'NOT RUN',
                              'offline_pilot_hardware': 'NOT RUN'},
            'limitations': 'Hash inventory, not a signature, SBOM or reproducible-build attestation. Test results are separate evidence.'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    data = create_receipt(repo, args.artifact)
    args.output.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
