# Integration Gate

Every connector is a doorway. Open only the doors you need, with the least privilege required, and keep a human owner responsible for review. Notion counts as an advanced connector even when it starts manually: it can become the team's shared memory, so it needs the same no-PHI and human-review discipline. Start with the Local HTML dashboard first when the user only needs a simple personal dashboard.

Before adding any integration, answer:

0. Has it passed the Skill & MCP Vetting Checklist (`Skill-and-MCP-Vetting-Checklist.md`) — named publisher, pinned version, read before run?
1. What account or folder is being connected?
2. What data can Hermes read?
3. What data can Hermes write or modify?
4. Can Hermes send messages, emails, invites, files, or links?
5. What is the approval gate before consequential action?
6. What should never pass through this connector?
7. How do I revoke access?
8. Who is the accountable human owner?
9. What logs or audit trail will I review?
10. What is the safe fallback if the integration fails?

Default boundary:

> No PHI, patient-specific care, confidential employer systems, secrets, API keys, legal decisions, financial transactions, or public publishing without explicit review.

Notion-specific boundary:

> Use Notion for operations, learning, governance review, and coordination. Do not use it as an EHR, clinical documentation system, clinical decision support tool, credentialing authority, care coordination platform, or storage place for passwords, API keys, tokens, PHI, or patient-specific information.


Local HTML Life Dashboard first boundary:

> The local HTML dashboard is Green only when it stays browser-only, personal, no-PHI, no-secrets, and manually reviewed. Bookmark it under **Dashboards** for access, but do not use it as a clinical, financial, employer, family-surveillance, or automated decision system.

Notion Life Dashboard Pack advanced boundary:

> The Notion Life Dashboard Pack for health, finances, goals, habits, tasks, and routines is Green only when it stays personal, no-PHI, and manually reviewed. Add a human gate before sharing, syncing wearables/banks/calendars, adding API automation, or using any trend to make health, financial, work, family, or clinical decisions.
