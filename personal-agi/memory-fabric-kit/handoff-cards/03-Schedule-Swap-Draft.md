# Handoff Card — Schedule-Swap Draft

When you need a shift covered, your AI drafts the request — the dates, the framing, the fallback options — and stops. Sending is yours, always. This card exists to remove the composing burden, not the asking.

| Field | Value |
|---|---|
| **Sphere** | professional (non-clinical) |
| **EDENA risk tier** | Green — posture ceiling: Draft |
| **Action mode** | Draft (this card does not promote past Draft in v0.1) |
| **Data class** | D1 |
| **What the AI does** | From your schedule notes and the constraint you give it ("need the 22nd off, can cover the 25th or 26th"), drafts the swap request in your voice: the specific ask, what you're offering in return, and a graceful line if the answer is no. Saves the draft; you copy it into whatever channel your unit uses. |
| **What the AI never does** | Send the message, post to any scheduling system or group chat, contact a colleague, or reference why you need the day beyond what you explicitly wrote. It never mentions colleagues' circumstances, staffing levels, or anything unit-internal. |
| **Accounts/credentials touched** | None. It drafts text; it doesn't hold the channel. |
| **Stop conditions** | Universal list, plus: if your stated reason for the swap includes anything patient- or unit-sensitive, it halts immediately — no draft, and the reason is neither processed further nor logged — and asks you to restart with a non-sensitive framing. |
| **Evidence log** | `Memory/spheres/professional/swap-drafts/` — one file per draft, including the version you actually sent if you edited it. |
| **Revoke** | Record `REVOKED: Schedule-Swap Draft` in the trust ledger, tell your AI the card is revoked, then delete the card. |

## Why this card is capped at Draft

The message crosses into other people's time and goodwill — a social action, not a filing action. v0.1 keeps every social action fully human. If a future version proposes otherwise, that's a DESIGN.md amendment conversation, not a ledger promotion.

## Prompt seed

> Per handoff card 03, draft a swap request: I need [date] covered and can offer [dates]. My voice, brief and warm, with a no-pressure out. Draft only — I'll send it myself.
