# NIN Knowledge Commons

> **Status: proposed architecture and operating doctrine, version 0.1.** This directory specifies a future governed knowledge fabric. It does not establish an operating service, school partnership, reviewer council, marketplace, hosted RAG system, institutional authorization, clinical validation, certification, or permission to process PHI.

The proposed public umbrella is **NIN Knowledge Commons**. The internal architecture is the **Nurse AI OS Knowledge Fabric**: one federated fabric distributed as portable, versioned Knowledge Packs and discovered through a thin shared registry.

## Documents

- [Doctrine](DOCTRINE.md) — constitutional principles, authority boundaries, scope, risk posture, ownership, retrieval, graph, hosting, and commerce rules.
- [Operational Playbook](PLAYBOOK.md) — the contribution, review, publication, localization, retrieval, incident, pilot, and staged implementation procedures.

## Foundational architecture

```text
Learn     → student, subject, school, and locality libraries
Practice  → specialty, unit, department, and professional libraries
Lead      → leadership, management, educator, and wisdom libraries
Build     → dashboards, designs, simulations, and creator showcase
```

All four lanes use one package and governance standard. They are views over the same fabric, not four incompatible databases.

> **Content packages are the source of truth. Search, vector, and graph indexes are disposable derivatives.**

> **Contributors propose. Reviewers verify. Institutions authorize. Nurses steward.**

> **Inclusion means available for governed use—not endorsement, certification, clinical validation, institutional authorization, or permission to change practice.**

## Relationship to Nurse AI OS

- **NIN** develops community and contributor participation.
- **NAIO** develops standards, review rules, registry governance, and future marketplace governance.
- **Nurse AI OS** is the local workspace where users may inspect, install, search, adapt, and combine explicitly authorized packs.
- **Hermes** may retrieve from user-authorized libraries while preserving source, version, review, and limitation information.
- **Florence-X** may route among permitted libraries and editions when that capability is implemented and evidenced.
- **EDENA** governs data class, risk, publication, retrieval, permitted use, and stop conditions.
- **SOUL** may personalize discovery by role, locality, language, specialty, context, and mission; it may not override access, risk, evidence, or institutional rules.

## Current implementation status

As of this version:

- the doctrine and playbook are documented;
- no separate Commons repository or hosted catalog has been created by these documents;
- no Knowledge Pack schema, registry, ingestion service, RAG index, graph database, school tenant, creator payment system, or native marketplace is made operational by these documents;
- MCP, connectors, external actions, PHI processing, clinical decision support, competency scoring, and institutional integrations remain outside this documentation change.

## Related implementation evidence

Several retrieval principles in this doctrine already have a tested reference implementation in this repository's [Integration Contract](../naio-integrations/): governed retrieval that refuses to answer without an indexed source and preserves per-passage provenance and warnings; an evidence ledger in which source-backed claims require citations that exist ("no citation, no claim"); tenant-scoped stores whose foreign reads fail closed; and synthetic teaching content that always retrieves with an explicit warning, ranked after policy, local practice, and research. That code is reference implementation evidence for the direction — it is not the Commons, a catalog, or a hosted retrieval service.

## Authority and precedence

These documents are subordinate to applicable law, professional duties, institutional policy, the current NIN–NAIO Master Directive, repository governance, EDENA requirements, and artifact-specific licenses. Where a conflict exists, the more protective applicable authority controls.

## Licensing note

This doctrine and playbook are repository documentation and follow the documentation license stated in the root [README](../README.md). Future Knowledge Packs do **not** inherit one blanket license merely because they are listed in the Commons. Every pack and every third-party component must carry an explicit artifact-specific license and rights record.
