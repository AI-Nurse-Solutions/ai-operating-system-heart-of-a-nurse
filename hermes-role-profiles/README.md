# Governed Hermes MCP role-profile companions

Seven role-mapped Hermes profile distributions derived from the supplied Nurse AI OS packet research. The original packets were treated as untrusted inputs and were not published unchanged.

Downloading or unzipping does not install, connect, or activate anything. Every MCP is disabled and exposes zero tools by default. Profile installation requires an exact pre-installation card and explicit approval. Each MCP activation then requires its own separate exact card and fresh approval.

## One architecture, three different jobs

- **SOUL tells Hermes who it serves:** the user's approved purpose, roles, preferences, memory choices, boundaries, and human red lines. It personalizes assistance but never proves authority.
- **Mission Control turns intention into governed work:** role-specific priorities, projects, learning, evidence, approvals, and progress. It comes from the separate role build kit; these MCP companions do not build it.
- **MCP defines what Hermes may eventually reach:** approved tools and information under least privilege. In this release every candidate remains blocked, disabled, and tool-denied.

Giving a companion ZIP to Hermes starts read-only inspection only. It does not import a SOUL, build Mission Control, install a profile, authenticate, connect, remember, schedule, or act.

## Why each role companion matters

| Profile | Nurse AI OS significance | Conditional connection value |
|---|---|---|
| Study Coach | Builds disciplined study, reflection, and academic-integrity habits before clinical authority is at stake. | Approved personal learning notes, files, calendar, and documents for reviewed study preparation. |
| Curator | Converts information overload into traceable, claim-versus-proof signal intelligence. | Approved knowledge vault and bounded public-source retrieval for drafts that Hermes does not publish. |
| Builder / Operator | Carries healthcare innovation from problem framing to testable, versioned artifacts with human release gates. | Approved workspace, documents, and repository inspection for bounded change preparation—not merge or deployment. |
| Manager / Lead | Converts leadership pressure into clearer priorities, accountable plans, and visible follow-through without creating a shadow HR system. | Approved files, documents, calendar, and spreadsheet drafts without workforce records or organizational action. |
| Administrator / Pilot Operations | Provides a rehearsal space for safer pilots before proposals touch live people or systems. | Approved files, forms, documents, and calendar preparation while live intake and institutional systems stay out of scope. |
| Clinician — Nurse Practitioner | Strengthens evidence fluency and professional growth without becoming a clinical decision system. | Approved public literature and bounded personal work materials; no patient cases, diagnosis, treatment, or prescribing. |
| Clinician — Medical Resident | Supports evidence study, research preparation, and longitudinal formation while preserving supervision. | Approved public literature and bounded personal work materials; no charts, sign-out, evaluation, entrustment, or clinical decisions. |

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
