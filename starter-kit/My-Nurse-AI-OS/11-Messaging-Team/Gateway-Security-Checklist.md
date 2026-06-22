# Gateway Security Checklist

Never expose a tool-using Hermes bot to everyone.

## Controls

- [ ] Platform allowlist configured.
- [ ] DM pairing / approval codes used where available.
- [ ] Separate profile for personal, team, and experimental bots.
- [ ] Manual approval remains on for risky actions.
- [ ] Home channel selected for cron delivery.
- [ ] No-PHI and no-secrets boundary posted in the channel.
- [ ] Gateway logs reviewed after first use.
- [ ] Human owner assigned for gateway, skills, cron jobs, and integrations.

## Do not use

```text
GATEWAY_ALLOW_ALL_USERS=true
```

Do not use this for any bot with access to tools, private notes, terminal, email, GitHub, Google Workspace, Google Drive, Obsidian, or MCP integrations.

## Boundary

> One agent can have many doors, but every door needs an owner, an allowlist, and a clear purpose.
