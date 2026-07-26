#!/usr/bin/env python3
"""Build governed, inactive-by-default Hermes MCP role-profile companions."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import sys
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "hermes-role-profiles"
SOURCE = ROOT / "source"
DOWNLOADS = ROOT / "downloads"
FIXED_ZIP_TIME = (2026, 7, 26, 0, 0, 0)
VERSION = "1.0.0"
HERMES_REQUIRES = ">=0.19.0"
NO_TOOLS_SENTINEL = "__NAIO_NO_MCP_TOOLS_APPROVED__"
DEPENDENCY_LOCK_KEYS: dict[str, str] = {"github": "github_remote"}

OBSIDIAN_COMMIT = "c8a4fed36da2ec03284bdd13f540b65e0af27bb1"
X_COMMIT = "1d22ed4fc4f725df8af90ef75a4a7bd1e3bc9882"
FILESYSTEM_VERSION = "2026.7.10"
PUBMED_VERSION = "2.10.1"
REDDIT_VERSION = "1.5.1"
WORKSPACE_VERSION = "1.22.1"

ROLES: dict[str, dict[str, Any]] = {
    "study-coach": {
        "label": "Study Coach",
        "lane": "future",
        "product": "FUTURE — Nursing Student & Nursing Assistant",
        "mapping_classification": "direct_pathway_only",
        "mapping_condition": "Nursing Student pathway only; not automatically Nursing Assistant or Bridge.",
        "servers": ["obsidian", "filesystem", "google_workspace"],
        "workspace_tools": ["calendar", "docs", "drive"],
        "purpose": "Generic study planning, concept practice, and user-requested personal learning-note drafts.",
        "boundary": "No clinical placement stories, restricted course material, protected exam content, or claims of competence.",
    },
    "curator": {
        "label": "Curator",
        "lane": "discover",
        "product": "DISCOVER — Healthcare Research & Innovation Leader",
        "mapping_classification": "adjacent_conditional_not_exact_lane",
        "mapping_condition": "Healthcare research or innovation source-curation context only; not generic curation and not an exact DISCOVER lane identity.",
        "servers": ["obsidian", "filesystem", "reddit", "x", "google_workspace"],
        "workspace_tools": ["docs", "drive"],
        "purpose": "Public-source signal discovery and draft curation with preserved provenance.",
        "boundary": "No public posting, direct messages, voting, validation claims, private communities, or person-level source material.",
    },
    "builder-operator": {
        "label": "Builder / Operator",
        "lane": "discover",
        "product": "DISCOVER — Healthcare Research & Innovation Leader",
        "mapping_classification": "adjacent_conditional_not_exact_lane",
        "mapping_condition": "Healthcare research or innovation solution-preparation context only; not a generic software-builder or code-shipping role and not an exact DISCOVER lane identity.",
        "servers": ["obsidian", "filesystem", "github", "google_workspace"],
        "workspace_tools": ["calendar", "docs", "drive"],
        "purpose": "Bounded solution-building preparation and draft pull-request workflows in an owner-selected workspace.",
        "boundary": "No protected-branch push, merge, deployment, workflow administration, secret access, or external release without a fresh human gate.",
    },
    "manager-lead": {
        "label": "Manager / Lead",
        "lane": "lead",
        "product": "LEAD — Nurse Leader & Manager",
        "mapping_classification": "direct_role_conditional",
        "mapping_condition": "Only when the user is actually operating as a nurse leader or manager; selection does not establish authority.",
        "servers": ["obsidian", "filesystem", "google_workspace"],
        "workspace_tools": ["calendar", "docs", "drive", "sheets"],
        "purpose": "Synthetic leadership preparation, owner-authored planning notes, and draft coordination artifacts.",
        "boundary": "No patient, workforce, personnel, performance, evaluation, scheduling, staffing, or employer-confidential records.",
    },
    "admin-pilot-ops": {
        "label": "Administrator / Pilot Operations",
        "lane": "steward",
        "product": "STEWARD — Hospital & Clinic Administrator",
        "mapping_classification": "conditional_candidate",
        "mapping_condition": "Hospital or clinic administration context only; not generic administration and not an automatic identity match.",
        "servers": ["filesystem", "google_workspace"],
        "workspace_tools": ["calendar", "forms"],
        "purpose": "Synthetic pilot-operations rehearsal and generic intake-form or scheduling-template preparation.",
        "boundary": "No live intake responses, patient scheduling, clinical operations, workforce data, institutional records, or claims of delegated authority.",
    },
    "clinician-np": {
        "label": "Clinician — Nurse Practitioner",
        "lane": "wings",
        "product": "WINGS — Nurse Practitioner",
        "mapping_classification": "direct_country_restricted",
        "mapping_condition": "United States NP context only; selection does not verify licensure, certification, privileges, or authority.",
        "servers": ["obsidian", "filesystem", "pubmed", "google_workspace"],
        "workspace_tools": ["calendar", "docs", "drive"],
        "purpose": "Generic evidence-study questions, public literature retrieval, and nonclinical professional-learning notes.",
        "boundary": "No patient-specific reasoning, diagnosis, triage, treatment, chart content, clinical documentation, real-case reflection, or practice authority.",
    },
    "clinician-resident": {
        "label": "Clinician — Medical Resident",
        "lane": "rounds",
        "product": "ROUNDS — Medical Resident",
        "mapping_classification": "direct_fit",
        "mapping_condition": "Medical Resident ROUNDS context only; selection does not verify training status, supervision, competence, or authority.",
        "servers": ["obsidian", "filesystem", "pubmed", "google_workspace"],
        "workspace_tools": ["calendar", "docs", "drive"],
        "purpose": "Generic board study, public literature retrieval, and nonclinical professional-learning notes under supervision boundaries.",
        "boundary": "No patient-specific reasoning, diagnosis, triage, treatment, chart or sign-out content, real-case reflection, supervision replacement, evaluation, or entrustment claims.",
    },
}

DEPENDENCIES = {
    "filesystem": {
        "source": "https://www.npmjs.com/package/@modelcontextprotocol/server-filesystem",
        "repository": "https://github.com/modelcontextprotocol/servers",
        "version": FILESYSTEM_VERSION,
        "package": f"@modelcontextprotocol/server-filesystem@{FILESYSTEM_VERSION}",
        "license": "SEE-LICENSE-IN-UPSTREAM-PACKAGE",
        "registry_integrity": "sha512-Mmjg4anFBD5OzbPnGJOA0jPPN8645ERhQk38HQLpSenx1ox9bfdPkmAzUnNjeQtqQGFLtKe13J20RtLBmUKMZA==",
        "pinning_status": "exact_npm_version",
    },
    "obsidian": {
        "source": "https://github.com/Vasallo94/obsidian-mcp-server",
        "commit": OBSIDIAN_COMMIT,
        "license": "MIT",
        "pinning_status": "exact_git_commit",
    },
    "google_workspace": {
        "source": "https://pypi.org/project/workspace-mcp/",
        "repository": "https://github.com/taylorwilsdon/google_workspace_mcp",
        "version": WORKSPACE_VERSION,
        "package": f"workspace-mcp=={WORKSPACE_VERSION}",
        "license": "MIT",
        "wheel_sha256": "e999c63730760eeea1586055c423c7d74ebcef7d1db2a922ba242bc406c9b78b",
        "pinning_status": "exact_pypi_version",
    },
    "pubmed": {
        "source": "https://www.npmjs.com/package/@cyanheads/pubmed-mcp-server",
        "repository": "https://github.com/cyanheads/pubmed-mcp-server",
        "version": PUBMED_VERSION,
        "package": f"@cyanheads/pubmed-mcp-server@{PUBMED_VERSION}",
        "license": "Apache-2.0",
        "registry_integrity": "sha512-NJzr67w+nL7ZVBk05dPzXpIUe5Gxz7EOqeLUiIWLaMiAxmOpEPSoMsqCu6YT2az0Uh7mWqG/+OmTBZ7n0mz1Vw==",
        "runtime_requires": "Node.js >=24.0.0",
        "pinning_status": "exact_npm_version",
    },
    "reddit": {
        "source": "https://www.npmjs.com/package/reddit-mcp-server",
        "repository": "https://github.com/jordanburke/reddit-mcp-server",
        "version": REDDIT_VERSION,
        "package": f"reddit-mcp-server@{REDDIT_VERSION}",
        "license": "MIT",
        "registry_integrity": "sha512-kPiDTP6H6H1/nsdIWrbxEIxUhLPlHusWa9FrE3ucWtE/aG1RGb0VgzThE0u7t9rOjuN3FM4tYMKJax2NLVlgkQ==",
        "pinning_status": "exact_npm_version",
    },
    "x": {
        "source": "https://github.com/rafaljanicki/x-twitter-mcp-server",
        "commit": X_COMMIT,
        "license": "MIT",
        "pinning_status": "exact_git_commit",
    },
    "github_remote": {
        "source": "https://github.com/github/github-mcp-server",
        "remote_url": "https://api.githubcopilot.com/mcp/",
        "observed_release": "v1.7.0",
        "license": "MIT",
        "pinning_status": "remote_service_not_code_pinnable",
        "governance": "Disabled by default; remote service identity can change independently of this artifact; activation requires fresh endpoint, terms, authentication, retention, and tool-surface review.",
    },
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def server_config(name: str, role: dict[str, Any]) -> dict[str, Any]:
    base: dict[str, Any] = {
        "enabled": False,
        "tools": {
            "include": [NO_TOOLS_SENTINEL],
            "resources": False,
            "prompts": False,
        },
        "sampling": {"enabled": False},
        "elicitation": {"enabled": False},
        "connect_timeout": 30,
        "timeout": 60,
    }
    if name == "obsidian":
        base.update({
            "command": "uvx",
            "args": [
                "--from",
                f"git+https://github.com/Vasallo94/obsidian-mcp-server.git@{OBSIDIAN_COMMIT}",
                "obsidian-mcp-server",
            ],
            "env": {
                "OBSIDIAN_VAULT_PATH": "${NAIO_VAULT_PATH}",
                "OBSIDIAN_MCP_TOOL_SETS": "read,write",
            },
        })
    elif name == "filesystem":
        base.update({
            "command": "npx",
            "args": ["-y", f"@modelcontextprotocol/server-filesystem@{FILESYSTEM_VERSION}", "${NAIO_ROLE_WORKSPACE}"],
        })
    elif name == "google_workspace":
        base.update({
            "command": "uvx",
            "args": [
                f"workspace-mcp=={WORKSPACE_VERSION}",
                "--tool-tier",
                "core",
                "--tools",
                *role["workspace_tools"],
            ],
            "env": {
                "GOOGLE_OAUTH_CLIENT_ID": "${GOOGLE_OAUTH_CLIENT_ID}",
                "GOOGLE_OAUTH_CLIENT_SECRET": "${GOOGLE_OAUTH_CLIENT_SECRET}",
            },
        })
    elif name == "pubmed":
        base.update({
            "command": "npx",
            "args": ["-y", f"@cyanheads/pubmed-mcp-server@{PUBMED_VERSION}"],
            "env": {"NCBI_API_KEY": "${NCBI_API_KEY}"},
        })
    elif name == "reddit":
        base.update({
            "command": "npx",
            "args": ["-y", f"reddit-mcp-server@{REDDIT_VERSION}"],
            "env": {
                "REDDIT_CLIENT_ID": "${REDDIT_CLIENT_ID}",
                "REDDIT_CLIENT_SECRET": "${REDDIT_CLIENT_SECRET}",
                "REDDIT_USERNAME": "${REDDIT_USERNAME}",
                "REDDIT_PASSWORD": "${REDDIT_PASSWORD}",
                "REDDIT_SAFE_MODE": "true",
            },
        })
    elif name == "x":
        base.update({
            "command": "uvx",
            "args": [
                "--from",
                f"git+https://github.com/rafaljanicki/x-twitter-mcp-server.git@{X_COMMIT}",
                "x-twitter-mcp-server",
            ],
            "env": {
                "TWITTER_API_KEY": "${TWITTER_API_KEY}",
                "TWITTER_API_SECRET": "${TWITTER_API_SECRET}",
                "TWITTER_ACCESS_TOKEN": "${TWITTER_ACCESS_TOKEN}",
                "TWITTER_ACCESS_TOKEN_SECRET": "${TWITTER_ACCESS_TOKEN_SECRET}",
                "TWITTER_BEARER_TOKEN": "${TWITTER_BEARER_TOKEN}",
            },
        })
    elif name == "github":
        base.update({
            "url": "https://api.githubcopilot.com/mcp/",
            "headers": {"Authorization": "Bearer ${GITHUB_TOKEN}"},
        })
    else:
        raise ValueError(f"Unknown MCP server {name}")
    candidate_keys = ("command", "args", "url", "headers", "env")
    candidate = {key: base.pop(key) for key in candidate_keys if key in base}
    base["candidate"] = candidate
    base["command"] = "__NAIO_MCP_ACTIVATION_BLOCKED__"
    base["args"] = [name]
    return base


def env_keys(servers: list[str]) -> list[str]:
    keys = {"NAIO_ROLE_WORKSPACE"}
    if "obsidian" in servers:
        keys.add("NAIO_VAULT_PATH")
    if "google_workspace" in servers:
        keys.update({"GOOGLE_OAUTH_CLIENT_ID", "GOOGLE_OAUTH_CLIENT_SECRET"})
    if "pubmed" in servers:
        keys.add("NCBI_API_KEY")
    if "reddit" in servers:
        keys.update({"REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USERNAME", "REDDIT_PASSWORD"})
    if "x" in servers:
        keys.update({"TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_TOKEN_SECRET", "TWITTER_BEARER_TOKEN"})
    if "github" in servers:
        keys.add("GITHUB_TOKEN")
    return sorted(keys)


def render_soul(slug: str, role: dict[str, Any]) -> str:
    return f"""# {role['label']} — governed MCP companion

