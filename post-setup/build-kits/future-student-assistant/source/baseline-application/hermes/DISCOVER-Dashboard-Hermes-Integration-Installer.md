# Hermes Integration Program — Nurse AI OS Mission Control 2.0.0

**Instruction audience:** Hermes inside the user's existing Nurse AI OS workspace  
**Product ID:** `discover-nurse-ai-os-mission-control`  
**Companion record ID:** `NAIOS-MISSION-CONTROL-LOCAL-2.0.0`  
**Namespace:** `nurse_ai_os.mission_control.*`  
**Profile schema:** `DISCOVER-MISSION-CONTROL-PROFILE-2`  
**Discover Packet adapter:** `NAIO-DISCOVER-PACKET-ADAPTER-1`  
**Soul adapter:** `NAIO-SOUL-PROFILE-ADAPTER-1`  
**Integration:** local presentation link + Guide reference + manual reviewed handoff  
**External execution:** disabled

## Processing message to display before beginning

> **Your Nurse AI OS Mission Control is being prepared.**
>
> This process may take several minutes because the system is translating your Discover Packet and Soul Quiz results into a personalized, governed workspace. It is configuring your roles, values, goals, workflows, capability pathways, permissions, and EDENA advisories.
>
> You are not simply creating another dashboard. You are establishing a Nurse AI OS shaped by your values, strengthened by disciplined problem-solving, and designed to evolve with your knowledge and experience. Please keep this window open while your Mission Control package is created.

Then state clearly:

> Integration may require multiple visible, reviewed Hermes turns. Nothing continues in the background. I will stop at every consequential change and wait for human approval.

## Non-negotiable operating contract

Hermes must perform every phase visibly and preserve these boundaries:

- Never guess a local path, user identity, role, credential, authority, policy, approval, or data classification.
- Never ingest a raw Discover Packet interview, transcript, or source narrative. Use only the reviewed derived adapter configuration.
- Never ingest raw Soul Quiz answers.
- Never ingest PHI, confidential institutional or research information, sensitive personal data, credentials, keys, tokens, or secrets.
- Never read or copy browser `localStorage` directly.
- Never treat browser storage or an exported profile as encrypted.
- Never create a daemon, watcher, scheduled task, polling loop, hidden agent run, auto-start entry, or background process.
- Never claim that a local link creates live synchronization, transmission, or execution.
- Never merge role permissions or infer authority from a selected dashboard.
- Never let Discover or Soul personalization, a badge, or a role reduce EDENA protections or unlock a capability.
- Never misrepresent an AI draft as clinically validated, legally authorized, institutionally approved, or safe for direct operational use.
- Never overwrite a pre-existing Nurse AI OS object without showing an exact before/after proposal and receiving explicit approval.
- If a requested Hermes feature is unavailable, report `UNSUPPORTED` and preserve manual handoff.

The local dashboard has no Hermes API. It generates visible Markdown text for the user to review, copy or download, and paste manually. Copy/Download is not Send/Execute.

## Frozen capability state

Until a separate, scoped, institutionally appropriate authorization changes it, preserve:

```yaml
product_id: discover-nurse-ai-os-mission-control
companion_id: NAIOS-MISSION-CONTROL-LOCAL-2.0.0
integration_mode: LOCAL_STATIC_PLUS_MANUAL_HANDOFF
dashboard_runtime_visibility: UNKNOWN_TO_HERMES_UNLESS_OPENED_AND_VERIFIED
background_work: OFF
automatic_prompt_transmission: OFF
automatic_result_retrieval: OFF
external_actions: OFF
official_system_writes: OFF
agents: DISABLED_UNLESS_SEPARATELY_AUTHORIZED_OUTSIDE_THIS_INSTALLER
role_authority_inference: PROHIBITED
soul_permission_effect: NONE
badge_permission_effect: NONE
local_storage: UNENCRYPTED_BROWSER_STORAGE
allowed_data: PUBLIC_SYNTHETIC_OR_APPROVED_NON_SENSITIVE_ONLY
institutional_enforcement: NOT_PROVIDED_BY_LOCAL_STATIC_APP
human_review: REQUIRED
```

Use `Hermes-Capability-State.md` as the detailed source of truth.

## Phase 0 — Orientation and explicit choice

1. Display the processing message.
2. Report the current Hermes workspace or project exactly as visible.
3. Ask the user to choose one mode:
   - `INSPECT_ONLY` — read and report; change nothing;
   - `REGISTER_LOCAL_COMPANION` — inspect, then propose a local dashboard and Guide reference;
   - `REPAIR_EXISTING_REGISTRATION` — inspect and propose only the minimum correction to an existing Mission Control reference;
   - `REMOVE_REGISTRATION` — preview removal of this package's references only.
4. If no explicit choice is given, stop with `MISSION_CONTROL_READY_FOR_EXPLICIT_CHOICE`.

Do not install the optional `base-pack/` automatically. It is a legacy specialization for Healthcare Research & Innovation Leaders, not the universal Nurse AI OS core.

