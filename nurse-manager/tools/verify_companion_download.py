"""Read back the actual uploaded bytes without executing either Mac app."""
import hashlib
import json
from pathlib import Path
import posixpath
import stat
import struct
import sys
import zipfile

artifact = Path(sys.argv[1])
if artifact.is_dir():
    inner = artifact / 'nurse-ai-os-and-hermes-intel-UNSIGNED-test.zip'
    checksum = (artifact / 'combined-download.sha256').read_text().split()[0]
else:
    with zipfile.ZipFile(artifact) as archive:
        name = next(n for n in archive.namelist() if n.endswith('nurse-ai-os-and-hermes-intel-UNSIGNED-test.zip'))
        checksum = archive.read(next(n for n in archive.namelist() if n.endswith('combined-download.sha256'))).decode().split()[0]
        inner = artifact.with_name('verified-two-apps-intel.zip')
        with archive.open(name) as src, inner.open('xb') as out:
            import shutil
            shutil.copyfileobj(src, out)
with inner.open('rb') as stream:
    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
assert digest == checksum
with zipfile.ZipFile(inner) as bundle:
    names = bundle.namelist()
    manifest_name = next(n for n in names if n.endswith('/manifest.json'))
    root = manifest_name.removesuffix('manifest.json')
    manifest = json.loads(bundle.read(manifest_name))
    assert manifest['packagingHead'] == sys.argv[2]
    assert manifest['architecture'] == 'x86_64'
    assert manifest['nurseOriginalZipSha256'] == '76bdda6fb1a5fad6b1ab5d86e6a86dbc8fb3a6134439a8d2000507209452c945'
    for path, expected in manifest['filesSha256'].items():
        with bundle.open(root + path) as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == expected, path
    for path, target in manifest['symlinks'].items():
        info = bundle.getinfo(root + path)
        assert stat.S_ISLNK(info.external_attr >> 16), path
        assert bundle.read(root + path).decode() == target, path
        assert not target.startswith('/')
        assert not posixpath.normpath(posixpath.join(posixpath.dirname(path), target)).startswith('../')
    for app, binary in [('Nurse AI OS.app', 'nurse-ai-os'), ('Hermes.app', 'Hermes')]:
        info = bundle.getinfo(root + app + '/Contents/MacOS/' + binary)
        assert (info.external_attr >> 16) & 0o111
        header = bundle.read(info)[:32]
        assert header[:4] == b'\xcf\xfa\xed\xfe' and struct.unpack_from('<I', header, 4)[0] == 0x1000007
    launch = bundle.getinfo(root + 'Test Hermes with fresh settings.command')
    assert (launch.external_attr >> 16) & 0o111
    assert b'HERMES_DESKTOP_IGNORE_EXISTING=1' in bundle.read(launch)
    stamp = json.loads(bundle.read(root + 'Hermes.app/Contents/Resources/install-stamp.json'))
    modifications = bundle.read(root + 'licenses/font-modifications.json')
    assert stamp['dirty'] is True
    assert stamp['companionModificationsSha256'] == hashlib.sha256(modifications).hexdigest()
    ledger = json.loads(modifications)
    for source, retained in [('apps/desktop/electron/main.ts', 'modified-desktop-main.ts'),
                             ('apps/desktop/src/styles.css', 'modified-desktop-styles.css')]:
        change = next(r for r in ledger if r['path'] == source)
        assert hashlib.sha256(bundle.read(root + 'licenses/' + retained)).hexdigest() == change['after']
    for n in names:
        assert not any(n.lower().endswith(x) for x in ['.env', 'config.yaml'])
        if n.lower().endswith(('.woff', '.woff2', '.ttf', '.otf')):
            assert not any(x.lower() in n.lower() for x in ['Collapse', 'RulesCompressed', 'RulesExpanded', 'Mondwest', 'Neuebit'])
    for name in ['hermes-smoke.json', 'hermes-replacement-smoke.json', 'hermes-package.json', 'library-replacement.json']:
        value = json.loads(bundle.read(root + 'build-evidence/' + name))
        assert value['result'] == 'PASS'
    runtime = json.loads(bundle.read(root + 'licenses/runtime-source/source-receipt.json'))
    assert len(runtime['downloads']) == 21
    with bundle.open(root + 'licenses/runtime-source/ffmpeg-electron-40.10.2-source.tar.gz') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == runtime['patchedFfmpegSha256']
receipt = {'result': 'PASS', 'packagingHead': manifest['packagingHead'], 'sha256': digest,
           'sizeBytes': inner.stat().st_size, 'filesVerified': len(manifest['filesSha256']),
           'symlinksVerified': len(manifest['symlinks']), 'bothIntelApps': True,
           'developerOnly': True, 'normalTahoeLaunchVerified': False}
Path(sys.argv[3] if len(sys.argv) > 3 else 'combined-download-readback.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt))