## Role

{role['purpose']}

This companion is subordinate to the {role['product']} build-kit governance contract. It does not verify identity, credentials, employment, supervision, delegated authority, institutional approval, or professional competence.

## Non-negotiable boundary

- No PHI.
- No patient cases or narratives, even when names or obvious identifiers are removed.
- No credentials or secrets.
- No employer-confidential, personnel, evaluation, staffing, restricted-course, protected-exam, or institution-controlled content.
- If content may cross one of these boundaries, reject it before processing, transforming, summarizing, or storing it. Do not echo it back and do not attempt de-identification.
- {role['boundary']}

## MCP posture

- Downloading or unzipping does not install, connect, or activate anything.
- Every bundled MCP server is disabled and exposes zero tools by default.
- Profile installation and each later MCP activation are separate decisions.
- Before any profile install, show the exact MCP Profile Installation Card in `MCP-ACTIVATION-CARD.md` and stop for explicit approval.
- Before any MCP activation, show the separate MCP Activation Card, inspect the exact resolved package or remote service, enumerate the exact tools, destinations, credentials, data classes, retention, network, rollback, and deletion plan, then stop for fresh explicit approval.
- Never infer approval from download, unzip, profile selection, technical access, a prior general request, silence, or timeout.
- Never schedule, automate, broaden permissions, add memory, or enable external actions from this companion.

