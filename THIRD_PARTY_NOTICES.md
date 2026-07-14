# Preserve Every Upstream Notice

**File:** `THIRD_PARTY_NOTICES.md`
**Rule:** every third-party component distributed in this codebase must appear in this inventory with its license and original copyright notice intact. Notices are preserved, never replaced. Components are never relicensed beyond what their upstream license permits.

---

## 1. Inventory

| Component | Upstream project | License | Distribution status | Modified |
|---|---|---|---|---|
| Hermes Agent | [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) | MIT | External runtime; not vendored in this repository | No |
| OpenClaw | [openclaw/openclaw](https://github.com/openclaw/openclaw) | MIT | Referenced for interoperability and architectural research; not vendored in this repository | No |

No Hermes or OpenClaw source code is vendored in this repository as of July 14, 2026. Their notices are reproduced below for transparent attribution and to establish the notices that must travel with any future substantial incorporation. Independently developed Nurse AI OS components are licensed under Apache License 2.0 and are not listed here; see `LICENSE`.

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

Nurse AI OS is an independent project. References to Hermes Agent and OpenClaw do not imply endorsement by, partnership with, or affiliation with those projects. Their names are used only for factual identification and attribution.

---

Upstream notices were verified against the canonical `LICENSE` files for [Hermes Agent](https://github.com/NousResearch/hermes-agent/blob/main/LICENSE) and [OpenClaw](https://github.com/openclaw/openclaw/blob/main/LICENSE) on July 14, 2026.

