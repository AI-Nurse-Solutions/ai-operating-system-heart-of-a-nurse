# Packaged app verification handoff

2026-10-04 (steward's local date). Worktree `codex/packaged-capture` at
`/workspace/ai-operating-system-heart-of-a-nurse.codex-packaged-capture`.
Base commit `9ebd2134bf0354d8cab8635d340e45f8f48b0699` plus the preserved,
completed capture implementation. Changes remain local and uncommitted.
No remote workflow, push, merge or release was performed.

## Outcome in common language

The app can now be tested as an actual standalone executable, with its
Python runtime and capture screens inside it. The Linux build passed the
capture journey, the broader app journey and restart checks from an empty
working directory with Python source paths removed. This closes a test gap:
the capture test previously ignored the packaged-app setting and silently
ran the source instead.

The existing macOS build job now runs the same journeys against the binary
inside **Nurse AI OS.app**, then creates its unsigned ZIP and hash receipt.
A Mac runner must still execute this job. This Linux machine cannot create
or verify a genuine Mac app. The tested Linux file is not a Mac download.

## Concrete local artifact

- Executable: `dist/nurse-ai-os`, Linux x86_64; 12,638,544 bytes.
- SHA-256: `6d5d31b0ce4b3ca49647fe85b0883097379160bf1e468a059ccdcca667b8916a`.
- Receipt: `dist/build-receipt.json`.
- Source-input inventory SHA-256:
  `7c1d3b39e1218d7dc93b09bbad379e455ae91ffe6a507a987719f79f7fbd8a1d`.
- Build tool: existing pinned PyInstaller 6.22.3, installed wheel-only in
  `/workspace/scratch/nm-package-venv`; actual dependencies recorded in
  `.task-evidence/build-environment.txt`. CI now also requires wheels.

The receipt records current source file hashes, the Git base, dirty-source
status, artifact bytes and build-host platform. It is an unsigned inventory,
not a signature, an SBOM or a reproducible-build attestation. It is separate
from test evidence. Runtime redistribution licensing remains a release gate.

## Verification and corrections

Evidence and exit codes are retained in `.task-evidence/`.

| Gate | Result | Evidence |
|---|---|---|
| Genuine RED / GREEN for packaged target | RED: nonexistent configured executable was ignored and source passed; GREEN: missing target refuses, no fallback | `packaged-target-red.*`, `packaged-target-green.*` |
| PyInstaller build | PASS, exit 0 | `package-build-final.*` |
| Packaged startup checks | PASS, exit 0; capture view and both new assets checked | `package-self-test-final.*` |
| Packaged capture browser | PASS, exit 0; records, all task changes, citations/acceptance, stale/privacy/role refusals, lost reply, failed refresh, navigation, narrow reflow, actual process restart | `packaged-capture-final.*` |
| Packaged broader app browser | PASS, exit 0; existing source-only JEV stand-in portion explicitly NOT RUN in packaged mode | `packaged-app-second.*` |
| Source app/capture browser | PASS, exit 0; source JEV stand-in remains covered | `source-app-second.*`, `source-capture-final.*` |
| Manager regression | PASS: 519 tests ran, four skipped, exit 0 | `manager-second.*` |
| IPC and renderer typecheck | PASS: 174 real envelopes | `ipc-final.*` |
| Build-receipt tests | PASS: two tests; changed inputs change inventory hash; outside artifacts and symlinked files refused; gates remain NOT RUN | `receipt-tests.*` |
| Launcher refusal / fresh review | PASS independently; no remaining blocking findings | `independent-review.md` |
| Exact artifact/source hash readback | PASS; receipt matches current inputs and executable | Completion receipt |
| macOS / Windows builds and exact-head CI | NOT RUN here | Existing CI job prepared; not dispatched |
| Signing, notarization, runtime license review, offline pilot hardware | NOT RUN | Existing release gates |

Calendar rollover exposed two preexisting test-fixture gaps. The broader
browser assumed the synthetic September week was still the current week;
it now supplies that fixture's dates through supported request parameters,
retaining explicit dates and every original assertion. The CLI journey read
September's brief after writes using the real October clock; it now injects
the existing deterministic clock into real workspace writers. Independent
review cleared both fixes. No production clock or completion rule changed.
Earlier failed logs remain available; failures were not skipped or suppressed.

The packaged launcher has a bounded startup deadline, refuses a missing
configured executable, and does not echo launch credentials in errors.
The self-test now detects a missing capture asset; its intentional failure
probe is included in the passing Manager suite. Windows still uses the
existing windowed-process exit-code check. CI retains read-only repository
permissions and unsigned developer-only artifact labels.

The completed capture worktree remains unchanged: its tracked patch,
status and all 25 untracked implementation-file hashes match the saved
snapshot. Temporary Node dependencies were linked only for task checks;
source checkouts were not cleaned, reset or altered.

## Next action and gates

Run the reviewed combined source on the macOS build runner, inspect its
native self-test and packaged browser results, and verify the resulting
unsigned ZIP/hash receipt. That produces the developer Mac download;
reviewed source publication and remote execution have not occurred here.
Signing/notarization, full runtime notice review, signed candidate evidence,
and offline first launch on actual pilot Macs follow under existing gates.

WeKnora and Paperclip remain open requests. No real provider, agent dispatch,
new telemetry, cloud credential, organization authorization or clinical
release permission was added. Human approval and repository controls remain.
