
# Security and Privacy Checklist

- [ ] Loopback-only binding; authenticated owner; server-owned secure session
- [ ] CSRF, Origin, Host, cookie, session rotation, timeout, and brute-force controls
- [ ] Secrets remain server-side and outside logs, exports, backups, prompts, and UI
- [ ] App data root and every database/attachment/log/export/temp path are owner-only: POSIX directories `0700`, files `0600`, or equivalent verified current-owner/System-only Windows ACL
- [ ] Effective path permissions are rechecked after install, restore, update, rollback, restart, and clean-machine setup; no application-layer encryption claim exists without implementation evidence
- [ ] Backups use a verified encrypted destination or tested encrypted archive with a separately stored key; secrets, keys, sessions, raw profile identity, and rejected payloads are excluded
- [ ] Data admission occurs before echo, transformation, persistence, provider, agent, tool, search, memory, backup, or export
- [ ] PHI, real/name-removed cases, clinical media, sign-outs, events, evaluations, restricted exams, secrets, and unknown content leave no residue
- [ ] No request for more clinical detail after rejection; emergency route remains immediate
- [ ] No clinical, institutional, evaluation, QI/research, communication, prescribing, ordering, coding, billing, claim, or credential executor
- [ ] One resident lane; purpose-bound record scopes; partition-scoped queries and exports
- [ ] Institutional routes, stores, toggles, connectors, and P3/P4 transitions are absent/disabled
- [ ] Whole-life data excluded from program/employer views, analytics, badges, and institutional exports
- [ ] Upload type/size/malware/rights/content controls; rejected media is not extracted
- [ ] Prompt injection cannot change ATTEND, EDENA, tools, permissions, partitions, or citations
- [ ] P0 default; exact one-run P1/P2 ORBIT; no retry/recursion/background work; P3/P4 unavailable; P5 blocked
- [ ] Visible Stop, selected Kill, Pause All, Safe Reset, correction, export, delete, and purge
- [ ] Log minimization, rotation, inspection, deletion, and backup tombstones
- [ ] Dependency lock, license inventory, SBOM, migrations, and clean-machine tests
- [ ] Encrypted backup/isolated restore/update/rollback/ROUNDS removal/uninstall and prohibited-canary absence tested on each claimed platform
- [ ] Keyboard, screen reader, focus, noncolor status, contrast, zoom/reflow, reduced motion, plain-language errors, and Markdown/manual mode tested
- [ ] Threat model and all negative-test evidence retained without sensitive payloads