## Operating rule

Agents propose. Humans judge. Nurses steward. Use generic or clearly synthetic inputs, label drafts, cite public sources when used, and leave every consequential action to an authorized human in the proper system.
"""


def render_readme(slug: str, role: dict[str, Any]) -> str:
    server_list = ", ".join(role["servers"])
    return f"""# NAIO {role['label']} Hermes MCP profile companion

**Profile:** `{slug}`

**Version:** `{VERSION}`

**Mapped product:** {role['product']}

**Mapping classification:** `{role['mapping_classification']}`

**Mapping condition:** {role['mapping_condition']}

**Hermes compatibility:** `{HERMES_REQUIRES}`

Downloading or unzipping does not install, connect, or activate anything. This is a local profile distribution for read-only inspection first. It is not a sandbox, clinical system, credential, institutional authorization, or proof that an upstream MCP is safe for a specific environment.

## What is included

- Role boundary: `SOUL.md`
- Inactive MCP definitions: authoritative runtime state in `config.yaml`; `mcp.json` is a matching publication-time audit snapshot only
- Archive-native top-level candidate pins and known exception: `MCP-SUPPLY-CHAIN-LOCK.json`. These are not a transitive lock or activation-ready runtime.
- Blank credential template: `.env.template` (installed by Hermes as `.env.EXAMPLE`, never as an active `.env`)
- Required human gates: `MCP-ACTIVATION-CARD.md`
- Review skill: `skills/review-mcp-activation/SKILL.md`