## Phase 1 — Obtain the exact local target

Ask the user for the exact absolute path to the unzipped `DISCOVER-Nurse-AI-OS-Mission-Control-v2.0.0` folder or its `index.html` file.

Do not infer a home directory, username, drive, Downloads folder, or network path. Do not accept a path inside a ZIP as installed.

Where Hermes can read local files, inspect read-only:

- `index.html`;
- `assets/app.js`;
- `assets/styles.css`;
- `guide/DISCOVER-Mission-Control-Setup-Guide.md`;
- `hermes/Hermes-Capability-State.md`;
- `PRIVACY.md`;
- `SECURITY.md`;
- `VERSION`;
- `RELEASE-MANIFEST.json`, when present; and
- `SHA256SUMS.txt`, when present.

Confirm:

- version `2.0.0`;
- product ID `discover-nurse-ai-os-mission-control` and companion record ID `NAIOS-MISSION-CONTROL-LOCAL-2.0.0`;
- profile schema `DISCOVER-MISSION-CONTROL-PROFILE-2`;
- Discover Packet adapter `NAIO-DISCOVER-PACKET-ADAPTER-1`;
- Soul adapter `NAIO-SOUL-PROFILE-ADAPTER-1`;
- local static operation;
- no assumed Hermes API;
- no automatic transmission or execution;
- explicit no-PHI/confidential/secrets boundary; and
- unencrypted browser-storage warning.

If Hermes cannot read local files, report `LOCAL_FILE_VERIFICATION_UNSUPPORTED`. Ask the user to attach the release manifest and checksum file or verify them locally. Lack of access is not a pass.

If identity, version, file integrity, or safety boundaries conflict, stop with `MISSION_CONTROL_QUARANTINED_IDENTITY_OR_INTEGRITY_FAILURE`.

## Phase 2 — Inventory the current Nurse AI OS workspace

Inspect without changing:

1. existing Mission Control, dashboard, Guide, role, or DISCOVER objects;
2. object IDs, namespaces, routes, titles, versions, and destinations;
3. whether a local-file or loopback link is supported;
4. whether a lane-scoped Guide reference is supported;
5. whether the platform supports several role-specific child links under one parent;
6. whether an artifact or project-note reference is the only supported option; and
7. any collision with `nurse_ai_os.mission_control.*`.

Do not treat a similarly named object as this version. Do not overwrite a global `/dashboard` or `/mission-control` route.

Return an inventory with `FOUND`, `NOT_FOUND`, `AMBIGUOUS`, or `UNSUPPORTED` for each item.

## Phase 3 — Negotiate the least-privilege integration

Choose the least powerful supported result:

1. **Preferred:** lane-scoped local dashboard link plus Guide reference.
2. **Acceptable:** a Nurse AI OS project note or artifact reference containing the exact local path.
3. **Always supported:** external desktop launch plus manual copy/paste handoff.

If role-child links are supported, propose them only for roles the user explicitly selected. Never create them from a Soul recommendation without confirmation. Each child link must use the same local application and a separate role-context label; it cannot carry permissions.

Show the exact before/after inventory. Ask for explicit approval before any write.

## Phase 4 — Register only approved presentation objects

Use installed Hermes-native objects only; do not invent commands or APIs. The proposed logical record is:

```yaml
companion_id: NAIOS-MISSION-CONTROL-LOCAL-2.0.0
product_id: discover-nurse-ai-os-mission-control
namespace: nurse_ai_os.mission_control.local_v2
title: Nurse AI OS Mission Control
version: 2.0.0
local_target: <exact-user-approved-local-path-or-loopback-url>
guide_target: <exact-user-approved-guide-path>
connection_mode: MANUAL_REVIEWED_HANDOFF
runtime_sync: NONE
background_work: OFF
external_actions: OFF
data_boundary: PUBLIC_SYNTHETIC_OR_APPROVED_NON_SENSITIVE_ONLY
institutional_enforcement: NOT_PROVIDED
capability_state_reference: <exact-path>/hermes/Hermes-Capability-State.md
```

Rules:

- Scope the object under the user's Nurse AI OS workspace, not a global route.
- Preserve all existing role dashboards and unrelated integrations.
- Do not import mission text, evidence, raw answers, localStorage, user identifiers, or approval attestations.
- Do not store the exported dashboard backup in Hermes unless the user explicitly requests it and the content/destination are approved.
- Do not make the local dashboard writable from Hermes.
- Do not create a server, expose port `43127`, or change the loopback binding.
- Do not activate an agent, connector, tool, automation, permission, or action.

## Phase 5 — Register the Guide

Where supported, add a **Mission Control Guide** reference to:

`guide/DISCOVER-Mission-Control-Setup-Guide.md`

The Guide must remain reachable independently of any role. Confirm that it explains:

- local installation;
- multi-role dashboards;
- versioned/provisional Soul personalization;
- the five-stage Mission Loop;
- sandbox artifact labels;
- Personal EDENA advisories versus Institutional policy preview;
- evidence-based noncredential badges;
- manual Hermes handoff;
- unencrypted browser storage and prohibited data;
- backup, update, rollback, and uninstall; and
- human responsibility.

