# Profile Setup Guide

Profiles let you run separate Hermes agents on the same machine. Each profile has its own config, `.env`, `SOUL.md`, memories, sessions, skills, cron jobs, state database, gateway state, and identity.

Recommended beginner profiles:

- Personal Projects
- Personal Learning
- Professional Non-PHI

Boundary:

> Profiles help separate memory, configuration, skills, and sessions. They are not a substitute for privacy governance or clinical review.

## CLI examples

```bash
hermes profile create personal-projects
hermes profile create personal-learning
hermes profile use personal-learning
hermes profile
```

Use the Desktop app profile settings when available if you prefer the GUI.
