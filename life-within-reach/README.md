# Life Within Reach

A Nurse AI OS web app: an AI community organizer that helps a household lower its costs across the five pillars of the Affordability App Map. Those are groceries (PantryPlan), health care (CareBridge), housing (HomeHold), energy (WattWise) and family care (KinCare). It also includes the Household Command Center and a Policy Watch preview.

Target URL: **https://nurse-ai-os.org/life-within-reach/**

## Structure

| Path | What it is |
| --- | --- |
| `index.html` | Public landing page |
| `app/index.html` | The app (Household Command Center plus the five pillar tabs and Policy Watch) |
| `assets/rules.js` | Versioned benefits rules engine. Every threshold has an effective date and a source |
| `assets/app.js` | Five-step loop (Assess → Understand → Plan → Act → Check in): intake, situation summary, ranked 30/60/90 plan, "Do it with me" drafts, weekly check-in and story bank |
| `assets/lwr.css` | Styles, using the shared Nurse AI OS palette and type (Fraunces, Source Sans 3) |
| `assets/favicon-lamp.svg` | Nurse AI OS lamp mark |

The app is static, with no build step, no backend and no dependencies. All paths are relative, so the folder works when served from any sub-path.

## Deploy to nurse-ai-os.org

nurse-ai-os.org is already served by GitHub Pages from a different repository, so this repo does **not** set a `CNAME`. Doing that would take the domain away from the existing site. To publish:

1. Copy this whole `life-within-reach/` folder into the root of the repository that serves nurse-ai-os.org.
2. Commit and push. The app is then live at `https://nurse-ai-os.org/life-within-reach/` and the app itself at `/life-within-reach/app/`.
3. Optional: link to it from the nurse-ai-os.org home page and navigation.

Until then, it is previewable from this repo's GitHub Pages site at `/life-within-reach/`.

## Privacy and guardrails (as built)

- The AI is presented as a community organizer and says plainly that it is an AI tool, not a nurse, doctor, lawyer, or other licensed professional. Keep it that way: don't describe the AI persona as a nurse or with nursing credentials anywhere in the app or landing page.
- Answers are stored only in the browser's `localStorage`. The user can export them as JSON or erase them in one click. Nothing is sent to a server.
- The app never asks about immigration status, a Social Security number, symptoms or diagnoses.
- Eligibility comes from `rules.js`, not from generated text. Every result is labeled as a screening estimate, with its rule source and effective date shown.
- Crisis numbers (911, 988, Poison Control) stay visible on every app screen. Legal and clinical steps link out to legal aid and licensed professionals.

## Updating rules

Edit the tables at the top of `assets/rules.js`, including `effective` and `source`, and bump `RULESET.version`. Review these when they change:

- **HHS poverty guidelines.** The tables currently use the 2025 guidelines, which also apply to the 2026 ACA plan year. Load the 2026 figures for programs that have switched.
- SNAP cost-of-living adjustments, each Oct 1.
- The ACA applicable percentage.
- The list of states that have not expanded Medicaid.
- State paid-leave programs and rent caps.
