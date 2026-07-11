## gstack (optional — recommended for local development, pinned)

gstack provides AI-workflow skills (/qa, /ship, /review, /investigate, /browse)
that can help when working on this repo locally in Claude Code.

**It is not required.** Sessions without gstack — cloud/web sessions, CI, fresh
containers — proceed normally. Do not stop work, block tools, or treat a missing
gstack as an error.

To install locally, use the pinned version below. Do not install "latest":
this repo upgrades the pin deliberately, by commit, after reviewing upstream
changes (supply-chain hygiene — the same reason our naio-os installer pins its
release key).

```bash
git clone https://github.com/garrytan/gstack.git ~/.claude/skills/gstack
cd ~/.claude/skills/gstack && git checkout 7c9df1c568a9ea745508f679a329332b2c338063 && ./setup --team
```

Then restart your AI coding tool.

Pinned commit: `7c9df1c568a9ea745508f679a329332b2c338063` (adopted 2026-07-11).
To upgrade: review the upstream diff, then update the pinned commit here in a PR.

When gstack is installed: prefer /browse for web browsing, and use
`~/.claude/skills/gstack/...` (the global path) for gstack file paths.
