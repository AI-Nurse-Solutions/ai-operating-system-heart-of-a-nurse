
# Start Here — Medical Resident ROUNDS Mission Control

This download gives Hermes the complete materials needed to build `My ROUNDS`. It is not the finished application.

## Five-minute start

1. Keep the original ZIP unchanged as a recovery copy.
2. Do not add PHI, a real case, clinical images or recordings, formal evaluations, peer-review/event material, credential secrets, or restricted institutional information.
3. Extract a private working copy and run `python3 tools/verify-build-kit.py --package .`.
4. Give Hermes the complete extracted folder—not selected files.
5. Paste the instruction from `README-FIRST.md`.
6. Review the Implementation Activation Card and choose **Approve**, **Revise**, or **Cancel**.
7. Keep the S0–S4 checkpoint receipts. The build may take several visible turns.
8. Accept the application only after the final report states what was built, tested, blocked, and supported.

## Intended finished product

- one isolated `medical_resident` lane at `/medical-residents` and one `My ROUNDS` home;
- the exact Core Four and an empty optional fifth launcher;
- five protected record scopes inside the one home—not five dashboards or authority silos;
- 24 ROUNDS powers `Available Inactive`, 24 workflows `Preview Only`, and 30 templates;
- ten governed agent definitions, all `PERM-P0 Disabled`;
- a five-stage Assess → Define → Plan → Implement preparation → Evaluate loop;
- Guides, sources, capability evidence, privacy, memory, diagnostics, recovery, and accessible degraded mode.

## Honest completion states

- **Operational** — all 424 records are reconciled, with zero Not Run, Failed, Blocked, or Not applicable results; genuine authenticated incremental streaming and server-work cancellation pass through the downloaded UI.
- **Core operational; AI setup pending** — all 424 records are reconciled, with zero Not Run or Failed results and zero Blocked results outside the exact live-backend-only set; the controlled-unconfigured AI path passes. Only `CTL-AI-002` through `CTL-AI-007` and `INT-044` may remain Blocked, solely because no configured backend was available.
- **Not operational** — every other condition, including any extra Blocked row, any Failed or Not Run row, or a live-AI blocker for any reason other than the exact absent-configured-backend condition.

Until Hermes evidences one of those states, readiness remains `not_operational_build_required`.
