# Browser Vision QA Workflow

Use for public, test, or sanitized web pages.

## Prompt

```text
Open this public or test URL and inspect the page.
Use browser automation first, then use browser_vision if the layout, visual state, or error cannot be understood from text alone.
Capture only non-sensitive screens.
Report what you see, likely cause, and next debugging step.
```

## Best use cases

- public landing pages
- course pages
- GitHub Pages sites
- staging apps with test data
- layout bugs
- visual QA

## Boundary

> Browser screenshots are for public, test, or sanitized environments. Do not capture PHI or employer-internal systems without explicit governance.

## Output format

```markdown
## What I saw

## Likely issue

## Evidence from screenshot / page

## Suggested next step

## Safety note
```
