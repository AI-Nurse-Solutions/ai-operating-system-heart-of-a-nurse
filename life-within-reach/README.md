# Life Within Reach

A Nurse AI OS web app: an AI community organizer that helps a household lower its costs across the five pillars of the Affordability App Map. Those are groceries (PantryPlan), health care (CareBridge), housing (HomeHold), energy (WattWise) and family care (KinCare). It also includes the Household Command Center and a Policy Watch preview.

Target URL: **https://nurse-ai-os.org/life-within-reach/**

## Structure

| Path | What it is |
| --- | --- |
| `index.html` | Public landing page |
| `es/index.html` | Spanish landing page |
| `app/index.html` | The app (Household Command Center plus the five pillar tabs and Policy Watch) |
| `assets/rules.js` | Versioned benefits rules engine. Every threshold has an effective date and a source |
| `assets/app.js` | Five-step loop (Assess → Understand → Plan → Act → Check in): intake, situation summary, ranked 30/60/90 plan, "Do it with me" drafts, weekly check-in and story bank |
| `assets/lwr.css` | Styles, using the shared Nurse AI OS palette and type (Fraunces, Source Sans 3) |
| `assets/favicon-lamp.svg` | Nurse AI OS lamp mark |

The app is static, with no build step, no backend and no dependencies. All paths are relative, so the folder works when served from any sub-path.

## Languages (English and Spanish)

- The app picks its language from `?lang=es` / `?lang=en`, then the visitor's saved choice, then the page's `lang`. The header toggle switches and remembers it. The English landing page links to `app/?lang=en`; the Spanish one to `app/?lang=es`.
- English is the source of truth. Spanish sits beside it: `T("English", "Español")` in `app.js`, `tr("English", "Español")` in `rules.js`, `nameEs` / `labelEs` / `itemEs` on tables, and `DRAFTS_ES_IMPL` / `LESSONS_ES_IMPL` for the drafts and lessons. **When you change an English string or rule text, change its Spanish twin in the same edit.**
- Formal letters to institutions (hospital, insurer, landlord, employer, HR, utility commission) stay in English with a Spanish explanation above them; checklists and call scripts are fully Spanish and remind people they can ask for a free interpreter. The de-identified story is offered in Spanish with an English copy.
- Spanish uses formal "usted" and plain language. It was written with AI assistance and has **not yet been reviewed by a native-speaker community partner** — do that before promoting the Spanish version.

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

Every value in `assets/rules.js` was checked against its primary source on **2026-11-07** (ruleset `2026.11-verified.1`). Each table carries its effective date and source. When a value changes, update it there, update `effective` and `source`, and bump `RULESET.version`.

Calendar of updates:

| When | What changes | Where in `rules.js` |
| --- | --- | --- |
| Mid-January | HHS poverty guidelines | `FPL` |
| January | Manufacturer insulin programs renew (Lilly's current card ends Dec 31, 2026) | `DRAFTS.rx` |
| Spring (for July 1) | WIC and school-meal income limits (follow the new poverty guidelines) | screened as % of `FPL` |
| June | CPUC CARE/FERA income limits (June 1–May 31) | `discount` task |
| Summer–fall | IRS Rev. Proc. with next year's ACA applicable percentage; next year's Oregon and Washington rent caps | `ACA.maxContributionPctByYear`, `RENT_CAP_STATES` |
| Oct 1 | SNAP cost-of-living adjustment (max allotments, standard deductions, shelter cap, minimum benefit) | `SNAP` (current values expire 2027-09-30) |
| As enacted | Medicaid expansion or partial-coverage changes (Georgia Pathways after Dec 31, 2026), state paid leave (Maryland FAMLI benefits Jan 2028), enhanced ACA credits, LIHEAP full-year FY2027 funding, the 4th Circuit appeal on Open Enrollment dates | `NON_EXPANSION`, `PARTIAL_ADULT_COVERAGE`, `PAID_LEAVE_STATES`, `ACA`, lessons |

Known simplifications: SNAP estimates use the household's actual energy bill rather than state utility allowances, and California's AB 1482 cap is treated as "never more than 10%" because the CPI part differs by region.
