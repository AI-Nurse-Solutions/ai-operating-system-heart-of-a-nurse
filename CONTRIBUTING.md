# Contribute Under Clear Terms

**File:** `CONTRIBUTING.md`

Thank you for improving Nurse AI OS. Contributions of code, documentation, tests, and translations are welcome from anyone. This file states the terms, so that nothing about ownership, licensing, or attribution is ever ambiguous later.

---

## 1. Contributor License Agreement

Every contribution requires agreement to the Contributor License Agreement below. By opening a pull request and submitting a contribution, you state that you agree to Section 1. If the repository later enables a separate CLA-recording check, contributors will complete it once on their first pull request. Corporate contributors whose employment agreements assign their work should have an authorized representative agree on the organization's behalf.

### 1.1 What you grant

By submitting a contribution, you grant the project steward (currently Robert Domondon, and any successor entity under `GOVERNANCE.md` Section 5):

1. A perpetual, worldwide, non-exclusive, royalty-free license to use, reproduce, modify, distribute, publicly display, and sublicense your contribution as part of the project.
2. Permission to relicense your contribution under the project's published licenses — Apache License 2.0 for code, CC BY 4.0 for documentation — and under future versions of those licenses.
3. Permission to translate and adapt your contribution for international distributions.
4. Permission to attribute the contribution to you.

You also represent that the contribution is your original work, or that you have the right to submit it under these terms, and that it identifies any third-party material it carries along with that material's license.

### 1.2 What this agreement does not do

The agreement is bounded. It does not:

- Transfer your copyright. You retain ownership of your contribution.
- Transfer any trademark rights, in either direction.
- Prevent you from using, publishing, or licensing your own contribution elsewhere, for any purpose.
- Prevent you from publishing critical commentary about this project or about your own contribution. No non-disparagement term exists here, and none will be added.
- Collect personal data beyond what attribution and authorship records require.

## 2. Licensing of New Work

- New source files are licensed under Apache License 2.0 and carry the standard Apache header naming the copyright holder per `NOTICE`.
- New documentation is licensed under CC BY 4.0.
- Files derived from Hermes, OpenClaw, or any other upstream project keep their original license headers and copyright notices intact. Never replace an upstream notice with a project notice. Modifications to upstream files are noted in the file header.

## 3. License Compatibility

License compatibility is a required maintainer review before merge:

- Every distributed dependency must have a known, verified license recorded in `THIRD_PARTY_NOTICES.md`; when a machine-readable software bill of materials is added, it must agree with that inventory.
- Code of unclear provenance is not merged. If you cannot state where code came from and under what license, do not submit it.
- Copyleft code (GPL family) is not introduced into Apache-licensed components. If a copyleft dependency is genuinely necessary, open an issue first; the decision is made explicitly and documented, never by silent merge.

## 4. Disclosure of AI-Assisted Work

Contributions produced with substantial AI assistance are welcome and are disclosed. State in the pull-request description whether the work is human-authored, jointly authored with AI assistance, or substantially AI-generated with human review. Documentation contributions record the same in frontmatter. Two hard rules: AI-generated content is never attributed to a human as sole author, and contributions must not contain fabricated citations, quotes, or evidence. This disclosure also preserves the human-authorship record that supports the project's copyright registrations.

## 5. Contribution Process

1. Open an issue describing the change before large work; small fixes may go straight to a pull request.
2. Fork, branch, and keep changes focused — one idea per pull request.
3. Include tests for behavior changes and update documentation the change touches.
4. Confirm agreement to the CLA in Section 1 in the pull-request description; complete the repository's CLA check if one is enabled.
5. A maintainer reviews for correctness, safety posture (see `SAFETY.md`), license compatibility, and fit with project scope.

Do not report security vulnerabilities in a public issue. Use GitHub's private vulnerability-reporting channel if it is enabled, or email the maintainer contact listed in `README.md` with the subject “Private security report.”

---

To make your first contribution, open an issue describing what you intend to change.

