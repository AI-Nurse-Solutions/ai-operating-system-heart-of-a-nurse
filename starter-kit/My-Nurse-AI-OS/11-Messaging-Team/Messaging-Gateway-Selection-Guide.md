# Messaging Gateway Selection Guide

Hermes messaging channels are doors into an agent profile. Every door needs an owner, an allowlist, and a clear purpose.

## Quick comparison

| Platform | Best for | Advantages | Watch-outs |
|---|---|---|---|
| Telegram | personal access, small groups, quick setup | easy BotFather setup, streaming, voice notes, images, files | separate from many work environments |
| WhatsApp Cloud API | family / field teams / public-facing access | familiar app, official business API, buttons and media | Meta setup, webhooks, policies, 24-hour windows |
| Slack | work teams | channel workflows, threads, team visibility | admin approval, not ideal for personal life |
| Discord | communities and dev groups | streaming, media, community workflow | not common for healthcare professional settings |
| Signal | privacy-focused communication | privacy posture | smaller ecosystem and less mainstream bot support |
| SMS | universal phone access | no app required | provider cost, weak formatting, limited media |
| Email | longform summaries and reports | universal, good for digests and triage | not real-time and can clutter inbox |

## Recommended first setup

```text
Personal use: Telegram or WhatsApp
Longform reports: Email
Team use: Slack or Telegram
```

## Prompt

```text
Help me choose the safest first Hermes messaging channel for my use case.
Compare Telegram, WhatsApp, Slack, Email, and SMS for setup difficulty, privacy, media support, team use, and risk.
Recommend one starting channel and one reporting channel.
Before setup, define allowed users, home channel, no-PHI boundary, and approval rules.
```