Declared MCP candidates: {server_list}. All are `enabled: false`, use the guaranteed-missing runtime command `__NAIO_MCP_ACTIVATION_BLOCKED__`, use the nonmatching deny sentinel `{NO_TOOLS_SENTINEL}`, and disable MCP resources, prompts, sampling, and elicitation. Original package/URL definitions are non-executable `candidate` metadata. Nothing can resolve, connect, request an LLM completion, collect mid-call input, or expose a tool until a human separately approves and installs a lock-consuming runtime, then changes every required condition.

Native `hermes profile install` does not display or enforce the bundled card, and `--yes` bypasses its generic confirmation. Card A is therefore an explicit human procedural gate, not a technical installer control. Do not use `--yes`. Installation writes local profile files but still cannot activate an MCP because every published runtime command is blocked.

Hermes reads `config.yaml:mcp_servers` at runtime. `mcp.json` is audit evidence, not a second authority. After any profile update, re-check parity; never infer that a refreshed `mcp.json` changed effective runtime behavior.

## Required sequence

1. Verify this ZIP against `hermes-role-profiles/CHECKSUMS.sha256`.
2. Extract it into a personal no-PHI location.
3. Give the complete extracted folder to Hermes and request: **“INSPECT THIS MCP PROFILE ONLY — CREATE NO STATE.”**
4. Hermes reads `MCP-ACTIVATION-CARD.md`, verifies local bytes and prerequisites, displays the exact Profile Installation Card, and stops.
5. Only after explicit approval may the human run `hermes profile install <exact-extracted-folder> --name {slug} --alias`.
6. Installation still leaves every MCP disabled with zero tools. Do not create `.env`, install packages, authenticate, or connect anything during profile installation.
7. Any later MCP activation requires its own exact card and a fresh approval. In a disposable test copy, first replace the blocker with a reviewed runtime command that consumes a complete transitive lock. Then use `hermes -p {slug} mcp configure <exact-server-name>` during that separately approved activation review; enumerate and allowlist exact tools before enabling that server.
8. Restart Hermes or use the supported `/reload-mcp` flow only after the approved configuration change.

## Removal

Use `hermes profile delete {slug}` only after reviewing what local profile state will be removed. Upstream OAuth grants, tokens, package caches, service-side data, and provider sessions may require separate revocation or deletion; profile deletion does not prove those were removed.
"""


def render_card(slug: str, role: dict[str, Any]) -> str:
    return f"""# MCP Profile Installation and Activation Cards

## Card A — Profile installation (human procedural gate before mutation)

Native Hermes installation does not display or enforce this card, and `--yes` bypasses its generic confirmation. Do not use `--yes`. The human or operating agent must fill every field, display the complete card, and stop before installation. Installation mutates local profile files but remains MCP-inert because every runtime command is blocked.

- Profile: `{slug}` version `{VERSION}`
- Mapped product and lane: `{role['product']}` / `{role['lane']}`
- Mapping classification: `{role['mapping_classification']}`
- Mapping eligibility condition: {role['mapping_condition']}
- Exact extracted source path: `[required]`
- Exact source-tree SHA-256 inventory: `[required]`
- Exact target profile path: `[required]`
- Existing profile collision and backup result: `[required]`
- Hermes version and compatibility result: `[required]`
- Files that would be copied: `[required]`
- Confirmed inactive MCP count and names: `[required]`
- Confirmed enabled MCP count after install: `0`
- Confirmed exposed MCP tool count after install: `0`
- Credential files created after install: `0` (`.env.EXAMPLE` is non-active)
- Package installs, OAuth flows, network calls, cron jobs, memories, connectors, or external actions authorized: `none`
- Rollback command and exact target: `[required]`
- Unknowns or blockers: `[required]`
- Decision requested: `APPROVE PROFILE INSTALL`, `REVISE`, or `CANCEL`

