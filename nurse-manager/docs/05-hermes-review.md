---
title: Hermes branding and redistribution review (build step 0.8)
date: 2026-09-29
authorship: Substantially AI-generated (Claude Code) with human review pending
status: Draft for steward review. This is not legal advice.
---

# Hermes branding and redistribution review

This is build step 0.8. It checks what this project must include if it
ever redistributes Hermes Desktop, what it may say about Hermes, and
whether our own text implies a relationship that does not exist.

**Verdict.** Today the Manager Edition references Hermes Desktop and
does not redistribute it. The only obligation now is truthful
attribution, and `THIRD_PARTY_NOTICES.md` now meets it. Redistribution
at step 1.11 brings more obligations than the MIT notice (§3). The
name "Hermes" and the Nous Research marks get no license from MIT, and
upstream treats "Hermes" as a trademark (§2.2). Some of our wording
presents "Nurse AI OS + Hermes" as one product. §4 lists those places
for the owner.

## 1. Sources read

"Hermes Desktop" is the `apps/desktop` app inside the Hermes Agent
monorepo. The tag the validation report names, `v2026.9.24`, is a tag
of that repository.

| Source | Version read | Date read | Result |
|---|---|---|---|
| `NousResearch/hermes-agent` `LICENSE` | tag `v2026.9.24` (`f97608f178d1`), and main `ee5f49b943f8` | 2026-09-29 | MIT, "Copyright (c) 2025 Nous Research". Byte-identical at both commits, and identical to the text in `THIRD_PARTY_NOTICES.md` §2 |
| Same repository: file listing for `NOTICE`, `TRADEMARK*`, brand-guideline, or third-party files | both commits | 2026-09-29 | No root `NOTICE`, `TRADEMARKS`, or brand-guidelines file. Nested licenses exist (§3) |
| `README.md` and `apps/desktop/README.md` | `v2026.9.24` | 2026-09-29 | "MIT — see LICENSE" and "Built by Nous Research". No trademark or logo terms |
| `apps/desktop/DESIGN.md`, section "Iconography & brand" | `v2026.9.24` | 2026-09-29 | The app's brand glyph is the `nous-girl` mark (`BrandMark`). No license terms for it beyond the repository's MIT file |
| `apps/desktop/package.json` (`build`) | `v2026.9.24` | 2026-09-29 | `productName: "Hermes"`, `appId: com.nousresearch.hermes`, `author: "Nous Research"`, and **`win.legalTrademarks: "Hermes"`** |
| `apps/desktop/electron-builder.config.cjs` | main `ee5f49b` | 2026-09-29 | `legalTrademarks: displayName` and `publisherDisplayName: 'Nous Research'` |
| `apps/desktop/BUILDING.md` | main `ee5f49b` | 2026-09-29 | The "Bundled" payload holds "Pinned CPython and uv", Node.js, npm, and "supported managed tools". Windows ships MSIX only, for Windows 11 22H2 or later |
| `pm/lock.json` (managed-tool pins) | main `ee5f49b` | 2026-09-29 | CPython `3.14.7+20260901` from `astral-sh/python-build-standalone`, `uv 0.12.3`, `node 26.7.0`, `npm 12.0.2`, and other tools (§3) |
| `scripts/bundles/*.py` | main `ee5f49b` | 2026-09-29 | Stages `python`, `node`, and `npm`. No step that collects license files was found in these scripts. That does not prove there is none elsewhere |
| Nous Portal Terms of Service, <https://portal.nousresearch.com/terms> | live page, no date shown | 2026-09-29 | §12.1: "Nous Research trade names and trademarks" are reserved. Commercial or promotional use of "Nous Research Materials" needs prior written permission. These terms govern the Portal's services, not the MIT code |
| `nousresearch.com/brand`, `/terms`; the `hermes-agent.nousresearch.com` site | live | 2026-09-29 | `/brand` 404; `/terms` 404. No brand or trademark guidelines were found |
| `astral-sh/uv` `LICENSE-MIT`, `LICENSE-APACHE`, README | tag `0.12.3` (`507230998c95`) | 2026-09-29 | Dual MIT or Apache-2.0. Copyright Astral Software Inc. |
| `astral-sh/python-build-standalone` `LICENSE*`, `docs/running.rst` "Licensing" | tag `20260901` (`4bb01f09aaf3`) | 2026-09-29 | The project is MPL-2.0. Distributions carry per-component license texts, including CPython, OpenSSL, SQLite, libffi, bzip2, liblzma, zlib, Tcl/Tk, ncurses, and libedit. They are built against libedit, not GPL readline, and `_gdbm` is disabled "to avoid" GPL. "The archive contains copies of license texts" |

**Not reached or not checked.** No trademark registry (USPTO or others)
was searched, so whether "Hermes" or the Nous marks are *registered* is
**unverified**. The `apps/desktop` icons carry no separate license
statement. Only the repository-wide MIT file covers them, and MIT does
not grant trademark rights. Licenses of each managed tool the payload
includes were not read one by one (§3).

