# Intel two-app developer download

The requested download contains two separate applications: Nurse AI OS and
Hermes Desktop. It does not make Hermes the Nurse AI OS host, connect their
data stores, activate an AI provider, or install an agent runtime automatically.
The host integration and session mapping in ADR 0003 remain deferred.

Target hardware: Intel Mac. The steward reports macOS Tahoe 26.5.2. Electron
40 supports macOS 12 and later; this is a compatibility floor, not proof that
the application has passed tests on that particular laptop or OS version.

## Official installer result

The official site's `Hermes-Setup.dmg?build=439334127f01` has SHA-256
`b61e047efe3059faf1c55fec3252e661f2d2a993a7a3eebf5cc6a9aa5c1790f5`.
Native, read-only inspection found a notarized Developer ID installer,
version 0.0.1, whose executable is **arm64 only**. It cannot be presented as
an Intel application. Its website query is not evidence of the binary's
source commit. The installer was not executed.

## Source build

The dedicated workflow builds Desktop 0.17.6 from NousResearch/hermes-agent
commit `f97608f178d1ffeca59860195ab7da295f7c8e5f` (tag v2026.9.24), with
Electron 40.10.2, on `macos-15-intel`. Dependency versions come from the
upstream lockfile. Lifecycle scripts are disabled during installation;
reviewed Electron, esbuild and node-pty preparation is explicit. The upstream
build stamp records the upstream commit, not this repository's commit.

This is a source-built developer application, not an official signed Nous
Research release. Nurse AI OS is not affiliated with or endorsed by Nous
Research. Developer signing, notarization, pilot approval and real-hardware
testing remain independent gates.

The native smoke test launches the packaged x64 executable with fresh
synthetic settings and a kernel sandbox denying non-loopback network traffic.
Chromium cannot initialize its own sandbox inside that inherited macOS policy,
so this constrained smoke uses a test-only `--no-sandbox` argument while
retaining the outer kernel network policy for the app and its children. This
flag is not added to the application build or user launch instructions.
Normal launch with Chromium's own sandbox remains unverified. The smoke must
prove that outbound traffic is denied, then verify that setup remains
idle and that no runtime or provider configuration is created. It does not
choose an installation or connection option. Passing this test would not
mean that ordinary launches have the same network sandbox.

Hermes Desktop alone is not the complete offline Hermes agent. A later human
setup choice can download/install its runtime or connect to another system.
Those choices and the resulting privacy boundaries must remain explicit.

## Developer distribution checks

The steward authorized a combined developer download on October 5, 2026.
Publication is conditional on the workflow passing the actual bundle, source,
notice, constrained smoke and replacement-loader checks. Signing/notarization,
ordinary Tahoe hardware launch and a pilot release remain separate NOT RUN gates.

The build-input tool records renderer and main/preload inputs. The notice tool
retains exact installed manifests and available full notices, including native
external dependencies and Codicons. An exact installed MIT grant without a
standalone notice retains its complete package source and permission text;
no copyright holder/year is invented. Six recovered exact-source MIT notices
are separately downloaded with reviewed byte hashes. Unknown licenses fail.
noVNC MPL preferred source travels in the download; DOMPurify uses its Apache
alternative. JetBrains Mono is SIL OFL 1.1, despite an incorrect upstream CSS
comment; Codicons credits Microsoft under CC-BY-4.0. Full texts are included.

The UI dependency includes commercial fonts not covered by its MIT code grant.
The developer font patch removes all UI font binaries from both dist and src,
and removes the matching font-face declarations from UI and Desktop CSS.
The remaining system fallback changes the appearance. Modification hashes and
modified source are retained; the packaged stamp explicitly says dirty=true.
Actual archive assets are compared with the build inventory, and the complete
assembled download is checked for excluded fonts, including retained sources.

Runtime source archives are verified against reviewed SHA-256 pins. Gitiles
archives regenerate member timestamps, so those archives use a canonical tree
hash covering paths, types, modes and file/link contents; actual download hashes
are also recorded. The exact Electron FFmpeg patch is checked and applied to
preferred source. Matching Electron source, Chromium build controls, Opus,
NASM and a pinned complete-workspace build recipe travel with it. No library
rebuild is claimed. A separate app copy changes the library signature bytes,
then proves the changed library is mapped into the actual Electron process
while the constrained setup smoke passes. The original app is unchanged.
 In particular, noVNC uses MPL-2.0, Codicons uses
CC-BY-4.0, and Electron's dynamically linked FFmpeg uses LGPL-2.1. The exact
FFmpeg source, Electron patches and build controls must be addressed, along
with the ability to replace the library. A generic source link or Chromium
notice HTML alone is not recorded as completion.

Verified source chain: Electron v40.10.2 pins Chromium 144.0.7559.236 and
Node v24.15.0; Chromium pins FFmpeg
`e18f48eba6b367ac68b9c477ae6cbe224e36b031`. Electron applies
`patches/ffmpeg/link_with_loader_path.patch`. Do not substitute a different
upstream FFmpeg release or promise a source offer on the steward's behalf.

When these checks pass, the combined ZIP contains both real `.app`
bundles, notices/source material, a hash/provenance manifest and clear human
setup instructions. Existing Nurse AI OS tests and release gates remain in
force. No approval is inferred for provider activation, data sharing, plugins,
updates, a pilot release, WeKnora or Paperclip.

The unchanged Nurse Intel app is reused from run 37263039161; its ZIP SHA-256 is
76bdda6fb1a5fad6b1ab5d86e6a86dbc8fb3a6134439a8d2000507209452c945.
Assembly checks every recorded runtime source file against this checkout,
verifies both executable architectures, and reruns the Nurse self-test. Its
original receipt stays intact, including its original NOT RUN release gates.
The combined package additionally carries CPython 3.12.10, PyInstaller 6.22.3
(with bootloader exception) and OpenSSL 3.0.16 notices. The manifest covers all
regular files and internal symlinks; it is an inventory, not a signature.

Download the Actions artifact, extract its outer ZIP, then extract
nurse-ai-os-and-hermes-intel-UNSIGNED-test.zip. START-HERE.txt explains opening
each app and the setup boundary. Do not disable Gatekeeper globally.

For the first Hermes trial use the included fresh-settings .command launcher
beside Hermes.app. Ordinary launch can reuse an existing runtime or saved
connection and automatically start/attach its backend. The launcher clears
inherited credentials and uses new temporary Hermes/settings directories;
it does not change HOME or impose a network sandbox. Stop and report if an
existing session appears instead of setup.

The companion extends upstream’s explicit HERMES_DESKTOP_IGNORE_EXISTING=1
flag to skip system-Python fallback as well as CLI fallback. The fresh
launcher sets this flag; ordinary resolution is unchanged. The actual
resolver is exercised with simulated installed agents: before patch it
selects Python despite the flag (RED); afterward it returns setup without
CLI/Python probes, while ordinary CLI/Python discovery still works (GREEN).
The modified main source and before/after hashes travel with the download.

Runtime source verification runs as a Linux prerequisite with four bounded
retries for transient HTTP 429/5xx/network errors; hash failures remain fatal.
The Intel Mac job consumes those verified source/notices before assembly.
Complete CPython preferred source and Doc/license.rst plus accessible HACL,
BLAKE2/CC0, libmpdec and Expat notices are retained. Native linkage inspection
identifies statically included public-domain liblzma5.2.3 and SQLite3.49.1;
their exact notices/source are included. zlib, bzip2, libedit and libffi
are linked to macOS system libraries, which are not bundled.
