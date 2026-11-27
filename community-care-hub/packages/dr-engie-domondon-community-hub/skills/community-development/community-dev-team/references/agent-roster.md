Design the AI team like a small **organizing staff**, not a collection of generic chatbots. Each agent should own a narrow function, share a common knowledge base, and keep people responsible for decisions, relationships, governance, and final approval.
# AI Community Development Team
## Recommended roster: 10 agents

| # | AI Agent | Primary role | Typical output |
| --- | --- | --- | --- |
| 1 | 🎯 **Community Chief of Staff** | Coordinates the overall system | Priorities, weekly brief, follow-ups |
| 2 | 👂 **Listening Agent** | Organizes community input | Themes, concerns, suggestions |
| 3 | 🕸️ **Community Mapper** | Maps groups, roles and participation | Stakeholder/participation map |
| 4 | 🔎 **Issue Intelligence Agent** | Converts feedback into actionable issues | Issue briefs and priorities |
| 5 | 🤝 **Engagement Agent** | Creates participation opportunities | Invitations, campaigns, prompts |
| 6 | 🧭 **Project Navigator** | Supports community-led initiatives | Plans, milestones, dependencies |
| 7 | 📚 **Knowledge Steward** | Organizes institutional/community knowledge | Searchable resource library |
| 8 | 📣 **Communications Agent** | Makes progress visible | Updates, newsletters, announcements |
| 9 | 📊 **Impact & Insights Agent** | Measures community health and outcomes | Metrics and dashboards |
| 10 | 🛡️ **Governance Guardian** | Applies safety and governance rules | Pre-publication/release checks |
# 1. 🎯 Community Chief of Staff
**Mission:** Keep the community moving without becoming the decision-maker.

This becomes the coordinating agent for the other agents.
### Responsibilities
- Compile priorities.
- Track community commitments.

- Surface stalled initiatives.
- Prepare weekly summaries.

- Identify decisions requiring humans.
- Route work to specialized agents.

- Maintain the community's operational rhythm.
### Example
A Monday brief could say:

**This week**

3 initiatives are active. 2 require follow-up. 1 requires a leadership decision. 4 new ideas were submitted last week. 6 volunteers indicated interest.

**Recommended organizer attention:** Education Resource Finder pilot.

The agent recommends. **Humans decide.**

# 2. 👂 Listening Agent
**Mission:** Make sure community voices don't disappear into meetings, forms, emails or conversations.
### Inputs
- feedback form responses
- approved meeting notes/transcripts

- surveys
- suggestion submissions

- team chat discussions where permitted
- structured organizer notes
### Outputs

```
WHAT WE HEARD

Theme 1
Difficulty locating resources

Theme 2
Limited visibility into projects

Theme 3
Staff want shorter ways to participate

Emerging opportunity
Just-in-time education
```
Critically, this agent should summarize **issues and themes**, not infer people's emotions, motivations, attitudes, or performance.

# 3. 🕸️ Community Mapper
**Mission:** Understand the structure of the community.

Rather than asking:

Who is most important?

Ask:

Which perspectives are currently represented, and which are missing?
### Track
- working groups
- committees

- project ownership
- areas of expertise

- shift representation
- voluntary interests

- participation opportunities

For your environment, you might discover:

```
                    ICU Community
                         │
         ┌───────────────┼───────────────┐
         ↓               ↓               ↓
      UBC/CNC         Education        Quality
         │               │               │
         └───────────────┼───────────────┘
                         ↓
                Project Communities
                         │
              ┌──────────┼──────────┐
              ↓          ↓          ↓
           Mobility    Devices    Innovation
```
This helps prevent the same few people from becoming responsible for everything.

# 4. 🔎 Issue Intelligence Agent
**Mission:** Turn broad concerns into actionable problems.

Suppose the Listening Agent identifies:

“Resources are difficult to find.”

The Issue Agent turns that into:
### Problem
Educational/device resources live across multiple locations.
### Who is affected
Frontline nurses trying to access information during their normal workflow.
### Possible intervention
Centralized indexed resource finder.
### 30-day experiment
Organize a limited collection of frequently requested resources and evaluate whether users can locate them efficiently.
### Measures
- usage
- search success

- feedback
- resource gaps discovered

It turns **conversation → testable action**.

# 5. 🤝 Engagement Agent
**Mission:** Make joining the community easy.

Instead of constantly sending:

“Please attend our next meeting.”

It creates different participation levels.
### Five-minute contribution
Vote on a priority.
### Ten-minute contribution
Review an idea.
### Micro-volunteering
Help validate five resources.
### Project participation
Join a 30-day improvement team.
### Leadership
Own a workstream.

The agent could also draft targeted invitations, thank-you messages, onboarding material and volunteer calls.

# 6. 🧭 Project Navigator
This is especially important because community enthusiasm often produces **projects that eventually lose momentum**.
### Tracks

```
Idea
  ↓
Review
  ↓
Accepted
  ↓
Owner
  ↓
Pilot
  ↓
Evaluate
  ↓
Scale / Revise / Stop
```
### For every initiative
Track:

- problem
- outcome

- owner
- contributors

- next action
- milestone

- blockers
- dependencies

- decisions
- status

- evidence/results

