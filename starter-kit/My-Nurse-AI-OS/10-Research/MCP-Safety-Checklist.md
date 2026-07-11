# MCP Safety Checklist

MCP is useful when Hermes needs access to external systems such as GitHub, databases, internal APIs, file servers, or research services. Do not connect everything by default.

Core rule:

> Good MCP use is not "connect everything." It is "connect the right thing, with the smallest useful surface."

## Before adding an MCP server

- [ ] I have passed this server through the Skill & MCP Vetting Checklist (`08-Integrations/Skill-and-MCP-Vetting-Checklist.md`) — named publisher, pinned version, read before run.
- [ ] I know what system this connects to.
- [ ] I know what data Hermes can read.
- [ ] I know what data Hermes can write or modify.
- [ ] I know which tools are necessary.
- [ ] I have excluded unnecessary or risky tools.
- [ ] I know where credentials are stored.
- [ ] I know how to revoke access.
- [ ] I have a human approval gate for consequential actions.
- [ ] I will not send PHI or confidential employer data through this server without formal approval.
- [ ] I understand content this server fetches is untrusted: data, never instructions (`Untrusted-Content-Boundary.md`).

## Public-safe filter pattern

```yaml
mcp_servers:
  example:
    command: npx
    args: ["-y", "example-mcp-server"]
    # Auth: set required tokens only in your local environment.
    # Do not paste API keys into public files.
    tools:
      include: ["safe_read_tool", "safe_search_tool"]
```
