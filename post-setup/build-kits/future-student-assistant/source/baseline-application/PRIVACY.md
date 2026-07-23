# Privacy Notice — Nurse AI OS Mission Control 2.0.0

## Local-first design

Mission Control is a static local application. It does not require an account, remote database, analytics service, tracking pixel, remote font, CDN, or automatic Hermes connection. Its content security policy is designed to block dashboard network connections.

The optional launcher serves files only on the computer's loopback interface, `127.0.0.1:43127`. It is not intended to expose the dashboard to a local network or the internet.

## Information the dashboard may retain

Depending on the user's choices, browser `localStorage` may contain:

- app and profile version information;
- a random local instance identifier;
- selected roles and their primary/supporting/emerging/contextual relationships;
- per-role dashboard preferences and favorites;
- an applied derived Discover Packet configuration;
- an applied derived Soul Profile and a restorable prior derived profile;
- locally retained non-sensitive missions and stage text;
- capability-evidence records;
- Guide/onboarding state; and
- display settings.

Locally saved content is **not encrypted** by this application. Anyone with access to the browser profile, computer account, exported file, device backup, or synced folder may be able to read it.

Session-only missions are kept for the active page session and are not intentionally written to persistent dashboard storage. Closing or reloading the page can discard them. Session-only mode is not a secure processing environment and does not make prohibited data acceptable.

## Discover Packet and Soul Profile privacy

The Discover Packet adapter is versioned as `NAIO-DISCOVER-PACKET-ADAPTER-1`. It stores only reviewed, derived settings such as mission language, values, priorities, goals, working preferences, role goals, workflow recommendations, AI boundaries, and governance defaults. Do not import raw interview notes, source transcripts, identifying narratives, or sensitive material. Preview every proposed setting before applying it.

The Soul adapter is versioned as `NAIO-SOUL-PROFILE-ADAPTER-1`. It is designed for derived results, not raw quiz responses. The legacy 12-question demonstration scores in the browser and is intended to discard raw answers after scoring.

Do not import raw answers, narratives containing sensitive personal information, or hidden assessment data. Preview every Soul Profile before applying it. The quiz is provisional and should not be used for psychological, employment, educational, credentialing, or competence assessment.

## Mission and evidence privacy

Mission text, approval references, stage notes, outcomes, and capability evidence are user-entered. The application cannot know every sensitive phrase. Pattern warnings are incomplete and are not de-identification, data-loss prevention, or policy enforcement.

Use public, synthetic, or explicitly approved non-sensitive information only. Do not enter:

- PHI or patient identifiers;
- participant-level research information;
- confidential institutional, personnel, academic, sponsor, legal, contract, financial, peer-review, or invention information;
- passwords, API keys, tokens, access links, connection strings, or secrets; or
- sensitive personal information.

## Exports and downloads

Dashboard backups, Discover and Soul templates, capability reports, and Hermes handoffs are ordinary readable files. They are not encrypted, automatically redacted, or access-controlled by this package. Review every file before saving, syncing, attaching, or sharing it.

An exported dashboard backup may contain role, derived Discover Packet, Soul Profile, mission, and capability-evidence text. Store it only where that content is permitted. Delete obsolete exports intentionally.

## Hermes handoff

The dashboard generates Markdown locally. It does not automatically send a prompt to Hermes or retrieve a response. The user chooses whether to copy/download, opens Hermes separately, selects the destination, pastes the text, and reviews the response.

The optional Open Hermes control opens only the address the user supplies for that session. Prompt content must not be placed in the URL.

Once information is pasted into Hermes, the privacy and retention rules of that Hermes deployment apply. Confirm those rules before pasting.

## User controls

The user can:

- select session-only instead of local retention for a mission;
- delete a mission or capability evidence;
- clear an applied Discover Packet;
- clear or restore a Soul Profile;
- export a readable backup for inspection;
- reset all local personalization; and
- uninstall the package and remove backups.

See `UNINSTALL.md` for cleanup steps. Browser-level backups, enterprise device backups, downloaded files, or copies shared elsewhere are outside this application's deletion control.

## Institutional use

The Institutional policy-preview setting does not create managed privacy controls. A real institutional deployment requires approved architecture, data classification, identity, access control, encryption, retention, audit, legal review, incident response, and technical validation appropriate to the intended use.