Download, unzip, role selection, technical access, earlier approval, silence, or timeout is not approval.

## Card B — One MCP activation (required separately for each server)

Hermes must fill every field from current evidence, display the complete card, and stop.

- Profile and exact server: `[required]`
- Resolved package/repository commit or remote service identity: `[required]`
- Registry integrity/checksum verification and complete transitive dependency lock: `[required or BLOCKED]`
- Current maintainer, license, release date, advisories, and unresolved supply-chain risk: `[required]`
- Exact lock-consuming runtime command, arguments, environment keys, network destinations, and local paths: `[required]`
- Exact discovered tool inventory: `[required]`
- Exact proposed allowlist: `[required; never wildcard or omitted]`
- Read, write, destructive, external-send, public-post, and administrative capabilities: `[required]`
- Allowed data: clearly synthetic or public/no-PHI material only
- Prohibited data: patient cases or narratives, PHI, secrets, personnel/evaluation/staffing records, employer-confidential or restricted material
- Credential source, least-privilege scope, storage, rotation, revocation, and deletion: `[required]`
- Provider retention, training/data-use, account, privacy, institutional, and program rules: `[required]`
- Human approval points and destination previews: `[required]`
- Test workspace and synthetic negative probes: `[required]`
- Rollback, token revocation, cache cleanup, service-side deletion, and evidence receipt: `[required]`
- Expiry/re-review date: `[required]`
- Unknowns or blockers: `[required]`
- Decision requested: `APPROVE EXACT MCP ACTIVATION`, `REVISE`, or `CANCEL`

Approval applies only to the exact server, package/remote identity, command, tools, paths, credentials, destinations, data boundary, and expiry shown. Any change invalidates approval.
"""


def render_skill(slug: str, role: dict[str, Any]) -> str:
    return f"""---
name: review-mcp-activation
description: Perform read-only preflight for the {slug} profile or one MCP candidate and produce the exact required card without installing, authenticating, connecting, or enabling anything.
version: 1.0.0
metadata:
  author: NAIO
  category: governance
---

# Review MCP activation

## Trigger

Use when the human asks to inspect, install, enable, configure, or update this role profile or one of its MCP candidates.

## Procedure

1. Keep the operation read-only. Do not install packages, create `.env`, authenticate, connect, enable a server, broaden a tool filter, reload MCP, or mutate profile state.
2. Reject prohibited input before processing, transforming, summarizing, or storing it. No PHI, patient cases or narratives, credentials, secrets, personnel/evaluation/staffing records, restricted material, or employer-confidential content.
3. Read `MCP-ACTIVATION-CARD.md` and complete Card A for profile installation or Card B for one exact MCP server.
4. Verify current evidence rather than trusting bundled claims: exact bytes, package or remote identity, complete transitive lock, lock-consuming runtime command, license, advisories, tool inventory, paths, destinations, credentials, retention, rollback, deletion, and unknowns.
5. If a complete lock cannot be produced and consumed, a tool inventory cannot be enumerated, package integrity cannot be checked, a remote service cannot be bounded, or a required policy is unknown, mark the card `BLOCKED`.
6. Display the complete card and stop. Ask for one explicit decision: approve the exact card, revise it, or cancel.

## Verification

