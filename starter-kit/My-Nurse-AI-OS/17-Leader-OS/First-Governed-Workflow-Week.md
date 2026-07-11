# Your First Governed Workflow in One Week

The research on nurse managers and AI is blunt: the barrier is training and infrastructure, not willingness. So this sprint is deliberately small — **seven days, ~30 minutes a day, one real workflow running under real governance by Sunday**, plus the one-page accountability charter that makes your method defensible to anyone who asks.

The default first workflow is the **weekly unit brief** (`Weekly-Brief.SKILL.md`) — low risk, honest value, weekly rhythm. If your pain lives elsewhere, substitute; the days don't change.

## The week

**Day 1 — Name the workflow and its risk.** With `Governance-Facilitator`, classify your chosen workflow: what task, whose data, what happens on failure, proposed EDENA tier. Output: the one-page classification. (New to the tiers? The 90-minute workshop in `../13-Living-Thriving-AI/` is the unit-grade orientation — schedule it for your team this month, not this week.)

**Day 2 — Write the Loop Charter.** Fill `../04-Governance/Loop-Charter.md` for the workflow: leash, log, limit, human owner, stop condition, rollback. Twenty minutes, honestly answered, especially "what does *contain* look like?" (see the incident one-pager).

**Day 3 — Set the memory boundary.** Confirm your Do-Not-Remember rules with the Manager/Leader extension are in your Governance boot; tell your AI what this workflow may keep (unit priorities, project states) and must not (anything on the extension list). Test it: paste something borderline and watch it refuse.

**Day 4 — First supervised run.** Run the workflow start to finish with the skill, reviewing every step. Edit hard — your edits are training *you* on where the tool is weak, and they're gate-health data. Log the run in `../04-Governance/Human-Review-Log.md`.

**Day 5 — Run the Five Rights pre-flight and go live.** Right task, right data, right tier, right human, right review — any "no" is a redesign, not a footnote. Passing: schedule the cron (for a weekly brief: draft lands Thursday, you approve Friday).

**Day 6 — Write your Unit AI Accountability Charter** (template below). This is the professional-accountability move: leaders establish explicit responsibility-and-accountability measures for AI use — yours now exist in writing.

**Day 7 — Journal and tell one person.** Log the whole decision (what, why, review date in 30 days) with `Decision-Journal`. Then tell one colleague or your director what you built and show the charter — governance kept private protects no one, and the telling is what makes you the unit's credible AI voice.

## The Unit AI Accountability Charter (copy, fill, sign, post)

```
UNIT AI ACCOUNTABILITY CHARTER — <unit> · <date> · v1

Accountable owner: <name>. AI assistance on this unit runs under
this charter; the owner answers for it.

What runs: <workflow list>, each with a Loop Charter on file at
<location>.

The standing rules:
1. No patient information enters any AI system. If it could
   identify a patient, it counts.
2. The AI never evaluates, ranks, or recommends action on a named
   staff member. People decisions are human decisions.
3. Everything staff-facing is approved by <owner/delegate> before
   it goes out. Rejections and edits are logged — they are data.
4. No connections to employer systems (HRIS, EHR, scheduling,
   Teams/Slack) without <org compliance path> approval.
5. Any of us can say "this output looks wrong" and pause the
   workflow — the stop condition is in each charter. Incident
   process: see the unit one-pager, posted at <location>.

Review: gate health checked monthly (unchanged-approval streaks
trigger a spot-check); this charter re-read quarterly;
review log at <location>.

Signed: ________________  Date: ________
```

## After the week

One workflow governed is a method proven. The pattern repeats: classify → charter → boundary → supervised run → pre-flight → live → journal. Second candidates: QI project support (`QI-Coach`), the staffing-pattern brief (`Staffing-Lens`), policy drafting (`Policy-Drafter`). And when your organization asks how you're governing AI — and it will — you hand them the charter, the charters behind it, and the review log. That's the defensible method.

> Agents propose. Humans judge. Nurses steward.
