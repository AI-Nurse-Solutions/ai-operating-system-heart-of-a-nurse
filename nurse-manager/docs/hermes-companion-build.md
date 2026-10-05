# Intel Hermes Desktop companion investigation

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

## Redistribution gate

The workflow currently uploads **no application binary**. A successful build
does not complete redistribution review.

The build-input tool records renderer and main/preload bundler inputs. The
notice tool inventories their installed packages, plus Electron and native
external packages, retains available notices and copies noVNC source. Its
output is diagnostic and always says `redistributionReady: false`.

Before assembling or publishing a combined download, resolve missing notices,
custom license terms, asset attribution, nested runtime obligations and the
actual package contents. In particular, noVNC uses MPL-2.0, Codicons uses
CC-BY-4.0, and Electron's dynamically linked FFmpeg uses LGPL-2.1. The exact
FFmpeg source, Electron patches and build controls must be addressed, along
with the ability to replace the library. A generic source link or Chromium
notice HTML alone is not recorded as completion.

Verified source chain: Electron v40.10.2 pins Chromium 144.0.7559.236 and
Node v24.15.0; Chromium pins FFmpeg
`e18f48eba6b367ac68b9c477ae6cbe224e36b031`. Electron applies
`patches/ffmpeg/link_with_loader_path.patch`. Do not substitute a different
upstream FFmpeg release or promise a source offer on the steward's behalf.

When these checks pass, the combined ZIP must contain both real `.app`
bundles, notices/source material, a hash/provenance manifest and clear human
setup instructions. Existing Nurse AI OS tests and release gates remain in
force. No approval is inferred for provider activation, data sharing, plugins,
updates, a pilot release, WeKnora or Paperclip.
