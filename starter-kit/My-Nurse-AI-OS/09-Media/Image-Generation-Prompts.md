# Image Generation Prompts

Hermes image generation is exposed through tools, commonly through Nous Portal / Tool Gateway or a direct FAL.ai backend.

Setup concept:

```bash
hermes setup --portal
hermes tools
```

Enable image generation and choose a backend such as Nous Subscription or FAL.ai. Tool availability, models, and prices can change; check current Hermes docs and provider terms.

## Nurse-safe boundaries

- No patient photos.
- No PHI in prompts.
- No screenshots containing patient identifiers.
- Do not imply clinical endorsement or diagnostic capability.
- Treat generated images as drafts until reviewed by a human.

## Starter prompts

```text
Generate a calm 16:9 hero illustration for a personal learning dashboard: warm navy, soft gold, subtle knowledge graph motif, nurse-centered but non-clinical, no text, no patient imagery.
```

```text
Create a square logo concept for a personal learning vault called "Learning OS": simple vector style, warm human-centered design, no medical symbols, no text unless typography is reliable.
```

```text
Generate a background for an Obsidian Personal Learning dashboard: dark mode friendly, subtle interconnected notes and soft glow, minimal distraction, no text.
```
