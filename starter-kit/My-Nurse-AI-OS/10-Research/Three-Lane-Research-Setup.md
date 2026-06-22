# Three-Lane Research Setup

Hermes research should start simple and become more specialized only when needed.

Core pattern:

```text
Native web tools → specialized MCP when needed → reusable research skills → scheduled review only after workflow is proven
```

## Lane 1 — Personal Knowledge Research

Best for articles, newsletters, essays, podcasts, web pages, and learning notes.

- Storage: Obsidian or a markdown vault.
- Tools: `web_search`, `web_extract`, and browser automation only when needed.
- Skills to create after the workflow works: `capture-article`, `compare-sources`, `weekly-digest`.
- Output: a clean learning note with source link, summary, key ideas, open questions, and links to related notes.

Prompt:

```text
Research this topic for my Personal Learning profile.
Use open-web sources first.
Create one Obsidian-ready markdown note with source links, key ideas, open questions, and what I should verify.
Do not use PHI or confidential employer material.
```

## Lane 2 — Academic / Medical Reading

Best for papers, guidelines, white papers, reports, and evidence summaries.

- Storage: vault folders such as Reading Inbox, Papers, Clinical Topics, and Evidence Summaries.
- Tools: `web_search`, `web_extract`, PDF URL extraction, and browser only when needed.
- Skills to create after the workflow works: `read-paper`, `summarize-guideline`, `compare-studies`, `evidence-brief`.
- Output: question, population, intervention/exposure, findings, limitations, confidence, practical takeaway, and source link.

Boundary:

> Hermes may summarize and compare sources. It does not replace clinical judgment, guideline review, institutional policy, or licensed decision-making.

Prompt:

```text
Read this academic or medical source as evidence, not as clinical advice.
Separate claims, methods, findings, limitations, uncertainty, and practical implications.
Create an evidence-aware note I can review against the original source.
Do not make patient-specific recommendations.
```

## Lane 3 — Technical Project Research

Best for codebases, GitHub issues, package choices, technical docs, and implementation decisions.

- Storage: project repo `research/` or `notes/` folder.
- Tools: `web_search`, `web_extract`, GitHub workflow, and MCP only when useful.
- Skills to create after the workflow works: `repo-brief`, `research-lib`, `compare-approaches`, `weekly-tech-digest`.
- Output: decision note, alternatives, tradeoffs, evidence links, and next implementation step.

Prompt:

```text
Research this technical project question.
Use web sources for external docs and GitHub/repo context only if approved.
Write findings into a project research note with options, tradeoffs, risks, evidence links, and a recommended next step.
Do not publish, push, or change code without approval.
```
