# Hermes Setup Safety Checklist

Use this checklist before connecting models, tools, memory, voice, messaging, or sub-agents.

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

## 6. Sub-agent safety

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

## 7. Connectors

Before connecting Telegram, Discord, Slack, voice, or other channels, ask:

- What data can pass through this channel?
- Who else can see it?
- Can messages be forwarded, stored, or searched?
- What should never be sent here?
- How do I disconnect it?

Connector rule:

> Do not connect Hermes to sensitive healthcare systems, employer systems, patient data, or confidential channels without formal approval.
