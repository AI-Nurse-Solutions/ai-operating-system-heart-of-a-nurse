# FUTURE Security, Privacy, Integrity, and Safety Checklist

Hermes must copy this checklist into the target release and link every checked item to runtime evidence. An unchecked, Not Run, Failed, Blocked, or Unsupported critical item blocks Operational status. Text presence is not evidence.

## Supply chain and install

- [ ] Build-kit manifest, checksums, source hashes, and archive paths verified before work.
- [ ] Immutable source is unchanged; implementation is copy-on-write.
- [ ] Dependency versions are locked; licenses and SBOM are recorded; vulnerability results are reviewed.
- [ ] Final ZIP has one safe root, no traversal/symlink/collision, exact checksums, and reproducible or explained provenance.
- [ ] Clean install, upgrade, backup, restore, rollback, overlay removal, and uninstall pass on every claimed OS/version.

## Local service and authentication

- [ ] Service binds only to loopback and rejects unsafe Host/Origin values.
- [ ] First-run owner enrollment, unique install secret, authenticated sessions, expiry, logout, and failed-login limits pass.
- [ ] Cookies are HttpOnly, SameSite=Strict, and Secure whenever transport supports it.
- [ ] CSRF protection covers every state-changing request; CORS is deny-by-default.
- [ ] Security headers, request/body/file limits, timeouts, safe content types, and rate limits pass.
- [ ] No public-share, remote-admin, unauthenticated API, or wildcard-binding path exists.

## Secrets and diagnostics

- [ ] Provider keys and database credentials are server-side only and absent from JS, HTML, URLs, browser storage, logs, errors, exports, backups, screenshots, and analytics.
- [ ] `.env.example` has names only; permissions and secret rotation are documented.
- [ ] Diagnostics are redacted, local, user-visible, bounded, and deletable.
- [ ] Production contains no test key, default password, canned response, fake tool event, or mock-provider fallback.

## Data screening and minimization

- [ ] PHI, identifiable clinical stories, chart content, images/screenshots with patient information, and unknown clinical narratives are rejected before persistence and not echoed.
- [ ] Live-care, charting, medication, device, assignment, delegation, scope, care-plan, and competence requests stop and route to accountable humans/processes.
- [ ] Exams, prohibited assessed work, fabricated hours/skills/citations/credentials/reflections/signatures, and deceptive AI use are refused and converted to allowed coaching where possible.
- [ ] Restricted student, employment, discipline, accommodation, investigation, peer-review, incident, credential, security, secret, and financial-account content is rejected.
- [ ] Public, synthetic, owner-authored nonsensitive, restricted, prohibited, and unclassified rules are compiled server-side and consistent across UI/API/import/AI/memory/export.
- [ ] Sensitive-data tests confirm no payload fragment reaches logs, receipts, search indexes, caches, memory, badge evidence, exports, or backups.

## Pathway and context isolation

- [ ] Student, Assistant, and Bridge are explicit user choices and never inferred.
- [ ] Learning, work growth, life, and community/future spaces are partitioned.
- [ ] Academic, clinical-placement, employment, personal, and public/community contexts enforce ownership in repository queries.
- [ ] Bridge school and employment records cannot leak through search, suggestions, memory, exports, analytics, agent context, or browser cache.
- [ ] Role/context/site/rule/authority changes return affected runs to Preview and invalidate stale approvals.
- [ ] Typed approved transfer is purpose-, field-, source-, destination-, version-, hash-, expiry-, and receipt-bound.

## Academic and professional integrity

- [ ] Applicable course, program, assessment, clinical-site, employer, supervision, scope, delegation, and disclosure rules are visible or explicitly Unknown.
- [ ] Attempt-before-answer and learner-authorship behavior passes representative and adversarial tests.
- [ ] AI Use & Integrity Receipts accurately separate learner work, AI assistance, verified sources, edits, human review, and disclosure.
- [ ] Résumé, portfolio, application, scholarship, interview, service, and career claims require truthful evidence.
- [ ] The app never impersonates faculty, a nurse, supervisor, school, employer, certifier, or institution.
- [ ] No hidden monitoring, ranking, sentiment inference, mental-health/motivation diagnosis, risk profiling, or faculty/employer reporting exists.

## Governance and permissions

- [ ] EDENA Green/Yellow/Orange/Red/Unclassified produces the same behavior from every route and agent.
- [ ] Personal Red acknowledgment can only continue allowed sanitized sandbox exploration; Institutional Red blocks pending required review.
- [ ] EDENA never overrides prohibited data/action, missing authority, live safety, context partition, or P0 permission.
- [ ] All 18 powers start Inactive; all 18 workflows Preview Only; all agents P0 Disabled; external actions/connectors/schedules/sharing/background jobs Off.
- [ ] One-run grants are exact-purpose/context/data/tool/limit/expiry/reviewer bound and automatically return to safe state.
- [ ] No self-activation, recursion, delegation, permission widening, silent retry, or invisible continuation exists.
- [ ] Pause All and Kill cancel real work and record no false completion.

## Hermes, retrieved content, and memory

- [ ] Connection state comes from recent authenticated health/capability checks, not timers or saved URLs.
- [ ] Genuine streaming, cancellation, retry limits, structured errors, sessions, and tool-event separation pass with the selected backend.
- [ ] Raw `SOUL.md` and raw quiz answers are never displayed, duplicated, logged, exported, or persisted; only user-approved minimum derived context is used.
- [ ] Retrieved instructions cannot override governance; prompt-injection, tool-output injection, and malicious-file tests pass.
- [ ] Citations are rendered only from retrieved/validated records with claim mapping, source status/date, applicability, conflict, and uncertainty.
- [ ] Memory is opt-in, structured, purpose-bound, inspectable, editable, exportable, forgettable, deletable, expiring, and context-partitioned.

## Persistence, deletion, and recovery

- [ ] Transactions, constraints, optimistic concurrency, forward-only migrations, and restart persistence pass.
- [ ] Backup is consistent, versioned, protected, checksummed, and restore-tested.
- [ ] Import is schema-, size-, content-, version-, duplicate-, ownership-, and migration-validated before commit.
- [ ] Correction marks dependent artifacts, approvals, citations, and badges stale and preserves a non-sensitive correction history.
- [ ] Complete deletion covers primary, derived, cache, index, memory, export staging, attachments, and eligible audit payloads.
- [ ] Safe Reset is previewed and returns to the documented safe baseline without deleting unrelated work.

## Accessibility and humane use

- [ ] Keyboard-only path, visible focus, semantic landmarks, labels, error association, screen-reader order, reduced motion, zoom, reflow, and mobile layout pass.
- [ ] Status never depends on color alone; empty, unknown, stale, blocked, offline, and synthetic states are explicit.
- [ ] No dark patterns, engagement streaks, shame, coerced disclosure, or deceptive urgency.
- [ ] Minimum/re-entry modes include sleep, meals, transport, work, caregiving, recovery, and help-seeking.
- [ ] Crisis/safety cues pause productivity and direct the user to local human/emergency pathways without diagnosis.

## Release evidence

- [ ] Every visible control has a unique test and works or is truthfully disabled.
- [ ] All applicable full-stack and cross-cutting checks have execution records.
- [ ] All 136 canonical FUTURE checks have execution records against the packaged runtime.
- [ ] Production-mode, offline, outage, cancellation, restart, clean-install, and real-Hermes safe smoke paths are recorded.
- [ ] Final readiness statement matches evidence and lists every remaining blocker.
