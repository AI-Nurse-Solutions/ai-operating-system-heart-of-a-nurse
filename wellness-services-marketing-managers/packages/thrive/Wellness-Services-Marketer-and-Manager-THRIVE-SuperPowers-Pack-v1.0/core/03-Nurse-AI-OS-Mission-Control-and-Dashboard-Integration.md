# Nurse AI OS Mission Control & Dashboard Integration

## Canonical location and source of truth

`My THRIVE Mission Control` is an accessible Markdown dashboard at `/wellness-services-marketing-managers/dashboard`; `/wellness-services-marketing-managers/mission-control` is an alias to the same dashboard state, never a copy. `/wellness-services-marketing-managers` redirects only to `/wellness-services-marketing-managers/dashboard` after S2; it never redirects to a global or another population's `/dashboard`. If rich rendering fails, Markdown is the canonical fallback and source of truth. If Hermes supports a self-contained responsive local HTML artifact, it may render the same schema and launcher bindings only after dashboard tests pass; it must contain no remote script, tracker, network call or independent state.

Parent Nurse AI OS Mission Control shows a single **THRIVE** navigation/status card and deep link. It may show only product/version and coarse state after explicit approval. No campaign, audience, service, relationship, financial, personal or agent data crosses to the parent.

## Embedded wireframe

```text
┌────────────────────── My THRIVE Mission Control ──────────────────────┐
│ Context: Private / Approved Aggregate     Hat: [verify]   S2: [state] │
│ Permanent controls: CLAIM | Consent/Rights | Privacy/Data | Sources   │
│ Human Approval Queue | SEND/SPEND/PUBLISH OFF | Agents/Kill | Pause   │
├───────────────────────────────────────────────────────────────────────┤
│ FOCUS — maximum 7, each with source · owner · due · state · safe exit │
│ 1 [question]  2 [question]  3 [question] ...                         │
├────────────────────────── LAUNCHERS ──────────────────────────────────┤
│ [Ground Truth & Offer]       [Reach & Relationships]                 │
│ [Run Services & Campaigns]   [Learn, Govern & Grow]                  │
│ [Optional fifth slot — empty until human configured]                 │
├───────────────────────────────────────────────────────────────────────┤
│ Claims needing review | Content expiry | Service/team capacity/SOP   │
│ Experiments/learning  | Source freshness | Agent registry (all P0)   │
│ Tamper-evident receipts | Pause · Reset View · Export Off · Uninstall  │
└───────────────────────────────────────────────────────────────────────┘
```

## Launcher binding contract

| Launcher | Bound workflows | Allowed inputs | Permission/state | Human gate | Receipt | Expiry | Failure/rollback and safe exit |
|---|---|---|---|---|---|---|---|---|
| Ground Truth & Offer | WF-01–WF-06, WF-17 and WF-19 | Public/synthetic or approved aggregate service facts and sources | Preview only; agents P0 | CLAIM + named claim/service owner | Input/source/version + gate + decision | Source/claim expiry | Block, save draft, discard or route; never publish |
| Reach & Relationships | WF-08–WF-12 | Approved organization facts and coarse aggregate insight | Preview only; agents P0 | CHART + CLAIM + relationship owner | Partition + role + commitment/decision | Plan review date | Stop, purge working copy or route; never contact |
| Run Services & Campaigns | WF-13–WF-16 and WF-20 | Approved brief, content metadata, aggregate service/team capacity, RACI/SOP refs and approved claim refs | Preview only; agents P0 | CLAIM + ALIGN + service/team/release-owner queue | Workflow steps + gates + owner + state | Campaign/asset/SOP expiry | Pause, roll back draft and reconcile; no launch/send/spend/assignment |
| Learn, Govern & Grow | WF-07, WF-18 and WF-21–WF-24 | Approved aggregate measures, sources, synthetic tests and private goals only in isolated store | Preview only; agents P0 | CHART; ORBIT for agents; owner-only for private | Evidence + human decision + kill/expiry state | Review/delete date | Reject, kill, roll back, purge or retire |
| Optional fifth | None | None | Empty Disabled | New governed binding required | No receipt until separately designed | N/A | Remains empty |

A launch button opens a form/workflow preview; it is not an automation trigger. Each binding records input class, source, owner, version, state, human checkpoint, expiry and safe exit. A button cannot invoke an agent above P0, call an API, send, publish, spend, book, write or create a lead.

## Focus and attention rules

Show **no more than seven attention items**. Deterministic order is: blocked/expired human decisions first; earliest due timestamp second; immutable `attention_item_id` ascending as the final tie-breaker. Never rank people, inferred urgency or engagement likelihood. The order must remain byte-stable across render, resume and Markdown/HTML fallback. Every item shows ID, source/freshness, named owner, exact question, due/expiry, state and close/escalate path. No silent carry-forward.

## Accessibility and resilience

Meet the operator's declared WCAG target; semantic headings/table labels; keyboard-only operation; visible focus; skip link; 44×44 target intent; text equivalents; sufficient contrast; zoom/reflow; plain language; no color-only meaning; reduced motion honored; no auto-advance, flashing or timed disappearance. Dashboard failure falls back to canonical Markdown. Reset View changes presentation only. Pause stops proposed work. Uninstall exports only explicitly approved nonsensitive records, purges eligible THRIVE state and leaves other lanes untouched. If an authorized external legal/records hold applies, THRIVE must report exact retained record refs, owner, authority source, ACL and release condition and state `UNINSTALL_INCOMPLETE_AUTHORIZED_HOLD`; it must never claim total purge.
