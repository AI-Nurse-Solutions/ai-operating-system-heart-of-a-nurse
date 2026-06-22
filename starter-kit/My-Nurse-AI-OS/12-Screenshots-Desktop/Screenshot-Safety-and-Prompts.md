# Screenshot Safety and Prompts

Screenshots are powerful context, but they can accidentally include PHI, employer data, private messages, or credentials.

Core rule:

> Screenshot only what you are allowed to share. If it could identify a patient, employee, institution, account, secret, or private conversation, do not put it into Hermes.

## Good uses

- Hermes setup troubleshooting
- app settings pages
- error dialogs
- Obsidian dashboards
- public web UI testing
- research layouts
- non-PHI educational graphics

## Do not screenshot into Hermes

- EHR screens
- patient lists
- patient photos
- clinical messages
- staffing systems
- HR systems
- protected employer dashboards
- passwords, API keys, tokens, or 2FA screens

## Manual screenshot prompt

```text
I am attaching a screenshot of [app/page/context].
I was trying to [goal].
I expected [expected result].
What I see instead is [problem].
Please analyze only the visible UI and suggest the safest next steps.
Do not infer patient, clinical, or private details beyond what I explicitly provide.
```

## Research/layout prompt

```text
Critique this as a personal learning dashboard.
Suggest layout, information architecture, and visual improvements.
Do not treat any visible clinical material as patient data; if PHI appears, stop and tell me to remove or redact it.
```
