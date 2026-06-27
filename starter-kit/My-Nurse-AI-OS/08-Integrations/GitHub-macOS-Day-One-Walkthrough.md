# GitHub macOS Day-One Walkthrough

Use this when Hermes is ready to help with code storage or simple GitHub Pages sites.

## 1. Install and log into GitHub CLI

```bash
brew install gh
gh auth login
```

Recommended beginner choices:

- GitHub.com
- HTTPS
- browser-based login

Confirm:

```bash
hermes --version
gh auth status
```

## 2. Enable GitHub skills

In Hermes Desktop, use a Projects or Professional Non-PHI profile. Enable GitHub-related skills for repo management, PRs, issues, or code review as needed.

For most beginners, `gh auth login` plus Hermes GitHub skills is enough.

## 3. Optional MCP path

Only add a GitHub MCP server when there is a real need for richer issue, PR, or repo tools.

Do not paste live tokens into public notes, public repos, screenshots, slides, or course materials.

Safer public pattern:

```yaml
mcp_servers:
  github:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    # Auth: use `gh auth login` or a local environment variable.
    # Do not paste tokens into public files.
```

## 4. Private repo prompt

```text
This folder is my new project.
Initialize git here, create a GitHub repository, and connect the two.
Make the repository private by default.
Before pushing, show me the files that will be committed and scan for PHI, secrets, API keys, credentials, and private notes.
Do not push until I approve.
```

## 5. Public GitHub Pages prompt

```text
This folder is a public GitHub Pages site.
Create or update a simple static site using index.html, CSS, and public-safe assets.
Before publishing, scan for PHI, secrets, API keys, confidential employer material, personal notes, and anything not intentionally public.
Use the main branch root for GitHub Pages unless I specify otherwise.
Verify the live site after deployment.
```

Boundary:

> Private repo = working area. Public GitHub Pages repo = published output.
