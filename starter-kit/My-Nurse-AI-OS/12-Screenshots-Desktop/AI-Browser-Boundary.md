# AI Browser Boundary: Comet, Atlas, and Hermes

AI browsers can be useful research surfaces, but they should not become the control center for local files, terminal access, or Hermes tool execution.

## Rule of thumb

```text
Hermes = hub, memory, tools, profiles, skills, local workflows
Comet / Atlas = optional human-facing research browsers
```

## Recommended posture

- Use Hermes native web tools for repeatable research and extraction.
- Use Hermes browser automation for web QA and controlled browsing tasks.
- Use Hermes Computer Use for native macOS apps when necessary.
- Use Perplexity or other research services through explicit API/MCP pathways if needed.
- Do not deeply wire an AI browser into Hermes local tools unless you fully understand the security model.

## Special caution

Avoid giving AI browsers broad access to:

- Hermes local tools
- filesystem tools
- terminal tools
- secrets
- API keys
- local automation
- private notes
- employer systems

Treat AI browsers as manual research companions unless a specific governed integration is approved.