## 2. Answers

### 2.1 What must a redistributor include?

- **The MIT notice.** "The above copyright notice and this permission
  notice shall be included in all copies or substantial portions of
  the Software" (`LICENSE`, `v2026.9.24`).
- **The notices of nested components the build contains.** Examples at
  `v2026.9.24`:
  - `apps/desktop/src/plugins/hermes-bots/LICENSE` (MIT, Nous Research)
  - `plugins/hermes-achievements/LICENSE` (MIT, its contributors)
  - `plugins/security-guidance/LICENSE` and `NOTICE` (Apache-2.0; the
    NOTICE credits work from Anthropic, PBC). Apache-2.0 §4(d)
    requires the NOTICE to travel with it.
  - license files under `skills/` (for example `humanizer`: MIT,
    Siqi Chen) and `optional-skills/`, including
    `pixel-art/ATTRIBUTION.md`. Not every one of these was read; each
    must be read before release
- **For a "Bundled" build, the runtime's notices** (§2.4 and §3).

### 2.2 Are the name "Hermes", its logo, or its icons restricted?

- The MIT license has **no trademark clause** and grants no trademark
  rights. Using a name to identify the software factually needs no
  license. Using it as, or inside, our product's name is a trademark
  question the license does not answer.
- Upstream **asserts "Hermes" as a trademark** in its Windows build
  metadata (`win.legalTrademarks: "Hermes"` at `v2026.9.24`;
  `legalTrademarks: displayName` on main). The Nous Portal terms
  (§12.1) reserve "Nous Research trade names and trademarks".
- The logo and icons (`apps/desktop/assets/*`, `public/hermes*.png`,
  and the `nous-girl` brand mark) are identity marks. The MIT copyright
  license covers them as files, but it does not permit using them to
  brand another product. **Treat them as restricted. Do not use them
  without written permission.**
- Registration status: **unverified** (§1).

### 2.3 What may this project say?

Based on the sources above, and matching this project's own
`TRADEMARKS.md` §2–§3 for our mark:

| Acceptable (factual) | Not acceptable |
|---|---|
| "Runs on Hermes Desktop", "works with Hermes Agent", "compatible with Hermes" when true and tested | "Official", "certified", "endorsed", or "partner", or anything implying Nous Research approves Nurse AI OS |
| "Hermes Agent is an open-source project by Nous Research" | Using the Hermes or Nous logos or icons, or the `nous-girl` mark, on our products or pages |
| Linking to the official Hermes site for installation | Naming our product, edition, or download with "Hermes" as if it were part of the name, such as "Nurse AI OS + Hermes" |
| Plain-text "Hermes" when discussing that software | Stating that an unmodified or modified build *is* "Hermes" once we change or rebrand it |

Whether "Hermes-powered Nurse AI OS" and file names such as
`…-Hermes-Program.md` stay on the acceptable side is a judgement for
the owner or counsel. It is listed under open questions in the PR.

### 2.4 Do the bundled CPython and `uv` bring their own notices?

Yes, both do.

- **CPython from python-build-standalone:**
  - CPython's own license (PSF).
  - The per-library texts the distribution ships (`LICENSE.*.txt`).
  - python-build-standalone itself is MPL-2.0 (`LICENSE`, tag
    `20260901`). Its build scripts are MPL-2.0. The distributed
    interpreter is covered by the component licenses. **Whether MPL
    terms attach to the distributed artifacts is unverified.** The
    docs say only that consumers must "understand the licensing
    requirements", and the JSON metadata carries per-component
    licensing.
- **`uv`:** MIT or Apache-2.0, at our choice (tag `0.12.3`). Keep the
  chosen license text and copyright.

The same applies to the Manager Edition's own CI builds today. They
bundle CPython (`THIRD_PARTY_NOTICES.md` §1). That is a separate item
already inventoried, and this step does not change it.

## 3. Obligations checklist for step 1.11

Step 1.11 is deferred until after the pilot (ADR 0003). Before any
Hermes Desktop build, or a substantial portion of it, reaches a
manager:

- [ ] Pin and record the upstream tag and commit (step 0.7). Note: the
  candidate `v2026.9.24` predates the MSIX packaging now on main. At
  that tag, Windows targets are NSIS and MSI.
- [ ] Ship the Hermes Agent MIT notice unchanged with the build.
- [ ] Ship every nested notice the build includes (§2.1). Keep
      Apache-2.0 `NOTICE` files.
- [ ] For a "Bundled" build, ship:
  - [ ] CPython and python-build-standalone component license texts
  - [ ] `uv` license
  - [ ] Node.js and npm licenses
  - [ ] the notice of each managed tool actually in the payload
- [ ] Check GPL items before shipping them. `pm/lock.json` pins the
      Git for Windows `PortableGit` (GPL-2.0) and BtbN FFmpeg `-gpl-`
      builds. If the payload includes them, a written source offer or
      the source is required.
