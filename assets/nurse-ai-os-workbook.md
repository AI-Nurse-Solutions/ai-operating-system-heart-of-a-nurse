# AI Operating System with the Heart of a Nurse

## Starter Kit + Course Workbook

**Course promise:** Build a nurse-centered AI operating system for personal, professional, and community / entrepreneurial use — governed by human agency, evidence-awareness, systems thinking, ethical stewardship, safety, and dignity.

**Default posture:** Hermes becomes your nurse-centered Chief of Staff, Learning OS, strategic advisor, and stewardship partner.

**Core line:**

> Hermes supports. Humans judge. Nurses steward.

---

## Read This First: Boundaries

This course is for personal productivity, learning, research, writing, reflection, career planning, community building, and non-PHI professional work.

It is **not** for:

- patient-specific clinical decisions
- medication, diagnosis, or treatment recommendations
- EHR screenshots
- patient names, MRNs, chart excerpts, or identifiers
- confidential employer information without authorization
- replacing licensed judgment or institutional policy

If the work could affect patient care, expose PHI, or create clinical accountability, pause and route through appropriate human and institutional governance.

---

# The Nurse-Centered AI OS Stack

```text
Heart of Nursing
  ↓
Human Agency
  ↓
Evidence Awareness
  ↓
Systems Thinking
  ↓
Ethical Governance
  ↓
Actionable Workflows
  ↓
Safe Execution
  ↓
Reflective Learning
```

A nurse-centered AI OS should be:

- nurse-centered
- human-agency preserving
- evidence-aware
- systems-thinking oriented
- ethically governed
- actionable
- safety-first
- dignity-protecting
- entrepreneurially imaginative but not reckless

---

# Course Map

## Week 1 — Heart Before Tools

**Goal:** Define the values and boundaries that will guide your AI OS.

### Build

- `MY-AI-VALUES.md`
- `NO-PHI-BOUNDARY.md`
- `HUMAN-AGENCY-RULES.md`

### Prompt

```text
Help me write a personal AI values statement as a nurse.

It should reflect:
- human judgment
- privacy
- dignity
- evidence-awareness
- critical thinking
- safety
- wellbeing
- service
- professional boundaries

Use clear language I can paste into my AI OS setup.
```

---

## Week 2 — Set Up Hermes Desktop Safely

**Goal:** Install Hermes Desktop and create a nurse-centered AI workspace.

### Build

- Hermes Desktop installed
- nurse-centered profile or working folder
- starter markdown architecture
- no-PHI safety boundary

### Starter folder

```text
My-Nurse-AI-OS/
  00-Start-Here/
  01-Personal/
  02-Professional/
  03-Community-Entrepreneurship/
  04-Governance/
  05-Templates/
```

### Prompt

```text
Help me set up my Nurse-Centered AI Operating System folder.
Create a simple structure for personal, professional, and community / entrepreneurial support.
Include safety boundaries, human-agency rules, and weekly review templates.
```

### Hermes Desktop Setup Walkthrough

Use the setup tutorial as a practical orientation, but translate it through the nurse-centered safety lens.

#### 1. Install and launch Hermes

For macOS, the easiest beginner path is the official Hermes Desktop installer.

- Go to the official Hermes Agent site: https://hermes-agent.nousresearch.com/
- Download the macOS Desktop installer from the official site or official Nous Research GitHub release path.
- Avoid third-party mirrors and unofficial download sites.
- Open the downloaded `.dmg` file.
- Drag Hermes into Applications when prompted.
- Eject the DMG, then launch Hermes from Applications or Spotlight.
- If Gatekeeper warns that the app came from the internet, confirm it came from the official Hermes/Nous source before opening.

The Desktop app and CLI share the same Hermes core: config, provider settings, sessions, skills, memory, and profiles. A setup completed in Desktop also prepares the underlying Hermes CLI for later advanced use.

If you are comfortable with Terminal, you can verify the terminal UI after setup:

```bash
hermes --tui
```

If the command does not work, use the official docs path first: run Hermes Desktop onboarding, or use the official `hermes setup` flow to repair provider/config issues.

Beginner note: current platform support and installer details can change. Always use the official Hermes Agent docs as the source of truth.

After launch:

- Open a new session.
- Notice the main areas: sessions, pinned messages, artifacts, skills, tools, messaging, settings, and provider/model settings.

#### 2. Configure the workspace

Set the workspace to a folder you intentionally created for this course, such as:

```text
My-Nurse-AI-OS/
```

Do not point Hermes at folders that contain patient information, confidential employer files, tax records, passwords, or sensitive family documents unless you fully understand and approve the access.

