# Google Workspace Setup Boundary

Use this for a dedicated non-personal Google account when you need Gmail, Drive, Docs, Sheets, Calendar, or Contacts support.

Recommended route:

- Use the Hermes Google Workspace skill.
- Use a dedicated non-personal Google account when possible.
- Complete OAuth through the official Google Cloud / OAuth flow.
- Enable only the APIs required for the workflow.
- Keep a human approval step before sending emails, modifying files, or sharing documents.

Email-only alternative:

- Use email / IMAP-SMTP if you only need mailbox access.
- For Gmail, turn on 2-step verification and use an app password.
- Do not use your normal Google password.

Boundary:

> Do not connect Hermes to personal Gmail, employer Gmail, Drive folders with PHI, confidential HR files, legal documents, or clinical operations folders unless formal governance and approval exist.

Safe first prompt:

```text
Help me set up a dedicated non-personal Google Workspace connection for non-PHI learning and project work.
Before any setup, list the scopes or APIs needed, what data they can access, and the approval boundaries.
Do not send emails, modify files, share documents, or access clinical/employer data without explicit approval.
```
