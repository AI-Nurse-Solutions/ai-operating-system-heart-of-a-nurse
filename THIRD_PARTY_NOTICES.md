# Preserve Every Upstream Notice

**File:** `THIRD_PARTY_NOTICES.md`
**Rule:** every third-party component distributed in this codebase must appear in this inventory with its license and original copyright notice intact. Notices are preserved, never replaced. Components are never relicensed beyond what their upstream license permits.

---

## 1. Inventory

| Component | Upstream project | License | Distribution status | Modified |
|---|---|---|---|---|
| Hermes Agent | [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) | MIT | External runtime; not vendored in this repository | No |
| Hermes Desktop (`apps/desktop` in the Hermes Agent repository) | [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent/tree/main/apps/desktop), reviewed at tag `v2026.9.24` (`f97608f`) and main `ee5f49b` | MIT (same root `LICENSE` as Hermes Agent) | Referenced, not bundled: the Manager Edition does not ship, bundle, or modify Hermes Desktop. Its host (build step 1.11) is deferred until after the pilot (ADR 0003). Obligations for step 1.11 are in §2.1 | No |
| OpenClaw | [openclaw/openclaw](https://github.com/openclaw/openclaw) | MIT | Referenced for interoperability and architectural research; not vendored in this repository | No |
| Florence-X contract schemas (`candidate_action.schema.json`, `edena_decision.schema.json`) | [AI-Nurse-Solutions/florence-x](https://github.com/AI-Nurse-Solutions/florence-x) at `09675bf` | Apache-2.0 | Vendored as data in `nurse-manager/contracts/florence-x/` for contract tests; provenance and hashes in `PROVENANCE.md` there | No |
| CPython runtime | [python/cpython](https://github.com/python/cpython) | PSF-2.0 | Bundled inside the Nurse AI OS app builds produced by CI (`.github/workflows/nurse-manager-app.yml`); not vendored in this repository | No |
| PyInstaller bootloader | [pyinstaller/pyinstaller](https://github.com/pyinstaller/pyinstaller) | GPL-2.0-or-later with the PyInstaller bootloader exception | Build tool (pinned); its bootloader is embedded in the app builds. The exception expressly permits distributing the resulting executables under any license; the repository's own code stays Apache-2.0 | No |

No Hermes or OpenClaw source code is vendored in this repository as of July 14, 2026. Their notices are reproduced below for transparent attribution and to establish the notices that must travel with any future substantial incorporation. Files covered by this repository's Apache License 2.0 grant remain under that grant and are not listed here; separately governed Nurse AI OS artifacts may carry different terms. See `LICENSE` and `licensing.html`.

## 2. Hermes

Hermes Agent is distributed under the MIT License. Its original notice is reproduced verbatim:

```text
MIT License

Copyright (c) 2025 Nous Research

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### 2.1 Hermes Desktop: current status and step 1.11 obligations

**Status (September 29, 2026): referenced, not bundled.** The Nurse AI OS Manager Edition names Hermes Desktop as a possible future host. No Hermes Desktop code, build, icon, or other asset is in this repository or in the Manager Edition app builds. The notice above is reproduced for attribution only. The review behind this entry, with sources and dates, is `nurse-manager/docs/05-hermes-review.md`.

**When step 1.11 redistributes a Hermes Desktop build, or any substantial portion of it, the release must:**

1. Include the MIT notice above, unchanged, with the build.
2. Include the notices of every nested component the build carries. Examples at the reviewed commits: `apps/desktop/src/plugins/hermes-bots/LICENSE` (MIT); `plugins/security-guidance/LICENSE` and `NOTICE` (Apache-2.0, work from Anthropic, PBC); and further license files under `skills/` and `optional-skills/`, which must each be read before release.
3. For a "Bundled" build, include the notices of the runtime it stages. These cover CPython from `python-build-standalone`, which ships per-library license texts such as OpenSSL, SQLite, and libffi; `uv` (MIT or Apache-2.0); and Node.js and npm. They also cover any managed tools the payload includes. Some pinned tools are GPL-licensed, such as the Git for Windows and FFmpeg "gpl" builds, and would bring source-offer duties. Record each one in §1 before release.
4. Not use the Hermes or Nous Research names, logos, or icons (including the `nous-girl` brand mark) as our product's name or icon. Say only what is true, such as "runs on Hermes Desktop". Do not state or imply endorsement.
5. Record the exact upstream tag and commit in §1 and in the step's evidence.

## 3. OpenClaw

OpenClaw is distributed under the MIT License. Its original notice is reproduced verbatim:

```text
MIT License

Copyright (c) 2026 OpenClaw Foundation

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Third-party notices for incorporated or adapted code are recorded in
THIRD_PARTY_NOTICES.md.
```

## 4. Additional Dependencies

Before a release distributes any third-party source or binary component, maintainers must record it here, preserve all required notices, and verify license compatibility. A component with unknown or incompatible terms blocks release until remediated. When the project adds a release-generated software bill of materials or automated license audit, this section will identify the artifact and verification command; neither is claimed before it exists.

## 5. No Affiliation

Nurse AI OS is an independent project. References to Hermes Agent, Hermes Desktop, and OpenClaw do not imply endorsement by, partnership with, or affiliation with those projects or their maintainers, including Nous Research. Their names are used only for factual identification and attribution.

---

Upstream notices were verified against the canonical `LICENSE` files for [Hermes Agent](https://github.com/NousResearch/hermes-agent/blob/main/LICENSE) and [OpenClaw](https://github.com/openclaw/openclaw/blob/main/LICENSE) on July 14, 2026. The Hermes notice was re-verified on September 29, 2026, byte-for-byte against `LICENSE` at Hermes Agent tag `v2026.9.24` (`f97608f`) and main `ee5f49b`.