#### 3. Choose safety controls

Start with manual approval, not full autonomy.

For nurses, the recommended beginner posture is:

```text
Manual approval first.
Small safe tasks first.
No PHI.
No clinical decisions.
No background automation until you understand the risk.
```

Smart or autonomous approval settings should be treated as advanced features. More access means more governance.

#### 4. Understand memory

Hermes can remember durable preferences and context. This is powerful, but nurses should treat memory as a governed space.

Use memory for:

- writing preferences
- learning goals
- non-PHI professional interests
- course progress
- recurring workflow preferences

Do not store:

- patient identifiers
- confidential employer details
- secrets, passwords, or API keys
- sensitive family information
- anything you would not want resurfacing later

#### 5. Configure models and providers

Hermes can connect to providers such as OpenRouter, Google Gemini, GitHub Copilot, Anthropic, and others depending on current Hermes support and your account access.

Some providers may list free or low-cost models. Treat “free” as temporary and subject to change. Always check current provider terms, privacy policy, rate limits, and cost before using a model for serious work.

Never paste API keys into public notes, screenshots, course forums, shared documents, or GitHub repos. If a key appears in a file, revoke it and create a new one.

#### 6. Test with a safe task

Start with a low-risk task such as:

```text
Read my Nurse-AI-OS folder and summarize the starter files you see. Do not access other folders. Do not modify anything yet.
```

Then try a bounded file task:

```text
Create a new folder called Practice inside My-Nurse-AI-OS and write a short README explaining that this is a safe test folder.
```

#### 7. Use sub-agents responsibly

Sub-agents can research different sides of a question in parallel while Hermes supervises and synthesizes the result.

Safe beginner example:

```text
Fire two sub-agents for a non-clinical learning task.
Agent 1: summarize the benefits of using AI for nurse professional development.
Agent 2: summarize the risks and limitations.
Then synthesize both sides and tell me what I should verify before acting.
No PHI. No clinical decisions.
```

Avoid using sub-agents for patient-specific care, confidential employer work, or decisions with financial, legal, clinical, or employment consequences without human expert review.

#### 8. Voice, messaging, and connectors

Voice, Telegram, Discord, Slack, and other messaging integrations can make Hermes more useful, but each connector creates a new doorway.

Before connecting a channel, ask:

- What data can pass through this channel?
- Who else can see it?
- Can messages be forwarded, stored, or searched?
- What should never be sent here?
- How do I disconnect it?

Connector rule:

> Do not connect Hermes to sensitive healthcare systems, employer systems, patient data, or confidential channels without formal approval.

### macOS Day-One Checklist

Use these first tasks after installation:

1. **Verify a normal chat works**

```text
Give me a 5-bullet orientation to this Nurse-AI-OS course. Do not use clinical advice. Do not ask for PHI.
```

2. **Create a safe daily brief**

```text
Act as my nurse-centered Chief of Staff. Create a daily brief for personal priorities, professional learning, and one community or entrepreneurial action. Do not include patient information.
```

3. **Check your workspace boundary**

```text
Tell me what workspace folder you can see. Do not read outside the course folder. Tell me if anything looks sensitive before opening it.
```

4. **Try a balanced sub-agent research task**

```text
Use two sub-agents for a non-clinical learning question. One should summarize benefits; one should summarize risks. Synthesize the result and tell me what requires human verification.
```

5. **Do not add advanced features yet**

Do not enable computer use, messaging connectors, cron jobs, background loops, or autonomous approval until a normal chat, workspace boundary, and no-PHI workflow are working reliably.

### Personal Projects and Personal Learning Profiles

Hermes profiles let you run separate agents on the same machine. Each profile has its own configuration, `.env`, `SOUL.md`, memories, sessions, skills, cron jobs, state database, gateway state, and identity.

Use profiles to avoid mixing personal learning, personal projects, and professional work.

Recommended beginner profiles:

```text
Personal Projects
Personal Learning
Professional Non-PHI
```

Important boundary:

> Profiles help separate memory, configuration, skills, and sessions. They are not a substitute for data governance, access control, or clinical privacy review.

#### Personal Projects profile

Use this for side projects, writing, small apps, personal goals, and low-stakes experiments.

Suggested `SOUL.md`:

```markdown
# Personal Projects SOUL

You help me plan and ship small personal side projects and learning experiments.
You keep my goals realistic, help me choose next actions, and protect my time and energy.
You do not access work files, patient information, or confidential employer material.
You preserve my judgment and ask for approval before changing files or creating scheduled jobs.
```

