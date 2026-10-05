"""Retain verified runtime source and notices; never execute downloaded code."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request

config = json.loads(Path(sys.argv[1]).read_text())
output = Path(sys.argv[2]).resolve()
output.mkdir(exist_ok=False)
receipts = []
def source_tree_hash(path):
    """Gitiles archives regenerate member timestamps; hash their actual tree."""
    digest = hashlib.sha256()
    with tarfile.open(path) as archive:
        for member in sorted(archive.getmembers(), key=lambda m: m.name):
            data = archive.extractfile(member).read() if member.isfile() else member.linkname.encode()
            header = [member.name, member.type.decode('ascii'), member.mode, len(data)]
            digest.update(json.dumps(header, separators=(',', ':')).encode() + b'\0' + data + b'\0')
    return digest.hexdigest()

for item in config['downloads']:
    target = output / item['name']
    with urllib.request.urlopen(item['url'], timeout=120) as response:
        with target.open('xb') as stream:
            shutil.copyfileobj(response, stream)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    if item.get('treeSha256'):
        if source_tree_hash(target) != item['treeSha256']:
            raise ValueError('Source tree differs from reviewed files: ' + item['name'])
    elif digest != item['sha256'] or target.stat().st_size != item['bytes']:
        raise ValueError('Source/notice does not match reviewed bytes: ' + item['name'])
    receipts.append({**item, 'downloadSha256': digest, 'downloadBytes': target.stat().st_size})

# Include the preferred source after Electron's actual patch, not another
# FFmpeg release. Matching build controls and dependencies travel alongside it.
with tempfile.TemporaryDirectory(prefix='naio-corresponding-source-') as scratch:
    scratch = Path(scratch)
    for name, dest in [('ffmpeg.tar.gz', 'ffmpeg'), ('electron.tar.gz', 'electron')]:
        with tarfile.open(output / name) as archive:
            archive.extractall(scratch / dest, filter='data')
    electron = scratch / 'electron/electron-40.10.2'
    deps = (electron / 'DEPS').read_text()
    if config['chromium'] not in deps or 'v24.15.0' not in deps:
        raise ValueError('Unexpected Electron dependency chain')
    ffmpeg = scratch / 'ffmpeg'
    conf = (ffmpeg / 'chromium/config/Chrome/mac/x64/config.h').read_text()
    for flag in ['CONFIG_GPL', 'CONFIG_NONFREE', 'CONFIG_VERSION3']:
        if '#define ' + flag + ' 0' not in conf:
            raise ValueError('Review changed FFmpeg license configuration')
    patch = electron / 'patches/ffmpeg/link_with_loader_path.patch'
    subprocess.run(['git', 'apply', '--check', str(patch)], cwd=ffmpeg, check=True)
    subprocess.run(['git', 'apply', str(patch)], cwd=ffmpeg, check=True)
    if '@loader_path/libffmpeg.dylib' not in (ffmpeg / 'BUILD.gn').read_text():
        raise ValueError('Electron FFmpeg patch not applied')
    patched = output / 'ffmpeg-electron-40.10.2-source.tar.gz'
    with tarfile.open(patched, 'w:gz') as archive:
        archive.add(ffmpeg, arcname='ffmpeg')
    shutil.copyfile(patch, output / 'electron-ffmpeg.patch')
    # Full source is retained in the patched archive; omit its duplicate.
    (output / 'ffmpeg.tar.gz').unlink()

(output / 'source-receipt.json').write_text(json.dumps({
    **config, 'downloads': receipts,
    'verification': 'Reviewed SHA-256 matched (canonical source trees for Gitiles archives); Electron patch applied',
    'patchedFfmpegSha256': hashlib.sha256(patched.read_bytes()).hexdigest(),
    'buildExecuted': False,
}, indent=2) + '\n')
(output / 'BUILD-AND-LIBRARY-REPLACEMENT.txt').write_text('''Electron 40.10.2 / Chromium 144.0.7559.236 / Node 24.15.0
FFmpeg source: e18f48eba6b367ac68b9c477ae6cbe224e36b031, with the
included Electron link_with_loader_path.patch already applied in the archive.
Chrome/mac/x64 config: GPL=0, NONFREE=0, VERSION3=0; LGPL 2.1 or later.
See ffmpeg/COPYING.LGPLv2.1 and the per-file notices. Corresponding library
source, Chromium build controls, Opus, NASM and Electron patches/build scripts
are included. These archives are source, not installers; do not run them to
test the two applications. No FFmpeg rebuild is claimed.

To obtain the complete matching application build workspace, use depot_tools
and the instructions included in electron-40.10.2/docs/development/
build-instructions-gn.md. Pin the Electron checkout to
fd8ec408db9ca3d1f55c5746e19f63f30615ba10:
  gclient config --name src/electron --unmanaged https://github.com/electron/electron
  gclient sync --revision src/electron@fd8ec408db9ca3d1f55c5746e19f63f30615ba10 --with_branch_heads --with_tags
  cd src
  gn gen out/Release --args='import("//electron/build/args/release.gn") target_cpu="x64"'
  ninja -C out/Release ffmpeg
This needs the documented compiler/SDK and significant disk space. Inspect
the pinned scripts and dependencies before running them. The supplied source
archives permit inspection of the library and its build controls immediately.

Hermes dynamically loads libffmpeg.dylib from its Electron framework. You may
modify the LGPL library and reverse engineer this application for debugging
those modifications. No agreement in this developer package restricts that.
Work on your own COPY of Hermes.app; replace
Contents/Frameworks/Electron Framework.framework/Versions/A/Libraries/libffmpeg.dylib
with an ABI-compatible x86_64 build. Mac signatures may need regeneration:
  codesign --force --deep --sign - "Hermes.app"
This is local ad-hoc signing, not Developer ID signing or notarization. It
changes signatures of your copy. Never disable Gatekeeper globally. The
developer build includes a separate, limited replacement-loader test receipt;
it does not establish that arbitrary ABI changes will work or that a library
was rebuilt from modified source.
''')
print(json.dumps({'verifiedDownloads': len(receipts), 'patchedFfmpegSource': True}))
