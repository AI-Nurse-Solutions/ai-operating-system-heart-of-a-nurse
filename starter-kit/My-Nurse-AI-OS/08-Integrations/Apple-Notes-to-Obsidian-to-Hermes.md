# Apple Notes → Obsidian Vault → Hermes

Use this when moving personal learning notes from Apple Notes into a durable markdown vault that Hermes can help search, organize, and refine.

Pipeline:

```text
Apple Notes → Obsidian vault → Hermes working with markdown files
```

## Step 1 — Import Apple Notes into Obsidian

Recommended path:

- Install Obsidian.
- Use Obsidian's official Importer plugin.
- Choose Apple Notes as the import format.
- Follow Obsidian's instructions for selecting the Apple Notes database folder.
- Confirm imported notes are markdown files and attachments are referenced correctly.

Alternative path:

- Use an Apple Notes exporter tool to export notes as markdown.
- Open the exported folder as an Obsidian vault.

## Step 2 — Make Obsidian the note home

Suggested structure:

```text
Obsidian Vault/
  Archive/Apple Notes Archive/
  Inbox/
  Learning/
  Projects/
  Personal/
  Professional-Non-PHI/
```

## Step 3 — Point Hermes at the vault

Set a vault path convention, for example:

```bash
OBSIDIAN_VAULT_PATH=/Users/yourname/path/to/your/vault
```

Safety:

- Do not publish `.env` files.
- Do not publish private vault paths, API keys, or note contents.
- Do not process PHI or confidential employer material.
- Hermes file tools need a concrete absolute path, not `$OBSIDIAN_VAULT_PATH`.

Starter prompt:

```text
Use my Obsidian vault as my long-term learning notebook.
Before writing, confirm the vault path and target folder.
Create new learning notes under Learning/Inbox unless I specify otherwise.
Use wikilinks when helpful.
Do not process PHI, patient identifiers, confidential employer data, passwords, API keys, or private family information.
```