Start with one recurring personal workflow:

- weekly project review
- daily idea grooming
- lightweight learning plan
- personal project next-action list

Day-one prompt:

```text
I am in my Personal Projects profile.
Here are my current personal projects and rough goals: [PASTE LIST]
Design one simple weekly review workflow with clear input, output, manual approval, and a reusable prompt.
Do not create a cron job yet. Do not access work or clinical files.
```

#### Personal Learning profile

Use this for books, articles, podcasts, videos, courses, research notes, and your second brain.

Suggested `SOUL.md`:

```markdown
# Personal Learning SOUL

You help me learn efficiently, turn reading into structured notes, and surface past insights when relevant.
You are evidence-aware, systems-thinking oriented, and careful about uncertainty.
You distinguish source claims, assumptions, implications, and my own reflections.
You do not turn learning notes into clinical recommendations.
```

Choose one knowledge home:

- a local markdown folder such as `~/Notes/Learning`
- an Obsidian vault
- a course folder inside `My-Nurse-AI-OS`

Create an inbox pattern:

```text
Learning/
  Inbox/
  Notes/
  Weekly-Digests/
  Skills/
```

Knowledge inbox prompt:

```text
I am in my Personal Learning profile.
Process this as a learning inbox item.
Use the HERMES Transformation Protocol:
1. Hear and Harvest the source faithfully.
2. Evaluate claims, assumptions, uncertainty, and bias.
3. Reframe for nursing, wellbeing, leadership, policy, AI, or innovation.
4. Map the system: stakeholders, incentives, feedback loops, constraints, and leverage points.
5. Enable: create prompts, checklists, workflows, learning steps, or experiments.
6. Steward: name safety, privacy, equity, accountability, reversibility, and stop conditions.

Output a markdown note with:
- title and date
- 5–10 bullet summary
- key concepts and definitions
- what this changes for my thinking or practice
- open questions
- what I should verify
- related notes or tags

Do not use PHI. Do not make patient-specific recommendations.
```

#### Saving workflows as skills

When a workflow works after 2–3 uses, turn it into a skill or reusable template.

Good candidates:

- `process-learning-inbox`
- `weekly-project-review`
- `research-claim-check`
- `career-map-review`

Skill rule:

> Save repeated procedures as skills only after the workflow has proven useful. Do not create a skill for every one-off prompt.

#### Weekly review cron — only after the manual workflow works

Cron jobs run in fresh sessions, so prompts must be self-contained. Do not assume the cron job remembers the current chat.

Begin with a manual weekly review. If the output is consistently useful, then create a scheduled job.

Safe personal-learning cron concept:

```text
Every Sunday at 5pm, review the Learning/Notes folder for new or updated notes from the past 7 days. Create a weekly learning digest with: what I read, top 5 ideas, 3 follow-up questions, and 1 grounded learning focus for next week. Do not access clinical or work files. Do not process PHI. Save the digest to Learning/Weekly-Digests/.
```

Safe personal-project cron concept:

```text
Every Sunday at 5pm, review the Personal Projects folder and create a weekly project review with: completed progress, blocked items, highest-leverage next actions, and one thing to pause. Do not make purchases, send messages, change files outside this folder, or create new automations without approval.
```

Cron boundary:

> Schedule only low-stakes, non-PHI, review-oriented workflows at first. Anything involving messaging, external systems, financial actions, legal decisions, clinical work, or employer systems requires a higher EDENA tier and human approval.

---

## Week 3 — Build Your Nurse-Centered Chief of Staff

**Goal:** Create a daily and weekly operating rhythm.

### Daily Brief Prompt

```text
Act as my nurse-centered Chief of Staff.

Create my daily brief using this structure:
1. What matters today
2. What needs preparation
3. What could create stress or overload
4. What I should not forget
5. What can wait
6. One action that protects my wellbeing
7. One decision that remains mine
```

### Weekly Review Prompt

```text
Run my weekly nurse-centered review.

Use this structure:
1. What happened this week?
2. What did I carry well?
3. What drained me?
4. What needs follow-up?
5. What pattern should I notice?
6. What relationship or responsibility needs attention?
7. What should I stop, start, or continue?
8. What is the safest next step?
```

---

## Week 4 — Build Your Learning OS

**Goal:** Turn information into capability without outsourcing judgment.

### Learning Pathway Prompt

