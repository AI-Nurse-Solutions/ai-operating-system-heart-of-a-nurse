# MCP Profile Installation and Activation Cards

## Card A — Profile installation (human procedural gate before mutation)

Native Hermes installation does not display or enforce this card, and `--yes` bypasses its generic confirmation. Do not use `--yes`. The human or operating agent must fill every field, display the complete card, and stop before installation. Installation mutates local profile files but remains MCP-inert because every runtime command is blocked.

- Profile: `curator` version `1.0.0`
- Mapped product and lane: `DISCOVER — Healthcare Research & Innovation Leader` / `discover`
- Mapping classification: `adjacent_conditional_not_exact_lane`
- Mapping eligibility condition: Healthcare research or innovation source-curation context only; not generic curation and not an exact DISCOVER lane identity.
- Exact extracted source path: `[required]`
- Exact source-tree SHA-256 inventory: `[required]`
- Exact target profile path: `[required]`
- Existing profile collision and backup result: `[required]`
- Hermes version and compatibility result: `[required]`
- Files that would be copied: `[required]`
- Confirmed inactive MCP count and names: `[required]`
- Confirmed enabled MCP count after install: `0`
- Confirmed exposed MCP tool count after install: `0`
- Credential files created after install: `0` (`.env.EXAMPLE` is non-active)
- Package installs, OAuth flows, network calls, cron jobs, memories, connectors, or external actions authorized: `none`
- Rollback command and exact target: `[required]`
- Unknowns or blockers: `[required]`
- Decision requested: `APPROVE PROFILE INSTALL`, `REVISE`, or `CANCEL`

Download, unzip, role selection, technical access, earlier approval, silence, or timeout is not approval.

## Card B — One MCP activation (required separately for each server)

Hermes must fill every field from current evidence, display the complete card, and stop.

- Profile and exact server: `[required]`
- Resolved package/repository commit or remote service identity: `[required]`
- Registry integrity/checksum verification and complete transitive dependency lock: `[required or BLOCKED]`
- Current maintainer, license, release date, advisories, and unresolved supply-chain risk: `[required]`
- Exact lock-consuming runtime command, arguments, environment keys, network destinations, and local paths: `[required]`
- Exact discovered tool inventory: `[required]`
- Exact proposed allowlist: `[required; never wildcard or omitted]`
- Read, write, destructive, external-send, public-post, and administrative capabilities: `[required]`
- Allowed data: clearly synthetic or public/no-PHI material only
- Prohibited data: patient cases or narratives, PHI, secrets, personnel/evaluation/staffing records, employer-confidential or restricted material
- Credential source, least-privilege scope, storage, rotation, revocation, and deletion: `[required]`
- Provider retention, training/data-use, account, privacy, institutional, and program rules: `[required]`
- Human approval points and destination previews: `[required]`
- Test workspace and synthetic negative probes: `[required]`
- Rollback, token revocation, cache cleanup, service-side deletion, and evidence receipt: `[required]`
- Expiry/re-review date: `[required]`
- Unknowns or blockers: `[required]`
- Decision requested: `APPROVE EXACT MCP ACTIVATION`, `REVISE`, or `CANCEL`

Approval applies only to the exact server, package/remote identity, command, tools, paths, credentials, destinations, data boundary, and expiry shown. Any change invalidates approval.
