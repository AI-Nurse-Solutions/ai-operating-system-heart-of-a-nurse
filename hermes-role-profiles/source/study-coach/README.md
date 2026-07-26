# NAIO Study Coach Hermes MCP profile companion

**Profile:** `study-coach`

**Version:** `1.0.0`

**Mapped product:** FUTURE — Nursing Student & Nursing Assistant

**Mapping classification:** `direct_pathway_only`

**Mapping condition:** Nursing Student pathway only; not automatically Nursing Assistant or Bridge.

**Hermes compatibility:** `>=0.19.0`

Downloading or unzipping does not install, connect, or activate anything. This is a local profile distribution for read-only inspection first. It is not a sandbox, clinical system, credential, institutional authorization, or proof that an upstream MCP is safe for a specific environment.

## What is included

- Role boundary: `SOUL.md`
- Inactive MCP definitions: authoritative runtime state in `config.yaml`; `mcp.json` is a matching publication-time audit snapshot only
- Archive-native top-level candidate pins and known exception: `MCP-SUPPLY-CHAIN-LOCK.json`. These are not a transitive lock or activation-ready runtime.
- Blank credential template: `.env.template` (installed by Hermes as `.env.EXAMPLE`, never as an active `.env`)
- Required human gates: `MCP-ACTIVATION-CARD.md`
- Review skill: `skills/review-mcp-activation/SKILL.md`

Declared MCP candidates: obsidian, filesystem, google_workspace. All are `enabled: false`, use the guaranteed-missing runtime command `__NAIO_MCP_ACTIVATION_BLOCKED__`, use the nonmatching deny sentinel `__NAIO_NO_MCP_TOOLS_APPROVED__`, and disable MCP resources, prompts, sampling, and elicitation. Original package/URL definitions are non-executable `candidate` metadata. Nothing can resolve, connect, request an LLM completion, collect mid-call input, or expose a tool until a human separately approves and installs a lock-consuming runtime, then changes every required condition.

Native `hermes profile install` does not display or enforce the bundled card, and `--yes` bypasses its generic confirmation. Card A is therefore an explicit human procedural gate, not a technical installer control. Do not use `--yes`. Installation writes local profile files but still cannot activate an MCP because every published runtime command is blocked.

Hermes reads `config.yaml:mcp_servers` at runtime. `mcp.json` is audit evidence, not a second authority. After any profile update, re-check parity; never infer that a refreshed `mcp.json` changed effective runtime behavior.

## Required sequence

1. Verify this ZIP against `hermes-role-profiles/CHECKSUMS.sha256`.
2. Extract it into a personal no-PHI location.
3. Give the complete extracted folder to Hermes and request: **“INSPECT THIS MCP PROFILE ONLY — CREATE NO STATE.”**
4. Hermes reads `MCP-ACTIVATION-CARD.md`, verifies local bytes and prerequisites, displays the exact Profile Installation Card, and stops.
5. Only after explicit approval may the human run `hermes profile install <exact-extracted-folder> --name study-coach --alias`.
6. Installation still leaves every MCP disabled with zero tools. Do not create `.env`, install packages, authenticate, or connect anything during profile installation.
7. Any later MCP activation requires its own exact card and a fresh approval. In a disposable test copy, first replace the blocker with a reviewed runtime command that consumes a complete transitive lock. Then use `hermes -p study-coach mcp configure <exact-server-name>` during that separately approved activation review; enumerate and allowlist exact tools before enabling that server.
8. Restart Hermes or use the supported `/reload-mcp` flow only after the approved configuration change.

## Removal

Use `hermes profile delete study-coach` only after reviewing what local profile state will be removed. Upstream OAuth grants, tokens, package caches, service-side data, and provider sessions may require separate revocation or deletion; profile deletion does not prove those were removed.