```text
Act as my nurse-centered Learning OS.

I want to learn: [TOPIC]

Build a learning pathway that includes:
1. What I need to understand first
2. Core concepts
3. Common misconceptions
4. Practice scenarios
5. Questions to test my understanding
6. What evidence or guidelines I should review
7. What I should ask a human expert
8. How I will know I am improving
9. What I should not use AI for in this topic
```

---

## Week 5 — Build Your Professional + Community OS

**Goal:** Map career growth, contribution, and nurse-led innovation.

### Career Map Prompt

```text
Act as my nurse-centered career strategist.

Use my background, values, interests, constraints, and energy realities to create a career map.

Include:
1. Current strengths
2. Possible paths
3. Skills to build
4. Credentials to consider
5. People to learn from
6. Risks of each path
7. First small experiment
8. What decision remains mine
```

### Entrepreneurial Idea Prompt

```text
Act as my nurse-centered entrepreneurship advisor.

I have this idea: [IDEA]

Help me explore it without becoming reckless.

Use this structure:
1. Who might this help?
2. What problem does it address?
3. What evidence do we have?
4. What assumptions are we making?
5. What could go wrong?
6. What ethical or equity issues matter?
7. What is the smallest safe test?
8. What should not be promised yet?
9. What human review is needed?
10. What is the next grounded action?
```

---

## Week 6 — Govern, Review, and Sustain Your AI OS

**Goal:** Build long-term trust, boundaries, and review habits.

## HERMES Transformation Protocol

Use this for transcripts, links, articles, lectures, podcasts, ideas, or research.

### H — Hear and Harvest

Faithfully understand the source before remixing it.

### E — Evaluate

Assess evidence, assumptions, uncertainty, and bias.

### R — Reframe for Nursing

Translate into bedside, education, leadership, AI, policy, wellbeing, or innovation.

### M — Map the System

Identify stakeholders, incentives, feedback loops, constraints, and leverage points.

### E — Enable

Create tools, prompts, checklists, workflows, pilots, or learning plans.

### S — Steward

Check safety, privacy, equity, accountability, reversibility, and stop conditions.

---

## EDENA Stewardship Lens

Use this for major recommendations.

### E — Equity and Ethics

Who benefits? Who could be excluded or harmed?

### D — Dignity and Data

What data is involved? Is privacy protected? Is dignity preserved?

### E — Environment and Externalities

What effects appear outside the immediate task?

### N — Nursing Relevance and Nurse Wellbeing

Does this support nursing judgment, workflow, and wellbeing?

### A — Agency and Action

Who remains accountable? What action is safe, reversible, and human-led?

---

# Governed Loop Charter

Every loop needs a leash, a log, a limit, and a human owner.

```text
Loop Name:
Purpose:
Trigger:
Goal:
EDENA Tier:
Data Used:
PHI Risk:
Tools/Connectors:
Evaluation Method:
Stop Condition:
Maximum Runtime:
Maximum Cost:
Human Review Point:
Escalation Condition:
Audit Log Location:
Rollback Plan:
Named Human Owner:
```

---

# Practical Integrations: Notes, Google Workspace, and GitHub

These integrations should be added only after your basic Hermes setup, no-PHI boundary, workspace folder, and manual workflows are working.

Integration principle:

> Every connector is a doorway. Open only the doors you need, with the least privilege required, and keep a human owner responsible for review.

## Apple Notes → Obsidian Vault → Hermes

For learning and personal knowledge, the cleanest macOS pipeline is:

```text
Apple Notes → Obsidian vault → Hermes working with the vault as markdown files
```

### Step 1 — Move Apple Notes into Obsidian

Goal: convert Apple Notes into durable markdown files.

Recommended path:

- Install Obsidian.
- Use Obsidian's official Importer plugin.
- Choose Apple Notes as the import format.
- Follow Obsidian's instructions for selecting the Apple Notes database folder.
- Confirm the imported notes appear as `.md` files with attachments preserved where possible.

Alternative path:

- Use an Apple Notes exporter tool to export notes as markdown.
- Open the exported folder as an Obsidian vault.

Result:

```text
A stable Obsidian vault folder on disk that contains your notes as markdown.
```

### Step 2 — Make Obsidian the home for notes

Choose one single source of truth for notes going forward.

Simple structure:

```text
Obsidian Vault/
  Archive/Apple Notes Archive/
  Inbox/
  Learning/
  Projects/
  Personal/
  Professional-Non-PHI/
```

Keep Apple Notes read-only or occasional. Use Obsidian as the durable knowledge home.

### Step 3 — Point Hermes at the vault

Hermes' Obsidian workflow is filesystem-first. It reads, searches, creates, and edits markdown notes in a vault folder.

Set a vault path convention such as:

