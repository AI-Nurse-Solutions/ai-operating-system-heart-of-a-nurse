# Video Walkthrough Scripts

These are short first-version scripts for a GitHub Pages + PDF workbook launch. Record as screen-share videos. Keep each video 5–8 minutes.

---

## Video 1 — Welcome: A System with the Heart of a Nurse

**Goal:** Explain the course promise and nursing posture through the Florence Nightingale frame.

Opening:

> Florence Nightingale carried a lamp — and a notebook. She stayed present with the suffering, and she charted the data that proved most deaths were preventable. Heart and evidence, together. This course hands you both instruments for the AI age. It is not about replacing nursing judgment with AI. It is about building an operating system that carries the busywork so you can carry the patient.

Cover:

1. Florence's two instruments: the caring heart and the counting mind
2. Who this is for — student nurse, staff nurse, nurse leader — and the ache each one carries
3. The three spheres: personal, professional, community / entrepreneurship
4. Core rule: Hermes supports. Humans judge. Nurses steward.
5. What this course is not: no PHI, no patient-specific care decisions, no replacement for licensed judgment
6. What students will build by the end

Close:

> Your first task is not to install a tool. Your first task is to define the values that will guide the tool. Carry the lamp. Keep the ledger.

---

## Video 2 — Install Hermes Desktop and Set Safe Boundaries

**Goal:** Walk through installation and safe orientation.

Cover:

1. Download/install Hermes Desktop from the official Hermes Agent site or official Nous Research release path
2. On macOS: open the `.dmg`, drag Hermes into Applications, eject the DMG, and launch from Applications or Spotlight
3. Complete first-run onboarding
4. Open the UI: sessions, pinned messages, artifacts, skills, tools, messaging, settings
5. Pick a provider/model; use Nous Portal or another supported provider if available, and remember that free/low-cost model availability can change
6. Optional Terminal verification: `hermes --tui`
7. Set the workspace to the course folder, not the whole computer
8. Protect API keys: never place keys in public notes, screenshots, GitHub, or course forums
9. Keep manual approval on for beginner use
10. Explain memory as useful but governed: no PHI, no secrets, no confidential employer data
11. Create a nurse-centered workspace folder
12. Add `NO-PHI-BOUNDARY.md`
13. Add `HUMAN-AGENCY-RULES.md`
14. Run first safe prompt
15. Demonstrate one bounded file task inside the course folder
16. Create separated profiles: Personal Projects, Personal Learning, and Professional Non-PHI
17. Explain that profiles separate config, SOUL, memory, sessions, skills, cron jobs, and identity — but do not replace privacy governance

Safe first prompt:

```text
Read my Nurse-AI-OS folder and summarize the starter files you see. Do not access other folders. Do not modify anything yet.
```

Safe file-task prompt:

```text
Create a new folder called Practice inside My-Nurse-AI-OS and write a short README explaining that this is a safe test folder.
```

Safety line:

> If it could identify a patient, do not paste it. If it could affect care, do not outsource it.

---

## Video 3 — Build Your Nurse-Centered Chief of Staff

**Goal:** Create the personal mission-control workflow.

Cover:

1. Daily brief prompt
2. Weekly review prompt
3. Personal dashboard, with the Local HTML Life Dashboard fallback if Notion is unavailable
4. Save the local dashboard as a browser bookmark under Dashboards
5. Energy and recovery protection
5. Decision ownership

Demo prompt:

```text
Act as my nurse-centered Chief of Staff. Help me identify what matters today, what can wait, what needs follow-up, and what action protects my wellbeing.
```

---

## Video 4 — Build Your Learning OS

**Goal:** Show how AI supports learning without replacing expertise.

Cover:

1. Choose one topic
2. Build a pathway
3. Create practice scenarios
4. Generate self-test questions
5. Identify what evidence to review
6. Identify what a human expert should verify

Key line:

> A Learning OS should build your capability, not your dependency.

---

## Video 5 — Build Your Professional + Community OS

**Goal:** Map career and community/entrepreneurial support.

Cover:

1. Career map
2. Certification plan
3. Research review
4. Idea map
5. Community needs map
6. Smallest safe pilot

