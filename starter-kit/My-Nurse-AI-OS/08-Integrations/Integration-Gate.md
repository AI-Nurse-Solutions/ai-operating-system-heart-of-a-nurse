# Integration Gate

Every connector is a doorway. Open only the doors you need, with the least privilege required, and keep a human owner responsible for review. Notion counts as a connector even when it starts manually: it can become the team's shared memory, so it needs the same no-PHI and human-review discipline.

Before adding any integration, answer:

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
