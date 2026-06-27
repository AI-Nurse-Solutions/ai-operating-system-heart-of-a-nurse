# Perplexity MCP Research Boundary

Perplexity can be added as a specialized research source through MCP, but it should not replace Hermes' native web tools or source review.

## Best use

- citation-rich research questions
- current topic reconnaissance
- source discovery before deeper extraction
- comparing against Hermes native web-search results

## Recommended pattern

```text
Hermes = workflow brain
Native web tools = baseline research
Perplexity MCP = specialized citation-rich research source
Obsidian / repo notes = durable output
Skills = reusable method
```

## Setup options

1. Composio Perplexity MCP — easier managed route if already using Composio.
2. Direct Perplexity MCP server — more direct, self-managed route using a Perplexity API key.

## Safety requirements

- Store API keys in `.env` or the approved Hermes credential path.
- Never paste real keys into notes, public repos, slides, or screenshots.
- Use MCP tool filtering; expose only the tools needed.
- Treat Perplexity answers as source leads, not final truth.
- Verify high-stakes claims against original sources.
- Do not use Perplexity MCP for PHI, patient-specific decisions, confidential employer material, or clinical operations.

## Public-safe config pattern

```yaml
mcp_servers:
  perplexity:
    command: npx
    args: ["-y", "perplexity-mcp"]
    # Auth: set the required API token only in your local environment.
    # Do not paste API keys into public files.
    tools:
      include: ["search", "ask"]
```

## Prompt

```text
Use Perplexity MCP only as one research source.
Find source leads and citations, then verify important claims with original sources where possible.
Create an evidence-aware markdown note with: question, answer summary, sources to verify, uncertainties, and next research step.
Do not process PHI or patient-specific clinical questions.
```
