# Non-Nurse Ally pathway — local publication review

Date: 2026-09-30. Human release owner: **Robert Domondon**.
Status: **prepared locally; not published; human review and release approval pending**.
Worktree branch: `hermes/ally-stewardship-prepublish`, based on `1fd015b2abe16629a5e97bc5dbad1138a639ae45`.

## Scope and release boundary

A welcome pathway for allied health colleagues, ordinary people exploring personal AI, business builders, ethical managers, technologists, and community contributors. It is not a taxonomy addition, numbered role lane, activated profile, membership program, or professional course. No push, PR, merge, deployment, membership enrollment, runtime activation, or external publication was performed. Monitoring baseline and schedule are unchanged because the pathway is not live.

The primary homepage CTA and every pre-existing homepage byte outside the marked additive ally section are preserved by a portable contract test against the frozen upstream homepage SHA-256 baseline. Existing physician pages and packages are unchanged. Three existing files change: `index.html`, `sitemap.xml`, `.github/workflows/website-alignment.yml`.

## Four pillars and honest evidence

| Pillar | What this pathway provides | Evidence, not an outcome claim |
|---|---|---|
| Knowledge | Public-source learning, clear language, source attribution, uncertainty and third-party data-route guidance | Link/ID tests and local review of existing ecosystem/resource/about pages; no claim that all external resources remain current |
| Judgment | Self-described preferences; consequence stops; human accountability; purpose over hype and optional charter | Actual browser acknowledgment gates and generated-draft checks; no assessment of real ethical behavior or competence |
| Capability | Personal SOUL draft, generic starter archive, offline manual dashboard and Mission Control, read-only handoff | Actual download bytes, ZIP member/source parity, offline exports, no HTTP(S)/WebSocket requests observed during tested interactions; no installed plugins or runtime enforcement |
| Contribution–Stewardship | Voluntary reviewed contributions, provenance, rights, named owners, correction, review dates and retirement | Charter/guide content and certificate lifecycle tests; no automatic sharing, affiliation, enrollment or contribution verification |

## Observed local verification

The first portable ally contract run was **RED**: 11 tests, 3 failures and 8 missing-artifact errors, before implementation. After implementation and expanded coverage:

- `python3 -m unittest discover -s tests -p test_ally_stewardship.py -v`: **14 passed**.
- Existing physician stewardship suite: **8 passed**.
- Existing leader/educator homepage suite: **12 passed**.
- `git diff --check`: **exit 0**.
- Public healthcare artifact scanner: **16 new pathway artifacts passed**, including recursive ZIP contents. This scanner detects likely secret/PHI patterns, not all privacy or governance risks.
- Real installed Chrome via Python Playwright: **15 recorded check groups passed**. All **64** role × management × business combinations were exercised; every priority, contribution, communication, service and partnership option was also exercised. Selected text appears in generated drafts; no-business/no-management boundaries are preserved.
- Blank quiz and required acknowledgments block generation. SOUL download matches the displayed draft. Reset clears selections/acknowledgments; changed selections invalidate the draft. Starter browser download matches repository ZIP bytes.
- Public and packaged ceremonies: acknowledgment/date gates, optional blank name, literal HTML-like names via `textContent`, inert downloadable HTML, print-handler invocation, edit invalidation, reset, reload loss and no automatic enrollment were exercised.
- All three packaged HTML templates were exercised from `file://`. Notes/certificate exports worked; no HTTP(S)/WebSocket requests or automatic local/session storage observed. Manual notes disappear on reload. Browser document reload reads are not classified as network requests.
- Seven pages at **375px and 1280px**: no horizontal overflow; measured buttons/selects/text/date inputs/nav links and checkbox label hit areas meet 44px dimensions; first keyboard focus has visible outline. Sampled computed text contrast minimum **4.856:1**. This is not a complete accessibility conformance audit.
- Both `certificate.pdf` and the separately downloaded `downloaded-keepsake.pdf` were parsed with pypdf: **one A4 page each**, with visible commemorative and noncredentialing disclaimers. Arbitrary long names/custom print settings were not exhaustively validated.
- No JavaScript page errors were observed in the completed run.

Browser QA is repeatable with `tests/ally_browser_qa.py`; Playwright and installed Chrome are prerequisites. It runs an ephemeral loopback HTTP server and shuts it down in `finally`. It is a local QA runner, not a new automatic browser CI job. Portable contracts are discovered by the existing aggregate Python CI suite; workflow path filters cover ally sources, downloads and both test files, and safety scanner loops cover all public ally artifacts.

## Evidence paths (local; do not publish personal QA exports)

Root: `/Users/robertdomondon/.hermes/profiles/unattended/cache/scratch/ally-pathway-evidence/`.

- `browser-results.json`, `final-verification.json`, `unit-tests.txt`, `safety-scan.txt`, `diff-check.txt`.
- Screenshots: `ally-375.png`, `ally-1280.png`, `ally-soul-quiz-375.png`, `ally-soul-quiz-1280.png`, `ally-setup-375.png`, `ally-setup-1280.png`, `ally-stewardship-375.png`, `ally-stewardship-1280.png`, `certificate-1280.png`, `downloaded-keepsake.png`.
- `certificate.pdf`, `downloaded-keepsake.pdf`, extracted text sidecars, `soul-draft.md`, browser-downloaded ZIP and offline Markdown/HTML exports.

Screenshots were actually inspected with image tools (mobile landing including full-size top crop, desktop quiz, ceremony/certificate and downloaded keepsake). The visual direction uses navy, teal, restrained gold, system typography and readable cards; it is open to everyone and has no gender-based gate or stereotype.

## Safety and unresolved release gates

No clinical care is prescribed. Allied-health scope, employer permission and actual authority remain independent. Consequential health/employment/financial/legal decisions stop for qualified human review. Business claims need verification and appropriate AI disclosure; customers/employees must be protected from manipulation and discrimination. No guaranteed business success, comparative superiority, achieved AGI, model conscience, professional credential, institutional authority or assessed competence is claimed.

Personal data control is a practice, not automatic sovereignty. Runtime-local is not inference-local; users must inspect provider/account/sync/backup retention and permissions. Third-party ownership is not guaranteed. Clean dedicated hardware is recommended, not a compliance/security guarantee. Official Hermes/Nous links and plan/hardware distinctions are inherited from the inspected setup guide; no installation or provider purchase was made or validated in this task. Recheck current official requirements and subscription terms before release/use.

## Independent parent verification

The parent independently inspected the welcome/quiz/setup/ceremony copy and the scoped homepage/sitemap/workflow diff; visually inspected desktop/mobile landing screenshots; reran the 14 ally and 8 physician contracts; and reran all 15 real-Chrome browser check groups, including 64 context combinations. The full local repository suite then passed: **749 tests in 49.618 seconds**. This is observed local execution, not GitHub CI. Browser evidence and the aggregate log are retained in the active profile's scratch workspace; personal QA exports are not included in the public source or review bundle.

**Remaining gates:** Robert's copy/visual approval; exact-head GitHub CI and review after separately authorized push/PR; live deployment and served-byte/link checks only after explicit publication authorization; broader accessibility/assistive-technology and ordinary-user usability review if required. No local failing test or known functional defect remains in the tested scope. Local evidence does not validate clinical readiness, production runtime controls, privacy across arbitrary third parties, real user conduct or outcomes.
