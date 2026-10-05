"""Assemble the authorized, unsigned two-app Intel developer download."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

repo, upstream, nurse, notices, source, output = [Path(p).resolve() for p in sys.argv[1:]]
output.mkdir(exist_ok=False)
expected = '76bdda6fb1a5fad6b1ab5d86e6a86dbc8fb3a6134439a8d2000507209452c945'
archive = nurse / 'nurse-ai-os-macos-unsigned.zip'
if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
    raise ValueError('Nurse application archive differs from verified build')
receipt = json.loads((nurse / 'build-receipt.json').read_text())
if receipt['git_head'] != 'ecd84bd4547d97cd989cf3136a9dc827ef18d874':
    raise ValueError('Unexpected Nurse source revision')
for name, digest in receipt['source_files'].items():
    if hashlib.sha256((repo / name).read_bytes()).hexdigest() != digest:
        raise ValueError('Nurse runtime changed; rebuild required: ' + name)
subprocess.run(['ditto', '-x', '-k', str(archive), str(output)], check=True)
hermes = upstream / 'apps/desktop/release/mac/Hermes.app'
subprocess.run(['ditto', str(hermes), str(output / 'Hermes.app')], check=True)
for app, binary in [('Nurse AI OS.app', 'nurse-ai-os'), ('Hermes.app', 'Hermes')]:
    executable = output / app / 'Contents/MacOS' / binary
    arch = subprocess.check_output(['lipo', '-archs', str(executable)], text=True).strip()
    if arch != 'x86_64':
        raise ValueError('Unexpected executable architecture: ' + app + ': ' + arch)
subprocess.run([str(output / 'Nurse AI OS.app/Contents/MacOS/nurse-ai-os'), '--self-test'], check=True)
shutil.copytree(notices, output / 'licenses')
shutil.copytree(source, output / 'licenses/runtime-source')
for name in ['LICENSE', 'THIRD_PARTY_NOTICES.md']:
    shutil.copyfile(repo / name, output / 'licenses' / name)
shutil.copyfile(upstream / 'package-lock.json', output / 'licenses/upstream-package-lock.json')
receipts = output / 'build-evidence'
receipts.mkdir()
shutil.copyfile(nurse / 'build-receipt.json', receipts / 'original-nurse-build-receipt.json')
for name in ['hermes-smoke.json', 'hermes-replacement-smoke.json', 'hermes-package.json', 'library-replacement.json']:
    value = json.loads((repo / name).read_text())
    if value['result'] != 'PASS':
        raise ValueError('Required developer packaging check failed: ' + name)
    shutil.copyfile(repo / name, receipts / name)

# A normal opening can reuse an existing runtime/profile. Give the human a
# fresh settings path without changing their HOME or global Hermes settings.
launcher = output / 'Test Hermes with fresh settings.command'
launcher.write_text('''#!/bin/sh
set -eu
test_profile=$(mktemp -d "${TMPDIR:-/tmp}/naio-hermes-first-test.XXXXXXXX")
app_folder=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
printf '%s\\n' "Hermes first test uses fresh temporary settings." "Stop at the setup screen unless you deliberately want to install/connect." "Test settings: $test_profile"
exec /usr/bin/env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin HOME="$HOME" TMPDIR="${TMPDIR:-/tmp}" LANG=en_US.UTF-8 \\
  HERMES_HOME="$test_profile/hermes" HERMES_SHARED_AUTH_DIR="$test_profile/shared" \\
  HERMES_DESKTOP_USER_DATA_DIR="$test_profile/electron" HERMES_DESKTOP_HERMES_ROOT="$test_profile/no-runtime" \\
  HERMES_SKIP_INTRO=1 HERMES_GUEST_ONBOARDING=0 \\
  "$app_folder/Hermes.app/Contents/MacOS/Hermes"
''')
launcher.chmod(0o755)

(output / 'START-HERE.txt').write_text('''Nurse AI OS + Hermes Desktop: INTEL MAC DEVELOPER TEST

Two separate apps in one download. Extract the ZIP, then copy both .app
files to a new test folder on your Mac. Keep the Hermes first-test .command
file beside Hermes.app. Open Nurse AI OS first. For the first Hermes test,
double-click "Test Hermes with fresh settings.command"; Terminal opens the
included Hermes app with temporary fresh settings and cleared inherited
credentials. This does not connect their data or make Hermes the Nurse host.

Neither app has Developer ID signing or Apple notarization. If macOS blocks
an app, first attempt to open that app, then use System Settings > Privacy &
Security > Open Anyway for that specific app, if you trust this test build.
Do not disable Gatekeeper globally. Do not grant extra privacy permissions
unless you deliberately need the feature requesting them.

First test: confirm Nurse AI OS opens and the fresh-settings Hermes launcher
shows its setup screen. Ordinary opening of Hermes.app can reuse an existing
Hermes runtime/configuration and automatically start/attach that backend; use
the fresh-settings launcher for this first trial. If an existing session or
backend appears instead of setup, quit and report it. The launcher does not
provide a network sandbox; apps may make ordinary network requests.
On Hermes, stop before Install Hermes locally / Connect to existing Hermes
unless you have deliberately decided to install or connect its runtime.
Desktop itself is included; the full Hermes agent and its model are not.
Installing a runtime can download additional software and connecting a
provider or existing system creates separate data/privacy boundaries.
No provider credentials, runtime configuration or private data is bundled.

Hermes is our source-built developer companion from Nous Research's pinned
source, with commercial UI fonts removed and system-font fallbacks. It is
not an official Nous release. Nurse AI OS is not affiliated with or endorsed
by Nous Research. Original branding identifies the separate third-party app.

Use synthetic examples for this developer test. Clinical use, institutional
deployment and signed/pilot release gates remain unapproved. Normal launch
on your Intel macOS Tahoe 26.5.2 is for you to test. CI used a constrained
launch with outbound network denied and a test-only Chromium sandbox flag;
ordinary app launches do not inherit that network policy. No such flag is
required by these instructions or added to the app build.

Please report: which app, whether it opens, any exact error message, and
whether Hermes reaches the setup screen. You can quit either app normally.
The licenses/ folder contains attribution, full notices, MPL preferred
source and LGPL library source/build controls. None needs to be executed.
See build-evidence/ and manifest.json for source hashes and test limits.
''')
files = {}
links = {}
for path in sorted(output.rglob('*')):
    relative = path.relative_to(output).as_posix()
    if path.suffix.lower() in {'.woff', '.woff2', '.ttf', '.otf'} and any(
        name.lower() in relative.lower() for name in ['Collapse', 'RulesCompressed', 'RulesExpanded', 'Mondwest', 'Neuebit']
    ):
        raise ValueError('Commercial font survives in complete download: ' + relative)
    if path.is_symlink():
        if not path.resolve().is_relative_to(output):
            raise ValueError('Bundle symlink escapes download: ' + relative)
        links[relative] = str(path.readlink())
    elif path.is_file():
        files[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
manifest = {
    'format': 'naio-intel-two-app-developer@1',
    'packagingHead': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip(),
    'nurseSource': receipt['git_head'], 'nurseOriginalZipSha256': expected,
    'hermesSource': 'f97608f178d1ffeca59860195ab7da295f7c8e5f',
    'hermesModified': 'commercial font faces and font assets removed; modification hashes included',
    'architecture': 'x86_64', 'distribution': 'UNSIGNED developer test only',
    'gates': {'DeveloperIDSigning': 'NOT RUN', 'notarization': 'NOT RUN',
              'TahoeHardwareNormalLaunch': 'NOT RUN', 'pilotRelease': 'NOT RUN'},
    'filesSha256': files, 'symlinks': links,
    'limitations': 'Hash inventory, not a signature or reproducible-build attestation. Limited loader test changes signatures, not FFmpeg source.',
}
(output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps({'result': 'PASS', 'applications': ['Nurse AI OS.app', 'Hermes.app'], 'filesHashed': len(files)}))
