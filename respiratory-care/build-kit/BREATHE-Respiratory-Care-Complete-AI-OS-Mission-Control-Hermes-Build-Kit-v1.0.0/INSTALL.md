
# Installation and Hermes handoff

## Owner preparation

1. Keep the downloaded ZIP as a read-only recovery copy.
2. Require the trusted `CHECKSUMS.sha256` sidecar and verify the downloaded ZIP against it before extraction. Stop if the sidecar is missing, cannot be authenticated as the publisher's release ledger, or does not match.
3. Extract into a private local folder that does not synchronize to an unapproved service.
4. Run `python3 tools/verify-build-kit.py --package .`.
5. Give the entire folder to Hermes; do not paste only selected pages.

## Hermes sequence

Hermes must use a copy-on-write path and show one Activation Card before mutation. The controlled build order is:

1. S0 — verify sources, environment, paths, permissions and rollback.
2. S1 — build and test the durable offline Respiratory Care Professional foundation.
3. S2 — add the 24-power BREATHE overlay inactive and test isolation/removal.
4. S3 — add genuine provider integration, evidence, consent memory and bounded agents.
5. S4 — execute the complete 424-record inventory and package the application.

The process may take several turns. A checkpoint is not completion.

## Backup and rollback

- Preserve the original source ZIP and pre-install snapshot.
- Back up the application database, permitted attachments, configuration, migration state and manifest as one atomic set.
- Test restore into a separate path before relying on it.
- Roll back a failed BREATHE overlay to the healthy foundation checkpoint S1.
- Roll back a failed full build to S0.
- BREATHE-only removal must not change foundation or unrelated data.
- Full uninstall preserves only the user-approved export and unrelated work.