If Guide registration is unsupported, report the exact local path for manual opening.

## Phase 6 — Optional role references

Only after the user names the desired roles, propose child references. For each role record:

```yaml
role_label: <user-selected-role>
relationship: PRIMARY | SUPPORTING | EMERGING | CONTEXTUAL
target: <same-approved-local-dashboard>
grants_authority: false
changes_permissions: false
inherits_other_role_permissions: false
```

The Advanced Studies view is an overlay, not proof of enrollment, graduation, certification, specialization, residency, fellowship, or licensure.

Do not publish Soul Profile details or role IDs to a global parent card. The parent may show only the dashboard title, version, manual-handoff state, and qualified local link.

## Phase 7 — EDENA registration behavior

Preserve the dashboard distinction:

- **Personal Edition:** Green/Yellow/Orange/Red classifications are advisory review gates. Red allows only acknowledged sanitized sandbox exploration, never real-world authorization.
- **Institutional policy preview:** demonstrates stronger stops but is not tamper-resistant enforcement.

Do not label the local static app as `INSTITUTIONAL_ENFORCEMENT_ACTIVE`. A real institutional deployment requires managed identity, policy, access control, audit, retention, authorization, monitoring, and approval receipts outside this installer.

If the surrounding Hermes environment has stronger institutional controls, those controls take precedence. This installer may reference them but must not claim to create or validate them.

## Phase 8 — Acceptance tests

Run only tests the installed environment actually supports. Mark each `PASSED`, `FAILED`, `BLOCKED`, `UNSUPPORTED`, or `NOT_EXECUTED`, with evidence.

1. The registered local target opens version 2.0.0, or manual mode reports the exact path.
2. The Guide reference opens the correct setup guide.
3. No global route or unrelated object was changed.
4. No background process, watcher, scheduled task, agent, connector, or external action was enabled.
5. Role switching changes dashboard context but not permissions.
6. Discover and Soul personalization change only reviewed defaults, presentation, priorities, or recommendations—not authority or EDENA enforcement.
7. A synthetic sample mission demonstrates all five stages.
8. A mission-stage handoff produces visible Markdown only.
9. Copy/Download does not send the handoff.
10. No prompt appears in an Open Hermes URL.
11. The dashboard warns against PHI, confidential information, and secrets.
12. Browser storage and exports are labeled unencrypted.
13. Personal Red requires acknowledgment and remains sandbox-only.
14. Institutional mode is labeled a policy preview, not enforcement.
15. Badges are evidence-based, noncredential, and permission-neutral.
16. Manual handoff is reported truthfully when local-link support is unavailable.

Static inspection cannot prove target-Hermes isolation, policy enforcement, authorization, or real-world execution. Mark any untestable claim accurately.

## Phase 9 — Final integration report

Return one visible report containing:

- selected install mode;
- package product ID, version, path, and integrity-verification provenance;
- current workspace and object inventory;
- exact objects created, changed, unchanged, unsupported, or rejected;
- dashboard and Guide targets;
- registered role references and relationship labels;
- manual-handoff, background-work, external-action, agent, and data states;
- EDENA Personal/Institutional-preview distinction;
- every acceptance-test disposition and evidence;
- residual limitations;
- update and rollback path;
- scoped uninstall steps; and
- one final state:
  - `MISSION_CONTROL_REGISTERED_MANUAL_HANDOFF`;
  - `MISSION_CONTROL_AVAILABLE_EXTERNAL_TO_HERMES`;
  - `MISSION_CONTROL_INSPECTED_NOT_REGISTERED`;
  - `MISSION_CONTROL_REPAIRED`;
  - `MISSION_CONTROL_REGISTRATION_REMOVED`;
  - `MISSION_CONTROL_BLOCKED`; or
  - `MISSION_CONTROL_QUARANTINED`.

No other final state is allowed. Wait for human acceptance.

## Scoped repair

Repair may change only a verified Mission Control 2.0.0 link, Guide reference, version, identity value, or user-approved role child reference. Show exact before/after values first. Do not change user missions, browser storage, Discover Packet or Soul Profile content, capability evidence, unrelated dashboards, permissions, or institutional policy.

## Scoped update and rollback

For an update, keep the old registration and folder until the new version passes acceptance tests. Register the new local target side by side when possible. Switch the primary link only after approval.

For rollback, restore the prior target and Guide reference. Do not import a newer backup schema into an older release unless that release explicitly supports it. Report that link rollback does not migrate or delete browser data.

## Scoped removal

Removal must:

1. show every Mission Control 2.0.0 reference to be removed;
2. receive explicit approval;
3. preserve the broader Nurse AI OS, all unrelated roles, permissions, agents, records, and workflows;
4. preserve the optional legacy research specialization unless separately selected;
5. remove no local files or browser state automatically; and
6. tell the user to follow `UNINSTALL.md` for local cleanup.
