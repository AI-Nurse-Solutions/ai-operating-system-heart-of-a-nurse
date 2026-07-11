# Nurse AI OS — Media Packet

**nurse-ai-os.org** · July 2026 · Media contact: **great.ai.nurses@gmail.com**

*Ready-to-use language for three audiences — the general public, nursing organizations, and AI architects/technology press — plus fast facts, founder bio, accuracy notes, and assets. Everything in this packet may be quoted directly.*

---

## Executive summary

**Nurse AI OS is a free, governed personal-AI operating system for nurses — built by a 22-year ICU nurse so that the profession that governs medication, delegation, and scope of practice can govern AI the same way.** It gives nursing students, bedside nurses, managers, and nurse entrepreneurs a working AI system with nursing's safety culture built in: risk tiers on every task, human approval gates, a strict never-any-patient-data boundary, and a signed, verifiable software supply chain. It is deliberately *practice-adjacent*: it carries the professional life around the work — studying, certifications, portfolios, unit operations, side businesses — and treats the clinical core as permanently out of scope. Independent professional guidance from the ANA, NCSBN, and the American Academy of Nursing describes what safe nursing AI must look like; Nurse AI OS is that guidance, operationalized — and its research claims are adversarially verified, with refutations published as corrections.

---

## Fast facts

- **What:** a governed operating layer for personal AI, purpose-built for nurses, running on the open-source Hermes Agent runtime (Nous Research).
- **Who it serves:** four audience modules on one governance spine — nursing students & educators (Study OS), bedside & advanced-practice nurses (Bedside OS), nurse managers & leaders (Leader OS), and nurse entrepreneurs (Builder OS).
- **Cost:** free for nurses and nursing students during the founding year.
- **The hard boundary:** no patient information, ever — "if it could identify a patient, it counts." Refused at intake, not stored-then-deleted. No clinical decisions, at any tier, permanently.
- **The safety model:** EDENA risk tiers (🟢 proceed / 🟡 human approves first / 🟠 deferred until governed review / 🔴 stop) — tiers measure risk, not privilege. Doctrine: *AI drafts, humans judge, nurses steward.*
- **The engineering:** signed releases (pinned key fingerprint → signed manifest → per-file checksums, fail-closed), human-staged approval for AI-authored skills, refuse-at-intake memory rules, and an anti-anchoring "judgment first" pattern.
- **The evidence discipline:** research claims carry verified / source-reported / design-judgment labels; the latest adversarial verification pass confirmed 24 of 25 claims and the one refuted claim was publicly corrected.
- **Founder:** Robert Domondon, RN, CCRN, CSC, CMC — 22 years in the ICU, 13 years in healthcare management, physician training (Philippines), former US Naval Hospital administrator.

---

## For the general public

**The 50-word description.** Nurse AI OS is a free AI assistant system for nurses with nursing's safety rules built in: it never touches patient information, a human approves anything that matters, and it helps with everything around the work — studying, certifications, schedules, careers — so nurses arrive at the bedside lighter.

**The 150-word description.** Nurses are among the most trusted professionals in the world — and like everyone else, they're already using AI chatbots for everyday help. Nurse AI OS, built by a 22-year intensive-care nurse, gives them something safer than an open chat window: a personal AI system that runs on nursing's own safety culture. Every task carries a risk rating. Anything important waits for the nurse's approval. And patient information is refused outright — the system is designed so it *can't* become a shortcut around privacy. What it does instead is carry the life around the work: exam preparation for students, certification deadlines and after-shift decompression for bedside nurses, paperwork drafts for managers, honest marketing for nurses starting small businesses. It's free for nurses and nursing students during its founding year. The motto tells the story: *AI drafts. Humans judge. Nurses steward.*

**Three key messages.**

1. **Nurses are already using AI — this makes it safe.** The choice isn't AI or no AI; it's governed or ungoverned. Nurse AI OS is the governed option, built by a nurse.
2. **Patient privacy is protected by design, not by promise.** The system refuses patient information at the door — it never stores it, and it says so in plain language.
3. **The human stays in charge.** Every consequential action waits for the nurse's approval. The AI drafts; the nurse decides.

