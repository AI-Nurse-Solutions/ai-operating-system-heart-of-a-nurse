# Governed Hermes MCP role-profile companions

Seven role-mapped Hermes profile distributions derived from the supplied Nurse AI OS packet research. The original packets were treated as untrusted inputs and were not published unchanged.

Downloading or unzipping does not install, connect, or activate anything. Every MCP is disabled and exposes zero tools by default. Profile installation requires an exact pre-installation card and explicit approval. Each MCP activation then requires its own separate exact card and fresh approval.

## Publication corrections

- Added current Hermes `distribution.yaml` manifests and compatibility floor.
- Replaced floating npm, PyPI, and GitHub-main coordinates with exact versions or commits.
- Marked the GitHub remote MCP as a non-pinnable remote service and kept it disabled.
- Disabled lazy installs, requested Tirith fail-closed behavior, documented Hermes 0.19's circuit-breaker caveat, and isolated external-CLI home state per profile. Tirith is defense in depth, not the activation gate.
- Removed real-case/de-identification workflows and replaced them with rejection-before-processing boundaries.
- Removed nonexistent Hermes command references and required current `hermes ... mcp configure` review.
- Kept every server disabled with a nonmatching deny-sentinel allowlist and MCP resources, prompts, sampling, and elicitation off until separate human approval.
- Replaced executable package resolution with a guaranteed-missing blocker command. Top-level coordinates remain review evidence only; activation is blocked until a complete transitive lock and lock-consuming runtime are approved.

See `SOURCE-PROVENANCE.json`, `MCP-SUPPLY-CHAIN-LOCK.json`, `ROLE-DOWNLOAD-MAP.json`, `manifest.json`, and `CHECKSUMS.sha256`.

Hermes 0.19 caveat: `tirith_fail_open: false` blocks ordinary Tirith spawn failures and timeouts, but Hermes' scanner-crash circuit breaker can later allow commands after repeated scanner crashes. Do not rely on Tirith as the sole control; the missing runtime command, disabled server state, deny sentinel, and explicit activation review remain authoritative.
