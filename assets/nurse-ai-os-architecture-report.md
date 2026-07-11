# Nurse AI OS Architecture Report

## *Nurse AI OS architecture is the architecture professional bodies are asking for.*

**For AI architects and Chief Nursing Officers** · nurse-ai-os.org · July 2026

---

## Executive summary

Nurse AI OS is a governed personal-AI operating layer for nurses, built on the open-source Hermes Agent runtime. It exists to solve one design problem well: **give an individual nurse a genuinely useful personal AI system that is mechanically incapable of drifting into clinical practice, patient data, or unaccountable autonomy.**

This report describes the architecture for two readers at once. For the **AI architect**, it is a case study in governance that is *enforced by structure* — tiers, gates, signed releases, refuse-at-intake memory rules, and fail-closed output checks — rather than requested in a system prompt. For the **CNO**, it is evidence that when nurses adopt personal AI (and they are adopting it, with or without guidance), there is a disciplined, profession-aligned way to do it that never touches PHI, never enters the clinical record, and teaches every user the governance instincts your organization needs them to have.

The central claim is deliberately conservative and was adversarially verified against primary sources: **the profession's own bodies have already specified what safe nursing AI must look like, and this architecture operationalizes their guidance.** The American Nurses Association holds that assistive technologies are *adjunct to, not replacements for, the nurse's knowledge and skill*, that nurses remain accountable *even when the technology fails*, and that nurses integrating AI carry an ongoing duty to verify its validity and reliability. NCSBN's regulatory journal insists human clinical judgment remain the final arbiter. The American Academy of Nursing requires testing before deployment and funded post-deployment surveillance. ANA explicitly directs nurse *leaders* to establish responsibility-and-accountability measures for AI use. Each of those statements maps to a load-bearing component of this system — the review gates, the risk tiers, the deferred-integration tier, the re-review cycle, the leader module's accountability charter.

What no professional body supplies — and what this project genuinely contributes — is the **mechanical layer**: the working system that turns published guidance into daily practice for one nurse at a time. That layer is described in §3–§5.

A note on method, because it is itself an architectural feature: the research behind this report used three-vote adversarial verification against primary sources. Twenty-four of twenty-five verified claims survived; one — an early framing that nursing AI operates in a "regulatory vacuum" — was refuted and publicly corrected. A system whose marketing survives its own verification discipline is the system this report describes.

---

## 1. The design problem