**Suggested angles.** The ICU nurse who spent 22 years at the bedside and built an AI system on nursing's checklist culture · What every profession can learn from how nurses are governing AI · "No patient data, ever": the AI tool that leads with what it refuses to do.

**Pull quote.** *"Nurses shouldn't just use AI — they should govern it."* — Robert Domondon, founder

---

## For nursing organizations

**Boilerplate paragraph (quote freely).** Nurse AI OS is a nurse-led, governed personal-AI operating layer that operationalizes the profession's published guidance on artificial intelligence. Its design maps directly to positions the American Nurses Association, NCSBN, and the American Academy of Nursing have already taken: AI as adjunct to — never a replacement for — nursing judgment; nurses accountable and in the loop; capabilities tested before deployment and re-verified continuously. Every task runs under EDENA risk tiers with human-approval gates; patient information is refused at intake under a strict no-PHI boundary; academic-integrity workflows are built on process transparency rather than unreliable detection scores; and nurse leaders receive working templates — review logs, workflow charters, a unit AI accountability charter — for the oversight duties professional guidance assigns them. Nurse AI OS is free for nurses and nursing students during its founding year.

**Talking points.**

- **It operationalizes existing guidance rather than inventing its own.** The mapping from ANA/NCSBN/AAN positions to system components is published, citation by citation, in the project's Architecture Report — and those citations survived three-vote adversarial verification against primary sources.
- **It builds the AI-governance workforce the guidance assumes.** Every user practices daily inside risk tiers, review gates, escalation rules, and decision ledgers — the instincts organizations need as clinical AI arrives. Surveyed nursing programs report a large AI-literacy gap; the Student module is aimed squarely at it.
- **Academic integrity is handled the way the evidence says to.** Detection tools have documented false-positive problems; the Study OS builds integrity on disclosure templates, process logs, and educator review-and-interview workflows — never automated accusation.
- **Nurse review is structural.** A Steward Council of named nurses reviews shared skills against a published checklist, with quarantine power and a 90-day re-review cycle. Publication is never presented as endorsement or certification.
- **What it is not (say this plainly):** not clinical software, not decision support, not connected to the EHR, not HIPAA-covered (and it never claims to be), not a certification program, and it makes no patient-outcome claims.

**The collaboration invitation.** Nursing organizations, schools, and unions interested in pilots, workshops (a 90-minute unit-ready session ships in the kit), or governance collaboration can reach the project at great.ai.nurses@gmail.com.

---

## For AI architects and technology press

**Boilerplate paragraph (quote freely).** Nurse AI OS is a case study in domain-governed personal AI: a governance layer over the open-source Hermes Agent runtime in which safety properties are enforced by structure wherever the runtime allows, and honestly labeled where they are not. Distribution is a fail-closed signed supply chain (pinned key fingerprint, RSA-signed manifest, per-file checksums verified before execution). Agent-authored skills — Hermes autonomously writes and improves its own tools — are treated as a first-class supply-chain surface and land in a human-approval staging queue. Memory runs on refuse-at-intake prohibition lists rather than delete-after policies. Risk tiers attach to tasks, not tools; four audience modules specialize skills and tier defaults without forking the governance spine. And the project's research program applies three-vote adversarial verification to its own claims, publishing refutations as corrections — including about its own marketing.

**Talking points.**

- **Gates, not vibes.** The design treats standing instructions as necessary but insufficient for redline enforcement. Mechanically enforced points (staged skill writes, command approval, signed-release refusal checks) are distinguished — explicitly and in public documentation — from model-followed patterns like the Yellow-tier self-audit footer, which is audited at the human gate; a delivery-gating output verifier is the named next hardening step. The project corrected its own documentation when a reviewer flagged the distinction. That correction habit is the story.
- **The agent is part of its own supply chain.** In a runtime that writes its own tools and curates its own memory, vetting can't stop at install time: `write_approval` staging is on by default, security scanning applies regardless of origin, and Do-Not-Remember rules are enforced against the runtime's own memory-persistence behavior.
- **Anti-anchoring as skill structure.** For anything decision-adjacent, the human's assessment is elicited *before* AI material is shown — automation-bias mitigation encoded as interaction order, not advice.
- **A worked example of "operationalize the domain's existing governance."** The profession had published requirements (ANA, NCSBN, AAN); the contribution is the mechanical layer that turns them into a daily-use system — a transferable pattern for any regulated profession.
- **Read the receipts:** the Architecture Report (HTML + PDF at nurse-ai-os.org/architecture-report.html) carries the guidance-to-structure mapping and summarized citations; the naio-os standards crosswalk serves technical reviewers.

