# Standalone Healthcare Research & Innovation Leadership Lane

| Contract | Exact value |
|---|---|
| Product | DISCOVER — Healthcare Research & Innovation Leader Complete AI OS |
| Product ID | `HRIL-AIOS-DISCOVER-COMPLETE-1.0` |
| Foundation / overlay | `HRIL-AIOS-LIFE-LEADERSHIP-1.0` / `HRIL-AIOS-DISCOVER-1.0` |
| Lane | `healthcare_research_innovation_leadership` |
| Root / dashboard | `/healthcare-research-innovation-leaders` / `/healthcare-research-innovation-leaders/dashboard` |
| Only alias | `/healthcare-research-innovation-leaders/mission-control` |
| Namespace | `research_innovation_discover.*` |
| Home | My DISCOVER Mission Control |

No global `/dashboard` or `/mission-control` route is registered. The lane root may redirect only to its fully qualified dashboard after route verification. Exact partitions are `research_innovation_discover.tenant.<tenant_id>.governance`, `research_innovation_discover.tenant.<tenant_id>.portfolio`, `research_innovation_discover.tenant.<tenant_id>.evidence`, `research_innovation_discover.tenant.<tenant_id>.sandbox`, `research_innovation_discover.tenant.<tenant_id>.controls` and optional `research_innovation_discover.private.owner.<owner_id>`. References are typed, versioned, partition-bound and hash-bound; they do not grant dereference permission. Every cross-partition request blocks before lookup or dereference with zero field disclosure.

Source applicability records keep authority type, legal status, stability status and current-version status separate from jurisdiction, actor/product/setting scope, effective/compliance dates, supersession, local precedence, reviewer and expiry.

The parent Nurse AI OS card may display only product/version, coarse state (`INSTALLED`, `NEEDS_ATTENTION`, `PAUSED`, `QUARANTINED`) and the lane deep link after explicit approval. It receives no study titles, research questions, partners, findings, IP/funding details, private goals, agent traces, permissions, memory or underlying state.
