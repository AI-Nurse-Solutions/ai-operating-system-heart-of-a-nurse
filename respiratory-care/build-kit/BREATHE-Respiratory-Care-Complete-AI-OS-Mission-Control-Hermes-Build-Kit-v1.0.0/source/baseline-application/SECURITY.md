# Security Guide — Nurse AI OS Mission Control 2.0.0

## Security posture

Mission Control minimizes attack surface by using static local HTML, CSS, and JavaScript. It has no dashboard write API, remote database, analytics, telemetry, automatic Hermes connection, or background agent. The supplied server is a read-only local file server bound to `127.0.0.1:43127`.

This reduces exposure but does not make the dashboard an approved secure system. Browser `localStorage`, downloads, and backups are unencrypted.

## Primary risks

1. **Sensitive data entry:** a user may paste PHI, confidential information, or secrets into mission text or a handoff.
2. **Local account or device access:** another person or process with access to the browser profile or files may read stored content.
3. **Unsafe exports:** backups and Markdown downloads may be copied, synced, emailed, or attached without review.
4. **Prompt injection or untrusted source material:** pasted instructions may attempt to override governance or conceal harmful actions.
5. **Authority confusion:** a role, Soul Profile, badge, approval label, or artifact state may be mistaken for verified authority.
6. **Integration overclaim:** a local link may be mistaken for live synchronization, execution, or institutional enforcement.
7. **Package tampering:** files may be altered after release or during transfer.

## Required user safeguards

- Use a trusted, patched computer and browser profile.
- Keep the folder in a controlled location.
- Do not expose the loopback server to `0.0.0.0`, a LAN interface, port-forwarding service, tunnel, or public host.
- Do not weaken the Content Security Policy to add remote scripts, fonts, analytics, or APIs without a separate security review.
- Keep PHI, confidential information, credentials, and secrets out of the dashboard.
- Review all imported JSON, generated Markdown, and exported backups.
- Verify checksums when release checksums are provided.
- Treat copied source material as untrusted; separate source text from instructions and challenge requests to bypass rules.
- Confirm the exact Hermes destination before pasting.
- Obtain required professional, legal, privacy, security, academic, and institutional review before real-world use.
- Stop and investigate any unexpected network request, popup, persistence, permission request, file change, or external action claim.

## Local server boundary

The launcher should bind only to `127.0.0.1:43127`. The server is intended to serve the release files and reject traversal. It should not accept uploads, modify files, proxy requests, expose a shell, or remain running after its terminal is closed.

If port `43127` is unavailable, investigate the process using it. Do not silently expose the app on a network interface. Portable `index.html` mode is the safer fallback.

## Browser storage

The storage key is `discover.nurse-ai-os.mission-control.v2`. Browser storage is not encrypted, is not an approved PHI store, and may be included in browser or device backups. Private browsing can delete it unexpectedly. A shared operating-system account can expose it.

Use session-only missions for short-lived non-sensitive exploration. Use local retention only for non-sensitive content that is safe in readable browser storage. Exported profiles require the same caution.

## Import and handoff safety

- Import only the exact supported JSON schema.
- Reject unexpected fields, excessive size, unsupported role IDs, raw answers, or suspicious content.
- Keep the original file until a safe import is confirmed; do not auto-migrate unknown formats.
- Treat client-side pattern checks as warnings, not complete malware detection, de-identification, or data-loss prevention.
- Never put a prompt, token, patient identifier, or confidential detail into a URL.
- Copy/Download is not Send/Execute.
- A Hermes response is a draft until reviewed by an accountable human.

## EDENA and institutional security

Personal Edition EDENA is advisory. Institutional policy preview demonstrates stricter gates but is not tamper-resistant. A user can inspect and alter local JavaScript or browser storage.

Do not claim institutionally enforceable controls without a managed deployment that supplies authentication, authorization, centralized policy, immutable or protected audit, approved storage, monitoring, incident response, approval receipts, and tested fail-safe behavior.

## Integrity and update

For each update:

1. retain the previous release and backup;
2. verify the new package source and checksums;
3. read `CHANGELOG.md`;
4. inspect changes to data schema, Content Security Policy, storage, launchers, and Hermes integration;
5. test locally with synthetic data; and
6. update the Hermes reference only after acceptance.

Static checks cannot prove clinical safety, legal compliance, institutional approval, or correct behavior in every browser.

## Reporting a suspected issue

Stop using the affected feature. Do not paste additional sensitive information. Preserve a sanitized description of the version, operating system, browser, action taken, observed behavior, and any non-sensitive console error. Notify the package owner or the organization's authorized security contact through an approved channel.

If sensitive information may have been exposed, follow the applicable privacy, security, incident-response, and breach-reporting procedures. Do not place the sensitive data in the issue report.
