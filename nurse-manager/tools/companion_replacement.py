"""Prove changed LGPL library bytes load in an owned copy of the developer app."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

repo, upstream = [Path(p).resolve() for p in sys.argv[1:]]
original = upstream / 'apps/desktop/release/mac/Hermes.app'
library_path = 'Contents/Frameworks/Electron Framework.framework/Versions/A/Libraries/libffmpeg.dylib'
original_library = original / library_path
original_hash = hashlib.sha256(original_library.read_bytes()).hexdigest()
framework = original / 'Contents/Frameworks/Electron Framework.framework/Versions/A/Electron Framework'
dependencies = subprocess.check_output(['otool', '-L', str(framework)], text=True)
if 'libffmpeg.dylib' not in dependencies:
    raise ValueError('Expected dynamic FFmpeg linkage absent')

with tempfile.TemporaryDirectory(prefix='naio-library-replacement-') as scratch:
    copy = Path(scratch) / 'Hermes.app'
    subprocess.run(['ditto', str(original), str(copy)], check=True)
    library = copy / library_path
    arch = subprocess.check_output(['lipo', '-archs', str(library)], text=True).strip()
    if arch != 'x86_64':
        raise ValueError('Replacement library must be Intel')
    # Change only the local copy. A distinct signature makes bytes different;
    # this is a loader/replacement test, not a modified-source compilation.
    subprocess.run(['codesign', '--force', '--sign', '-', '--identifier',
                    'org.nurseaios.developer.ffmpeg-replacement-test', str(library)], check=True)
    subprocess.run(['codesign', '--force', '--deep', '--sign', '-', '--entitlements',
                    str(upstream / 'apps/desktop/electron/entitlements.mac.plist'), str(copy)], check=True)
    changed_hash = hashlib.sha256(library.read_bytes()).hexdigest()
    if original_hash == changed_hash:
        raise ValueError('Replacement must contain genuinely changed bytes')
    env = {**os.environ, 'NAIO_REPLACEMENT_LIBRARY': str(library),
           'NAIO_REPLACEMENT_SHA256': changed_hash}
    smoke = subprocess.run(['node', str(repo / 'nurse-manager/tests/test_hermes_desktop.mjs'),
                            str(upstream), str(copy / 'Contents/MacOS/Hermes')],
                           env=env, text=True, capture_output=True, timeout=180)
    if smoke.returncode:
        print(smoke.stderr, file=sys.stderr)
        print(smoke.stdout)
        raise ValueError('Changed-library packaged smoke failed')
    record = json.loads(smoke.stdout.strip())
    if record['result'] != 'PASS' or record['replacement']['changedLibraryLoaded'] is not True:
        raise ValueError('Actual loaded replacement was not verified')
    (repo / 'hermes-replacement-smoke.json').write_text(json.dumps(record, indent=2) + '\n')
    if hashlib.sha256(original_library.read_bytes()).hexdigest() != original_hash:
        raise ValueError('Original distribution library unexpectedly changed')
    (repo / 'library-replacement.json').write_text(json.dumps({
        'result': 'PASS', 'architecture': arch, 'originalSha256': original_hash,
        'replacementSha256': changed_hash, 'actualReplacementLoaded': True,
        'originalUnchanged': True, 'modifiedSourceRebuild': False,
        'method': 'separate app copy; signature changed; ad-hoc signed copy; actual lsof mapping',
        'normalLaunchVerified': False,
    }, indent=2) + '\n')
    print(json.dumps({'result': 'PASS', 'changedFfmpegLibraryActuallyLoaded': True}))