```bash
OBSIDIAN_VAULT_PATH=/Users/yourname/path/to/your/vault
```

Important safety rule:

> Do not publish `.env` files, API keys, vault paths with sensitive usernames, or private note contents.

When using file tools, Hermes needs the concrete absolute vault path. Do not pass unresolved variables like `$OBSIDIAN_VAULT_PATH` to file tools.

Starter prompt:

```text
Use my Obsidian vault as my long-term learning notebook.
Before writing, confirm the vault path and the target folder.
Create new learning notes under Learning/Inbox unless I specify another folder.
Use wikilinks when helpful.
Do not process PHI, patient identifiers, confidential employer data, passwords, API keys, or private family information.
```

## Google Workspace for a non-personal account

Use Google Workspace only after the no-PHI boundary is clear.

Recommended path when you need Gmail + Drive + Docs:

- Use the Hermes Google Workspace skill.
- Use a dedicated non-personal Google account when possible.
- Complete OAuth through the official Google Cloud / OAuth flow.
- Enable only the APIs required for the workflow.
- Keep a human approval step before sending emails, modifying files, or sharing documents.

The Google Workspace integration may support Gmail, Calendar, Drive, Docs, Sheets, and Contacts depending on current Hermes setup.

Email-only alternative:

- Use the email / IMAP-SMTP path if you only need mailbox access.
- For Gmail, use 2-step verification and an app password.
- Do not use your normal Google password.

Boundary:

> Do not connect Hermes to personal Gmail, employer Gmail, Drive folders with PHI, confidential HR files, legal documents, or clinical operations folders unless formal governance and approval exist.

Safe first Google Workspace prompt:

```text
Help me set up a dedicated non-personal Google Workspace connection for non-PHI learning and project work.
Before any setup, list the scopes or APIs needed, what data they can access, and the approval boundaries.
Do not send emails, modify files, share documents, or access clinical/employer data without explicit approval.
```

## GitHub and GitHub Pages

GitHub can serve two different purposes:

1. **Private working repos** for drafts, code, prompts, experiments, and project development.
2. **Public GitHub Pages repos** for polished websites, landing pages, docs, and public learning artifacts.

Recommended structure:

```text
Private repo = working area
Public GitHub Pages repo = published output
```

Use private repos when material includes:

- drafts
- unfinished code
- personal notes
- proprietary ideas
- private project planning
- anything not ready to be copied or indexed

Use public repos only when the content is intentionally publishable.

GitHub Pages is for static public websites. Do not use it for secrets, API keys, private notes, PHI, clinical files, or dynamic apps requiring server-side secrets.

Safe first GitHub prompt:

```text
Help me design a GitHub setup for this project.
Separate what belongs in a private working repo from what belongs in a public GitHub Pages repo.
Before creating or publishing anything, scan for PHI, secrets, API keys, confidential employer material, and private notes.
Do not push until I approve the repo name, visibility, and files.
```

### macOS GitHub day-one setup

Use this when participants are ready to let Hermes help with code storage or simple websites.

1. Install GitHub CLI:

```bash
brew install gh
```

2. Log in:

```bash
gh auth login
```

Recommended beginner choices:

- GitHub.com
- HTTPS
- browser-based login

3. Confirm Hermes and GitHub are available:

```bash
hermes --version
gh auth status
```

4. In Hermes Desktop, enable GitHub-related skills in the Projects or Professional Non-PHI profile.

5. Optional advanced path: add a GitHub MCP server only when there is a real need for richer issue, PR, or repo tools. Store tokens in a secure environment file or Hermes auth path. Do not paste live tokens into public notes, public repos, slides, or screenshots.

Safer MCP token pattern:

```yaml
mcp_servers:
  github:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "[REDACTED_OR_ENV_REFERENCE]"
```

For most beginners, `gh auth login` plus Hermes GitHub skills is enough.

### Private code repo prompt

```text
This folder is my new project.
Initialize git here, create a GitHub repository, and connect the two.
Make the repository private by default.
Before pushing, show me the files that will be committed and scan for PHI, secrets, API keys, credentials, and private notes.
Do not push until I approve.
```

### Public GitHub Pages prompt

```text
This folder is a public GitHub Pages site.
Create or update a simple static site using index.html, CSS, and public-safe assets.
Before publishing, scan for PHI, secrets, API keys, confidential employer material, personal notes, and anything not intentionally public.
Use the main branch root for GitHub Pages unless I specify otherwise.
Verify the live site after deployment.
```

## Image Generation for Personal Projects and Learning Dashboards

