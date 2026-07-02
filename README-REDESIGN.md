# Nurse AI OS — Site Restructure (July 2026)

New multi-page architecture replacing the single mega-homepage. Drop these files into the root of the GitHub Pages repo.

## Files

| File | Purpose |
|---|---|
| `index.html` | New homepage — 6 sections only: hero (one primary CTA), 4 role cards, 6-step roadmap, founding-year offer, what you receive, final CTA |
| `start-here.html` | The guided onboarding journey (assess → personalize → plan → download → set up → huddle) |
| `pathways.html` | 4 role pathways with pain/aspiration copy; advanced tracks separated below |
| `setup.html` | Door 1 / Door 2 + consolidated plain-language safety rules (`#safety`) |
| `resources.html` | Resource Hub — all downloads grouped by purpose, Beginner/Advanced labels |
| `faq.html` | FAQ + glossary in plain language (accordions, no JS needed) |
| `assets/nurse-ai.css` | Shared design system (navy / teal / lamplight gold, Fraunces + Source Sans 3) |

## Before deploying

1. **Back up the current `index.html`** (rename to `index-legacy.html`). Deep content from it (integrations, messaging, media tools, workspace/HIPAA detail, HERMES protocol, EDENA lens, advanced growth map) should become individual pages linked from the Resource Hub — it is intentionally NOT on the new homepage.
2. All links to existing assets (`soul-quiz.html`, `life-quiz.html`, `assets/*`, `hermes-downloads/`, `ascend/`, `side-gig-starter-kit/`, `builder-academy*.html`, `care-intelligence/`, `naio-os/*`, `starter-kit/*`) are relative and match current live paths — nothing to change if files stay where they are.
3. Fonts load from Google Fonts (Fraunces, Source Sans 3). Fully static otherwise; zero JavaScript.

## YouTube video slots (in priority order)

Each slot is a dashed placeholder box with a commented `<iframe>` next to it — paste your YouTube embed URL and delete the placeholder.

1. **`setup.html` — "Your first 15 minutes"** (Door 1 screen-share, 5–8 min). Highest-value video: it removes the fear of starting. Record this one first.
2. **`index.html` — "How the roadmap works"** (2 min, above the 6 steps). Converts skimmers into quiz-takers.
3. **`start-here.html` — "Welcome — a system with the heart of a nurse"** (60–90 sec, face to camera). Trust and warmth; nurses want to see a nurse.
4. **`pathways.html` — "Choosing your pathway"** (2 min, commented slot at top). One video covering all four roles beats four separate ones at launch.
5. **`setup.html` — "Installing Hermes safely"** (Door 2 walkthrough, commented slot). Record last; smallest audience at launch.

Embed pattern used everywhere:
```html
<iframe class="video-embed" src="https://www.youtube.com/embed/VIDEO_ID"
        title="..." allowfullscreen></iframe>
```

## Deliberate strategy decisions

- **Brand stays "Nurse AI OS"** — not "Hermes with the Heart of a Nurse." Hermes is Nous Research's product; the site already correctly positions it as the optional third-party runtime (Door 2 only).
- **Nursing-process structure (assess → plan → implement → evaluate) is used as the journey's logic** and named once on the homepage, without adding another acronym framework.
- **Public vocabulary trimmed to four terms**: Nurse AI OS, SOUL, No-PHI, human gate. NAIO/EDENA/Florence-X/HERMES-Protocol live in the FAQ glossary and Resource Hub, not the main journey.
- **No-PHI boundary appears once per page** (badge or boundary box) instead of ~10 repetitions, with one canonical safety section at `setup.html#safety`.

## Suggested next steps

- Replace the cohort/leader `mailto:` links with a static form (Tally or Formspree) — mailto loses mobile users.
- Add lightweight analytics (e.g., GoatCounter or Plausible — both static-friendly) to track: hero CTA clicks, quiz starts, roadmap opens.
- Split the legacy homepage's deep content into Resource Hub pages (integrations, wellbeing, workspace/HIPAA, advanced growth map).
