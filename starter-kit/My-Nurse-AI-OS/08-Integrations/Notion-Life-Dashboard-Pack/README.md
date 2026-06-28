# Notion Life Dashboard Pack

Use this pack to build a **no-PHI, database-style life dashboard** in Notion for health, finances, goals, habits, tasks, and routines.

This is a personal operations cockpit. It is not a clinical system, diagnosis tool, treatment tracker, financial adviser, or automated decision-maker.

> Notion carries the ledger. The nurse still carries the judgment.

## What this pack gives you

- Six Notion-importable CSV database templates:
  - `Health-Wellbeing.csv`
  - `Finances.csv`
  - `Goals.csv`
  - `Habits.csv`
  - `Tasks.csv`
  - `Routines.csv`
- A relation map: `Relation-Map.md`
- A setup guide with suggested views, formulas, and safety boundaries.

## Setup in Notion

1. Create a new Notion page called `My Nurse AI OS · Life Dashboard`.
2. Add this top safety note:

   > No PHI. No patient identifiers. No employer secrets. No passwords or API keys. No diagnosis, treatment, medication, or clinical decision support. This dashboard supports reflection and personal operations only.

3. Import each CSV as a database.
4. Rename the imported databases exactly:
   - Health & Wellbeing
   - Finances
   - Goals
   - Habits
   - Tasks
   - Routines
5. Add relation properties manually using `Relation-Map.md`.
6. Add one linked database view per section on the home dashboard.
7. Keep examples fictional or personal-safe. Replace rows with your real non-PHI life data only when you are ready.

## Home dashboard layout

Suggested sections:

1. **Today**
   - Tasks filtered to `Status is Today` or `Due Date is today`
   - Routines filtered to `Frequency is Daily`
   - Habits filtered to `Cadence is Daily`
2. **This Week**
   - Goals filtered to active quarter
   - Tasks due within 7 days
   - Budget review / finance check-in
3. **Health & Energy**
   - Sleep, energy, movement, meals, reflection notes
   - Use trends for self-awareness, not diagnosis
4. **Money Stewardship**
   - Bills, debt, savings goals, spending review
   - No bank credentials or account numbers
5. **Goals & Projects**
   - Goals related to tasks, habits, and routines
   - Keep one next action visible
6. **Weekly Reset**
   - Review what drained you, what restored you, and what needs a human gate

## EDENA tier

- **Green:** personal organization, routines, habits, goals, budget categories, reflection.
- **Yellow:** shared household coordination or coaching/mentor review — human approval before sharing.
- **Orange:** API automation, bank sync, wearable sync, shared team dashboards, or AI agents writing directly into Notion.
- **Red:** PHI, clinical decisions, patient care, employer secrets, account numbers, credentials, legal/financial decisions without a licensed professional.

## Starter prompt for Notion AI or Hermes

```text
Help me build a no-PHI Notion life dashboard using these six databases: Health & Wellbeing, Finances, Goals, Habits, Tasks, and Routines.
Keep it personal, non-clinical, non-financial-advice, and human-reviewed.
Suggest dashboard sections, database views, relation properties, and one weekly reset ritual.
Do not ask for patient data, employer secrets, bank credentials, account numbers, passwords, API keys, diagnosis, treatment, medication, or clinical advice.
```

## Weekly reset ritual

Ask:

1. What gave me energy?
2. What drained me?
3. What did I complete?
4. What needs a human decision?
5. What can be simplified next week?
6. What should never be automated?

Agents propose. Humans judge. Nurses steward.