Hermes does not need a separate local image generator installed. Image generation is exposed through Hermes tools, commonly through Nous Portal / Tool Gateway or a direct FAL.ai backend.

Simple setup path:

```bash
hermes setup --portal
hermes tools
```

In `hermes tools`, enable image generation and choose a backend such as Nous Subscription or FAL.ai. Tool availability, models, and pricing can change; check the current Hermes docs and provider terms.

Good first uses:

- personal website hero image
- learning dashboard background
- Obsidian dashboard visual
- project logo concepts
- article/banner draft images

Nurse-safe boundaries:

- No patient photos.
- No PHI in prompts.
- No screenshots containing patient identifiers.
- Do not imply clinical endorsement or diagnostic capability through generated images.
- Use generated images as drafts until reviewed by a human.

Starter image prompts:

```text
Generate a calm 16:9 hero illustration for a personal learning dashboard: warm navy, soft gold, subtle knowledge graph motif, nurse-centered but non-clinical, no text, no patient imagery.
```

```text
Create a square logo concept for a personal learning vault called "Learning OS": simple vector style, warm human-centered design, no medical symbols, no text unless typography is reliable.
```

```text
Generate a background for an Obsidian Personal Learning dashboard: dark mode friendly, subtle interconnected notes and soft glow, minimal distraction, no text.
```

## Video Generation for Learning Dashboards

Video generation is optional and advanced. Use it mainly for short, low-distraction loops, not long clinical explainers.

Common setup concepts:

- Enable video tools through `hermes tools` when available.
- Use Nous Tool Gateway when supported or a direct provider key such as FAL for video models.
- Keep generated clips short and non-distracting.
- Treat costs as variable and check provider pricing before repeated generation.

Best uses for the course audience:

- 4–8 second ambient learning dashboard loops
- subtle knowledge graph motion
- study timer background
- daily review loop
- gentle image-to-video animation from an already approved still image

Design rules:

- Prefer slow drift, pulse, glow, or parallax.
- Avoid fast cuts or dramatic camera movement.
- Avoid text inside videos unless the chosen model handles typography well.
- Do not use patient images, clinical screenshots, or PHI.
- Use human review before publishing.

Starter video prompts:

```text
Create a 6-second seamless loop for a learning dashboard background: soft blue and slate abstract gradients, gentle particle drift, minimal motion, clean modern interface aesthetic, no text, 16:9.
```

```text
Generate a subtle animated concept visual for a note-taking dashboard: interconnected nodes and faint lines pulsing slowly like a knowledge graph, calm and readable, dark-mode friendly, seamless 8-second loop, no text.
```

```text
Animate this existing dashboard hero image into a 5-second loop with slow parallax, slight glow movement, and gentle depth. Preserve the original composition and keep motion subtle.
```

### Knowledge Graph Dashboard Prompt Pack

Use these when building a personal learning dashboard, Obsidian homepage, or knowledge-management visual.

Static image prompts:

```text
Create a clean dark-mode knowledge graph dashboard background: interconnected glowing nodes and fine linking lines, soft blue and teal palette, subtle depth, modern research interface aesthetic, minimal visual clutter, large empty central area for dashboard cards, no text, no labels, no logos, 16:9.
```

```text
Generate a minimalist personal learning dashboard hero image: abstract knowledge graph with clustered concepts, gentle gradient background in slate and indigo, small luminous nodes, elegant line connections, premium software product feel, readable behind interface panels, no labels, no text, 16:9.
```

```text
Design a visual for a knowledge management dashboard: network map of ideas with a few brighter hub nodes and many faint peripheral nodes, calm scientific mood, clean dark background, subtle glassmorphism atmosphere, no text, no logos, 16:9.
```

Ambient loop prompts:

```text
Create a seamless 6-second loop for a dark-mode learning dashboard: a floating knowledge graph of glowing nodes and connecting lines, gentle pulse through the network, slow drifting particles, minimal camera movement, calm and non-distracting, slate blue and teal palette, no text, 16:9.
```

```text
Generate an 8-second ambient loop for a personal knowledge dashboard: clustered concept nodes connected by elegant lines, subtle wave of light moving through the graph, steady camera, soft depth, modern research-lab interface feel, seamless loop, dark background, no text, 16:9.
```

Image-to-video prompt:

```text
Animate this knowledge graph dashboard image into a 5-second seamless loop with slow parallax, faint node pulsing, and a soft traveling light across a few connections. Keep composition stable and motion subtle for use behind interface cards. No scene changes, no camera jumps, no text.
```

Style variations:

