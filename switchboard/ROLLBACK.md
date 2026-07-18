# Switchboard publication rollback

Use this procedure if the published Switchboard introduces a broken route, misleading governance claim, privacy regression, inaccessible interaction, or package-integrity failure.

1. Stop promotion and record the observed failure, affected URL, browser, and time. Do not collect user configuration or PHI.
2. Revert the single release commit through a reviewed pull request. Do not rewrite shared history.
3. Wait for the GitHub Pages deployment sourced from `main` to complete.
4. Verify that `/switchboard/` is removed or restored to the last known-good version on both the custom domain and GitHub Pages origin.
5. Verify the Setup Helper, post-setup page, privacy policy, sitemap, and README no longer contain broken Switchboard links or stale claims.
6. Re-run the package manifest and checksum tests to confirm every existing Role Pack distribution remains byte-for-byte unchanged.
7. Record the cause, correction, verification evidence, and decision owner before attempting a new release.

Rollback never deletes a visitor’s browser-local configuration. If a schema must be retired, publish clear local-data export and clearing instructions before removal.