Entrepreneurship boundary:

> Be imaginative, but not reckless. Do not promise what you have not proven.

---

## Video 6 — Govern, Loop, and Sustain

**Goal:** Teach HERMES, EDENA, and safe loops.

Cover:

1. HERMES Transformation Protocol
2. EDENA Stewardship Lens
3. Loop Charter
4. Stop conditions
5. Monthly AI OS audit
6. Integration Gate for Obsidian, Notion, Google Workspace, GitHub, and GitHub Pages
7. macOS GitHub setup: `brew install gh`, `gh auth login`, private repo first, public Pages only when publishable
8. Image generation for learning dashboards, personal sites, and public-safe visual drafts
9. Knowledge graph dashboard prompt pack: static image, ambient loop, and image-to-video patterns
10. Video generation for short 4–8 second ambient dashboard loops
11. Three-lane research setup: personal knowledge, academic/medical reading, and technical project research
12. Perplexity MCP as an optional citation-rich source, never as final truth
13. Messaging gateway comparison: Telegram, WhatsApp, Slack, Discord, Signal, SMS, and Email
14. Team Lab profile blueprint: SOUL.md, allowlisted gateway, shared skills, cron reports, and launch checklist
15. Screenshot workflows: paste/attach images, browser_vision for public/test pages, and no-PHI visual boundaries
16. macOS Computer Use + Magnet layouts for study, writing, coding, and meeting setups
17. AI browser boundary: Hermes as hub, Comet/Atlas as optional manual research browsers unless governed
18. YouTube transcripts into Hermes: lecture → timestamped chapters, Obsidian note, follow-up questions
19. Living and thriving with AI: cognitive load, ergonomics, relationships, critical thinking, systems thinking, and leader/educator practice
20. 90-minute workshop outline for nurses, leaders, educators, or students
21. Notion as a no-PHI Command Center plus Notion Life Dashboard Pack: governance decisions, human review queues, agent intake, pilot tracking, content calendars, template libraries, and personal dashboards for health, finances, goals, habits, tasks, and routines — never EHR, CDS, patient-care coordination, credentialing, procurement, legal/compliance, secrets, PHI storage, bank credentials, or automated decisions
22. Google Workspace as a governed suite: Gmail, Drive, Docs, Sheets, Slides, Meet, Calendar, and core services under BAA only when eligible/configured/approved
23. Safe AI with PHI: personal Gmail and generic AI are no-PHI; use fictional/de-identified/public/synthetic material unless explicitly approved
24. Why every connector, media tool, messaging channel, screenshot, browser, Notion workspace, Workspace service, and MCP server needs least privilege, cost awareness, approval gates, and a human owner

Key line:

> Every loop needs a leash, a log, a limit, and a human owner.

Close:

> The goal is not a smarter machine. The goal is a stronger nurse.


### Optional segment — Notion life dashboard walkthrough

Show how to import the six CSV databases from `08-Integrations/Notion-Life-Dashboard-Pack/` and build a gentle home dashboard:

1. Today — tasks, routines, and daily habits.
2. This Week — goals, due tasks, and money stewardship check-in.
3. Health & Energy — reflection, sleep, energy, movement, and routines.
4. Goals & Projects — goals related to tasks, habits, and routines.
5. Weekly Reset — what gave energy, what drained energy, what needs a human decision.

Boundary line:

> This is a personal operations dashboard, not a clinical or financial decision system. No PHI, no patient care, no account numbers, no credentials, no automatic decisions.

### Optional segment — Local HTML dashboard fallback

If a learner cannot use Notion, open `08-Integrations/Local-HTML-Life-Dashboard/index.html` and show the browser-only template. Demonstrate:

1. The post-setup step: create a browser bookmarks folder named **Dashboards**.
2. Save the local dashboard as a bookmark under **Dashboards**.
3. Edit the six sections: Health & Wellbeing, Finances, Goals, Habits, Tasks, and Routines.
4. Click Save dashboard.
5. Export a private JSON backup.
6. Repeat the safety boundary: no PHI, no clinical advice, no account numbers, no credentials, no automatic decisions.