- Scientific: clinical, precise, network intelligence, cool blue, minimal glow.
- Creative PKM: hand-drawn constellation of ideas, warm neutral background, elegant ink-like links, modern notebook aesthetic.
- Futuristic: glassy nodes, volumetric depth, slow holographic pulse, premium AI dashboard aesthetic.
- Quiet productivity: soft grayscale graph, one accent color, almost no particle effects, distraction-free UI background.

Prompt rule:

```text
Create a [static image / seamless 6-second loop] for a [personal learning / knowledge management] dashboard: [knowledge graph subject], [color palette], [motion behavior], [camera behavior], [mood], readable behind interface panels, no text, 16:9.
```

## Research Integrations: Three-Lane Setup

Hermes research should start simple and become more specialized only when needed.

Core pattern:

```text
Native web tools → specialized MCP when needed → reusable research skills → scheduled review only after workflow is proven
```

### Lane 1 — Personal Knowledge Research

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

### Lane 2 — Academic / Medical Reading

Best for papers, guidelines, white papers, reports, and evidence summaries.

- Storage: vault folders such as `Reading Inbox`, `Papers`, `Clinical Topics`, and `Evidence Summaries`.
- Tools: `web_search`, `web_extract`, PDF URL extraction, and browser only when needed.
- Skills to create after the workflow works: `read-paper`, `summarize-guideline`, `compare-studies`, `evidence-brief`.
- Output: question, population, intervention/exposure, findings, limitations, confidence, practical takeaway, and original source link.

Boundary:

> Hermes may summarize and compare sources. It does not replace clinical judgment, guideline review, institutional policy, or licensed decision-making.

Prompt:

```text
Read this academic or medical source as evidence, not as clinical advice.
Separate claims, methods, findings, limitations, uncertainty, and practical implications.
Create an evidence-aware note I can review against the original source.
Do not make patient-specific recommendations.
```

### Lane 3 — Technical Project Research

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

## Perplexity Research via MCP

Perplexity can be added as a specialized research source through MCP, but it should not replace Hermes' native web tools or source review.

Best use:

- citation-rich research questions
- current topic reconnaissance
- source discovery before deeper extraction
- comparing against Hermes native web-search results

Recommended pattern:

```text
Hermes = workflow brain
Native web tools = baseline research
Perplexity MCP = specialized citation-rich research source
Obsidian / repo notes = durable output
Skills = reusable method
```

Setup options:

1. Composio Perplexity MCP — easier managed route if already using Composio.
2. Direct Perplexity MCP server — more direct, self-managed route using a Perplexity API key.

Safety requirements:

- Store API keys in `.env` or the approved Hermes credential path; never paste real keys into notes, public repos, slides, or screenshots.
- Use MCP tool filtering; expose only the tools needed.
- Treat Perplexity answers as source leads, not final truth.
- Verify high-stakes claims against original sources.
- Do not use Perplexity MCP for PHI, patient-specific decisions, confidential employer material, or clinical operations.

Public-safe config pattern:

```yaml
mcp_servers:
  perplexity:
    command: npx
    args: ["-y", "perplexity-mcp"]
    env:
      PERPLEXITY_API_KEY: "[REDACTED_OR_ENV_REFERENCE]"
    tools:
      include: ["search", "ask"]
```

Prompt:

```text
Use Perplexity MCP only as one research source.
Find source leads and citations, then verify important claims with original sources where possible.
Create an evidence-aware markdown note with: question, answer summary, sources to verify, uncertainties, and next research step.
Do not process PHI or patient-specific clinical questions.
```

---

# Advanced Growth and Sovereign Systems Pathway

The foundational class prepares participants to work responsibly with individual AI assistants and agents. As their responsibilities and projects expand, the **Advanced Growth Map** introduces the skills required to supervise an increasingly complex AI ecosystem.

Participants first learn to define agent roles, permissions, task boundaries, handoffs, escalation pathways, evaluation criteria, and human accountability. When one agent is no longer sufficient, the advanced pathway may include **OpenClaw integration** as an orchestration layer for coordinating multiple specialized agents across separate workspaces, functions, and communication channels. OpenClaw supports multi-agent routing with isolated agent workspaces, state, and session histories through a shared gateway.

Reference: https://docs.openclaw.ai/concepts/multi-agent

The progression is:

```text
AI user → AI supervisor → Agent manager → Multi-agent ecosystem steward
```

OpenClaw integration is introduced only when multiple agents create genuine operational value. Complexity is never added for appearance, novelty, or unnecessary automation.

Every multi-agent system must retain:

