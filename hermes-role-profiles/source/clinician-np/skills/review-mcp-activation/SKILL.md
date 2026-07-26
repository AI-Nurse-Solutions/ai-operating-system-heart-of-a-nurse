---
name: review-mcp-activation
description: Perform read-only preflight for the clinician-np profile or one MCP candidate and produce the exact required card without installing, authenticating, connecting, or enabling anything.
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
