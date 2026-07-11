# Skill & MCP Vetting Checklist — before anything new joins your system

Every skill file, MCP server, or plugin you add is **someone else's code running inside your assistant**, with whatever access your assistant has. Adding one is not like bookmarking a website; it's like granting a new float nurse badge access. Vet first, then trust — this is your supply-chain gate, the same principle as installing Hermes only from the official site.

## Before installing — the six checks

- [ ] **Who publishes it?** A named, findable maintainer or organization with a public repository and history. No anonymous zips, no "someone in a forum shared this."
- [ ] **Pin the version.** Install a specific release or commit — never "latest." Write down what you installed and when. (Same reason the Nurse AI OS installer pins its release key: what you vetted is what you run, until *you* decide to upgrade.)
- [ ] **Read before you run.** Open the SKILL.md / manifest / README and skim what it declares it will do and reach. For an MCP server, list which tools it exposes. If you can't tell what it does, that's a no.
- [ ] **Least privilege.** Connect the smallest useful surface: scope it to one folder, one account, one tool-allowlist (`tools: include:`). "Connect everything" is never the right first setting.
- [ ] **Lowest tier first.** New skills and servers start in **Green-tier work only** (drafts, summaries, private notes) for their first week. Nothing new touches messaging, external systems, or automation until it has a track record.
- [ ] **Name the owner and the exit.** Who on your system is accountable for this addition, and how do you disconnect it? If you can't answer both, don't install.

## After installing — the standing rules

- **90-day review:** a skill you have not reviewed in 90 days is suspect — re-read it, re-justify it, or archive it.
- **Upgrades are deliberate:** review the changelog/diff, then update your pinned version. Auto-update for third-party skills stays off.
- **One incident, straight to quarantine:** if a skill or server does anything you didn't expect, disconnect it first and investigate second.
- **Log it:** every install, upgrade, and removal goes in your ledger or Human Review Log — date, version, reason.

## The red flags — walk away

- Asks for your API keys, passwords, or full-disk access to "work properly."
- Instructions tell you to disable approvals, allowlists, or redaction "temporarily."
- No source visible, obfuscated code, or a maintainer who can't be identified.
- Pressure to install quickly ("limited," "before it's patched," "everyone's using it").

*Agents propose. Humans judge. Nurses steward.* · No PHI, no secrets, ever.