---

## Founder

**Short bio (50 words).** Robert Domondon, RN, CCRN, CSC, CMC, is a critical-care nurse with 22 years at the ICU bedside, 13 years in healthcare management, physician training in the Philippines, and former administration of a US Naval-base hospital. He is the founder of Nurse AI OS, the NAIO Institute, and the Nurse Intelligence Network.

**Longer bio (120 words).** Robert Domondon's career runs the full span of healthcare: physician training and practice in the Philippines, hospital administration on a former US naval base, thirteen years in healthcare management, AI-adoption consulting — and, by deliberate choice, more than two decades as a critical-care nurse in the United States. That combination is the design brief for Nurse AI OS: built by someone who has signed the budget, written the policy, and held the hand of the patient the policy was written for. His governing doctrine — "governance by design; clarity and values before velocity" — runs through the ecosystem he founded: the NAIO Institute (standards and credentialing), the Nurse Intelligence Network (the professional community), EDENA (the ethics-and-risk layer), and Nurse AI OS itself.

---

## The ecosystem at a glance

- **Nurse AI OS** — the governed personal-AI operating layer (this project; the front door).
- **EDENA** — Ethical Design & Enablement for Nursing Augmentation: the risk-classification and gating layer every task runs under.
- **NAIO Institute** — standards, credentialing, and compliance frameworks for AI workforce systems in healthcare.
- **Florence-X** — the orchestration control plane for governed AI-agent workforces; humans retain final decision authority at every layer.
- **Nurse Intelligence Network (NIN)** — the global professional community, summit, and podcast (nurseintelligence.com).
- **Florence Media Network** — the content engine; every piece EDENA-classified and human-reviewed before release.

---

## Accuracy notes — please describe us this way

Getting these right matters more to this project than coverage does.

- **Do say:** "a governed personal-AI system for nurses" · "refuses patient information by design" · "free for nurses and nursing students during the founding year" · "operationalizes ANA/NCSBN/AAN guidance" · "built on the open-source Hermes Agent runtime."
- **Please don't say:** "HIPAA-compliant" (it is a personal, non-covered tool and says so) · "clinical AI," "diagnoses," or "decision support" (clinical use is permanently out of scope) · "certifies nurses" (course completion is never competency certification) · "improves patient outcomes" (the project makes no patient-outcome, safety-outcome, or compliance claims — by policy).
- **The one-line boundary, quotable:** *"No PHI, ever — if it could identify a patient, it counts."*

---

## Assets & links

- **Site:** nurse-ai-os.org · **Start Here:** nurse-ai-os.org/start-here.html · **Pathways:** nurse-ai-os.org/pathways.html
- **Architecture Report** (for technical/executive readers): nurse-ai-os.org/architecture-report.html (with PDF)
- **Care Intelligence White Paper** (June 2026): nurse-ai-os.org/assets/care-intelligence-white-paper.pdf
- **Articles:** "Why Nurses Need an AI Operating System, Not Just an AI" · "Governance You Can Refute: The Evidence Behind Nurse AI OS" — both at nurse-ai-os.org/nurse-station.html
- **Community:** nurseintelligence.com · YouTube: @NurseIntelligence · Podcast: The Nurse Intelligence Podcast (Spotify)
- **Founder photo:** available on request (and at nurse-ai-os.org/about.html)
- **Interviews, speaking, pilots, and governance inquiries:** great.ai.nurses@gmail.com

---

*Carry the lamp. Keep the ledger. Agents propose. Humans judge. Nurses steward.*