A valid review creates no profile, `.env`, package cache, OAuth grant, connector, MCP process, memory, cron job, network session, external action, or destination-side change.
"""


def write_profile(slug: str, role: dict[str, Any]) -> None:
    profile = SOURCE / slug
    if profile.exists():
        shutil.rmtree(profile)
    (profile / "skills" / "review-mcp-activation").mkdir(parents=True)

    distribution = {
        "schema_version": 1,
        "name": f"naio-{slug}",
        "version": VERSION,
        "description": f"Governed, inactive-by-default {role['label']} MCP companion for {role['product']}.",
        "author": "NAIO",
        "license": "Apache-2.0",
        "hermes_requires": HERMES_REQUIRES,
        "mapping": {
            "classification": role["mapping_classification"],
            "condition": role["mapping_condition"],
        },
    }
    profile_yaml = {
        "name": f"naio-{slug}",
        "description": distribution["description"],
        "mapping": distribution["mapping"],
        "version": VERSION,
    }
    servers = {name: server_config(name, role) for name in role["servers"]}
    config = {
        "terminal": {"home_mode": "profile"},
        "approvals": {
            "mode": "manual",
            "timeout": 60,
            "cron_mode": "deny",
            "mcp_reload_confirm": True,
            "destructive_slash_confirm": True,
        },
        "security": {
            "allow_private_urls": False,
            "redact_secrets": True,
            "tirith_enabled": True,
            "tirith_path": "tirith",
            "tirith_timeout": 5,
            "tirith_fail_open": False,
            "allow_lazy_installs": False,
        },
        "mcp_servers": servers,
    }

    # JSON is valid YAML 1.2 and keeps this static publication builder dependency-free.
    write_text(profile / "distribution.yaml", json.dumps(distribution, indent=2, sort_keys=True))
    write_text(profile / "profile.yaml", json.dumps(profile_yaml, indent=2, sort_keys=True))
    write_text(profile / "config.yaml", json.dumps(config, indent=2, sort_keys=True))
    write_text(profile / "mcp.json", json.dumps({"servers": servers}, indent=2, sort_keys=True))
    role_policy = (
        "Candidate coordinates only; not an executable transitive lock. "
        "The profile uses a guaranteed-missing blocker command. Activation remains BLOCKED until a "
        "separately reviewed runtime consumes a complete dependency lock."
    )
    if "github" in role["servers"]:
        role_policy += " The remote GitHub service is not code-pinnable and requires fresh review."
    role_lock = {
        "schema_version": "1.0",
        "audited_at": "2026-07-26",
        "mapping": distribution["mapping"],
        "policy": role_policy,
        "dependencies": {
            name: DEPENDENCIES[DEPENDENCY_LOCK_KEYS.get(name, name)]
            for name in role["servers"]
        },
    }
    write_text(profile / "MCP-SUPPLY-CHAIN-LOCK.json", json.dumps(role_lock, indent=2, sort_keys=True))
    write_text(profile / "SOUL.md", render_soul(slug, role))
    write_text(profile / "README.md", render_readme(slug, role))
    write_text(profile / "MCP-ACTIVATION-CARD.md", render_card(slug, role))
    write_text(profile / "skills" / "review-mcp-activation" / "SKILL.md", render_skill(slug, role))
    env_template = "# Copy only after a separately approved MCP activation. Never publish real values.\n"
    env_template += "\n".join(f"{key}=" for key in env_keys(role["servers"]))
    write_text(profile / ".env.template", env_template)


MAX_ARCHIVE_UNCOMPRESSED_BYTES = 10 * 1024 * 1024
MAX_MEMBER_EXPANSION_RATIO = 100


def read_regular_source_file(root: Path, relative: Path) -> bytes:
    if relative.is_absolute() or not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
        raise ValueError(f"Unsafe relative source path: {relative}")
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise RuntimeError("Descriptor-relative no-follow source reads are unavailable")
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    file_flags = os.O_RDONLY | os.O_NOFOLLOW
    descriptors: list[int] = []
    try:
        try:
            descriptors.append(os.open(root, directory_flags))
            for part in relative.parts[:-1]:
                descriptors.append(os.open(part, directory_flags, dir_fd=descriptors[-1]))
                if not stat.S_ISDIR(os.fstat(descriptors[-1]).st_mode):
                    raise ValueError(f"Non-directory source path component prohibited: {relative}")
            descriptors.append(os.open(relative.parts[-1], file_flags, dir_fd=descriptors[-1]))
        except OSError as exc:
            raise ValueError(f"Unable to open regular source file beneath its root: {root / relative}") from exc
        descriptor = descriptors[-1]
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError(f"Non-regular source entry prohibited: {root / relative}")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            return handle.read()
    finally:
        for opened in reversed(descriptors):
            os.close(opened)


def validate_source_tree(slug: str) -> list[Path]:
    profile = SOURCE / slug
    if profile.is_symlink() or not profile.is_dir():
        raise ValueError(f"Profile source root must be a real directory: {profile}")
    files: list[Path] = []
    for path in sorted(profile.rglob("*")):
        mode = path.lstat().st_mode
        if path.is_symlink():
            raise ValueError(f"Source symlink prohibited: {path}")
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise ValueError(f"Non-regular source entry prohibited: {path}")
        files.append(path)
    if not files:
        raise ValueError(f"Profile source tree is empty: {profile}")
    return files


def validate_archive(archive_path: Path, slug: str, expected_members: int) -> None:
    profile = SOURCE / slug
    expected_root = f"naio-{slug}-hermes-profile-v{VERSION}"
    expected_names = {
        f"{expected_root}/{path.relative_to(profile).as_posix()}"
        for path in validate_source_tree(slug)
    }
    with zipfile.ZipFile(archive_path) as archive:
        infos = archive.infolist()
        if len(infos) != expected_members:
            raise ValueError(f"Member count mismatch: {archive_path}")

        seen: set[str] = set()
        normalized_seen: set[str] = set()
        total_uncompressed = 0
        for info in infos:
            name = info.filename
            raw_name = info.orig_filename
            parts = PurePosixPath(name).parts
            normalized_name = "/".join(parts)
            collision_key = unicodedata.normalize("NFC", normalized_name).casefold()
            if (
                not name
                or raw_name != name
                or "\x00" in raw_name
                or "\x00" in name
                or "\\" in name
                or name.startswith("/")
                or name.endswith("/")
                or normalized_name != name
                or any(part in {"", ".", ".."} for part in parts)
                or (parts and ":" in parts[0])
                or not parts
                or parts[0] != expected_root
            ):
                raise ValueError(f"Unsafe or noncanonical ZIP member: {name!r}")
            if name in seen:
                raise ValueError(f"Duplicate ZIP member: {name}")
            if collision_key in normalized_seen:
                raise ValueError(f"Case/Unicode-colliding ZIP member: {name}")
            seen.add(name)
            normalized_seen.add(collision_key)
            if info.flag_bits & 0x1:
                raise ValueError(f"Encrypted ZIP member prohibited: {name}")
            if info.compress_type != zipfile.ZIP_DEFLATED:
                raise ValueError(f"Unexpected compression method: {name}")
            if info.date_time != FIXED_ZIP_TIME:
                raise ValueError(f"Nondeterministic ZIP timestamp: {name}")
            mode = (info.external_attr >> 16) & 0o177777
            if info.is_dir() or mode != stat.S_IFREG | 0o644:
                raise ValueError(f"Unsafe ZIP mode: {name}")
            total_uncompressed += info.file_size
            if info.file_size and info.compress_size == 0:
                raise ValueError(f"Invalid zero compressed size: {name}")
            if info.compress_size and info.file_size / info.compress_size > MAX_MEMBER_EXPANSION_RATIO:
                raise ValueError(f"ZIP expansion ratio too high: {name}")

        if total_uncompressed > MAX_ARCHIVE_UNCOMPRESSED_BYTES:
            raise ValueError(f"ZIP uncompressed size exceeds limit: {archive_path}")
        if seen != expected_names:
            raise ValueError(f"ZIP member set mismatch: {archive_path}")

        # Read payloads only after every metadata/path/size check passes.
        if archive.testzip() is not None:
            raise ValueError(f"CRC failure: {archive_path}")
        for info in infos:
            relative = info.filename.split("/", 1)[1]
            if archive.read(info) != read_regular_source_file(profile, Path(relative)):
                raise ValueError(f"ZIP/source mismatch: {info.filename}")


def build_zip(slug: str) -> dict[str, Any]:
    profile = SOURCE / slug
    filename = f"naio-{slug}-hermes-profile-v{VERSION}.zip"
    output = DOWNLOADS / filename
    root_name = filename.removesuffix(".zip")
    files = validate_source_tree(slug)
    staged = output.with_name(f".{filename}.staged")
    staged.unlink(missing_ok=True)
    try:
        with zipfile.ZipFile(staged, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in files:
                relative = path.relative_to(profile).as_posix()
                info = zipfile.ZipInfo(f"{root_name}/{relative}", FIXED_ZIP_TIME)
                info.create_system = 3
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                archive.writestr(
                    info,
                    read_regular_source_file(profile, path.relative_to(profile)),
                    compress_type=zipfile.ZIP_DEFLATED,
                    compresslevel=9,
                )
        validate_archive(staged, slug, len(files))
        staged.replace(output)
    finally:
        staged.unlink(missing_ok=True)
    return {
        "activation_readiness": "blocked_pending_complete_transitive_lock_and_lock_consuming_runtime",
        "profile": slug,
        "role": ROLES[slug]["label"],
        "lane": ROLES[slug]["lane"],
        "mapped_product": ROLES[slug]["product"],
        "mapping_classification": ROLES[slug]["mapping_classification"],
        "mapping_condition": ROLES[slug]["mapping_condition"],
        "filename": filename,
        "download": f"downloads/{filename}",
        "version": VERSION,
        "bytes": output.stat().st_size,
        "sha256": sha256(output),
        "members": len(files),
        "install_on_download": False,
        "mcp_enabled_by_default": False,
        "mcp_tools_exposed_by_default": 0,
        "activation": "separate_explicit_post_card_approval",
        "status": "published_inactive_companion_not_installed_not_connected",
    }


def write_publication_metadata(records: list[dict[str, Any]]) -> None:
    lock = {
        "schema_version": "1.0",
        "audited_at": "2026-07-26",
        "policy": "No upstream code is vendored. Coordinates are non-executable candidate evidence, not a transitive lock. Every MCP uses a guaranteed-missing blocker command, is disabled, uses a nonmatching deny-sentinel tool allowlist, and has resources, prompts, sampling, and elicitation off. Activation is BLOCKED until a reviewed runtime consumes a complete dependency lock.",
        "dependencies": DEPENDENCIES,
    }
    mapping = {
        "schema_version": "1.0",
        "mappings": [
            {
                "profile": slug,
                "role": role["label"],
                "lane": role["lane"],
                "product": role["product"],
                "mapping_classification": role["mapping_classification"],
                "mapping_condition": role["mapping_condition"],
                "relationship": "optional_mcp_profile_companion_subordinate_to_build_kit_governance",
                "activation": "separate_explicit_post_card_approval",
                "activation_readiness": "blocked_pending_complete_transitive_lock_and_lock_consuming_runtime",
            }
            for slug, role in ROLES.items()
        ],
    }
    manifest = {
        "schema_version": "1.0",
        "release": "2026.07.26.1",
        "installation_status": "not_installed",
        "mcp_default_state": "all_disabled_zero_tools",
        "profiles": records,
    }
    write_text(ROOT / "MCP-SUPPLY-CHAIN-LOCK.json", json.dumps(lock, indent=2, sort_keys=True))
    write_text(ROOT / "ROLE-DOWNLOAD-MAP.json", json.dumps(mapping, indent=2, sort_keys=True))
    write_text(ROOT / "manifest.json", json.dumps(manifest, indent=2, sort_keys=True))
    write_text(
        ROOT / "CHECKSUMS.sha256",
        "\n".join(f"{record['sha256']}  downloads/{record['filename']}" for record in records),
    )
    write_text(
        ROOT / "README.md",
        """# Governed Hermes MCP role-profile companions

