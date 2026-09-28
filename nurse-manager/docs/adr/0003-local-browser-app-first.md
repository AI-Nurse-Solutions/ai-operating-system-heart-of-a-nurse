---
title: "ADR 0003: Ship the pilot as a local app in the browser first"
status: Accepted
date: 2026-09-28
decided_by: Robert Domondon (project steward, GOVERNANCE.md §1)
decided_on: 2026-09-28
---

# ADR 0003: Ship the pilot as a local app in the browser first

## Context

The plan's G1 prefers a thin customization of Hermes Desktop. Validation
found four problems with doing that first:

- Upstream ships Windows only as MSIX for Windows 11 22H2+, so Windows 10
  managers are excluded.
- Hermes desktop plugins are unsandboxed.
- Signing and notarization identities are not yet in place.
- Hospital laptops may block software installs.

The options considered were: survey first (A), a Windows 11 and Mac-only
pilot (B), our own Windows installer for the Hermes shell (C), or a
local app that runs the core and opens the screens in the browser (D).

## Decision

**Option D.** The pilot ships as a single double-click application per
platform. Its launcher:

- starts the manager core on the loopback interface
- opens the manager's default browser at the screens
- keeps all records in the manager's own user-data folder, outside the
  application bundle

The Hermes Desktop shell is deferred, not abandoned. The renderer
already reads through a replaceable `Source`, so a later Hermes host
can replace the HTTP transport without changing any screen.

Required properties of the local app:

1. **Loopback only.** It never listens beyond 127.0.0.1, and it refuses
   requests with any other Host header.
2. **Authenticated local calls.** A fresh random token is generated at
   each launch and handed to the browser in the URL fragment, which is
   never sent to servers or put in referrers. Every data call must carry
   it. A web page or another program cannot read or change records by
   guessing the port.
3. **No terminal, no installed Python, no API key.** The runtime is
   bundled.
4. **Honest lifetime.** The page says the app is running on this
   computer and offers Quit. When no page has been in contact for a
   while, the app stops by itself, so closing the tab never leaves it
   running indefinitely.
5. **Built by CI for Windows, macOS, and Linux.** Builds are unsigned
   until signing identities exist. An unsigned build is for testing
   only, never for distribution to managers.

## Consequences

- Windows 10 and locked-down machines that allow running a user-level
  program become reachable.
- Upstream Hermes features (voice, quick entry, worker HUD) are not in
  the pilot. They arrive with G4 or a later Hermes host.
- Code signing is still required before managers receive a build: an
  Apple Developer ID with notarization, and a Windows signing route.

## Decision record

Accepted by the project steward, Robert Domondon, on 2026-09-28. He chose
"G1: D" in the Claude Code session, after reviewing options A–D.
