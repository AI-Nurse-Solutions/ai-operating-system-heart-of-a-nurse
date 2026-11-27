# The Dr. Engie Domondon Community Hub Package

Hermes packet v0.1.0 · Community Development AI Team

## Dedication

This package is named in honor of **Dr. Engie Domondon**, a labor and delivery nurse leader. She organized a group of fishermen to carry medicines and healthcare staff across many islands, and she established schools and clinics in marginalized communities, including leper colonies.

This is what nurses are capable of with the right tools.

## What it is

A human-led, five-agent community organizing team packaged as skills for Hermes Agent, plus the organizer's 30-day playbook and a 56-case evaluation kit. Built for nurses organizing a unit, council, or project community.

**AI supports the community. People lead the community.**

## What's inside

| Skill | Use it for |
| --- | --- |
| `community-dev-team` | Overview, routing, shared rules, workspace template, full ten-agent roster and rollout |
| `community-listener` 👂 | Summarizing approved community input into themes |
| `issue-intelligence` 🔎 | Framing the problem before choosing a solution |
| `project-navigator` 🧭 | Tracking approved initiatives, owners, blockers, pilots |
| `community-chief-of-staff` 🎯 | The weekly brief of what needs human attention |
| `governance-guardian` 🛡️ | Green / Amber / Red screening and escalation |
| `community-organizer-30-day` | The organizer's first-month, relationship-first plan |
| `community-team-evaluation` | Test suite, rubric, score sheet, scorecard |

## Install
1. Unzip this packet.
2. Copy the folder `skills/community-development/` into `~/.hermes/skills/` so you have `~/.hermes/skills/community-development/community-listener/SKILL.md` and so on.
   - Alternative: leave the packet where it is and add its `skills` folder under `skills.external_dirs` in `~/.hermes/config.yaml`.
3. Copy `skills/community-development/community-dev-team/templates/workspace/` to `~/community-development/`. This is the team's shared, local workspace.
4. Start Hermes and type `/community-dev-team` to confirm the skills loaded.

## First use
- Start with people, not agents: `/community-organizer-30-day I'm on day 1`.
- Before any live use, run the evaluation: `/community-team-evaluation run batch 1`.
- Then put approved input in `~/community-development/inbox/` and try `/community-listener summarize what's in the inbox`.
- Weekly: `/community-chief-of-staff prepare my Monday brief`. You can ask Hermes to schedule this.

## Ground rules that do not change
- No PHI and no patient-specific clinical advice. This team is non-clinical.
- No ranking, scoring, or profiling of colleagues, and no guessing who wrote anonymous feedback.
- A recommendation is never a decision. Approvals live in `decisions/decision-log.md`, written by people.
- Follow your organization's policies on AI tools and on what information may be placed in the workspace. The Governance Guardian screens; it does not grant compliance.
- The targets in the evaluation kit are proposed MVP thresholds, not external standards.

## Notes
- All example people, projects, and scenarios are fictional.
- The packet is tool-neutral: records are plain markdown and CSV files on your own machine.
- Agent instructions are v0.1.0. Change → retest → regression test before raising the version.