Seven role-mapped Hermes profile distributions derived from the supplied Nurse AI OS packet research. The original packets were treated as untrusted inputs and were not published unchanged.

Downloading or unzipping does not install, connect, or activate anything. Every MCP is disabled and exposes zero tools by default. Profile installation requires an exact pre-installation card and explicit approval. Each MCP activation then requires its own separate exact card and fresh approval.

## Publication corrections

- Added current Hermes `distribution.yaml` manifests and compatibility floor.
- Replaced floating npm, PyPI, and GitHub-main coordinates with exact versions or commits.
- Marked the GitHub remote MCP as a non-pinnable remote service and kept it disabled.
- Disabled lazy installs, requested Tirith fail-closed behavior, documented Hermes 0.19's circuit-breaker caveat, and isolated external-CLI home state per profile. Tirith is defense in depth, not the activation gate.
- Removed real-case/de-identification workflows and replaced them with rejection-before-processing boundaries.
- Removed nonexistent Hermes command references and required current `hermes ... mcp configure` review.
- Kept every server disabled with a nonmatching deny-sentinel allowlist and MCP resources, prompts, sampling, and elicitation off until separate human approval.
- Replaced executable package resolution with a guaranteed-missing blocker command. Top-level coordinates remain review evidence only; activation is blocked until a complete transitive lock and lock-consuming runtime are approved.

