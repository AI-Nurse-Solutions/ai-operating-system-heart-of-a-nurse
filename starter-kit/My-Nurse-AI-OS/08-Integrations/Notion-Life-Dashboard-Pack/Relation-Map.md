# Notion Life Dashboard Relation Map

After importing the CSV files, add these Notion relation properties manually.

## Core relations

| From database | Relation property | To database | Why |
|---|---|---|---|
| Goals | Related Tasks | Tasks | Turns intention into visible next actions |
| Goals | Supporting Habits | Habits | Shows which habits keep the goal alive |
| Goals | Supporting Routines | Routines | Connects goals to repeatable rhythms |
| Tasks | Related Goal | Goals | Keeps tasks tied to purpose |
| Tasks | Related Routine | Routines | Links repeated task batches to a routine |
| Habits | Related Goal | Goals | Keeps habit tracking from becoming random streak chasing |
| Routines | Related Goal | Goals | Makes routines serve a season, not perfection |
| Health & Wellbeing | Related Routine | Routines | Connects energy, sleep, and movement to daily/weekly rhythm |
| Finances | Related Goal | Goals | Connects money stewardship to goals and values |

## Suggested rollups

| Database | Rollup | Source |
|---|---|---|
| Goals | Open Tasks | Related Tasks → Status |
| Goals | Active Habits | Supporting Habits → Status |
| Goals | Routine Support | Supporting Routines → Status |
| Routines | Tasks in Routine | Related Tasks → Name |
| Health & Wellbeing | Routine Support | Related Routine → Name |
| Finances | Goal Served | Related Goal → Name |

## Human gate rules

Use a human gate before:

- sharing a dashboard with another person
- importing data from a bank, wearable, calendar, or health app
- adding API automation
- letting AI write directly into Notion
- making financial, health, clinical, work, or family decisions from a dashboard trend

This dashboard supports self-awareness and organization. It does not replace licensed clinical, legal, financial, or mental-health advice.