Nurses are already using consumer AI tools, on personal devices, without governance. The naive institutional response — prohibition — does not stop the use; it removes it from view. The naive product response — "an AI for nurses" with clinical features — walks straight into the failure record: clinical AI that degraded in the real world, laundered bias through proxy metrics, or was expensively abandoned (the Epic sepsis model's external-validation collapse, Watson for Oncology, the Obermeyer bias findings — cited here as the widely reported cautionary record).

Nurse AI OS takes the third path: a **practice-adjacent** personal system. It carries the professional life *around* the work — study, certification upkeep, portfolios, teaching materials, unit operations drafting, quality-improvement scaffolding, side-business discipline — and treats the clinical core as permanently out of scope. The boundary is not a usage policy; it is the architecture's first invariant: **no PHI, ever; if it could identify a patient, it counts.**

## 2. Architecture overview

The system is four layers, each with a distinct trust model:

| Layer | What it is | Trust mechanism |
|---|---|---|
| **Runtime** | Hermes Agent (open source, MIT): SOUL.md standing instructions loaded first in the system prompt, skills as markdown files, persistent memory, cron, messaging gateways, MCP tools | Upstream security features: skill security scanning, staged `write_approval` for agent-authored skills, command approval, container isolation |
| **Governance layer** | EDENA risk tiers · human-review gates · no-PHI boundary · Do-Not-Remember memory rules · prompt-injection and untrusted-content boundaries · skill/MCP vetting checklist | Rules rendered into the system prompt *plus* enforcement points — mechanical where the runtime provides them (approval gates, staging queues, signed releases) and model-followed fail-closed self-audits reviewed at the human gate (see §4) |
| **Distribution** | The naio-os signed-release installer | Pinned public-key fingerprint → RSA-signed manifest → per-file checksums, verified before any downloaded byte executes; fail-closed |
| **Audience modules** | Four packs on one spine: Student Study OS, Builder OS (entrepreneurs), Leader OS (managers), Bedside OS (staff/APRN) | Shared boundary headers per pack; per-skill EDENA frontmatter; Yellow-tier skills carry fail-closed self-audit footers (model-followed, audited at the human gate) |

**EDENA tiers measure risk, not privilege:** 🟢 Green — proceed, human reviews output; 🟡 Yellow — human approves before use; 🟠 Orange — deferred advanced integrations, treated as Red until governed review; 🔴 Red — stop, human authorization mandatory (and for some categories, permanently human: patient-adjacent work, personnel decisions, policy adoption, payments).

Roughly 70% of the system is this shared spine; the audience modules are the remaining 30% — skills, personas, knowledge sources, and tier defaults specialized per audience.

## 3. The professional mandate, mapped to structure

Every row below pairs a professional-body position (verified against the primary source by three adversarial votes) with the component that operationalizes it.

| Professional guidance (verified) | Architectural response |
|---|---|
| ANA: assistive technology is *adjunct to, not a replacement for*, the nurse's knowledge and skill; nurses accountable even in technology failure | The doctrine "AI drafts, humans judge, nurses steward" as system-prompt invariant; the accountability line quoted verbatim in the Bedside module's boundary header |
| NCSBN (Journal of Nursing Regulation): human clinical judgment must remain the final arbiter; guard against overreliance on algorithms | Human gates on every consequential tier; the Judgment-First anti-anchoring pattern (nurse states their own assessment before seeing any draft) |
| ANA: ongoing duty to verify AI validity, application, transparency, and continued reliability, with traceability | Skill vetting as a lifecycle: review logs, 90-day re-review of shared skills, ledger-recorded decisions — never one-time approval |
| AAN: test before deployment; fund post-market surveillance of deployed AI | The Orange tier (integrations deferred until governed review) and adoption-signal outcome tracking in every module — with explicit *non-claims* (no patient-outcome or performance claims) |
| ANA: nurse leaders *must* establish responsibility-and-accountability measures for AI | The Leader OS module: governance-facilitator skill, Loop Charters, Human Review Logs, a one-week sprint ending in a signed Unit AI Accountability Charter |
| ANA: patients wrongly assume consumer health tools are legally protected; clinician endorsement compounds the misconception | The strict no-PHI boundary plus explicit "this is a personal, non-HIPAA-covered tool" framing throughout; FTC-aware Do-Not-Remember rules that treat *inferential* health data as sensitive |
| NCSBN: the Clinical Judgment Measurement Model is a *measurement* framework (Layer 3 = the measurable cognitive operations), not by itself a pedagogy | The Student module scaffolds NCJMM Layer-3 operations in-scenario and pairs them with Tanner's model for structured reflection — measurement and teaching kept distinct |
| Nursing-education research: AI-detection tools have unacceptable false-positive behavior; detection scores alone are an unjust enforcement basis | Integrity-by-design: process transparency, draft provenance, disclosure templates, and an educator process of detection *plus* review *plus* student interview — never automated accusation |
| Hermes runtime (primary docs): the agent autonomously creates and improves skills and curates memory | Agent-authored artifacts treated as a first-class supply-chain surface: `write_approval` staging gate on by default, security scanning regardless of origin, Do-Not-Remember enforced against automatic memory persistence |

## 4. Six design decisions AI architects should note

1. **Gates, not vibes.** Standing instructions alone are treated as insufficient for redline enforcement (the NEDA/Tessa forensic analysis — source-reported — found a strict refusal-first system prompt blocked only a fraction of adversarial prompts, while a fail-closed post-generation self-audit achieved full recall on its test set). The *mechanically enforced* points here belong to the runtime and installer: staged skill writes requiring human approval, command approval, and signed-release refusal checks. Every Yellow-tier skill adds a **fail-closed self-audit footer** — an in-context requirement that the model append a machine-checkable JSON verdict and withhold its own draft when the verdict is false or malformed. Stated precisely, because precision is this report's product: in the current kit that footer is **model-followed, not runtime-enforced** — there is no separate output verifier that can withhold a response after generation. Its verdict line is visible and auditable at the human approval gate every Yellow-tier skill already carries (a response missing or failing its verdict is treated as discarded at that gate), and a delivery-gating output verifier is the identified next hardening step.
2. **Memory is refuse-at-intake, not store-then-redact.** The Do-Not-Remember system (a global baseline plus per-audience extensions) rejects prohibited categories at the moment of intake — PHI, credentials, third-party personal data, named-staff performance information, inferential health data. A deletion policy protects against yesterday's mistake; a refusal policy prevents tomorrow's.
3. **The supply chain is signed and pinned.** The installer verifies a pinned public-key fingerprint, then an RSA-signed manifest, then per-file checksums — before executing anything it downloaded. Any byte change fails closed until a human re-signs. The same discipline extends to *agent-authored* skills via the staging queue: in a runtime that writes its own tools, the agent is part of its own supply chain.
4. **Judgment-first sequencing.** Wherever a request resembles decision support, the human's own assessment is elicited *before* any AI material is shown — an anti-anchoring control encoded as skill structure rather than advice.
5. **Tier the task, not the tool.** EDENA tiers attach to *work* (drafting vs. sending; analysis vs. people-decisions; reading evidence vs. applying it), so the same runtime safely spans a student's flashcards and a manager's staffing analysis — with the risky end of each spectrum gated or permanently human.
6. **Four modules, one spine.** Audience specialization lives in skills, boundary headers, and tier defaults — not in forks of the governance layer. This keeps every safety property global: a fix to the memory rules or the vetting checklist propagates to all four audiences at once.

## 5. What this offers a CNO

**What it is:** a personal, no-PHI, non-covered tool that your nurses may adopt as individuals — the governed alternative to the ungoverned consumer-AI use already happening. It is deliberately *not* a clinical system: nothing here connects to your EHR, scheduling, or messaging systems without your organization's formal approval (the architecture defers those integrations at the Orange tier and teaches users to route them through institutional vetting — agreements, audit rights, named review responsibility).

**Why it may interest you anyway:**

- **It builds the workforce capability the guidance assumes.** Every user works daily inside risk tiers, human gates, review logs, and escalation rules — the exact governance instincts AI-era nursing practice requires. The Leader OS module goes further: it operationalizes ANA's leader-accountability directive as templates a unit manager can actually sign and post.
- **It models the questions to ask vendors.** The same vetting checklist users apply to skills and integrations — provenance, least privilege, tier honesty, boundaries present, named reviewer — is a serviceable first screen for any clinical-AI procurement conversation.
- **Its outcome claims are disciplined.** The system reports adoption and learning signals (time reclaimed by self-estimate, CE progress, gate health, governed-workflow counts) and explicitly refuses patient-outcome, safety-outcome, or compliance claims. A tool that does not overclaim for itself is likelier to teach users not to overclaim for others.
- **The boundary protects you.** "No PHI, ever — refused at intake, and if it could identify a patient, it counts" is a stricter rule than most consumer-tool policies your staff currently operate under, and it is enforced in the tool's own memory architecture, not just requested of the user.

## 6. Evidence discipline

The research program behind this architecture distinguishes three evidence grades — **verified** (survived three-vote adversarial verification against the primary source), **source-reported** (quoted from a primary source, not yet adversarially verified), and **design judgment** (architectural reasoning, labeled as such). In the most recent verification pass, 24 of 25 top claims were confirmed unanimously; the single refuted claim (the "regulatory vacuum" framing) was corrected in place and in public. The failure cases cited in §1 and the Tessa forensics in §4 are source-reported; every professional-guidance row in §3 is verified.

This is the report's last argument to both audiences: the architecture's deepest habit — *drafts are checked, claims are gated, and refutations are corrections rather than embarrassments* — is applied to the project's own literature. That habit, more than any single component, is what professional bodies are asking software to have.

---

## Citations (summarized)

**Professional-body guidance (verified against primary sources):**

1. **American Nurses Association**, *The Ethical Use of Artificial Intelligence in Nursing Practice* — Board-approved position statement (Dec 2022 PDF) and OJIN 30(2) May 2025 revision; ANA Code of Ethics Provision 4.1. — *Adjunct-not-replacement; accountability in technology failure; ongoing validity-verification duty; leader accountability directive; patient data-protection misconception.*
2. **NCSBN** — Zhong et al., *Journal of Nursing Regulation* (2025), incl. the Wolters Kluwer/NLN survey of 307 nursing-school deans and faculty (17% currently use/teach generative AI; 60%/46% of larger/smaller programs plan adoption by ~2029). — *Human judgment as final arbiter; the AI-literacy gap.*
3. **NCSBN**, Clinical Judgment Measurement Model — nclex.com official pages. — *NCJMM as measurement model; Layer 3 cognitive operations.*
4. **American Academy of Nursing** — AI policy position; March 7, 2025 letter to HHS (HIPAA Security Rule NPRM, regulations.gov docket); March 14, 2025 NSF AI Action Plan letter (nitrd.gov). — *Test-before-advance; post-market surveillance; HIPAA-and-AI clarification requests.*

**Pedagogy and academic integrity (verified):**

5. Sessions, *Nursing Education Perspectives* 47(1) — CJMM-whiteboard simulation project paired with Tanner's model (feasibility evidence). 6. Grimm et al., *Nurse Educator* (2025) and the DNP detection-rubric reliability pilot (PMC12539509) — detector false-positive risk; detection+review+interview process. 7. Golchini et al., "Socratic AI" (medRxiv preprint, 2025) — gated case phases, guidance tiers, five-dimension feedback; *explicitly emerging/experimental, no learner-outcome data.*

**Comparable products (verified as vendor-stated design):**

8. UWorld UAsk launch materials (June 2026) — in-workflow embedded tutoring grounded in a proprietary nurse-authored corpus.

**Runtime (verified against official documentation):**

9. Hermes Agent docs and repository (Nous Research) — SOUL.md system-prompt position, skills model, autonomous skill creation and memory curation, `write_approval` staging, skill security scanning.

**Source-reported context (quoted from primary/secondary sources; not adversarially verified in this pass):** NEDA/Tessa guardrail forensics (arXiv 2509.07022); Epic Sepsis Model external validation; Watson for Oncology retrospectives; Obermeyer et al., *Science* (2019); ambient-scribe legal analyses (ABA Health Law 2026); NIST AI 600-1 Generative AI Profile; WHO guidance on large multi-modal models (Jan 2024); FTC health-information guidance and enforcement record; nurse-manager qualitative study (PMC12174894); Hippocratic AI Nurse Advisory Council reporting.

---

*Prepared from the Nurse AI OS research program (July 2026). No PHI, ever. AI drafts, humans judge, nurses steward.*