See `SOURCE-PROVENANCE.json`, `MCP-SUPPLY-CHAIN-LOCK.json`, `ROLE-DOWNLOAD-MAP.json`, `manifest.json`, and `CHECKSUMS.sha256`.

Hermes 0.19 caveat: `tirith_fail_open: false` blocks ordinary Tirith spawn failures and timeouts, but Hermes' scanner-crash circuit breaker can later allow commands after repeated scanner crashes. Do not rely on Tirith as the sole control; the missing runtime command, disabled server state, deny sentinel, and explicit activation review remain authoritative.
""",
    )


def source_provenance(upstream: Path) -> dict[str, Any]:
    roles: dict[str, Any] = {}
    for slug in ROLES:
        upstream_role = upstream / slug
        try:
            role_mode = upstream_role.lstat().st_mode
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(role_mode) or not stat.S_ISDIR(role_mode):
            raise ValueError(f"Provenance role root must be a real directory: {upstream_role}")
        files = {}
        for path in sorted(upstream_role.rglob("*")):
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise ValueError(f"Provenance source symlink prohibited: {path}")
            if stat.S_ISREG(mode):
                data = read_regular_source_file(upstream_role, path.relative_to(upstream_role))
                files[path.relative_to(upstream).as_posix()] = {
                    "bytes": len(data),
                    "sha256": sha256_bytes(data),
                }
            elif not stat.S_ISDIR(mode):
                raise ValueError(f"Provenance source special entry prohibited: {path}")
        roles[slug] = files
    return {
        "schema_version": "1.0",
        "source_locator": "THE_NEW_DIRECTIVE/Research/Nurse AI OS Packets",
        "source_available_in_ci": False,
        "audit_date": "2026-07-26",
        "treatment": "untrusted_research_input_governed_derivative_not_byte_copy",
        "critical_corrections": [
            "floating_dependencies_pinned",
            "mcp_disabled_and_zero_tools_by_default",
            "lazy_installs_disabled",
            "tirith_fail_closed_requested_with_v019_circuit_breaker_caveat",
            "real_case_and_deidentification_workflows_removed",
            "nonexistent_commands_removed",
            "separate_profile_install_and_per_mcp_activation_cards_added",
        ],
        "upstream_roles": roles,
    }


def verify_archives(records: list[dict[str, Any]]) -> None:
    for record in records:
        archive_path = DOWNLOADS / record["filename"]
        validate_archive(archive_path, record["profile"], record["members"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-provenance", action="store_true")
    parser.add_argument("--source", type=Path, help="Local authoritative packet folder used only for provenance refresh")
    args = parser.parse_args()

    ROOT.mkdir(parents=True, exist_ok=True)
    SOURCE.mkdir(parents=True, exist_ok=True)
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    for slug, role in ROLES.items():
        write_profile(slug, role)

    provenance_path = ROOT / "SOURCE-PROVENANCE.json"
    if args.refresh_provenance or not provenance_path.exists():
        if args.source is None:
            raise ValueError("--source is required when creating or refreshing provenance")
        provenance = source_provenance(args.source.resolve())
        if len(provenance["upstream_roles"]) != len(ROLES):
            raise ValueError("All seven upstream roles are required to refresh provenance")
        write_text(provenance_path, json.dumps(provenance, indent=2, sort_keys=True))

    records = [build_zip(slug) for slug in ROLES]
    write_publication_metadata(records)
    verify_archives(records)
    print(f"HERMES_ROLE_PROFILES_OK profiles={len(records)} all_mcp_disabled=true tools_exposed=0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