- [ ] Record each redistributed component in `THIRD_PARTY_NOTICES.md`
      §1 before release (§4 there).
- [ ] Do not ship Hermes or Nous logos, icons, or the `nous-girl`
      mark as our app's identity. Replace the upstream icons, product
      name, `appId`, `legalTrademarks`, and `publisherDisplayName`
      in any build we publish, unless we have written permission.
- [ ] Use factual wording only (§2.3). Carry the no-affiliation
      statement from `THIRD_PARTY_NOTICES.md` §5.
- [ ] Treat plugins as unsandboxed (validation report, correction 6).
      This is a security obligation, not a licensing one, but it
      belongs on the same release checklist.

## 4. Naming check across this repository

Method: `git grep -i hermes` (610 files on 2026-09-29), then searches
for "official", "endorse", "partner", "certified", "powered", "+
Hermes", and Hermes-named product titles. Image files with Hermes in
the name were viewed as well.

**Finding: no Hermes or Nous Research code, logos, or icons are in
this repository.** No upstream image is copied or hotlinked. The
`nous-girl` mark does not appear. Almost every mention uses the word
to name the software, for example "install from the official Hermes
site", which is factual. The "Hermes Program" files, including the
wellness THRIVE package, and `starter-kit/` use the name only as the
runtime that reads our instructions. They contain no Hermes code or
assets.

**Edited in this PR** (one sentence each, no other change). These are
Hermes-titled public pages that carried no attribution. Each gains:
"Hermes Agent is a separate open-source project by Nous Research.
Nurse AI OS is independent: it is not affiliated with or endorsed by
Nous Research, and uses the Hermes name only to identify that
software."

- `hermes-masterclass.html`
- `hermes-configuration-handbook.html`
- `remote-hermes-safely.html`

`hermes-downloads/index.html` already says Hermes is "a separate,
free, open-source desktop runtime from Nous Research", so it was left
as is.

**Follow-up (PR after #138).** A later check found ten more pages whose
`<title>` names Hermes and that carried no attribution. The English
sentence was added to:

- `cheat-sheet.html`
- `when-things-go-wrong.html`

A translation was added to the localized cheat sheets: `ar/`, `es/`,
`fr/`, `hi/`, `ru/`, `tl/`, `vi/`, and `zh/cheat-sheet.html`. These
translations are AI-drafted and need review by a fluent reader before
they are treated as final.

Every note now carries `data-attribution="hermes-independence"`.
`nurse-manager/tests/test_notices.py` finds every page whose title
names Hermes and requires exactly one such note mentioning Nous
Research and Nurse AI OS. `hermes-downloads/index.html` is the one
listed exception, for the reason above. `.github/workflows/nurse-manager.yml`
runs that test when any of these pages changes.

**Listed for the owner, not edited.** These are hash-bound or owned by
other areas.

| Where | Wording | Why listed |
|---|---|---|
| Mission Control baseline app in the build kits: `respiratory-care/build-kit/…`, `medical-residents/build-kit/…`, `post-setup/build-kits/future-student-assistant/…` (`index.html`, `README-FIRST.md`, `RELEASE-MANIFEST.json`, the QA build script, and the committed screenshots) | Eyebrow "Nurse AI OS + Hermes"; "Hermes-powered Nurse AI OS · Personal Edition" | Reads as a co-branded product. Files are checksum-bound in release manifests, so a change needs a rebuild |
| Build kit and program names in `respiratory-care/`, `medical-residents/`, `post-setup/`, `healthcare-research-innovation-leaders/`, `wellness-services-marketing-managers/` (THRIVE), and the zips in `post-setup/downloads/` | `…-Mission-Control-Hermes-Build-Kit-v1.0.0`, `…-SuperPowers-Hermes-Program.md` | "Hermes" inside our product names. Consider "…for Hermes" in the next release. Renaming needs checksum and manifest rebuilds |
| `assets/img/make-your-nurse-ai-os-hermes-work-for-you.webp`, shown on `nurse-station.html` | Image title "Make Your Nurse AI OS – Hermes Work for You" | Pairs the marks as one name. It is an image, so it needs a new graphic |
| `side-gig-starter-kit/index.html` | "Build your own Hermes-powered chief of staff" | Factual if true. Listed with the "powered" question |
| `starter-kit/My-Nurse-AI-OS/04-Governance/HERMES-Transformation-Protocol.md` and mentions in `WELCOME-Carry-the-Lamp.md` | Our own acronym "HERMES" (Hear and Harvest, Evaluate, Reframe…) | Not a Nous mark use, but next to Hermes Agent instructions it can confuse readers. Owner's call |
| `hermes-role-profiles/` (directory and "Hermes Role Profile") | Profile packs named for the runtime | Describes the target runtime. Likely acceptable; listed for completeness |
