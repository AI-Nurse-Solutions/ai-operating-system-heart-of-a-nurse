# Hermes Setup Safety Checklist

Use this checklist before connecting models, tools, memory, voice, messaging, or sub-agents.

## 0. Official Hermes Agent setup path

- [ ] I started at the official Hermes Agent site: https://hermes-agent.nousresearch.com/ or the official Nous Research Hermes documentation/GitHub path.
- [ ] I avoided third-party mirrors and unofficial download sites.
- [ ] I followed the current official instructions for my operating system instead of relying on a copied installer from Nurse AI OS.
- [ ] If my operating system warned me, I confirmed the source before opening or installing anything.
- [ ] I completed first-run onboarding and verified one normal chat works.
- [ ] Optional Terminal check for technical users: `hermes --help` or the current official Hermes command opens without error.

## 1. Workspace

- [ ] Hermes workspace points to my intentional course folder, not my whole computer.
- [ ] The folder does not contain patient information, confidential employer files, passwords, or private family data.
- [ ] I know what files Hermes can read and write.

## 2. Safety controls

- [ ] Manual approval is on for beginner use.
- [ ] Autonomous or smart approval is off unless I understand the risk.
- [ ] I know how to decline, stop, or cancel a tool action.
- [ ] I will start with small safe tasks first.

## 3. Memory

Use memory for:

- writing preferences
- learning goals
- non-PHI professional interests
- recurring workflow preferences

Do not store:

- patient identifiers
- confidential employer details
- API keys, passwords, or tokens
- sensitive family information
- anything that should not resurface later

## 4. Providers and API keys

- [ ] I understand that “free” model availability may change.
- [ ] I checked current provider terms, privacy policies, rate limits, and cost.
- [ ] I did not paste API keys into public notes, screenshots, GitHub, course forums, or shared documents.
- [ ] If an API key is exposed, I will revoke it and create a new one.

## 5. Safe first tasks

Try:

```text
Read my Nurse-AI-OS folder and summarize the starter files you see. Do not access other folders. Do not modify anything yet.
```

Then:

```text
Create a new folder called Practice inside My-Nurse-AI-OS and write a short README explaining that this is a safe test folder.
```

## 6. Post-setup dashboard bookmark

- [ ] I opened the **Local HTML Life Dashboard** first at `08-Integrations/Local-HTML-Life-Dashboard/index.html` in my browser for health, finances, goals, habits, tasks, and routines.
- [ ] I created a browser bookmarks folder named **Dashboards**.
- [ ] I saved the local dashboard as a bookmark under **Dashboards**.
- [ ] I confirmed the dashboard contains no PHI, patient identifiers, employer secrets, account numbers, credentials, diagnosis, treatment, medication, or clinical advice.
- [ ] I understand local browser storage can be cleared, so I will export a JSON backup if I begin relying on it.
- [ ] I understand Notion is an advanced option for relational dashboards, filters, shared views, or command-center structure after the Local HTML dashboard is stable.

## 7. Sub-agent safety

Sub-agents are useful for parallel research and comparison, but they still need boundaries.

Safe beginner pattern:

```text
Fire two sub-agents for a non-clinical learning task.
Agent 1: summarize the benefits.
Agent 2: summarize the risks and limitations.
Then synthesize both sides and tell me what I should verify before acting.
No PHI. No clinical decisions.
```

Avoid sub-agents for patient-specific care, confidential employer work, financial/legal/clinical decisions, or high-stakes recommendations without expert review.

## 8. Connectors

Before connecting Telegram, Discord, Slack, voice, or other channels, ask:

- What data can pass through this channel?
- Who else can see it?
- Can messages be forwarded, stored, or searched?
- What should never be sent here?
- How do I disconnect it?

Connector rule:

> Do not connect Hermes to sensitive healthcare systems, employer systems, patient data, or confidential channels without formal approval.
