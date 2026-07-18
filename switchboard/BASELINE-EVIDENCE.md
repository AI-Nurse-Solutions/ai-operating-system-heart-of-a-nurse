# Nurse AI OS Switchboard Baseline Evidence

**Baseline:** `origin/main` at `ed41b5d3bcc72ac24f86df3990f2380764e294be`

**Captured:** 2026-07-17
**Status:** Read-only inventory for the browser-local Switchboard preview

## Verified implementation at baseline

- `setup-helper/setup-helper-model.mjs` stores one `identityRole` and one `postSetupLane` under schema version 1.
- `tests/test_setup_helper.py` requires exactly four broad identities and six post-setup lanes.
- `post-setup/downloads/manifest.json` lists six nurse role packages.
- Existing role downloads declare `install_on_download: false` and preserve inactive optional features.
- `healthcare-research-innovation-leaders/packages/discover/ROLE-PACK.json` publishes DISCOVER as a separate healthcare research and innovation leadership lane.
- `privacy.html` discloses browser-local Setup Helper state.
- `.github/workflows/setup-helper.yml` runs deterministic tests, JavaScript syntax checks, and a public safety scan.

## Gap addressed by this branch

The baseline cannot represent one person holding several roles across facilities, departments, committees, schools, shifts, or community settings. It also cannot treat DISCOVER and FUTURE as additive capabilities or accept new nursing roles through a governed extension contract.

## Compatibility boundary

This preview must not change bytes or stable URLs under:

- `post-setup/packages/`
- `post-setup/downloads/`
- `healthcare-research-innovation-leaders/packages/discover/`
- `healthcare-research-innovation-leaders/downloads/`

The browser preview may link to those releases as references. It must not install, merge, rewrite, or activate them.

## Status language

- Existing packages: **live distribution**, not installed by this preview.
- Switchboard: **browser-local architecture preview**.
- Role registry draft entries: **documentation-only and inactive**.
- Hermes profile composition: **not implemented in this release**.
- Credential, assignment, and institutional authority: **not verified**.
- Runtime PHI interception and clinical safety: **not claimed**.
