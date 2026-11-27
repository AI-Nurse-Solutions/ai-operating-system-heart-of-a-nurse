# Handoff objects

Agents pass these four structured records to one another instead of unstructured paragraphs. That design decision keeps every record a plain file in the community workspace, easy to read, audit, and connect later to trackers, dashboards, or automations.

## CommunitySignal (Listener → Issue Intelligence)
```
Signal ID
Theme
Source type
Observation
Frequency if measurable
Affected area
Open question
Date
```

## IssueBrief (Issue Intelligence → human decision → Project Navigator)
```
Issue ID
Problem
Evidence
Impact
Unknowns
Options
Recommended experiment
Measures
Human decision
```

## ProjectRecord (Project Navigator → Chief of Staff)
```
Project ID
Problem
Human owner
Status
Next action
Target date
Milestone
Dependency
Blocker
Decision
Measures
```

## GovernanceReview (Governance Guardian → requester and human owner)
```
Review ID
Object reviewed
Data involved
Risk domains
Risk level
Required review
Restrictions
Decision
Reviewer
Review date
```

## Rules for every handoff
- Preserve counts, unknowns, and explicit volunteers exactly as received.
- Label each statement as sourced fact, synthesis, unresolved question, or AI recommendation.
- `Human decision` stays "Pending" until the decision log records who decided and when.
- Ownership never changes without human authorization.