- Clearly designated human ownership
- Least-privilege permissions
- Defined agent responsibilities
- Approval gates for consequential actions
- Complete logging and auditability
- Failure detection and escalation procedures
- Data-minimization and confidentiality controls
- Cost, energy, and environmental monitoring
- A manual fallback and safe shutdown process

OpenClaw or any comparable orchestration platform must not be connected to sensitive healthcare systems, patient information, clinical workflows, or organizational infrastructure without formal security review, technical validation, and institutional approval.

## Separate Advanced Module: Sovereign On-Premises AI Systems

Designing and implementing a **sovereign, on-premises AI system** for a hospital unit, clinic, public-health program, or community organization is a separate advanced module and implementation pathway.

The foundational masterclass does not by itself prepare or authorize participants to deploy production clinical AI infrastructure. It provides the essential conceptual foundation needed to participate intelligently in such work, including:

- AI and agent literacy
- Human-in-the-loop workflow design
- Critical and systems thinking
- Source and output evaluation
- Privacy-aware data practices
- Role and permission design
- AI governance fundamentals
- Risk identification
- Workflow mapping
- Ethical and environmental stewardship

The sovereign-systems module builds on those foundations and addresses:

- Local and private model deployment
- Secure infrastructure architecture
- Identity and access management
- Network segmentation
- Protected health information controls
- Data residency and retention
- Encryption and key management
- Retrieval-augmented knowledge systems
- Model and agent evaluation
- Audit trails and observability
- Cybersecurity and supply-chain review
- Backup, recovery, and business continuity
- Clinical validation and change control
- Interoperability with approved organizational systems
- Incident response and safe shutdown
- Regulatory, legal, privacy, and institutional governance
- Lifecycle cost and environmental impact

Such systems require collaboration among clinical leadership, nursing, informatics, information security, privacy, legal counsel, compliance, data governance, biomedical or technical teams, and the communities affected by their use.

> **The class teaches participants how to begin working with AI responsibly. The Advanced Growth Map teaches them how to steward multiple agents. The Sovereign Systems Module prepares qualified teams to explore institutionally governed, locally controlled AI infrastructure.**

---

# First 10 Prompts

## 1. Daily Chief of Staff

```text
Act as my nurse-centered Chief of Staff. Help me identify what matters today, what can wait, what needs follow-up, and what action protects my wellbeing.
```

## 2. Weekly Review

```text
Run my weekly review across personal, professional, and community spheres. Help me notice patterns, risks, unfinished commitments, and one grounded next action.
```

## 3. Learning Pathway

```text
Act as my Learning OS. Build a learning pathway for [topic] with concepts, practice, self-test, evidence check, and human-expert review points.
```

## 4. Career Map

```text
Act as my nurse-centered career strategist. Map possible paths from my current experience toward roles that match my values, strengths, constraints, and energy.
```

## 5. Research Transformation

```text
Use the HERMES Transformation Protocol on this article/transcript/link. Hear and Harvest, Evaluate, Reframe for Nursing, Map the System, Enable, and Steward.
```

## 6. Systems Map

```text
Help me map this situation as a system. Identify stakeholders, incentives, feedback loops, friction points, risks, and leverage points.
```

## 7. EDENA Review

```text
Apply the EDENA Stewardship Lens to this recommendation. Evaluate Equity and Ethics, Dignity and Data, Environment and Externalities, Nursing Relevance and Nurse Wellbeing, and Agency and Action.
```

## 8. Entrepreneurial Idea Review

```text
Review this nurse-led idea. Be imaginative but not reckless. Identify who it helps, assumptions, risks, smallest safe pilot, evidence needed, and what I should not claim yet.
```

## 9. Dependency Check

```text
Check whether I am over-relying on AI in this decision. What must I verify? What judgment remains mine? What human should I consult?
```

## 10. Loop Charter

```text
Help me design a safe AI loop for [workflow]. Define trigger, goal, EDENA tier, data boundary, stop condition, human review point, and named owner.
```

---

# 30-Day Sustainment Plan

Weekly:

- review your Daily Brief and Weekly Review workflow
- delete or correct memory that is outdated
- check if AI is strengthening or weakening your judgment
- update one prompt or template
- identify one thing that should remain human-only

Monthly:

- review your no-PHI boundary
- review your professional goals
- apply EDENA to one major recommendation
- retire one workflow that no longer helps
- choose one safe improvement for the next month

---

# Completion Statement

I have built a nurse-centered AI operating system for personal, professional, and community use, governed by human agency, evidence-awareness, safety boundaries, and nursing stewardship.
