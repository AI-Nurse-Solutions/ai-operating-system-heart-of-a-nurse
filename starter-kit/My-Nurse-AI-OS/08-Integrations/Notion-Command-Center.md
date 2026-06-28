# Notion Command Center

Use Notion as the **human-facing operations and knowledge cockpit** for your Nurse AI OS. Hermes may draft, summarize, or prepare records for review; humans decide what enters Notion.

> Agents propose. Humans judge. Nurses steward.

## What Notion is for

Notion is useful when you need shared visibility across projects, reviews, and decisions:

- Governance decisions
- Human review queues for AI-generated drafts
- EDENA tier review notes
- Agent intake and source verification
- Non-PHI pilot tracking
- Risk registers
- Content calendars
- Template and SOP libraries
- Reflection and evidence logs
- Lamp Huddle agendas and follow-ups

## What Notion is not for

Do **not** use Notion as:

- an EHR
- a clinical documentation system
- a clinical decision support tool
- a patient-care coordination board
- a credentialing or certification system
- a procurement approval system
- a legal/compliance determination system
- a storage place for passwords, API keys, tokens, secrets, PHI, patient identifiers, or confidential employer files

## Starter databases

Create these as separate Notion databases or tables:

| Database | Purpose | Minimum fields |
|---|---|---|
| Governance Decisions | Track advisory decisions and rationale | Decision, EDENA tier, status, reviewer, rationale, next step |
| Human Review Queue | Review AI-generated artifacts before use | Artifact, source, risk level, requested review, status, final human decision |
| AI Agent Intake | Evaluate tools before registry/listing | Agent, source URL, use case, evidence, risks, review status, recheck date |
| Pilot Tracker | Coordinate non-PHI learning pilots | Pilot, objective, boundaries, stakeholders, weekly status, risks, closeout note |
| Risk Register | Keep governance risks visible | Risk, severity, mitigation, owner, review date |
| Content Calendar | Move ideas into publishable assets | Topic, platform, campaign, CTA, claim-vs-proof status, publish status |
| Template Library | Reuse safe operating templates | Template, domain, EDENA tier, last reviewed, source link |
| Reflection / Evidence Log | Record learning without credential claims | Activity, AI proposed, human reviewed, boundary applied, lesson, next step |

## Safe first workflow

1. Build the databases manually first.
2. Add only non-PHI examples.
3. Use Hermes to draft a Notion-ready record in Markdown or table format.
4. Human reviews the record.
5. Human pastes or imports it into Notion.
6. If API automation is added later, read before write and verify by reading the created page/database item back.

## Safe first prompt

```text
Help me design a Notion Command Center for my Nurse AI OS.
Include databases for Governance Decisions, Human Review Queue, AI Agent Intake, Pilot Tracker, Risk Register, Content Calendar, Template Library, and Reflection / Evidence Log.
Keep the workspace no-PHI, non-clinical, advisory-only, and human-reviewed.
Do not include patient data, clinical recommendations, credentials/secrets, certification claims, procurement approval, or compliance/legal determinations.
Return the database names, fields, status options, and one safe example row for each.
```


## Notion Life Dashboard Pack

For personal operations, the starter kit now includes `Notion-Life-Dashboard-Pack/` with six Notion-importable CSV databases. This Notion Life Dashboard Pack covers health, finances, goals, habits, tasks, and routines:

- Health & Wellbeing
- Finances
- Goals
- Habits
- Tasks
- Routines

Use these as a **no-PHI personal life cockpit**. They are for self-organization, reflection, and weekly review — not diagnosis, treatment, medication advice, financial advice, patient care, employer systems, bank credentials, or automated decisions.

Recommended use:

1. Import the six CSV files into a new Notion page.
2. Add relations from `Relation-Map.md`.
3. Build Today, This Week, Health & Energy, Money Stewardship, Goals & Projects, and Weekly Reset views.
4. Keep all examples non-PHI and personal-safe.
5. Add a human gate before sharing, syncing, automating, or acting on any dashboard trend.

> Broad strokes now, go deeper later. Build enough structure to serve your life — not another dashboard that judges it.

## Local HTML fallback when Notion is unavailable

If Notion is blocked, inaccessible, or too much friction, use the **Local HTML Life Dashboard** at `Local-HTML-Life-Dashboard/index.html` instead. It is a single-file browser dashboard covering health, finances, goals, habits, tasks, and routines. Keep it No PHI. Post-setup, create a browser bookmarks folder named **Dashboards** and save the local dashboard there.

Use it for personal reflection, not clinical documentation, diagnosis, treatment, financial advice, account tracking, employer systems, or automated decisions. Export a JSON backup if you rely on it.

## EDENA boundary

- **Green:** personal organization, learning dashboard, public-safe content calendar, template library.
- **Yellow:** team review queues, pilot trackers, governance decision logs, agent intake ledgers — human review before sharing or acting.
- **Orange:** API automation, shared memory, cross-tool synchronization, institutional workflows, or anything that could affect organizational decisions.
- **Red:** PHI, clinical decision support, patient care coordination, credentialing, disciplinary action, procurement approval, or legal/compliance determinations.

> Notion carries the ledger. The nurse still carries the judgment.