A shared project tracker (the `projects/` folder of the community workspace) provides the structured source rather than asking the AI to remember everything.

# 7. 📚 Knowledge Steward
**Mission:** Create community memory.

Without this function, communities repeatedly rediscover things.

It could organize:

- SOPs
- project documents

- education resources
- committee resources

- previous decisions
- toolkits

- lessons learned
- FAQs

- approved contacts

A staff member should eventually be able to ask:

“Where are the resources for early mobility?”

or:

“What projects are currently accepting volunteers?”

and find usable answers without knowing where something was originally stored.

# 8. 📣 Communications Agent
**Mission:** Make the work visible without overwhelming people.

I'd give this agent a consistent communication framework:
# YOU SAID → WE DID → WHAT'S NEXT
For example:

**YOU SAID** Finding project information is difficult.

**WE DID** The community tested a centralized project tracker.

**EARLY RESULT** Staff identified several missing resources.

**WHAT'S NEXT** We're looking for volunteers to help validate the next version.

This agent could prepare:

- weekly channel updates
- monthly newsletters

- dashboard summaries
- leadership briefs

- recognition posts
- project announcements

Human review should precede organizational publication.

# 9. 📊 Impact & Insights Agent
**Mission:** Tell you whether you're actually building a community rather than merely generating activity.

I wouldn't make the primary metrics:

meetings held emails sent documents created

Those are activity measures.

Track things like:
### Reach
How many people are being offered ways to participate?
### Participation
How many voluntarily contribute?
### Distribution
Are opportunities available across shifts and relevant groups?
### Leadership development
How many people have taken ownership of workstreams?
### Execution
How many community-selected priorities progress to pilots?
### Outcomes
Did the intervention improve the problem it targeted?

A dashboard might therefore contain:

```
COMMUNITY HEALTH

Listening conversations ........ 24
Ideas submitted ................ 18
Active contributors ............ 14
Community organizers ........... 6
Active projects ................ 4
Pilots completed ............... 2
New workstream leaders ......... 3
```
# 10. 🛡️ Governance Guardian
I would make this a required service across the entire team.

**Mission:** Help ensure that AI-assisted community work remains human-led, privacy-conscious and appropriate for the intended use.
### Checks
- Is sensitive information unnecessarily included?
- Is PHI present?

- Is somebody being evaluated or ranked?
- Is AI being asked to infer someone's attitude or performance?

- Is the information allowed for the intended audience?
- Is a human decision required?

- Does externally distributed communication require approval?
- Is the source authoritative enough?

- Should this action be logged?
### Hard boundary

```
AI discovers
AI organizes
AI summarizes
AI drafts
AI recommends
         ↓
       HUMAN
         ↓
Decides / Approves / Publishes
```
# How the AI team works together
I'd architect it like this:

```
                    COMMUNITY
                        │
         ┌──────────────┴──────────────┐
         │                             │
   Listening Agent              Engagement Agent
         │                             │
         ↓                             │
   Issue Intelligence                  │
         │                             │
         └─────────────┬───────────────┘
                       ↓
            Community Chief of Staff
                       │
          ┌────────────┼────────────┐
          ↓            ↓            ↓
       Project      Knowledge    Communications
       Navigator     Steward        Agent
          │            │            │
          └────────────┼────────────┘
                       ↓
               Impact & Insights
                       │
                       ↓
                HUMAN LEADERSHIP

        Governance Guardian across all layers
```
The **Community Mapper** functions horizontally as well, helping identify where representation, expertise and opportunities exist.

# Don't deploy all 10 immediately
For the first 30-day organizing cycle, start with a **Minimum Viable AI Team of five**:
### 1. 👂 Listening Agent
Understand what people are saying.
### 2. 🔎 Issue Intelligence Agent
Turn themes into actionable issues.
### 3. 🎯 Community Chief of Staff
Coordinate everything.
### 4. 🧭 Project Navigator
Ensure commitments become action.
### 5. 🛡️ Governance Guardian
Provide boundaries and review gates.

Then introduce:

**Month 2**

🤝 Engagement Agent 📣 Communications Agent 📚 Knowledge Steward

**Month 3**

🕸️ Community Mapper 📊 Impact & Insights Agent

# Operating environment in Hermes
The agents sit around one shared, local workspace of plain files:

```
                 HERMES AGENT
        (skills in ~/.hermes/skills/)
                      │
          Community Chief of Staff
                      │
        ┌─────────────┼─────────────┐
        ↓             ↓             ↓
   Team channel   Community      Email
   (messaging)    home page
        │             │
        └──────┬──────┘
               ↓
     COMMUNITY WORKSPACE (local files)
               │
   ┌───────────┼───────────┬───────────┐
   ↓           ↓           ↓           ↓
 inbox/     signals/    projects/   decisions/
 feedback   issues/     tasks       human log
               │
               ↓
        briefs/  Community Health
```

Scheduled runs (for example the Monday brief) can move work between these parts, always stopping at the human approval gates.

## One principle should govern the entire system
**AI should reduce the administrative cost of participating in the community, not replace the people who make it a community.**

The agents can listen, organize information, find knowledge, maintain project visibility and prepare communications. **Nurses still choose the priorities, build relationships, make decisions, lead initiatives and receive credit for the work.**
